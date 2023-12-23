import numpy as np
import cv2
from typing import Callable, Optional, Union, List, Dict


def func(optical_flow_func: Callable, input_data: Union[str, List[np.ndarray]],
         params: Optional[Dict[str, float]] = None, debug: bool = False) -> List[np.ndarray]:
    """
    Funkcja wykonuje przepływ optyczny do przodu i do tyłu na podstawie podanej funkcji.

    Parametry:
        · optical_flow_func: Callable
            - Funkcja przepływu optycznego, która przyjmuje input_data, params i debug.
        · input_data: Union[str, List[np.ndarray]]
            - Jeśli jest to ścieżka do filmu, funkcja wczytuje klatki z filmu.
            - Jeśli jest to lista klatek (obiektów numpy.ndarray), funkcja używa tych klatek.
        · params: Optional[Dict[str, float]] = None
            - Parametry przekazywane do funkcji przepływu optycznego.
        · debug: bool = False
            - Określa, czy włączyć tryb debugowania.

    Zwraca:
        · List[np.ndarray]
            - Pierwszy element listy to flow z przepływu do przodu, a drugi to flow z przepływu do tyłu.
    """
    try:
        if not callable(optical_flow_func):
            raise ValueError("Podana funkcja nie jest wywoływalna.")

        if isinstance(input_data, str):
            cap = cv2.VideoCapture(input_data)
            frames = []
            ret, frame = cap.read()
            while ret:
                frames.append(frame)
                ret, frame = cap.read()
            cap.release()

        elif isinstance(input_data, list) and all(isinstance(frame, np.ndarray) for frame in input_data):
            frames = input_data

        else:
            raise ValueError("Nieprawidłowe dane wejściowe. Oczekiwano ścieżki do filmu lub listy klatek.")

        forward_flow = optical_flow_func(frames, params, debug)
        backward_flow = optical_flow_func(frames[::-1], params, debug)[::-1]

        return [forward_flow, backward_flow]

    except ValueError as e:
        raise ValueError(f"Błąd podczas obliczeń przepływu optycznego: {str(e)}")
    except Exception as e:
        raise ValueError(f"Niespodziewany błąd: {e}")
