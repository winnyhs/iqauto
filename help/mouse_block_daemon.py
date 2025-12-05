# file: mouse_block_daemon.py
# Python 3.4 compatible. WinXP(32bit) ~ Win10(64bit).
# Singleton mouse-blocker DAEMON with robust cleanup on normal/abnormal termination.


# TODO: 
# 1. medical_auto.exe를 실행할 때, 실행되도록 코드 추가 
# 2. kill, segmentation fault 같은 상황에서의 복구방법이 필요한데, watch dog을 또 띄워야 한다는 건데... 
from __future__ import print_function
import sys, os, time, threading, ctypes, platform, atexit, signal, subprocess
from ctypes import wintypes

# ====== pywin32 ======
import win32api, win32con

# ====== Config ======
CHECK_INTERVAL_SEC = 3.0
TARGET_PROCESSES   = ["medical_auto.exe", "python.exe"]  # 필요 시 수정
MUTEX_NAME         = u"Global\\MB_DAEMON_V2"
EVT_ACTIVATE_NAME  = u"Global\\MB_ACTIVATE_V2"

# ====== Platform detect ======
PTR_BITS = ctypes.sizeof(ctypes.c_void_p) * 8
IS_64 = (PTR_BITS == 64)
IS_XP = (sys.getwindowsversion().major < 6)  # 5.x = XP/2003

def _long_ptr():  return ctypes.c_longlong if IS_64 else ctypes.c_long
def _ulong_ptr(): return ctypes.c_ulonglong if IS_64 else ctypes.c_ulong

# ====== WinAPI base ======
user32   = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Console control handler (CTRL_C/BREAK/CLOSE/LOGOFF/SHUTDOWN)
PHANDLER_ROUTINE = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
kernel32.SetConsoleCtrlHandler.argtypes = (PHANDLER_ROUTINE, wintypes.BOOL)
kernel32.SetConsoleCtrlHandler.restype  = wintypes.BOOL
CTRL_C_EVENT=0; CTRL_BREAK_EVENT=1; CTRL_CLOSE_EVENT=2; CTRL_LOGOFF_EVENT=5; CTRL_SHUTDOWN_EVENT=6

# ====== Toolhelp for process enum (XP-safe) ======
TH32CS_SNAPPROCESS = 0x00000002
MAX_PATH = 260
class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_wchar * MAX_PATH),
    ]
CreateToolhelp32Snapshot = kernel32.CreateToolhelp32Snapshot
CreateToolhelp32Snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
CreateToolhelp32Snapshot.restype  = wintypes.HANDLE
Process32FirstW = kernel32.Process32FirstW
Process32FirstW.argtypes = (wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32))
Process32FirstW.restype  = wintypes.BOOL
Process32NextW = kernel32.Process32NextW
Process32NextW.argtypes = (wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32))
Process32NextW.restype  = wintypes.BOOL
CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = (wintypes.HANDLE,)
CloseHandle.restype  = wintypes.BOOL


import threading
import pythoncom
import win32com.client
def is_process_running(substrings):
    """
    True iff there exists a process whose full CommandLine contains ALL `substrings` (case-insensitive).
    Runs WMI in a dedicated thread to avoid 'Win32 exception occurred releasing IUnknown'.
    XP/Win10, Python 3.4+ compatible (requires pywin32).
    """
    subs = [s.lower() for s in (substrings or []) if s]
    if not subs:
        return False

    result = {"found": False, "err": None}
    def _worker():
        locator = svc = col = None
        try:
            # STA initialize
            pythoncom.CoInitialize()
            try:
                # Connect WMI
                locator = win32com.client.Dispatch("WbemScripting.SWbemLocator")
                svc = locator.ConnectServer(".", "root\\cimv2")
                # Forward-only, return-immediately flags (reduce COM caching)
                WBEM_FLAG_RETURN_IMMEDIATELY = 0x10
                WBEM_FLAG_FORWARD_ONLY       = 0x20
                col = svc.ExecQuery(
                    "SELECT CommandLine FROM Win32_Process",
                    "WQL",
                    WBEM_FLAG_RETURN_IMMEDIATELY | WBEM_FLAG_FORWARD_ONLY
                )

                # Materialize to pure Python list, then drop all COM refs
                cmds = []
                for p in col:
                    try:
                        cmds.append((p.CommandLine or u"").lower())
                    except Exception:
                        cmds.append(u"")

                # HARD RELEASE (very important before CoUninitialize)
                col = None; svc = None; locator = None

                # Filter on Python side
                for cmd in cmds:
                    if cmd and all(s in cmd for s in subs):
                        result["found"] = True
                        break
            finally:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass
        except Exception as e:
            result["err"] = e

    t = threading.Thread(target=_worker, name="WMICommandLineProbe")
    t.daemon = True
    t.start()
    t.join(5.0)  # 5s timeout; adjust if needed

    # If thread hung/failed, be conservative (no false positives)
    return bool(result["found"])


# ====== MouseBlocker (low-level hook) ======
HHOOK     = getattr(wintypes, "HHOOK", wintypes.HANDLE)
HWND      = wintypes.HWND
HINSTANCE = getattr(wintypes, "HINSTANCE", wintypes.HANDLE)
UINT      = wintypes.UINT
DWORD     = wintypes.DWORD
BOOL      = wintypes.BOOL
INT       = wintypes.INT
WPARAM    = getattr(wintypes, "WPARAM", _ulong_ptr())
LPARAM    = getattr(wintypes, "LPARAM", _long_ptr())
LRESULT   = getattr(wintypes, "LRESULT", _long_ptr())
try:
    ULONG_PTR = wintypes.ULONG_PTR
except Exception:
    ULONG_PTR = _ulong_ptr()

WH_MOUSE_LL  = 14
LLMHF_INJECTED          = 0x00000001
LLMHF_LOWER_IL_INJECTED = 0x00000002
ALLOW_FLAGS             = (LLMHF_INJECTED | LLMHF_LOWER_IL_INJECTED)
# our dwExtraInfo tag (32/64 safe)
INJECT_TAG              = 0x33ADF00DBEEF1111 if IS_64 else 0x0BEEF111

LowLevelMouseProc = ctypes.WINFUNCTYPE(LRESULT, INT, WPARAM, LPARAM)
user32.SetWindowsHookExW.argtypes = (INT, LowLevelMouseProc, HINSTANCE, DWORD)
user32.SetWindowsHookExW.restype  = HHOOK
user32.CallNextHookEx.argtypes    = (HHOOK, INT, WPARAM, LPARAM)
user32.CallNextHookEx.restype     = LRESULT
user32.UnhookWindowsHookEx.argtypes = (HHOOK,)
user32.UnhookWindowsHookEx.restype  = BOOL
user32.GetMessageW.argtypes       = (ctypes.POINTER(wintypes.MSG), HWND, UINT, UINT)
user32.GetMessageW.restype        = BOOL
user32.TranslateMessage.argtypes  = (ctypes.POINTER(wintypes.MSG),)
user32.TranslateMessage.restype   = BOOL
user32.DispatchMessageW.argtypes  = (ctypes.POINTER(wintypes.MSG),)
user32.DispatchMessageW.restype   = LRESULT

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]
class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("pt", POINT), ("mouseData", DWORD), ("flags", DWORD), ("time", DWORD), ("dwExtraInfo", ULONG_PTR)]

# SendInput (태그된 DOWN/UP용 최소 정의)
INPUT_MOUSE = 0
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", DWORD),
                ("dwFlags", DWORD), ("time", DWORD), ("dwExtraInfo", ULONG_PTR)]
class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]
class INPUT(ctypes.Structure):
    _fields_ = [("type", DWORD), ("u", INPUT_UNION)]
user32.SendInput.argtypes = (UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype  = UINT
def _send_mouse(flags, dx=0, dy=0, data=0, extra=INJECT_TAG):
    ip = INPUT(); ip.type = INPUT_MOUSE
    ip.u.mi = MOUSEINPUT(dx, dy, data, flags, 0, ULONG_PTR(extra))
    if user32.SendInput(1, ctypes.byref(ip), ctypes.sizeof(INPUT)) != 1:
        raise OSError("SendInput failed: %d" % ctypes.get_last_error())

class MouseBlocker(object):
    """Blocks human mouse events; our injected/flagged events pass."""
    def __init__(self):
        self._hook = HHOOK()
        self._thread = None
        self._stop_evt = threading.Event()
        self._block_active = threading.Event()
        self._tls = threading.local()

    @staticmethod
    def _is_our_injected(ms):
        if ms.flags & ALLOW_FLAGS: return True
        try: return int(ms.dwExtraInfo) == INJECT_TAG
        except Exception: return False

    def _install_hook(self):
        @LowLevelMouseProc
        def _proc(nCode, wParam, lParam):
            if nCode < 0:
                return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)
            ms = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            if self._block_active.is_set() and (not self._is_our_injected(ms)):
                return 1
            return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)
        self._tls.proc = _proc
        self._hook = user32.SetWindowsHookExW(WH_MOUSE_LL, self._tls.proc, HINSTANCE(0), DWORD(0))
        if not self._hook:
            raise OSError("SetWindowsHookExW failed: %d" % ctypes.get_last_error())

    def _uninstall_hook(self):
        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = HHOOK()

    def _hook_thread(self):
        try:
            self._install_hook()
            msg = wintypes.MSG()
            while not self._stop_evt.is_set():
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret in (0, -1): break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            self._uninstall_hook()

    def activate(self):
        if self._thread and self._thread.is_alive():
            self._block_active.set(); return
        self._stop_evt.clear(); self._block_active.set()
        self._thread = threading.Thread(target=self._hook_thread, name="MBHook")
        self._thread.daemon = True
        self._thread.start()
        time.sleep(0.03)

    def deactivate(self):
        self._block_active.clear()

    def shutdown(self):
        self._block_active.clear()
        self._stop_evt.set()
        if self._thread:
            self._thread.join(0.3)
        self._thread = None

# ====== IPC: Mutex + Event ======
ERROR_ALREADY_EXISTS = 183
CreateMutexW = kernel32.CreateMutexW
CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
CreateMutexW.restype  = wintypes.HANDLE
OpenEventW = kernel32.OpenEventW
OpenEventW.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR)
OpenEventW.restype  = wintypes.HANDLE
CreateEventW = kernel32.CreateEventW
CreateEventW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR)
CreateEventW.restype  = wintypes.HANDLE
SetEvent = kernel32.SetEvent
SetEvent.argtypes = (wintypes.HANDLE,)
SetEvent.restype  = wintypes.BOOL
WaitForSingleObject = kernel32.WaitForSingleObject
WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
WaitForSingleObject.restype  = wintypes.DWORD
WAIT_OBJECT_0 = 0

# ====== Global state for cleanup ======
_g_blocker = None
_g_evt = None
_g_mutex = None

def _cleanup():
    """Idempotent cleanup for all termination paths."""
    global _g_blocker, _g_evt, _g_mutex
    try:
        if _g_blocker: _g_blocker.shutdown()
    except Exception:
        pass
    try:
        if _g_evt: CloseHandle(_g_evt)
    except Exception:
        pass
    try:
        if _g_mutex: CloseHandle(_g_mutex)
    except Exception:
        pass

# atexit: 프로세스 정상 종료 시
atexit.register(_cleanup)

# signals: CTRL+C/SIGTERM/SIGBREAK
def _sig_handler(signum, frame):
    _cleanup()
    # 원래 동작 계속 진행 (프로세스 종료)
for _s in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None), getattr(signal, "SIGBREAK", None)):
    if _s is not None:
        try: signal.signal(_s, _sig_handler)
        except Exception: pass

# Console control handler: 콘솔 닫힘/로그오프/셧다운 등
@PHANDLER_ROUTINE
def _ctrl_handler(evt):
    _cleanup()
    return False  # OS 기본 종료 계속

try:
    kernel32.SetConsoleCtrlHandler(_ctrl_handler, True)
except Exception:
    pass

# 미처리 예외: shutdown 후 원래 excepthook 호출
_orig_excepthook = sys.excepthook
def _ex_hook(t, v, tb):
    try: _cleanup()
    except Exception: pass
    _orig_excepthook(t, v, tb)
sys.excepthook = _ex_hook


# ====== Daemon main loop ======
def daemon_main():
    global _g_blocker, _g_evt, _g_mutex
    _g_mutex = CreateMutexW(None, False, MUTEX_NAME)
    if not _g_mutex:
        print("[daemon] CreateMutex failed:", ctypes.get_last_error()); return 2
    existed = (ctypes.get_last_error() == ERROR_ALREADY_EXISTS)
    if existed:
        # 이미 떠 있음 → 활성화 신호만 주고 종료
        h = OpenEventW(0x0002, False, EVT_ACTIVATE_NAME)  # EVENT_MODIFY_STATE
        if h:
            SetEvent(h); CloseHandle(h)
            print("[daemon] already running; activated")
        else:
            print("[daemon] already running; activate event not found")
        return 0

    print("[daemon] started. Platform=%s %dbit XP=%s" % (platform.system(), PTR_BITS, IS_XP))
    _g_evt = CreateEventW(None, False, False, EVT_ACTIVATE_NAME)
    if not _g_evt:
        print("[daemon] CreateEvent failed:", ctypes.get_last_error()); return 3

    _g_blocker = MouseBlocker()
    miss_cnt = 0
    found_cnt = 0
    announce_left = 0

    try:
        while True:
            # 외부 activate 신호
            if WaitForSingleObject(_g_evt, 0) == WAIT_OBJECT_0:
                _g_blocker.activate()
                print("[daemon] external activate()")

            alive = is_process_running(TARGET_PROCESSES)
            if alive:
                if not _g_blocker._block_active.is_set():
                    _g_blocker.activate()
                    print("[daemon] activate() (target detected)")
                found_cnt += 1; miss_cnt = 0
                if found_cnt % 3 == 0:
                    announce_left = max(announce_left, 5)
            else:
                miss_cnt += 1; found_cnt = 0
                if miss_cnt >= 3:
                    print("[daemon] target missing x3 → blocker OFF; daemon exit")
                    break

            if announce_left > 0:
                print("[daemon] active (target present)"); announce_left -= 1

            time.sleep(CHECK_INTERVAL_SEC)

    except Exception as e:
        # 예외 종료 시 명시적 shutdown
        print("[daemon] exception:", e)
        _cleanup()
        return 1
    finally:
        _cleanup()
        print("[daemon] stopped")

# ====== Launcher (detached) ======
def start_daemon_detached():
    py = sys.executable
    this = os.path.abspath(__file__)
    # 완전 분리: 새 콘솔/새 그룹
    creation = 0x00000010 | 0x00000200  # CREATE_NEW_CONSOLE | CREATE_NEW_PROCESS_GROUP
    subprocess.Popen([py, this, "daemon"], close_fds=True, creationflags=creation)



# ====== CLI ======
def _usage():
    print("Usage:")
    print("  python mouse_block_daemon.py daemon         # run singleton daemon")
    print("  python mouse_block_daemon.py start          # start daemon detached")
    print("  python mouse_block_daemon.py poke           # signal existing daemon to activate()")
    print("Notes: edit TARGET_PROCESSES in this file as needed.")

def main(argv):
    if len(argv) < 2:
        _usage(); 
        return 1
    
    print("To turn on mouse, press [ Ctrl + Alt + M ] !")

    cmd = argv[1].lower()
    if cmd == "daemon":
        print("Started running as a daemon")
        return daemon_main()
    elif cmd == "start":
        print("Started running as a daemon, that is detached from the parent")
        start_daemon_detached(); return 0
    elif cmd == "poke":
        print("Presumed it's already running. Sent activation signal.")
        h = OpenEventW(0x0002, False, EVT_ACTIVATE_NAME)
        if h:
            SetEvent(h); CloseHandle(h); print("[poke] activate signaled"); return 0
        print("[poke] daemon not running"); return 2
    else:
        _usage(); return 1



if __name__ == "__main__":

    want = ["python", "main.py"]
    if is_process_running(want) == False: 
        print(f"Waiting for 5 second to start medical_auto ...")
        time.sleep(5.0)
    sys.exit(main(sys.argv))
