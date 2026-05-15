import cv2
import numpy as np
import os


DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(DIR, "training")

im_meta = []
suffix = 0
for filename in os.listdir(DATA_DIR):
    prefix = filename[:8]
    suffix = filename[10:-4]
    suffix_digit = ""
    if prefix not in im_meta:
        im_meta.append([prefix])
    if suffix.isdigit():
        suffix_digit = suffix
    elif len(im_meta[-1]) == 1:
        im_meta[-1].append(suffix_digit)

last_images = []


def show_images_with_algorithm(algorithm, images):
    pass