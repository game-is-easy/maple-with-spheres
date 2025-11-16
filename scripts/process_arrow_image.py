import cv2
import numpy as np
import time
from typing import Tuple


def euclidean_dist(arr1, arr2):
    return np.sqrt(((arr1[..., :3] - arr2[..., :3]) ** 2).sum(axis=-1))


def chebyshev_dist(arr1, arr2):
    return np.max(np.abs(arr1[..., :3] - arr2[..., :3]), axis=-1)


def gen_mask(im1, im2, metric_fn, threshold, drop_difference=True):
    if drop_difference:
        return metric_fn(im1, im2) >= threshold
    return metric_fn(im1, im2) <= threshold


def process_image(base_im, arrow_im, arrow_im2, metric_fn=euclidean_dist, change_threshold=5, drift_threshold=1, fill_color=None):
    # unchanged region can't contain arrows
    mask_no_change = gen_mask(base_im, arrow_im, metric_fn, threshold=change_threshold, drop_difference=False)
    # after arrows appear, changed region can't contain arrows
    mask_drift = gen_mask(arrow_im, arrow_im2, metric_fn, threshold=drift_threshold)
    mask_drift_2 = gen_mask(arrow_im, arrow_im2, metric_fn, threshold=2)

    if not fill_color:
        fill_color = arrow_im2[~mask_no_change & ~mask_drift].mean(axis=0)
    else:
        fill_color = np.array(fill_color)
    mask = mask_no_change | mask_drift
    arrow_im2[mask] = fill_color
    mask_2 = mask_no_change | mask_drift_2
    arrow_im[mask_2] = fill_color

    return arrow_im2, arrow_im


def detect_pad_region(image: np.ndarray) -> [np.ndarray, Tuple]:
    """Detect the semi-transparent pad that contains the arrows"""
    # Convert to HSV for better color detection
    hsv = image.astype(np.float32)
    hsv = cv2.cvtColor((hsv * 255).astype(np.uint8), cv2.COLOR_BGR2HSV)

    # Look for the semi-transparent pad - it should have consistent saturation/brightness
    saturation = hsv[:, :, 1]

    # The pad often appears as a region with moderate saturation
    pad_mask = cv2.inRange(saturation, 30, 200)

    # Find the largest connected component (should be the pad)
    contours, _ = cv2.findContours(pad_mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Get the largest contour (likely the pad)
        largest_contour = max(contours, key=cv2.contourArea)

        # Get bounding rectangle of the pad
        pad_x, pad_y, pad_w, pad_h = cv2.boundingRect(largest_contour)

        # Create a mask for just the pad region
        pad_region_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.fillPoly(pad_region_mask, [largest_contour], 255)

        return pad_region_mask, (pad_x, pad_y, pad_w, pad_h)

    return None, None


def preview_image(im, delay):
    cv2.namedWindow('image', cv2.WINDOW_AUTOSIZE)
    time.sleep(0.1)
    cv2.moveWindow('image', 0, 200)
    cv2.imshow('image', im)
    cv2.waitKey(delay)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    import os

    DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    IM_DIR = os.path.join(DIR, "training")
    im_prefix = "08190234"

    im_names = []
    for im_name in os.listdir(IM_DIR):
        if im_name.startswith(im_prefix) and im_name[-5].isdigit():
            im_names.append(im_name)
    im_names = sorted(im_names, key=lambda name: int(name[name.find('_')+1:name.find('.')]))
    print(im_names)
    im0 = cv2.imread(os.path.join(IM_DIR, im_names[0]))
    im1 = cv2.imread(os.path.join(IM_DIR, im_names[-2]))
    im2 = cv2.imread(os.path.join(IM_DIR, im_names[-1]))

    # pad, region = detect_pad_region(im2)
    # preview_image(pad, 2000)

    metric_fn = euclidean_dist
    mask = gen_mask(im1, im2, metric_fn, threshold=1)
    mask2 = gen_mask(im0, im2, metric_fn, threshold=5, drop_difference=False)
    mean_color = im2[~mask2 & ~mask].mean(axis=0)
    im2[mask | mask2] = mean_color
    preview_image(im2, 2000)
    cv2.imwrite(os.path.join(DIR, f"preprocessed_images/{im_prefix}.png"), im2)
