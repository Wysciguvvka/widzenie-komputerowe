import frame_interpolation
from typing import List, Dict, Callable, Tuple
import optical_flow
import numpy as np
import logging
import time
import cv2

from PySide6 import QtGui, QtCore
from PySide6.QtCore import QRect, Signal, Slot, QObject, QThread, Qt
from PySide6.QtGui import QPainter, QPaintEvent, QPixmap, QColor, QFontMetrics, QCursor, QPen, QDragEnterEvent, \
    QDropEvent, QImage
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, \
    QStyleOption, QStyle, QWidget, QVBoxLayout, QFileDialog, QPushButton, QComboBox, QLabel, QLineEdit
from .gui_video_processor import process_video

logging.getLogger().setLevel(logging.INFO)


# class Interpolations(QComboBox):
#     def __init__(self, scroll_widget=None, parent=None, *args, **kwargs):
#         super(ConfigList, self).__init__(*args, **kwargs)
#         self.scrollWidget = scroll_widget
#         self.setParent(parent)
#         # self.setFocusPolicy(QtCore.Qt.StrongFocus)
#
#     def wheelEvent(self, *args, **kwargs):
#         return self.scrollWidget.wheelEvent(*args, **kwargs)


class VideoThread(QThread):
    update_frame = Signal(QImage)

    def __init__(self, parent=None, frames: List = None, fps: float = 1):
        super().__init__(parent)
        self.frames = frames
        self.fps = fps
        self.current_index = 0
        self.paused = True

    def run(self):
        while True:
            # if not self.frames:
            #     logging.warning('Brak wideo')
            #     return
            try:
                frame = self.frames[self.current_index]
                color_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = QImage(color_frame.data, color_frame.shape[1], color_frame.shape[0], QImage.Format_RGB888)
                self.update_frame.emit(img)
                if not self.paused:
                    self.current_index += 1
                time.sleep(1 / self.fps)

            except IndexError:
                self.current_index = 0

    @Slot(bool)
    def request_pause(self, paused: bool):
        logging.info(f'received {paused}')
        self.paused = paused

    @Slot(int)
    def request_frame_index(self, idx):
        self.current_index = idx


class GenerateFrames(QThread):
    interpolated_video_signal = Signal(np.ndarray, float)
    flow_video_signal = Signal(np.ndarray, float)

    def __init__(self, frames: List, fps, configuration: Dict, parent=None):
        QThread.__init__(self, parent)
        self.frames = frames
        self.configuration = configuration
        self.fps = fps

    def run(self):
        # dict_data = {'interpolation_function': interp_func, 'interpolation_params': interp_params,
        #              'flow_function': flow_func, 'flow_params': flow_params}
        interp_func = self.configuration['interpolation_function']
        interp_params = self.configuration['interpolation_params']
        flow_function = self.configuration['flow_function']
        flow_params = self.configuration['flow_params']
        flow_video, _, interpolated_video = process_video(self.frames, interpolation=interp_func,
                                                          interpolation_args=interp_params, optical_flow=flow_function,
                                                          optical_flows_args=flow_params)
        # previous_num_frames = len(self.frames)
        # new_num_frames = len(interpolated_video)
        # total_num_frames = previous_num_frames + new_num_frames
        # total_time_duration_previous = previous_num_frames / self.fps
        # total_time_duration_new = previous_num_frames / self.fps
        # total_time_duration = total_time_duration_previous + total_time_duration_new
        # new_fps = total_num_frames / total_time_duration
        height, width, _ = interpolated_video[0].shape
        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        out = cv2.VideoWriter(f"testowe.mp4", fourcc, self.fps*2, (width, height))
        for frame in interpolated_video:
            out.write(frame)
        out.release()

        self.interpolated_video_signal.emit(interpolated_video, self.fps * 2)
        self.flow_video_signal.emit(flow_video, self.fps)

        self.quit()


class LoadVideoThread(QThread):
    video_data = Signal(list, float)

    def __init__(self, parent=None, video_path: str = '../video/slow_traffic_small.mp4'):
        QThread.__init__(self, parent)
        self.video_path = video_path

    def run(self):
        cap: cv2.VideoCapture = cv2.VideoCapture(self.video_path)
        frames: List[np.ndarray] = []
        ret: bool
        frame: np.ndarray
        ret, frame = cap.read()
        fps = cap.get(cv2.CAP_PROP_FPS)
        while ret:
            frames.append(frame)
            ret, frame = cap.read()
        cap.release()
        self.video_data.emit(frames, fps)


class VideoDisplay(QWidget):
    def __init__(self, parent: QObject = None, text='Video', *args, **kwargs) -> None:
        super(VideoDisplay, self).__init__(parent=parent, *args, **kwargs)
        self.frames: List = []
        self._pixmap = None
        self.text = text
        self.setStyleSheet('border-color: rgba(152,152,152,255);')
        # self.thread = VideoThread()
        self.fps = 1
        self.thread = VideoThread(self, self.frames, self.fps)

    @Slot(list, float)
    def paint_vid(self, frames, fps) -> None:
        self.frames = frames
        self.fps = fps
        self.thread.frames = self.frames
        self.thread.fps = fps
        # self.thread = VideoThread(self, frames, fps)
        self.thread.update_frame.connect(self.update_image)
        self.thread.start()

    @Slot(type(QImage))
    def update_image(self, img):
        """Updates the image_label with a new opencv image"""
        self.pixmap = QPixmap.fromImage(img)
        # self.image_label.setPixmap(qt_img)

    @property
    def pixmap(self) -> QPixmap:
        """returns QPixmap"""
        return self._pixmap

    @pixmap.setter
    def pixmap(self, value: QPixmap) -> None:
        """Update stylesheet on image upload
            (Remove borders)
        """
        self._pixmap = value
        if self._pixmap is None:
            self.setStyleSheet('border-color: rgba(152,152,152,255);')
            return
        self.setStyleSheet('border-color: rgba(152,152,152,0);')

    def paintEvent(self, event: QPaintEvent) -> None:
        """Re-implement paintEvent method"""
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)  # type: ignore
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)  # type: ignore
        if not self.pixmap:
            painter.end()
            return

        w, h = self.pixmap.size().width(), self.pixmap.size().height()
        if w == 0 or h == 0:
            painter.end()
            return
        ratio = w / h
        height_scaled = max(self.height(), h) if h <= self.height() else min(self.height(), h)
        width_scaled = height_scaled * ratio
        if width_scaled > self.width():  # scale if pixmap's width is greater than widget's width
            width_scaled = self.width()  # set pixmap's width to 100% of available space
            height_scaled = width_scaled * 1 / ratio
        y0 = abs(self.height() - height_scaled) * 0.5
        x0 = abs(self.width() - width_scaled) * 0.5
        _pixmap = self.pixmap.scaled(width_scaled, height_scaled, QtCore.Qt.KeepAspectRatio,  # type: ignore
                                     QtCore.Qt.SmoothTransformation)  # type: ignore
        painter.drawPixmap(QRect(x0, y0, width_scaled, height_scaled), _pixmap)  # draw pixmap (image)


class VideoHandler(QWidget):
    paint_video = Signal(list, float)  # List of frames, frame rate

    def __init__(self, parent: QObject = None, *args, **kwargs) -> None:
        super(VideoHandler, self).__init__(parent=parent, *args, **kwargs)
        self.video_widget = VideoDisplay(self)
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.video_widget)
        # self.loading_thread = LoadVideoThread()
        self._frames: List = []
        self.fps = 1
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.upload_button = QPushButton(self)
        self.upload_button.setText('Wybierz plik')
        self.upload_button.setEnabled(True)
        self.upload_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))  # type: ignore

        self.upload_button.released.connect(lambda: self.upload_button_function())
        self.setStyleSheet('border-color: rgba(152,152,152,255);')

        self.paint_video.connect(self.video_widget.paint_vid)

    def upload_button_function(self) -> None:
        """Image button"""
        data = QFileDialog.getOpenFileName(self, 'Wybierz plik', '', 'Video files (*.mp4 *.avi *.mkv *.mov)')
        if data:
            path = data[0]
            self.load_video(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Accept file"""
        if self.frames:
            return
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            urls = mime_data.urls()
            for url in urls:
                if url.isLocalFile() and url.toLocalFile().lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent) -> None:
        if self.frames:
            return
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                video_path = url.toLocalFile()
                self.load_video(video_path)

    @property
    def frames(self) -> List:
        return self._frames

    @frames.setter
    def frames(self, value: List) -> None:
        self._frames = value
        if not self._frames:
            self.setStyleSheet('border-color: rgba(152,152,152,255);')
            return
        self.setStyleSheet('border-color: rgba(152,152,152,0);')

    @Slot(list, float)
    def set_frames(self, frames: List, fps: float) -> None:
        """
        frames list, fps

        :param frames:
        :param fps:
        :return: None
        """
        self.fps = fps
        self.frames = frames
        self.paint_video.emit(self.frames, self.fps)

    def load_video(self, video_path: str) -> bool:
        try:
            video_formats = [".mp4", ".avi", ".mkv", ".mov"]
            if any(video_format in video_path.lower() for video_format in video_formats):
                vid_thread = LoadVideoThread(self, video_path)
                vid_thread.video_data.connect(self.set_frames)
                vid_thread.start()
                # media_content = QUrl.fromLocalFile(video_path)
                # self.video = media_content
                # self.player.setSource(media_content)
                #
                # self.play_video()
                return True
        except Exception as e:
            logging.exception(e)
            return False
        return False

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        It's recommended to reimplement paintEvent()
        A paint event is a request to repaint all or part of a widget.
        """
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)  # type: ignore
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)  # type: ignore
        if not self.frames:
            if self.video_widget.isVisible():
                self.video_widget.setVisible(False)
            if not self.upload_button.isVisible():
                self.upload_button.setVisible(True)
                self.upload_button.setEnabled(True)
            metrics = QFontMetrics(self.font())
            height = metrics.height()
            painter.setPen(QPen(QColor(0, 0, 0, 255)))
            text = f'Przeciągnij plik\n— lub —\nwybierz plik z dysku'
            text = metrics.elidedText(text,
                                      QtCore.Qt.ElideRight, self.width() - 12)  # type: ignore
            painter.drawText(QRect(0, int((self.height() - height * 3) * 0.5), self.width(), height * 3), 133, text)
            self.upload_button.move(int((self.width() - self.upload_button.width()) * 0.5),  # type: ignore
                                    int((self.height() + height * 3) * 0.5) + 8)  # moves image button to the center
            painter.end()
            return
        if self.upload_button.isVisible():
            self.upload_button.setEnabled(False)
            self.upload_button.setVisible(False)
        if not self.video_widget.isVisible():
            self.video_widget.setVisible(True)
        # w, h = self.pixmap.size().width(), self.pixmap.size().height()
        # if w == 0 or h == 0:
        #     painter.end()
        #     return
        # ratio = w / h
        # height_scaled = max(self.height(), h) if h <= self.height() else min(self.height(), h)
        # width_scaled = height_scaled * ratio
        # if width_scaled > self.width():  # scale if pixmap's width is greater than widget's width
        #     width_scaled = self.width()  # set pixmap's width to 100% of available space
        #     height_scaled = width_scaled * 1 / ratio
        # y0 = abs(self.height() - height_scaled) * 0.5
        # x0 = abs(self.width() - width_scaled) * 0.5
        # _pixmap = self.pixmap.scaled(width_scaled, height_scaled, QtCore.Qt.KeepAspectRatio,
        #                              QtCore.Qt.SmoothTransformation)  # scale pixmap
        # painter.drawPixmap(QRect(x0, y0, width_scaled, height_scaled), _pixmap)  # draw pixmap (image)
        #
        # """Get pixmap position (2x2 matrix) [(x0,y0),(x1,y1)]"""
        # self.pixmap_coordinates = [[int(x0), int(y0)], [int(x0 + width_scaled), int(y0 + height_scaled)]]
        #
        painter.end()


class InterFlowMenu(QWidget):

    def __init__(self, parent, item_list: List, params: Dict, *args, **kwargs):
        super(InterFlowMenu, self).__init__(parent=parent, *args, **kwargs)
        self.layout = QVBoxLayout(self)

        self.item_callable_mapping = {item.__name__: item for item in item_list}

        self.config_list = QComboBox(parent=self)
        self.config_list.addItems(self.item_callable_mapping.keys())
        self.layout.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.layout.addWidget(self.config_list)
        self.lines = []
        for param_name, default_value in params.items():
            param_widget = QWidget(self)
            input_layout = QHBoxLayout(param_widget)
            label = QLabel(f"{param_name}:", param_widget)
            line_edit = QLineEdit(param_widget)
            line_edit.setObjectName(param_name)
            # line_edit.setMaximumWidth(50)
            line_edit.setText(str(default_value))  # Set default value to line edit

            input_layout.addWidget(label)
            input_layout.addWidget(line_edit)
            self.layout.addWidget(param_widget)

            self.lines.append(line_edit)

    def get_settings(self) -> Tuple[Callable, Dict]:
        return self.selected_callable(), {label.objectName(): float(label.text()) for label in self.lines}

    def selected_callable(self):
        selected_item = self.config_list.currentText()

        selected_callable = self.item_callable_mapping.get(selected_item)

        return selected_callable

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Reimplement paintEvent() method
        It's recommended to reimplement paintEvent()
        A paint event is a request to repaint all or part of a widget.
        """
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)  # type: ignore
        painter.end()


class ButtonsWidget(QWidget):

    def __init__(self, parent: QObject = None, *args, **kwargs) -> None:
        super(ButtonsWidget, self).__init__(parent=parent, *args, **kwargs)
        self.buttons_layout = QVBoxLayout(self)
        self.generate_btn = QPushButton("Wygeneruj", parent=self)
        self.start_btn = QPushButton("Start", parent=self)
        self.stop_btn = QPushButton("Stop", parent=self)
        self.reset_btn = QPushButton("Reset", parent=self)
        self.buttons = [self.generate_btn, self.stop_btn, self.start_btn, self.reset_btn]
        self.buttons_layout.addWidget(self.generate_btn)
        self.buttons_layout.setSpacing(25)
        self.buttons_layout.addWidget(self.start_btn)
        self.buttons_layout.addWidget(self.stop_btn)
        self.buttons_layout.addWidget(self.reset_btn)
        self.buttons_layout.setAlignment(Qt.AlignCenter)
        for button in self.buttons:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))  # type: ignore

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Reimplement paintEvent() method
        It's recommended to reimplement paintEvent()
        A paint event is a request to repaint all or part of a widget.
        """
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)  # type: ignore
        painter.end()


class SettingsWidget(QWidget):
    request_generate = Signal(dict)
    request_state = Signal(bool)
    request_reset = Signal()

    def __init__(self, parent: QObject = None, *args, **kwargs) -> None:
        super(SettingsWidget, self).__init__(parent=parent, *args, **kwargs)
        self.layout = QHBoxLayout(self)
        interpolation_functions = [frame_interpolation.average_frame, frame_interpolation.bicubic,
                                   frame_interpolation.spline, frame_interpolation.lanczos]
        interpolation_params = {'t': 0.5}
        flow_functions = [optical_flow.gunnar_farneback, optical_flow.horn_schunck, optical_flow.phase_correlation,
                          optical_flow.test_flow]
        # flow_params = {'test': 666, 'jp2gmd': 2137}
        flow_params = {}
        self.interpolations_widget = InterFlowMenu(self, interpolation_functions, interpolation_params)
        self.flow_widget = InterFlowMenu(self, flow_functions, flow_params)

        self.buttons_widget = ButtonsWidget(self)
        self.buttons_widget.generate_btn.clicked.connect(self.send_params)
        self.buttons_widget.start_btn.clicked.connect(lambda: self.set_playback_state(False))
        self.buttons_widget.stop_btn.clicked.connect(lambda: self.set_playback_state(True))
        self.buttons_widget.reset_btn.clicked.connect(self.request_reset.emit)

        self.layout.addWidget(self.interpolations_widget)
        self.layout.addWidget(self.flow_widget)
        self.layout.addWidget(self.buttons_widget)
        self.__set_size_policy()

    def set_playback_state(self, status: bool):
        logging.info(f"Request {status}")
        self.request_state.emit(status)

    def send_params(self):
        interp_func, interp_params = self.interpolations_widget.get_settings()
        flow_func, flow_params = self.flow_widget.get_settings()
        dict_data = {'interpolation_function': interp_func, 'interpolation_params': interp_params,
                     'flow_function': flow_func, 'flow_params': flow_params}
        self.request_generate.emit(dict_data)

    def __set_size_policy(self):
        """sets size policy"""
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(1)
        self.interpolations_widget.setSizePolicy(size_policy)
        self.flow_widget.setSizePolicy(size_policy)
        self.buttons_widget.setSizePolicy(size_policy)

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Reimplement paintEvent() method
        It's recommended to reimplement paintEvent()
        A paint event is a request to repaint all or part of a widget.
        """
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)  # type: ignore
        painter.end()


class Content(QWidget):
    def __init__(self, parent: QObject = None, *args, **kwargs) -> None:
        super(Content, self).__init__(parent=parent, *args, **kwargs)
        """Initialize widgets"""
        self.widget_layout = QVBoxLayout(self)

        self.widget_top = QWidget(self)
        self.widget_top.layout = QHBoxLayout(self.widget_top)

        self.base_vid = VideoHandler(self.widget_top)
        self.flow_vid = VideoDisplay(self.widget_top, text='Flow')
        self.interpolated_vid = VideoDisplay(self.widget_top, text='Interpolated')

        self.widget_top.layout.addWidget(self.base_vid)
        self.widget_top.layout.addWidget(self.flow_vid)
        self.widget_top.layout.addWidget(self.interpolated_vid)

        """Layout size policy"""
        self.settings = SettingsWidget(self)  # color palette

        self.widget_layout.addWidget(self.widget_top)
        self.widget_layout.addWidget(self.settings)

        self.settings.request_generate.connect(self.start_generate)
        # self.settings.request_state.connect(self.change_video_state)
        self.settings.request_state.connect(self.base_vid.video_widget.thread.request_pause)
        self.settings.request_state.connect(self.flow_vid.thread.request_pause)
        self.settings.request_state.connect(self.interpolated_vid.thread.request_pause)
        self.__set_size_policy()

    # @Slot(bool)
    # def change_video_state(self, state:bool):
    #     self.
    @Slot(dict)
    def start_generate(self, video_data):
        frames = self.base_vid.frames
        if not frames:
            logging.warning('brak wideo')
            return
        fps = self.base_vid.fps
        generation_thread = GenerateFrames(frames=frames, fps=fps, configuration=video_data, parent=self)
        generation_thread.flow_video_signal.connect(self.flow_vid.paint_vid)
        generation_thread.interpolated_video_signal.connect(self.interpolated_vid.paint_vid)
        generation_thread.start()
        logging.info('Generowanie')

    def __set_size_policy(self):
        """sets size policy"""
        vertical_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        vertical_policy.setVerticalStretch(40)

        self.widget_top.setSizePolicy(vertical_policy)
        vertical_policy.setVerticalStretch(60)
        self.settings.setSizePolicy(vertical_policy)

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Reimplement paintEvent() method
        It's recommended to reimplement paintEvent()
        A paint event is a request to repaint all or part of a widget.
        """
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)  # type: ignore
        painter.end()


class UiMainWindow(QWidget):
    def __init__(self, parent: QObject = None, **kwargs) -> None:
        super(UiMainWindow, self).__init__(parent=parent, **kwargs)
        """Initialize UiMainWindow class instance"""
        self.widget_layout = QVBoxLayout(self)

        # self.header = Header(self)
        self.content = Content(self)

        # self.widget_layout.addWidget(self.header)
        self.widget_layout.addWidget(self.content)

        self.__set_size_policy()
        self.__set_style_sheet()

    def __set_style_sheet(self) -> None:
        """A method that applies custom style sheet."""
        with open('./src/qss/style.qss', 'r', encoding='utf-8') as qss:
            self.setStyleSheet(qss.read())

    def __set_size_policy(self) -> None:
        """Sets widget size policy"""
        self.widget_layout.setContentsMargins(0, 0, 0, 0)
        self.widget_layout.setSpacing(0)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Re-implement paintEvent method"""
        try:
            opt = QStyleOption()
            opt.initFrom(self)
            painter = QPainter(self)
            self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)  # type: ignore
            painter.end()
        except KeyboardInterrupt:
            return
