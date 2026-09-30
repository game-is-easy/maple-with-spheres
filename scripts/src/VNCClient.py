import datetime
import os
import cv2
from vncdotool import api


server_url = "127.0.0.1::5900"
password = "localpwd123"


class VNCClient:
    def __init__(self):
        self.client = None
        self.start_client()

    def start_client(self):
        self.client = api.connect(server_url, password=password)
        if self.client.protocol is None or not self.client.connected:
            raise ConnectionError("VNC Server is not connected.")

    def keyDown(self, key):
        self.client.keyDown(key)

    def keyUp(self, key):
        self.client.keyUp(key)

    def grab(self, image_name=None, region=None):
        if image_name is None:
            tmp_filename = f"screenshot{(datetime.datetime.now().strftime('%Y-%m%d_%H-%M-%S-%f'))}.png"
        else:
            tmp_filename = image_name
        if region is None:
            self.client.captureScreen(tmp_filename)
        else:
            x, y, w, h = region
            self.client.captureRegion(tmp_filename, x, y, w, h)
        im = cv2.imread(tmp_filename)
        if image_name is None:
            os.unlink(tmp_filename)
        return im
