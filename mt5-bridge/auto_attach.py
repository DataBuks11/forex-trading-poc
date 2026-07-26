import pyautogui
import time

# Find and activate MT5 window
print("Looking for MT5 window...")
windows = pyautogui.getAllWindows()
mt5 = None
for w in windows:
    if "CXMDirect-Live" in w.title:
        mt5 = w
        break

if not mt5:
    print("MT5 not found!")
    exit(1)

print(f"Found: {mt5.title}")
mt5.activate()
time.sleep(2)

# Press Ctrl+N to open Navigator
print("Opening Navigator...")
pyautogui.hotkey('ctrl', 'n')
time.sleep(2)

# Type "bridge" to find it in the Navigator
print("Selecting bridge EA...")
pyautogui.typewrite('bridge', interval=0.1)
time.sleep(1.5)

# Press Enter twice - first to select, second to open/attach
pyautogui.press('enter')
time.sleep(1)
pyautogui.press('enter')
time.sleep(3)

# Check if it worked by looking for the EA smiley face on the chart
print("Done. Checking if bridge is connected...")

# Test bridge file communication
import os
os.makedirs("C:\\mt5_bridge", exist_ok=True)
Path("C:\\mt5_bridge\\command.txt").write_text("PING")
time.sleep(3)
resp = Path("C:\\mt5_bridge\\response.txt").read_text().strip() if Path("C:\\mt5_bridge\\response.txt").exists() else ""
if resp:
    print(f"Bridge EA responding: {resp}")
else:
    print("Bridge not responding yet. Try dragging 'bridge' onto chart manually.")
    print("Press Ctrl+N in MT5, find 'bridge' under Expert Advisors, drag to EURUSD chart.")
