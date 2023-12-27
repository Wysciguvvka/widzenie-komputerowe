import numpy as np
import cv2
from typing import Union, List, Dict, Optional


def func(input_data: Union[str, List[np.ndarray]],
         params: Optional[Dict[str, float]] = None,
         debug: bool = False) -> Union[np.ndarray, List[np.ndarray]]:
    """
    Funkcja oblicza przepływ optyczny między klatkami wideo za pomocą metody Lucas-Kanade.

    Parametry:
        · input_data: Union[str, List[np.ndarray]]
            - Jeśli jest to ścieżka do filmu, funkcja wczytuje klatki z filmu.
            - Jeśli jest to lista klatek (obiektów numpy.ndarray), funkcja używa tych klatek.
        · params: Optional[Dict[str, float]] = None
            Parametry dla funkcji cv2.goodFeaturesToTrack, która znajduje silne krawędzie w pierwszej klatce:
                - 'maxCorners' (float): Maksymalna liczba detekowanych narożników. Domyślnie: 100.
                - 'qualityLevel' (float): Minimalna akceptowalna jakość detekowanego narożnika jako liczba z zakresu 0-1. Domyślnie: 0.3.
                - 'minDistance' (float): Minimalny dystans między detekowanymi narożnikami. Domyślnie: 7.
                - 'blockSize' (float): Rozmiar sąsiedztwa używanego do obliczeń. Domyślnie: 7.
        · debug: bool = False
            - Określa, czy włączyć tryb debugowania, który pokazuje wideo z przepływem optycznym.

    Zwraca:
        · Union[np.ndarray, List[np.ndarray]]
            - Jeśli debug=True, zwraca wideo z przepływem optycznym.
            - W przeciwnym razie zwraca listę obiektów numpy.ndarray reprezentujących przepływ optyczny między kolejnymi klatkami.
    """

    if params is None:
        params = {
            "maxCorners": 100,
            "qualityLevel": 0.3,
            "minDistance": 7,
            "blockSize": 7
        }

    try:
        if isinstance(input_data, str):
            cap: cv2.VideoCapture = cv2.VideoCapture(input_data)
            frames: List[np.ndarray] = []
            ret: bool
            frame: np.ndarray
            ret, frame = cap.read()
            while ret:
                frames.append(frame)
                ret, frame = cap.read()
            cap.release()
        elif isinstance(input_data, list) and all(isinstance(frame, np.ndarray) for frame in input_data):
            frames = input_data
        else:
            raise ValueError("Nieprawidłowe dane wejściowe. Oczekiwano ścieżki do filmu lub listy zdjęć")

        gray_frames: List[np.ndarray] = [cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) for frame in frames]

        prev_pts: np.ndarray = cv2.goodFeaturesToTrack(gray_frames[0], mask=None, **params)

        flow_frames: List[np.ndarray] = []
        for i in range(1, len(gray_frames)):
            next_pts, status, err = cv2.calcOpticalFlowPyrLK(gray_frames[i - 1], gray_frames[i], prev_pts, None)

            good_old: np.ndarray = prev_pts[status == 1]
            good_new: np.ndarray = next_pts[status == 1]

            flow: np.ndarray = np.zeros_like(frames[i])
            for j, (new, old) in enumerate(zip(good_new, good_old)):
                a, b = map(int, new.ravel())
                c, d = map(int, old.ravel())
                cv2.line(flow, (a, b), (c, d), (0, 255, 0), 2)
                cv2.circle(frames[i], (a, b), 5, (0, 255, 0), -1)

            flow_frames.append(flow)
            prev_pts = np.reshape(good_new, (-1, 1, 2))

        if debug:
            h, w, _ = frames[0].shape
            debug_video: np.ndarray = np.zeros((h, w * 2, 3), dtype=np.uint8)

            for i in range(len(frames)):
                debug_video[:, :w, :] = flow_frames[i]
                debug_video[:, w:, :] = frames[i]

                cv2.imshow('Debug Video', debug_video)
                if cv2.waitKey(30) & 0xFF == 27:  # ESC key to exit
                    break

            cv2.destroyAllWindows()

            return debug_video
        else:
            return np.array(frames)

    except cv2.error as e:
        raise ValueError(f"Błąd OpenCV: {e}")
    except Exception as e:
        raise ValueError(f"Niespodziewany błąd: {e}")

if __name__ == "__main__":
    func("/home/rskay/PycharmProjects/widzenie-komputerowe/slow_traffic_small.mp4", debug=True)