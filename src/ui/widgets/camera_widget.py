# -*- coding: utf-8 -*-
import cv2
import threading
import time

class VideoStream:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.cap = None
        self.current_frame = None
        self.running = False
        self.thread = None
        self.last_error = None

    def start(self):
        if self.running:
            return True

        self.last_error = None
        try:
            self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not self.cap.isOpened():
                self.last_error = f"Impossible d'ouvrir le flux RTSP : {self.rtsp_url}"
                print(f"[ERREUR] {self.last_error}")
                return False
        except Exception as e:
            self.last_error = f"Erreur lors de la connexion au flux : {e}"
            print(f"[ERREUR] {self.last_error}")
            return False

        self.running = True
        self.thread = threading.Thread(target=self._update, args=())
        self.thread.daemon = True
        self.thread.start()
        print(f"Connexion RTSP réussie : {self.rtsp_url}")
        return True

    def _update(self):
        while self.running:
            try:
                ret, frame = self.cap.read()
                if ret:
                    self.current_frame = frame
                else:
                    self.last_error = "Erreur de lecture du flux (frame vide)."
                    print(f"[ERREUR] {self.last_error}")
                    self.running = False
                    break
            except Exception as e:
                self.last_error = f"Erreur critique dans le thread de lecture : {e}"
                print(f"[ERREUR] {self.last_error}")
                self.running = False
                break
            time.sleep(0.01)

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.current_frame = None
        print("Flux vidéo arrêté.")

    def get_frame(self):
        if self.current_frame is not None:
            return self.current_frame.copy()
        return None
