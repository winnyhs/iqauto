# ===============================================
# file: app_control.py
# ===============================================
# -*- coding: utf-8 -*-
from __future__ import annotations

import os, time, psutil
from psutil    import Process
from pywinauto import Application
from lib.singleton_meta import SingletonMeta

try:
    from pywintypes import error as PyWinError  # pywin32 errors (e.g., winerror 740)
except Exception:
    PyWinError = OSError


class ProcessControl(metaclass=SingletonMeta):
    """Minimal app launcher. Only starts the EXE when asked."""
    def __init__(self, exe_path:str, backend:str = "win32"):
        self.exe_path = exe_path
        self.backend = backend
        self.app: Application = None # pid = .process 
        self.process: Process = None # name = .info["name"], pid = .info["pid"]
    
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
        app, process = self._find_process(os.path.basename(self.exe_path))
        
        # There's no running process yet
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
