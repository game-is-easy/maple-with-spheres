import Foundation
import ScreenCaptureKit
import CoreGraphics
import ImageIO
import VideoToolbox
import UniformTypeIdentifiers
import AppKit

private let BUILD_ID = "CaptureServer build 2026-01-16-fallback-v1"

private let ENABLE_DEBUG = false

@inline(__always) func logDebug(_ msg: String) {
    if ENABLE_DEBUG {
        logErr(msg)
    }
}

@inline(__always) func logErr(_ msg: String) {
    fputs(msg + "\n", stderr)
    fflush(stderr)
}

final class CaptureServer: NSObject, SCStreamOutput, SCStreamDelegate, @unchecked Sendable {
    private var latestBuffer: CMSampleBuffer?
    private var latestSeq: Int64 = 0
    private var lastSentSeq: Int64 = 0
    private var stream: SCStream?
    private var contentFilter: SCContentFilter?
    private var baseWindowFrame: CGRect = .zero

    private let semaphore = DispatchSemaphore(value: 0)
    private let bufferQueue = DispatchQueue(label: "com.capture.buffer")

    private var hasStarted = false
    private var startTime = Date()

    // 1) Find the window and start the stream
    func start(windowTitle: String) async {
        logErr("STARTING")
        logErr(BUILD_ID)

        // Ensure Screen Recording permission is granted (otherwise startCapture can stall indefinitely).
        if !CGPreflightScreenCaptureAccess() {
            logErr("Screen Recording permission not granted. Requesting access...")
            _ = CGRequestScreenCaptureAccess()

            // Poll briefly to see if permission becomes available.
            for _ in 0..<60 {
                if CGPreflightScreenCaptureAccess() { break }
                try? await Task.sleep(nanoseconds: 500_000_000)
            }

            if !CGPreflightScreenCaptureAccess() {
                logErr("Error: Screen Recording permission still not granted. Enable it in System Settings > Privacy & Security > Screen Recording for the app launching CaptureServer, then restart that app.")
                exit(1)
            }
        }

        do {
            let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: false)
            logErr("GOT_SHAREABLE_CONTENT")

            guard let window = content.windows.first(where: { ($0.title ?? "").contains(windowTitle) }) else {
                logErr("Error: Window '\(windowTitle)' not found")
                exit(1)
            }
            logErr("FOUND_WINDOW")
            self.baseWindowFrame = window.frame

            let filter = SCContentFilter(desktopIndependentWindow: window)
            self.contentFilter = filter

            let config = SCStreamConfiguration()
            // Request device-pixel output using the filter's point-to-pixel scale.
            let scale = CGFloat(filter.pointPixelScale)
            config.width = Int((window.frame.width * scale).rounded())
            config.height = Int((window.frame.height * scale).rounded())
            config.minimumFrameInterval = CMTime(value: 1, timescale: 15) // Limit to ~15fps
            config.queueDepth = 1

            stream = SCStream(filter: filter, configuration: config, delegate: self)
            try stream?.addStreamOutput(self, type: .screen, sampleHandlerQueue: DispatchQueue(label: "com.capture.fps", qos: .utility))
            logErr("ADDED_OUTPUT")
            logErr("STARTCAPTURE_BEGIN")

            // Hard timeout using GCD so we don't depend on Swift concurrency scheduling if startCapture wedges.
            DispatchQueue.global(qos: .userInitiated).asyncAfter(deadline: .now() + 12) { [weak self] in
                guard let self else { return }
                var started = false
                self.bufferQueue.sync { started = self.hasStarted }
                if !started {
                    logErr("Error starting stream: startCapture() hard-timeout (12s)")
                    logErr("Hint: This usually indicates TCC/permission identity issues with the CaptureServer binary or that ScreenCaptureKit requires being run from an app bundle.")
                    exit(1)
                }
            }

            let startCaptureTask = Task { @MainActor in
                try await self.stream?.startCapture()
            }

            try await withThrowingTaskGroup(of: Void.self) { group in
                group.addTask { _ = try await startCaptureTask.value }
                group.addTask {
                    try await Task.sleep(nanoseconds: 10_000_000_000) // 10s
                    throw NSError(domain: "CaptureServer", code: 2, userInfo: [NSLocalizedDescriptionKey: "startCapture() timed out"])
                }

                _ = try await group.next()
                group.cancelAll()
            }

            logErr("STARTCAPTURE_OK")
            self.startTime = Date()
            logErr("READY")
            self.hasStarted = true
        } catch {
            logErr("Error starting stream: \(error)")
            exit(2)
        }
    }

    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of type: SCStreamOutputType) {
        if type == .screen {
            bufferQueue.async {
                self.latestBuffer = sampleBuffer
                self.latestSeq &+= 1
                if self.latestSeq <= 5 || self.latestSeq % 30 == 0 {
                    let dt = Date().timeIntervalSince(self.startTime)
                    logDebug(String(format: "FRAME_SEQ=%lld t=%.3fs", self.latestSeq, dt))
                }
                self.semaphore.signal()
            }
        }
    }

    // MARK: - SCStreamDelegate (optional; may not fire on older macOS versions)
    func streamDidBecomeActive(_ stream: SCStream) { logErr("STREAM_ACTIVE") }
    func streamDidBecomeInactive(_ stream: SCStream) { logErr("STREAM_INACTIVE") }
    func stream(_ stream: SCStream, didStopWithError error: Error) { logErr("STREAM_STOP_ERROR: \(error)") }

    /// Send a JPEG frame.
    /// - Parameter region: Optional crop rect in *pixel* coordinates, with origin at the TOP-LEFT of the captured window.
    func sendFrame(region: CGRect? = nil) async {
        if !hasStarted {
            var bytes = Int64(-1)
            FileHandle.standardOutput.write(Data(bytes: &bytes, count: 8))
            return
        }

        // Try stream path first.
        var buffer: CMSampleBuffer?
        var seq: Int64 = 0
        bufferQueue.sync { buffer = self.latestBuffer; seq = self.latestSeq }

        if seq != 0 && seq == lastSentSeq {
            // Fast path: don't stall the caller if the stream isn't producing new frames.
            // Wait only a tiny amount (one tick) to give the stream a chance, then fall back.
            try? await Task.sleep(nanoseconds: 5_000_000) // 5ms
            bufferQueue.sync { buffer = self.latestBuffer; seq = self.latestSeq }
        }

        if seq != 0 && seq != lastSentSeq,
           let buffer,
           let imageBuffer = CMSampleBufferGetImageBuffer(buffer) {

            lastSentSeq = seq
            if seq <= 5 || seq % 30 == 0 {
                let dt = Date().timeIntervalSince(self.startTime)
                logDebug(String(format: "SEND_SEQ=%lld t=%.3fs", seq, dt))
            }

            var cgImage: CGImage?
            VTCreateCGImageFromCVPixelBuffer(imageBuffer, options: nil, imageOut: &cgImage)

            if let cgImage {
                writeJPEG(cgImage: cgImage, region: region)
                return
            }
        }

        // Debug: we are about to use the fallback path because the stream did not produce a new frame.
        logDebug("USING_FALLBACK_PATH")

        // Fallback: on-demand capture (works even if streaming only delivers a single frame).
        guard let filter = self.contentFilter else {
            var bytes = Int64(-1)
            FileHandle.standardOutput.write(Data(bytes: &bytes, count: 8))
            return
        }

        let cfg = SCStreamConfiguration()
        cfg.width = Int((baseWindowFrame.width * CGFloat(filter.pointPixelScale)).rounded())
        cfg.height = Int((baseWindowFrame.height * CGFloat(filter.pointPixelScale)).rounded())
        cfg.scalesToFit = false
        logDebug("FALLBACK_CFG size=\(cfg.width)x\(cfg.height) scale=\(filter.pointPixelScale)")

        let captured: CGImage? = await withCheckedContinuation { cont in
            SCScreenshotManager.captureImage(contentFilter: filter, configuration: cfg) { image, error in
                if let error { logErr("SCREENSHOT_ERROR: \(error)") }
                cont.resume(returning: image)
            }
        }

        guard let screenshot = captured else {
            var bytes = Int64(-1)
            FileHandle.standardOutput.write(Data(bytes: &bytes, count: 8))
            return
        }

        logDebug("FALLBACK_SCREENSHOT")
        writeJPEG(cgImage: screenshot, region: region)
    }

    private func writeJPEG(cgImage: CGImage, region: CGRect?) {
        let outImage: CGImage
        if let region {
            let fullW = cgImage.width
            let fullH = cgImage.height

            var x = Int(region.origin.x.rounded(.down))
            var yTop = Int(region.origin.y.rounded(.down))
            var w = Int(region.size.width.rounded(.down))
            var h = Int(region.size.height.rounded(.down))

            if w <= 0 || h <= 0 {
                var bytes = Int64(-1)
                FileHandle.standardOutput.write(Data(bytes: &bytes, count: 8))
                return
            }

            x = max(0, min(x, fullW - 1))
            yTop = max(0, min(yTop, fullH - 1))
            w = min(w, fullW - x)
            h = min(h, fullH - yTop)

//             let yBottom = fullH - yTop - h
//             let cropRect = CGRect(x: x, y: yBottom, width: w, height: h)
            let cropRect = CGRect(x: x, y: yTop, width: w, height: h)

            guard let cropped = cgImage.cropping(to: cropRect) else {
                var bytes = Int64(-1)
                FileHandle.standardOutput.write(Data(bytes: &bytes, count: 8))
                return
            }
            outImage = cropped
        } else {
            outImage = cgImage
        }

        let data = NSMutableData()
        if let destination = CGImageDestinationCreateWithData(data as CFMutableData, UTType.jpeg.identifier as CFString, 1, nil) {
            CGImageDestinationAddImage(destination, outImage, nil)
            CGImageDestinationFinalize(destination)

            let length = data.length
            var bytes = Int64(length)
            FileHandle.standardOutput.write(Data(bytes: &bytes, count: 8))
            FileHandle.standardOutput.write(data as Data)
        } else {
            var bytes = Int64(-1)
            FileHandle.standardOutput.write(Data(bytes: &bytes, count: 8))
        }
    }
}

// --- Main Execution ---
_ = NSApplication.shared
NSApp.setActivationPolicy(.regular)
NSApp.activate(ignoringOtherApps: true)
logErr("APP_ACTIVATED")

let server = CaptureServer()
let windowName = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "Windows 11"

Task { await server.start(windowTitle: windowName) }

Task.detached {
    while let line = readLine() {
        let parts = line.split(separator: " ")
        guard let cmd = parts.first else { continue }

        if cmd == "GET" {
            Task { await server.sendFrame() }
        } else if cmd == "GETR" {
            if parts.count == 5,
               let x = Double(parts[1]),
               let y = Double(parts[2]),
               let w = Double(parts[3]),
               let h = Double(parts[4]) {
                Task { await server.sendFrame(region: CGRect(x: x, y: y, width: w, height: h)) }
            } else {
                var bytes = Int64(-1)
                FileHandle.standardOutput.write(Data(bytes: &bytes, count: 8))
            }
        } else if cmd == "EXIT" {
            exit(0)
        }
    }
}

RunLoop.main.run()