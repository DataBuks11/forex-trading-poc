Add-Type @"
using System;
using System.Runtime.InteropServices;
public class K {
    [DllImport("user32.dll")] public static extern IntPtr FindWindow(string c, string w);
    [DllImport("user32.dll")] public static extern IntPtr FindWindowEx(IntPtr p, IntPtr c, string cls, string wnd);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte sc, uint f, UIntPtr d);
    [DllImport("user32.dll")] public static extern IntPtr PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
    public const byte ALT=0x12, CTRL=0x11, SHIFT=0x10, ENTER=0x0D, ESC=0x1B, TAB=0x09;
    public const byte A=0x41,N=0x4E,O=0x4F,I=0x49,R=0x52,DOWN=0x28,UP=0x26,F5=0x74,NUMPAD_ADD=0x6B;
    public const uint KEYUP=0x2, WM_KEYDOWN=0x100, WM_KEYUP=0x101;
}
"@

function SendKey($key) {
    [K]::keybd_event($key, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 80
    [K]::keybd_event($key, 0, [K]::KEYUP, [UIntPtr]::Zero)
}

function SendKeyCombo($mod, $key) {
    [K]::keybd_event($mod, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 50
    SendKey $key
    Start-Sleep -Milliseconds 50
    [K]::keybd_event($mod, 0, [K]::KEYUP, [UIntPtr]::Zero)
}

$mt5 = [K]::FindWindow("MetaQuotes::MetaTrader::5.00", $null)
if (-not $mt5) { Write-Output "MT5 not found"; exit 1 }

[K]::SetForegroundWindow($mt5)
Start-Sleep 2
Write-Output "MT5 active"

# Press F4 to open MT5 main menu, then navigate to EA properties
# Alternatively: right-click chart area, then Expert Advisors

# First, ensure a chart is focused by clicking in the middle
# Then press Ctrl+I to open "Expert Advisors" dialog
SendKeyCombo ([K]::CTRL) ([K]::I)
Start-Sleep 3
Write-Output "Ctrl+I sent"

# The Expert List dialog should be open
# Press Tab to move to the list
SendKey ([K]::TAB)
Start-Sleep -Milliseconds 200
SendKey ([K]::TAB)
Start-Sleep -Milliseconds 200

# Navigate to bridge
for ($i=0; $i -lt 5; $i++) {
    [K]::keybd_event([K]::DOWN, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 80
    [K]::keybd_event([K]::DOWN, 0, [K]::KEYUP, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 200
}
Write-Output "Navigated down"

# Press Space to check/select
SendKey 0x20
Start-Sleep -Milliseconds 200

# Press Enter
SendKey ([K]::ENTER)
Start-Sleep 3
Write-Output "Done - bridge EA should be attached"
