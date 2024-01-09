import numpy as np
from scipy.ndimage import convolve
import cv2


def func(prev_frame, next_frame, alpha=1, num_iterations=10):
    prev_frame_grayscale = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    next_frame_grayscale = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)

    prev_frame_grayscale = cv2.GaussianBlur(prev_frame_grayscale, (5, 5), 0)
    next_frame_grayscale = cv2.GaussianBlur(next_frame_grayscale, (5, 5), 0)

    prev_frame_grayscale = prev_frame_grayscale.astype(np.float32) / 255.0
    next_frame_grayscale = next_frame_grayscale.astype(np.float32) / 255.0

    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])

    dx = convolve(prev_frame_grayscale, kernel_x) + convolve(next_frame_grayscale, kernel_x)
    dy = convolve(prev_frame_grayscale, kernel_y) + convolve(next_frame_grayscale, kernel_y)
    dt = next_frame_grayscale - prev_frame_grayscale
    kernel_avg = np.array([[1 / 12, 1 / 6, 1 / 12],
                           [1 / 6, 0, 1 / 6],
                           [1 / 12, 1 / 6, 1 / 12]], float)

    u, v = np.zeros_like(prev_frame_grayscale), np.zeros_like(prev_frame_grayscale)

    for _ in range(num_iterations):
        u_avg = convolve(u, kernel_avg)
        v_avg = convolve(v, kernel_avg)

        numerator = dx * u_avg + dy * v_avg + dt
        denominator = alpha ** 2 + u_avg ** 2 + v_avg ** 2
        u = u_avg - numerator / denominator
        v = v_avg - numerator / denominator

        # tu dziala bez tego nwm co bedzie lepsze
        u = np.clip(u, -1, 1)
        v = np.clip(v, -1, 1)

    optical_flow = np.stack((u, v), axis=-1)

    flow_img = np.copy(next_frame)
    h, w = flow_img.shape[:2]
    step_size = 20
    for y in range(0, h, step_size):
        for x in range(0, w, step_size):
            dx, dy = optical_flow[y, x] * 7
            cv2.arrowedLine(flow_img, (x, y), (int(x + dx), int(y + dy)), (0, 255, 0), 1, cv2.LINE_AA, tipLength=0.8)

    return optical_flow, flow_img


func.__name__ = "Horn-Schunk"
