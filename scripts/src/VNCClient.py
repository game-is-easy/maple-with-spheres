import datetime
import os
import tempfile

import cv2
import numpy as np
from vncdotool import api


server_url = "127.0.0.1::5900"
password = "localpwd123"
# password = "vncpw123"


class VNCClient:
    def __init__(self):
        self.client = None
        self.start_client()

    def start_client(self, timeout=10):
        self.client = api.connect(server_url, password=password)
        self.client.timeout = timeout

        # `api.connect` 返回的 client 是一个异步对象
        # 调用 `client.captureScreen` 时，内部会等待 client.protocol 连接成功后才会继续执行
        tmp_filename = self._create_temp_filename()
        try:
            self.client.captureScreen(tmp_filename)

            if self.client.protocol is None:
                raise ConnectionError()

            if not os.path.isfile(tmp_filename) or os.path.getsize(tmp_filename) <= 0:
                raise ConnectionError()
        except Exception:
            self.client = None
            raise ConnectionError("VNC Server is not connected.")
        finally:
            self._delete_temp_file(tmp_filename)

        # 不需要心跳检测，原因是 VNC 不会断线，除非电脑自动熄屏

    def keyDown(self, key):
        self.client.keyDown(key)

    def keyUp(self, key):
        self.client.keyUp(key)

    def grab(self, image_name=None, region=None):
        if image_name is None:
            tmp_filename = self._create_temp_filename()
        else:
            tmp_filename = image_name

        if region is None:
            self.client.captureScreen(tmp_filename)
            im = cv2.imread(tmp_filename)
            im = np.vstack([np.zeros_like(im)[:38], im])
        else:
            x, y, w, h = region
            x //= 2
            y -= 76
            y //= 2
            w //= 2
            h //= 2
            self.client.captureRegion(tmp_filename, x, y, w, h)
            im = cv2.imread(tmp_filename)

        if image_name is None:
            self._delete_temp_file(tmp_filename)

        return im

    def _create_temp_filename(self):
        return os.path.join(
            tempfile.gettempdir(),
            f"screenshot{(datetime.datetime.now().strftime('%Y-%m%d_%H-%M-%S-%f'))}.png",
        )

    def _delete_temp_file(self, filename):
        try:
            if os.path.exists(filename):
                os.unlink(filename)
        except OSError:
            pass


if __name__ == '__main__':
    vnc = VNCClient()
    vnc.start_client()
    vnc.grab("save.png", region=(36, 202, 30, 30))
