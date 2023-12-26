import cv2
import numpy as np
from typing import List

def func(frames: List[np.ndarray], flow_frames: List[np.ndarray], scale_factor: float) -> List[np.ndarray]:
    """
    Wykonuje interpolację bicubiczną na podanej liście klatek.

    Parametry:
        · frames: List[np.ndarray]
            - Lista klatek do interpolacji.
        · flow_frames: List[np.ndarray]
            - Lista klatek z przepływem optycznym.
        · scale_factor: float
            - Współczynnik skali do zastosowania podczas interpolacji.

    Zwraca:
        · List[np.ndarray]
            - Lista przeskalowanych klatek bicubicznych o zachowanej oryginalnej rozdzielczości.
    """
    interpolated_frames: List[np.ndarray] = []

    for i in range(len(frames)):
        height, width = frames[i].shape[:2]
        new_height, new_width = int(height * scale_factor), int(width * scale_factor)

        # Przeskaluj oryginalną klatkę do nowych wymiarów
        new_frame = cv2.resize(frames[i], (new_width, new_height))

        # Sprawdź, czy istnieje odpowiadająca klatka przepływu optycznego
        if i < len(flow_frames):
            # Przeskaluj klatkę przepływu optycznego do nowych wymiarów
            scaled_flow = cv2.resize(flow_frames[i], (new_width, new_height), interpolation=cv2.INTER_CUBIC)

            # Utwórz dwie mapy przesunięcia dla X i Y
            map_x = scaled_flow[:, :, 0].astype(np.float32)
            map_y = scaled_flow[:, :, 1].astype(np.float32)

            # Wykonaj interpolację bicubiczną przy użyciu map przesunięcia
            remapped_frame = cv2.remap(new_frame, map_x, map_y, interpolation=cv2.INTER_CUBIC)
            interpolated_frames.append(remapped_frame)
        else:
            # Jeśli brak klatki przepływu optycznego, dodaj oryginalną klatkę
            interpolated_frames.append(new_frame)

    return interpolated_frames
