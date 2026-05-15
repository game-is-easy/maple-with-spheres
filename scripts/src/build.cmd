swiftc -O \
  -framework ScreenCaptureKit \
  -framework AppKit \
  -framework CoreGraphics \
  -framework VideoToolbox \
  -framework ImageIO \
  -framework UniformTypeIdentifiers \
  CaptureServer.swift \
  -o CaptureServer

strings ./CaptureServer | grep "CaptureServer build 2026-01-16-fallback-v1"

cp ./CaptureServer ./CaptureServer.app/Contents/MacOS/CaptureServer
chmod +x ./CaptureServer.app/Contents/MacOS/CaptureServer
codesign --force --deep --sign - ./CaptureServer.app

strings ./CaptureServer.app/Contents/MacOS/CaptureServer | grep "CaptureServer build 2026-01-16-fallback-v1"