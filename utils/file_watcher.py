"""
file_watcher.py
===============
렌더링 완료를 감지하는 파일 시스템 워처입니다.
watchdog 라이브러리를 사용하여 output 디렉토리에 새 PNG 파일이
생성될 때마다 콜백을 호출합니다.
"""

import os
import json
import threading
import time

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False


class RenderCompleteHandler(FileSystemEventHandler if HAS_WATCHDOG else object):
    """
    디렉토리에 새 PNG 파일이 생성되면 on_render_complete 콜백을 호출합니다.
    """
    
    def __init__(self, on_render_complete, extensions=(".png", ".jpg", ".exr")):
        if HAS_WATCHDOG:
            super().__init__()
        self.on_render_complete = on_render_complete
        self.extensions = extensions

    def on_created(self, event):
        if not event.is_directory:
            _, ext = os.path.splitext(event.src_path)
            if ext.lower() in self.extensions:
                self.on_render_complete(event.src_path)


class RenderStatusPoller:
    """
    렌더링 상태 JSON 파일을 주기적으로 폴링하여 상태 변경을 감지합니다.
    watchdog 없이도 동작하는 대안적 방법입니다.
    """
    
    def __init__(self, status_file_path, on_status_change, poll_interval=0.5):
        self.status_file   = status_file_path
        self.callback      = on_status_change
        self.poll_interval = poll_interval
        self._running      = False
        self._thread       = None
        self._last_state   = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def _poll_loop(self):
        while self._running:
            if os.path.exists(self.status_file):
                try:
                    with open(self.status_file, "r", encoding="utf-8") as f:
                        status = json.load(f)
                    state = status.get("state")
                    if state != self._last_state:
                        self._last_state = state
                        self.callback(status)
                except (json.JSONDecodeError, IOError):
                    pass
            time.sleep(self.poll_interval)


class FileWatcher:
    """
    디렉토리에서 새 렌더링 파일을 감지하는 워처입니다.
    watchdog이 있으면 watchdog을 사용하고, 없으면 폴링을 사용합니다.
    """
    
    def __init__(self, watch_dir, on_new_file, extensions=(".png", ".jpg", ".exr")):
        self.watch_dir    = watch_dir
        self.on_new_file  = on_new_file
        self.extensions   = extensions
        self._observer    = None
        self._poll_thread = None
        self._running     = False
        self._known_files = set()

    def start(self):
        os.makedirs(self.watch_dir, exist_ok=True)
        self._running = True
        
        # 현재 존재하는 파일 기록
        self._known_files = self._scan_existing()
        
        if HAS_WATCHDOG:
            handler = RenderCompleteHandler(self.on_new_file, self.extensions)
            self._observer = Observer()
            self._observer.schedule(handler, self.watch_dir, recursive=False)
            self._observer.start()
        else:
            # 폴링 방식 폴백
            self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._poll_thread.start()

    def stop(self):
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join()
        if self._poll_thread:
            self._poll_thread.join(timeout=2.0)

    def _scan_existing(self) -> set:
        files = set()
        if os.path.isdir(self.watch_dir):
            for fname in os.listdir(self.watch_dir):
                _, ext = os.path.splitext(fname)
                if ext.lower() in self.extensions:
                    files.add(os.path.join(self.watch_dir, fname))
        return files

    def _poll_loop(self):
        while self._running:
            current = self._scan_existing()
            new_files = current - self._known_files
            for fpath in new_files:
                self.on_new_file(fpath)
            self._known_files = current
            time.sleep(1.0)
