import subprocess
import struct
import io
import time
import threading
import os
from typing import Optional, Tuple
from pathlib import Path

import cv2
import numpy as np

import atexit
import signal

THIS_DIR = Path(__file__).resolve().parent
CAPTURE_APP = (THIS_DIR / "CaptureServer.app" / "Contents" / "MacOS" / "CaptureServer").resolve()


class WindowStreamer:
    def __init__(self, binary_path=str(CAPTURE_APP), window_name="Windows 11"):
        self.process = subprocess.Popen(
            [binary_path, window_name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            text=False
        )

        self._ready_event = threading.Event()
        self._stderr_thread = None
        self._start_stderr_pump()

        # Wait (with timeout) for READY, but continue even if it never arrives.
        if not self._ready_event.wait(timeout=10.0):
            print("Warning: did not receive READY from Swift within timeout; continuing anyway.")

    def _start_stderr_pump(self):
        """Continuously print Swift stderr so we still see logs after READY wait times out."""
        def _pump():
            try:
                for raw in iter(self.process.stderr.readline, b""):
                    if not raw:
                        break
                    line = raw.decode(errors="ignore").rstrip("\n")
                    if line:
                        print(f"Swift Signal: {line}")
                        if "READY" in line or line.startswith("Error"):
                            self._ready_event.set()
            except Exception:
                pass

        t = threading.Thread(target=_pump, daemon=True)
        t.start()
        self._stderr_thread = t

    def _read_exact(self, n: int) -> bytes:
        """Read exactly n bytes from the process stdout (or return b'' if EOF)."""
        buf = bytearray()
        while len(buf) < n:
            chunk = self.process.stdout.read(n - len(buf))
            if not chunk:
                return b""
            buf.extend(chunk)
        return bytes(buf)

    def _request_jpeg(self, cmd: bytes) -> Optional[bytes]:
        """Send a command and return the JPEG payload bytes, or None."""
        # If the Swift process has exited, don't try to write to its stdin.
        if self.process.poll() is not None:
            return None

        if not self.process.stdin or not self.process.stdout:
            return None

        try:
            self.process.stdin.write(cmd)
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            return None

        header = self._read_exact(8)
        if not header:
            return None

        size = struct.unpack('q', header)[0]
        if size <= 0:
            return None

        payload = self._read_exact(size)
        if not payload:
            return None

        return payload

    def _jpeg_to_bgr(self, jpeg_bytes: bytes) -> Optional[np.ndarray]:
        """Decode JPEG bytes into an OpenCV-style BGR uint8 ndarray (H,W,3)."""
        arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img

    def get_frame(self) -> Optional[np.ndarray]:
        """Get a full-frame screenshot as a BGR uint8 ndarray (H,W,3)."""
        payload = self._request_jpeg(b"GET\n")
        if payload is None:
            return None
        return self._jpeg_to_bgr(payload)

    def get_frame_region(self, x: float, y: float, w: float, h: float) -> Optional[np.ndarray]:
        """Get a cropped screenshot region.

        Coordinates are in *pixel* coordinates with origin at the TOP-LEFT of the captured window,
        matching the Swift server's GETR implementation.
        Returns a BGR uint8 ndarray (h,w,3).
        """
        cmd = f"GETR {x} {y} {w} {h}\n".encode("utf-8")
        payload = self._request_jpeg(cmd)
        if payload is None:
            return None
        return self._jpeg_to_bgr(payload)

    def stop(self):
        if self.process.stdin:
            try:
                self.process.stdin.write(b"EXIT\n")
                self.process.stdin.flush()
            except Exception:
                pass

        try:
            self.process.terminate()
        except Exception:
            pass

        try:
            self.process.wait(timeout=2)
        except Exception:
            pass

        # If it is still alive, force kill as a fallback.
        if self.process.poll() is None:
            try:
                self.process.kill()
            except Exception:
                pass


# --- Shared Screenshot Provider ---

class ScreenshotProvider:
    """Shared screenshot provider.

    Keeps a single CaptureServer process alive and provides synchronous methods that return
    OpenCV-style BGR numpy arrays. Use one instance across your whole program.

    Thread safety: a lock is used so two callers don't interleave reads/writes on the same pipes.
    """

    def __init__(self, window_name: str = "Windows 11", binary_path: Optional[str] = None):
        self._lock = threading.Lock()
        self._streamer = WindowStreamer(binary_path=(str(CAPTURE_APP) if binary_path is None else binary_path), window_name=window_name)

    def grab_region(self, x: float, y: float, w: float, h: float) -> Optional[np.ndarray]:
        with self._lock:
            return self._streamer.get_frame_region(x, y, w, h)

    def grab(self, region=None) -> Optional[np.ndarray]:
        with self._lock:
            if region is None:
                return self._streamer.get_frame()
            else:
                return self._streamer.get_frame_region(*region)

    def close(self):
        with self._lock:
            self._streamer.stop()


def _shutdown_provider():
    global _provider_instance
    try:
        if _provider_instance is not None:
            _provider_instance.close()
    except Exception:
        pass
    finally:
        _provider_instance = None


# --- Singleton access ---

_provider_instance = None
_provider_lock = threading.Lock()


def get_screenshot_provider() -> ScreenshotProvider:
    global _provider_instance
    if _provider_instance is None:
        with _provider_lock:
            if _provider_instance is None:
                _provider_instance = ScreenshotProvider(window_name="Windows 11")

                # Best-effort cleanup on normal interpreter exit.
                atexit.register(_shutdown_provider)

                # Best-effort cleanup on Ctrl+C / SIGTERM (may not run if the IDE force-kills the process).
                for sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)):
                    if sig is None:
                        continue
                    try:
                        signal.signal(sig, lambda *_: (_shutdown_provider(), (_ for _ in ()).throw(SystemExit(0))))
                    except Exception:
                        pass
    return _provider_instance


# --- Example Usage ---
if __name__ == "__main__":
    provider = ScreenshotProvider(window_name="Windows 11")

    print("Capturing 10 full frames...")
    start_time = time.time()

    for i in range(10):
        frame = provider.grab()
        if frame is None:
            print(f"No frame available yet (i={i}); retrying...")
            time.sleep(0.2)
            frame = provider.grab()

        if frame is None:
            print(f"Still no frame (i={i}); skipping.")
            continue

        cv2.imwrite(f"frame_{i}.jpg", frame)
        print(f"Captured frame {i}")

    print(f"Total time: {time.time() - start_time:.4f} seconds")

    print("Capturing 5 region frames (x=0,y=0,w=300,h=200)...")
    for i in range(5):
        region = provider.grab_region(0, 0, 300, 200)
        if region is None:
            print(f"No region frame (i={i}); skipping.")
            continue
        cv2.imwrite(f"region_{i}.jpg", region)
        print(f"Captured region frame {i}")

    provider.close()