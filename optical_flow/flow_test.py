import cv2
import numpy as np
from scipy.ndimage import sobel


def func(prev_frame, next_frame, window_size=20, delta_t=1.0):
    prev_frame_grayscale = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    next_frame_grayscale = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)

    prev_frame_grayscale = cv2.GaussianBlur(prev_frame_grayscale, (5, 5), 0)
    next_frame_grayscale = cv2.GaussianBlur(next_frame_grayscale, (5, 5), 0)

    prev_frame_grayscale = prev_frame_grayscale.astype(np.float32) / 255.0
    next_frame_grayscale = next_frame_grayscale.astype(np.float32) / 255.0

    I_x = sobel(prev_frame_grayscale, axis=1, mode='constant') / 8.0
    I_y = sobel(prev_frame_grayscale, axis=0, mode='constant') / 8.0

    I_t = (next_frame_grayscale - prev_frame_grayscale) / delta_t

    u = np.zeros_like(prev_frame_grayscale)
    v = np.zeros_like(next_frame_grayscale)

    half_window = window_size // 2

    for i in range(half_window, I_x.shape[0] - half_window):
        for j in range(half_window, I_x.shape[1] - half_window):
            I_x_window = I_x[i - half_window:i + half_window + 1, j - half_window:j + half_window + 1].flatten()
            I_y_window = I_y[i - half_window:i + half_window + 1, j - half_window:j + half_window + 1].flatten()
            I_t_window = I_t[i - half_window:i + half_window + 1, j - half_window:j + half_window + 1].flatten()

            A = np.vstack((I_x_window, I_y_window)).T
            uv = np.linalg.lstsq(A, -I_t_window, rcond=None)[0]

            u[i, j] = uv[0]
            v[i, j] = uv[1]
    print(u.shape, v.shape)
    optical_flow = np.stack((u, v), axis=-1)
    print(optical_flow.shape)

    flow_img = np.copy(next_frame)
    h, w = flow_img.shape[:2]
    step_size = 20
    for y in range(0, h, step_size):
        for x in range(0, w, step_size):
            dx, dy = optical_flow[y, x] * 5
            cv2.arrowedLine(flow_img, (x, y), (int(x + dx), int(y + dy)), (0, 255, 0), 1, cv2.LINE_AA, tipLength=0.8)

    return optical_flow, flow_img


# prev_frame = np.random.rand(10, 10)  # Example: Random initial frame
# next_frame = prev_frame + 0.5 * np.random.randn(10, 10)  # Example: Small motion
#
# # Calculate optical flow using dense method
# u, v = calculate_optical_flow_dense(prev_frame, next_frame)
#
# # Display results
# plt.figure(figsize=(12, 4))
#
# plt.subplot(1, 3, 1)
# plt.imshow(prev_frame, cmap='gray', vmin=0, vmax=1)
# plt.title('Previous Frame')
#
# # plt.subplot(1, 3, 2)
# # plt.quiver(u, v, color='b', angles='xy', scale_units='xy', scale=2)
# # plt.title('Optical Flow Field (Dense Method)')
#
# plt.subplot(1, 3, 3)
# plt.imshow(next_frame, cmap='gray', vmin=0, vmax=1)
# plt.quiver(u, v, color='r', angles='xy', scale_units='xy', scale=2)
# plt.title('Next Frame with Optical Flow Overlay (Dense Method)')
#
# plt.show()
