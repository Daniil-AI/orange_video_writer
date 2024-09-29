#!/bin/sh

import os
import time
import threading
from datetime import datetime
import cv2
import numpy as np
import screeninfo

os.environ["CV_GUI_BACKEND"] = "HEADLESS"


class Display:
    """Class for capturing and displaying video frames."""

    def __init__(
        self,
        frame_queue: list[np.ndarray],
        queue_lock: threading.Lock,
        open_flag: threading.Event,
        camindex: int = 1,
        framerate: int = 30,
        capture_width: int = 1280,
        capture_height: int = 960,
    ) -> None:

        self.frame_queue: list[np.ndarray] = frame_queue
        self.queue_lock: threading.Lock = queue_lock
        self.__open: threading.Event = open_flag

        video_pipline = (
            f"v4l2src device=/dev/video{camindex} "
            f"! image/jpeg, width={capture_width}, height={capture_height}, framerate={framerate}/1 "
            f"! jpegdec ! videoconvert ! appsink max-buffers=1 drop=true"
        )
        self.video_cap = cv2.VideoCapture(video_pipline, cv2.CAP_GSTREAMER)

        screen = screeninfo.get_monitors()[0]
        self.screen_width, self.screen_height = screen.width, screen.height
        self.display_thread: threading.Thread | None = None

    def get_cam_fps(self) -> int:
        """Get current FPS capture device"""
        return int(self.video_cap.get(cv2.CAP_PROP_FPS))

    def get_width_and_height(self) -> [int, int]:
        """Get current shape capture"""
        width = int(self.video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width, height)

    def capture(self) -> None:
        """Capture video from camera"""
        while self.__open.is_set():
            ret, frame = self.video_cap.read()
            if ret:
                with self.queue_lock:
                    if len(self.frame_queue) < 10:  # To avoid excessive memory usage
                        self.frame_queue.append(frame)
            else:
                print("Error: Failed to capture video frame.")
                break
        self.cleanup()

    def display(self) -> None:
        """Display video in a separate thread"""
        while self.__open.is_set() or len(self.frame_queue) > 0:
            with self.queue_lock:
                if self.frame_queue:
                    frame = self.frame_queue.pop(0)
                    frame = cv2.resize(frame, (self.screen_width, self.screen_height))

                    cv2.moveWindow("Video Feed", 0, 0)
                    cv2.imshow("Video Feed", frame)
        cv2.destroyAllWindows()

    def start(self) -> None:
        """Start the capture and display threads"""
        self.display_thread = threading.Thread(target=self.display)
        self.capture_thread = threading.Thread(target=self.capture)
        self.display_thread.start()
        self.capture_thread.start()

    def stop(self) -> None:
        """Stop the capture and display threads"""

        self.__open.clear()
        if self.display_thread is not None:
            self.display_thread.join()
        if self.capture_thread is not None:
            self.capture_thread.join()
        self.cleanup()

    def cleanup(self) -> None:
        """Release resources"""
        if self.video_cap.isOpened():
            self.video_cap.release()


class VideoRecorder:
    """Class for recording video using OpenCV"""

    def __init__(
        self,
        name: str = "temp_video.mp4",
        fourcc: str = "mp4v",
        fps: int = 20,
        frame_size: list[int] = [640, 480],
        frame_queue: list[np.ndarray] = [],
        queue_lock: threading.Lock = threading.Lock(),
    ) -> None:

        self.video_filename: str = name
        self.fourcc: str = fourcc
        self.fps: int = fps
        self.frame_queue = frame_queue
        self.queue_lock = queue_lock
        self.frame_size = frame_size

        gst_pipeline = (
            f"appsrc ! videoconvert "
            f" ! x264enc tune=zerolatency bitrate=5000 speed-preset=superfast "
            f"! mp4mux  ! filesink location={name}"
        )
        self.video_writer = cv2.VideoWriter(
            gst_pipeline, cv2.CAP_GSTREAMER, 0, self.fps, self.frame_size
        )
        self.__open: threading.Event = threading.Event()
        self.__open.set()
        self.video_thread: threading.Thread | None = None

    def record(self) -> None:
        """Record video from the queue"""
        while self.__open.is_set() or len(self.frame_queue) > 0:
            with self.queue_lock:
                if self.frame_queue:
                    frame = self.frame_queue.pop(0)
                    self.video_writer.write(frame)
        self.video_writer.release()

    def start(self) -> None:
        """Start video recording in a separate thread"""
        self.video_thread = threading.Thread(target=self.record)
        self.video_thread.start()

    def stop(self) -> None:
        """Stop recording video and join the thread"""
        self.__open.clear()
        if self.video_thread is not None:
            self.video_thread.join()
        self.cleanup()

    def cleanup(self) -> None:
        """Release resources"""
        if self.video_writer:
            self.video_writer.release()


def get_video_path() -> str:
    """Generate a directory path based on the current datetime"""

    current_datetime: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    current_dir: str = os.path.join(os.getcwd(), current_datetime)
    if not os.path.exists(current_dir):
        os.mkdir(current_dir)
    return current_dir


if __name__ == "__main__":

    MEAN_TIME_RECORDING: int = 30  # Duration recording session in seconds
    START_FREZ_TIME: int = 30
    CURENT_DIR: str = get_video_path()
    number_video: int = 0
    frame_queue: list[np.ndarray] = []
    queue_lock: threading.Lock = threading.Lock()
    open_flag = threading.Event()
    open_flag.set()

    time.sleep(START_FREZ_TIME)
    display = Display(
        frame_queue,
        queue_lock,
        open_flag,
        capture_width=1280,
        capture_width=960,
        camindex=0,
    )
    display.start()
    while True:

        FPS = int(display.get_cam_fps() // 2 - 3)
        cam_shape = display.get_width_and_height()
        print(f"CAM SHAPE: {cam_shape}")
        print(f"FPS: {FPS}")

        recorder = VideoRecorder(
            name=f"{CURENT_DIR}/video_{number_video}.mp4",
            fourcc="XVID",
            fps=FPS,
            frame_size=cam_shape,
            frame_queue=frame_queue,
            queue_lock=queue_lock,
        )
        recorder.start()

        time.sleep(MEAN_TIME_RECORDING)
        recorder.stop()
        number_video += 1
