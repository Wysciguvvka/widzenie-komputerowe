import cv2
import numpy as np
from typing import List


def bicubic_interpolation(frames: List[np.ndarray], scale_factor: float) -> List[np.ndarray]:
    """
    Wykonuje interpolację bicubiczną na podanej liście klatek.

    Parametry:
        · frames: List[np.ndarray]
            - Lista klatek do interpolacji.
        · scale_factor: float
            - Współczynnik skali do zastosowania podczas interpolacji.

    Zwraca:
        · List[np.ndarray]
            - Lista przeskalowanych klatek bicubicznych.
    """
    interpolated_frames: List[np.ndarray] = []

    for frame in frames:
        height, width = frame.shape[:2]
        new_height, new_width = int(height * scale_factor), int(width * scale_factor)

        new_frame = cv2.resize(frame, (new_width, new_height))

        interpolated_frame = cv2.resize(new_frame, (width, height), interpolation=cv2.INTER_CUBIC)

        interpolated_frames.append(interpolated_frame)

    return interpolated_frames
