"""Windows-specific utility to globally suppress console windows for all subprocesses."""
from __future__ import annotations

import subprocess
import sys
import os
import ctypes
import threading
import time
from ctypes import wintypes
from datetime import datetime

# AUDIT LOG to identify any bypasses
AUDIT_LOG = os.path.expanduser("~/.devready/logs/process_audit.log")

# BEDROCK PATCH: Patch _winapi.CreateProcess directly.
import _winapi
_original_create_process = _winapi.CreateProcess

def _patched_create_process(app_name, cmd_line, proc_attrs, thread_attrs, inherit, flags, env, cwd, sinfo):
    """
    Lowest level hook for process creation on Windows.
    Applies DETACHED_PROCESS and SW_HIDE at the kernel-call boundary.
    """
    try:
        log_dir = os.path.dirname(AUDIT_LOG)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] SPAWN (IRON CURTAIN): {cmd_line or app_name}\n")
    except Exception:
        pass
        
    # SILENT FLAGS: DETACHED_PROCESS (0x8) + CREATE_NO_WINDOW (0x08000000)
    flags |= 0x00000008 | 0x08000000
    
    if sinfo:
        try:
            sinfo['dwFlags'] = sinfo.get('dwFlags', 0) | 0x00000001 # STARTF_USESHOWWINDOW
            sinfo['wShowWindow'] = 0 # SW_HIDE
        except (TypeError, AttributeError):
            pass
            
    return _original_create_process(app_name, cmd_line, proc_attrs, thread_attrs, inherit, flags, env, cwd, sinfo)

# TREE-WIDE WINDOW REAPER: Active Stealth Watcher
def _window_reaper():
    """Background thread that aggressively finds and hides windows from our entire process tree."""
    try:
        import psutil
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        current_process = psutil.Process(os.getpid())
        
        # We'll maintain a set of PIDs to hunt
        target_pids = {os.getpid()}
        
        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def enum_window_proc(hwnd, lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
                
            lp_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lp_pid))
            
            if lp_pid.value in target_pids:
                # Capture window title for audit
                length = user32.GetWindowTextLengthW(hwnd)
                title = "Untitled"
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                
                # SW_HIDE = 0
                if user32.ShowWindow(hwnd, 0):
                    try:
                        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
                            f.write(f"[{datetime.now().isoformat()}] REAPED: '{title}' (PID: {lp_pid.value})\n")
                    except: pass
            return True

        while True:
            # 1. Update the tree of PIDs to monitor
            try:
                new_pids = {os.getpid()}
                for child in current_process.children(recursive=True):
                    new_pids.add(child.pid)
                
                # Common case: also check for any process named "osqueryd" or "syft" 
                # even if they managed to escape our direct tree (rare but possible with shims)
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'] in ['osqueryd.exe', 'syft.exe']:
                        new_pids.add(proc.info['pid'])
                
                target_pids.update(new_pids)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            # 2. Scour and Reap
            user32.EnumWindows(enum_window_proc, 0)
            time.sleep(0.02) # 20ms polling to beat the flicker
    except Exception:
        pass

def start_window_reaper():
    """Starts the active tree-wide window reaper."""
    t = threading.Thread(target=_window_reaper, daemon=True, name="DevReadyWindowReaper")
    t.start()

# OS LEVEL MONKEYPATCHES
_orig_os_system = os.system

def _patched_os_system(command):
    """Replacement for os.system that uses subprocess.run to ensure silence."""
    try:
        res = subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode
    except Exception:
        return _orig_os_system(command)

# IRON CURTAIN: Job Object Lockdown
class JOBOBJECT_BASIC_UI_RESTRICTIONS(ctypes.Structure):
    _fields_ = [("UIRestrictionsClass", wintypes.DWORD)]

def apply_iron_curtain():
    """Places the current process and all its children into a UI-restricted Job Object."""
    if sys.platform != "win32":
        return

    try:
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        hJob = kernel32.CreateJobObjectW(None, f"DevReadySentinelJob_{os.getpid()}")
        if hJob:
            # 0x00000041 = JOB_OBJECT_UILIMIT_HANDLES | JOB_OBJECT_UILIMIT_DESKTOP
            ui_restrictions = JOBOBJECT_BASIC_UI_RESTRICTIONS(0x00000041)
            kernel32.SetInformationJobObject(hJob, 4, ctypes.byref(ui_restrictions), ctypes.sizeof(ui_restrictions))
            kernel32.AssignProcessToJobObject(hJob, kernel32.GetCurrentProcess())
    except Exception:
        pass

def apply_silence(is_background_daemon: bool = False):
    """Apply the final Tree-Wide Reaper protocol if running on Windows."""
    if sys.platform == "win32":
        # 0. Environmental Shield
        os.environ["GIT_PYTHON_REFRESH"] = "quiet"
        os.environ["SHELLINGHAM_SUPPRESS_DETECTION"] = "1"
        os.environ["PYTHONUTF8"] = "1"
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = "git"

        # 1. Kernel Lockdown (Job Objects)
        apply_iron_curtain()

        # 2. Active Stealth (The Tree-Wide Window Reaper)
        start_window_reaper()

        # 3. Global Bedrock Patch
        _winapi.CreateProcess = _patched_create_process
        
        # 4. Redundant Popen Patch
        subprocess.Popen.__init__ = _patched_popen_init
        
        # 5. OS System Patch
        os.system = _patched_os_system

# Preserve Popen hook logic
_original_popen_init = subprocess.Popen.__init__

def _patched_popen_init(self, *pargs, **kwargs):
    if sys.platform == "win32":
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | 0x00000008 | 0x08000000
        sinfo = kwargs.get("startupinfo")
        if sinfo is None:
            sinfo = subprocess.STARTUPINFO()
            kwargs["startupinfo"] = sinfo
        sinfo.dwFlags |= 0x00000001
        sinfo.wShowWindow = 0
        if "stdin" not in kwargs or kwargs["stdin"] is None:
            kwargs["stdin"] = subprocess.DEVNULL
    _original_popen_init(self, *pargs, **kwargs)
