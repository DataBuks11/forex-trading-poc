"""
Final attempt - uses context menu to attach EA.
"""
import pyautogui
import time
import os
import uuid

pyautogui.FAILSAFE = True

# Find MT5 window
print("Looking for MT5...")
mt5_win = None
for w in pyautogui.getAllWindows():
    if "732959" in w.title:
        mt5_win = w
        break
if not mt5_win:
    print("MT5 not found")
    exit(1)

mt5_win.activate()
time.sleep(1)

# Step 1: Open Navigator
print("Step 1: Opening Navigator...")
pyautogui.hotkey('ctrl', 'n')
time.sleep(2)

# Step 2: Search for bridge
print("Step 2: Searching bridge...")
pyautogui.hotkey('ctrl', 'f')
time.sleep(0.5)
pyautogui.write('bridge', interval=0.05)
time.sleep(1.5)

# Step 3: Press Tab to move focus to the tree results
print("Step 3: Moving to tree...")
pyautogui.press('tab')
time.sleep(0.5)

# Step 4: Navigate down to Expert Advisors section then to bridge
print("Step 4: Navigating to bridge...")
for _ in range(3):
    pyautogui.press('right')  # Expand folders
    time.sleep(0.3)
for _ in range(5):
    pyautogui.press('down')
    time.sleep(0.3)

# Step 5: Open context menu and select "Attach to chart"
print("Step 5: Context menu -> Attach to chart...")
pyautogui.hotkey('shift', 'f10')  # or apps key
time.sleep(1.5)

# Navigate to "Attach to chart" - usually the first option
pyautogui.press('enter')  # First item in context menu is usually "Attach to chart"
time.sleep(3)

# If a dialog opens, press OK
pyautogui.press('enter')
time.sleep(2)

# Step 6: Test connection
print("Step 6: Testing connection...")
common = os.path.join(os.environ["APPDATA"], "MetaQuotes", "Terminal", "Common", "Files")
os.makedirs(common, exist_ok=True)
cmd_file = os.path.join(common, "command.txt")
resp_file = os.path.join(common, "response.txt")

with open(resp_file, 'w') as f: f.write("")
with open(cmd_file, 'w') as f: f.write(f"{uuid.uuid4().hex[:8]}|PING")

for i in range(15):
    time.sleep(1)
    try:
        with open(resp_file, 'r') as f:
            r = f.read().strip()
        if r:
            print(f"  Response: {r}")
            if "PONG" in r:
                print("\n*** SUCCESS! Bridge connected! ***")
                exit(0)
    except:
        pass

print("\nCould not auto-attach. Please drag 'bridge' EA onto your MT5 chart.")
