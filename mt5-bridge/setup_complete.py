"""
Auto-setup: Install ngrok, start MT5 with EA, run bridge, expose via ngrok.
Run this once to set up everything.
"""
import subprocess
import os
import time
import sys
import shutil
import uuid

def run(cmd, shell=True):
    return subprocess.run(cmd, shell=shell, capture_output=True, text=True)

print("=" * 60)
print("  ForexTrade - Complete Auto Setup")
print("=" * 60)

# ====== 1. Ensure bridge.ex5 is in MT5 Experts ======
print("\n[1/5] Ensuring EA is installed...")
experts = os.path.join(os.environ["APPDATA"], "MetaQuotes", "Terminal", 
                        "D0E8209F77C8CF37AD8BF550E51FF075", "MQL5", "Experts")
bridge_dir = os.path.dirname(os.path.abspath(__file__))
src_mq5 = os.path.join(bridge_dir, "bridge.mq5")
dst_mq5 = os.path.join(experts, "bridge.mq5")
shutil.copy2(src_mq5, dst_mq5)
print(f"  EA copied to: {dst_mq5}")

# ====== 2. Kill MT5 and restart ======
print("\n[2/5] Restarting MT5...")
run("taskkill /F /IM terminal64.exe", shell=True)
time.sleep(3)
mt5_path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
subprocess.Popen([mt5_path, "/portable"])
print("  MT5 starting, waiting 25s...")
time.sleep(25)

# ====== 3. Try to compile and attach EA via keystrokes ======
print("\n[3/5] Attempting to compile and attach EA...")

import pyautogui
pyautogui.FAILSAFE = True

# Find MT5
mt5_win = None
for w in pyautogui.getAllWindows():
    if "CXMDirect-Live" in w.title or "732959" in w.title:
        mt5_win = w
        break

if mt5_win:
    mt5_win.activate()
    mt5_win.maximize()
    time.sleep(2)
    
    # Compile: F4 (MetaEditor) -> Ctrl+F7 (compile)
    print("  Opening MetaEditor...")
    pyautogui.hotkey('f4')
    time.sleep(3)
    print("  Compiling...")
    pyautogui.hotkey('ctrl', 'f7')
    time.sleep(3)
    
    # Close MetaEditor
    pyautogui.hotkey('alt', 'f4')
    time.sleep(2)
    
    print("  EA should be compiled. Check MT5 Navigator.")
else:
    print("  MT5 window not found for automation")

# ====== 4. Start the bridge ======
print("\n[4/5] Starting MT5 Bridge...")
os.environ["MT5_LOGIN"] = "732959"
os.environ["MT5_SERVER"] = "CXMDirect-Live"

# Start bridge in background
bridge_proc = subprocess.Popen(
    [sys.executable, os.path.join(bridge_dir, "bridge.py")],
    cwd=bridge_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
time.sleep(5)
print(f"  Bridge PID: {bridge_proc.pid}")

# Test health
import urllib.request
try:
    resp = urllib.request.urlopen("http://localhost:8765/health", timeout=5)
    print(f"  Bridge health: {resp.read().decode()}")
except:
    print("  Bridge not responding yet...")

# ====== 5. Check for ngrok ======
print("\n[5/5] Checking ngrok...")
ngrok_path = shutil.which("ngrok")
if not ngrok_path:
    # Try common paths
    for p in [r"C:\ngrok\ngrok.exe", os.path.expanduser(r"~\ngrok\ngrok.exe")]:
        if os.path.exists(p):
            ngrok_path = p
            break

if ngrok_path:
    print(f"  ngrok found: {ngrok_path}")
    print(f"  Run: ngrok http 8765")
    print(f"  Then set bridge URL in web app")
else:
    print("  ngrok not found. Download from https://ngrok.com")
    print("  After installing, run: ngrok http 8765")

print("\n" + "=" * 60)
print("  SETUP COMPLETE")
print("=" * 60)
print(f"  Bridge: http://localhost:8765")
print(f"  Web app: https://frontend-fawn-omega-29.vercel.app")
print()
print("  ONE MANUAL STEP:")
print("  In MT5, press Ctrl+N, find 'bridge' under Expert")
print("  Advisors, drag it onto EURUSD chart, click OK.")
print()

# Keep running
input("Press Enter to stop the bridge...")
bridge_proc.terminate()
