# ===============================================
# file: app_control.py
# ===============================================
# -*- coding: utf-8 -*-
from __future__ import annotations

import os, time, psutil
from psutil    import Process
from pywinauto import Application
from common.singleton import SingletonMeta
from common.log import logger

try:
    from pywintypes import error as PyWinError  # pywin32 errors (e.g., winerror 740)
except Exception:
    PyWinError = OSError


class ProcessControl(metaclass=SingletonMeta):
    """Minimal app launcher. Only starts the EXE when asked."""
    def __init__(self, exe_path:str, worker_exe_path, backend:str = "win32"):
        self.exe_path = exe_path
        self.worker_exe_path = worker_exe_path
        self.backend = backend
        self.app: Application = None # pid = .process 
        self.process: Process = None # name = .info["name"], pid = .info["pid"]
        self.worker_process: Process = None
    
    def _find_process(self, name_prefix: str = None) -> Application: 
        name_prefix = name_prefix if name_prefix else self.process.name if self.process else None
        if name_prefix == None: 
            raise FileNotFoundError(f"process name must be given")
        
        start_time = time.time()
        while True: 
            for p in psutil.process_iter(["name"]):
                name = p.name() #.lower()
                if name.startswith(name_prefix): 
                    app = Application(backend=self.backend).connect(process=p.pid)
                    # print(f"{name} is running (pid={p.pid})")
                    return app, p
            
            time.sleep(1.0)
            if time.time() - start_time >= 2:
                return None, None
            
    def start(self) -> ProcessControl: 
        cnt = self.kill_all()
        logger.info("Killed %s processes", cnt)
        if cnt > 0: 
            time.sleep(1.5)
        # Assure that there's no running process

        app, process = self._find_process(os.path.basename(self.exe_path))
        # Start it 
        if process == None: 
            if not self.exe_path or not os.path.exists(self.exe_path):
                raise FileNotFoundError(f"{type(e).__name__}: {e}: {self.exe_path} is not found")
            
            """Start the EXE. If UAC (740) blocks, ignore (window finder will retry)."""
            try:
                app = Application(backend=self.backend).start(f'"{self.exe_path}"')
            except Exception as e:
                # Elevation required, or already running under elevated context.
                if getattr(e, "winerror", None) == 740:
                    # Silently proceed; MainWinCtrl will try to find the window by title.
                    return self
                raise OSError(f"{self.exe_path} failed to start {e.strerror}")
        
            time.sleep(1.0)
            if psutil.pid_exists(app.process): # pid 
                process = psutil.Process(app.process)
                print(f"Process is running: {process.name}")
            else: 
                raise OSError(f"{self.exe_path} failed to start")
        else: 
            print(f"Process is running: {process.name}")
        
        self.app = app
        self.process = process
        return self

    def kill_all(self):
        cnt = 0
        for name in [self.exe_path, self.worker_exe_path]: 
            cnt += self.kill_by_exe_name(name)
        return cnt

    def kill_by_exe_name(self, exe_path): 
        """
        exe 파일의 full path에서 파일명만 추출한 뒤,
        그 파일명을 prefix로 갖는 모든 프로세스를 kill한다.
        """
        if not exe_path:
            return 0

        # 파일명 추출 (예: "C:\\a\\b\\worker.exe" → "worker.exe")
        exe_name = os.path.basename(exe_path)
        prefix = os.path.splitext(exe_name)[0]  # worker.exe → worker

        cnt = 0
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                pname = proc.info.get("name", "") or "" # 파일 이름 
                pexe  = proc.info.get("exe", "") or ""  # 전체 경로 이름

                # prefix match 판단
                # 1) 프로세스 이름으로 판단
                if pname.lower().startswith(prefix.lower()):
                    proc.kill()
                    cnt += 1
                    continue

                # 2) exe path로 판단 (파일명이 같은 경우)
                base = os.path.basename(pexe)
                if base.lower().startswith(prefix.lower()):
                    proc.kill()
                    cnt += 1

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return cnt

