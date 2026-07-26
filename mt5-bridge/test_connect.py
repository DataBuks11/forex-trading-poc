"""
Simple MT5 connection test - no bridge, no FastAPI, just direct connection.
This bypasses all the bridge complexity.
"""
import MetaTrader5 as mt5
import os
import time

print("=== MT5 Direct Connection Test ===")
print()

# Use the credentials directly
LOGIN = 732959
PASSWORD = "Ca7@nmX2"
SERVER = "CXMDirect-Live"

# Try method 1: Direct initialize with credentials (bypasses IPC)
print("[1] Trying mt5.initialize() with direct login credentials...")
for attempt in range(3):
    try:
        # First shutdown any previous attempt
        try:
            mt5.shutdown()
        except:
            pass
        time.sleep(1)
        
        result = mt5.initialize(
            path=r"C:\Program Files\MetaTrader 5\terminal64.exe",
            login=LOGIN,
            password=PASSWORD,
            server=SERVER,
            timeout=30000
        )
        if result:
            print(f"    SUCCESS on attempt {attempt+1}!")
            break
        else:
            err = mt5.last_error()
            print(f"    Attempt {attempt+1}: FAILED - {err}")
    except Exception as e:
        print(f"    Attempt {attempt+1}: EXCEPTION - {e}")

if not result:
    print()
    print("[2] Trying default mt5.initialize() then login...")
    for attempt in range(3):
        try:
            try:
                mt5.shutdown()
            except:
                pass
            time.sleep(1)
            
            if mt5.initialize():
                print(f"    initialize() OK on attempt {attempt+1}")
                auth = mt5.login(login=LOGIN, password=PASSWORD, server=SERVER)
                if auth:
                    print(f"    login() SUCCESS!")
                    result = True
                    break
                else:
                    print(f"    login() FAILED - {mt5.last_error()}")
                    mt5.shutdown()
            else:
                print(f"    initialize() FAILED - {mt5.last_error()}")
        except Exception as e:
            print(f"    Attempt {attempt+1}: EXCEPTION - {e}")

if result:
    print()
    print("=== CONNECTED SUCCESSFULLY ===")
    info = mt5.account_info()
    if info:
        print(f"  Account:  {info.login}")
        print(f"  Server:   {info.server}")
        print(f"  Company:  {info.company}")
        print(f"  Balance:  {info.balance} {info.currency}")
        print(f"  Equity:   {info.equity}")
        print(f"  Leverage: 1:{info.leverage}")
        print(f"  Type:     {'Demo' if info.trade_mode == 0 else 'Live'}")
    print()
    
    # Get positions
    positions = mt5.positions_get()
    if positions:
        print(f"  Open positions: {len(positions)}")
        for p in positions:
            print(f"    #{p.ticket} {p.symbol} {p.type} vol={p.volume} profit={p.profit}")
    else:
        print(f"  No open positions")
    
    mt5.shutdown()
else:
    print()
    print("=== FAILED ===")
    print("MetaTrader5 package cannot connect to your terminal.")
    print()
    print("Reasons:")
    print("1. MT5 terminal not running - open MT5, log in, then retry")
    print("2. Python 3.13 incompatible - use Python 3.10 or 3.11")
    print("3. MT5 build too new/old for this package version")
    print("4. Try: pip install MetaTrader5==5.0.45")
