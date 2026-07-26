//+------------------------------------------------------------------+
//|                                          ForexTrade Bridge EA.mq5  |
//|                                  MT5 <-> Python File Bridge       |
//+------------------------------------------------------------------+
#property copyright "ForexTrade"
#property version   "1.00"
#property strict

#define BRIDGE_DIR "C:\\mt5_bridge\\"
#define COMMAND_FILE BRIDGE_DIR "command.txt"
#define RESPONSE_FILE BRIDGE_DIR "response.txt"
#define LOG_FILE BRIDGE_DIR "log.txt"

input int    PollIntervalMs = 500;    // Check for commands every N ms
input bool   EnableLogging   = true;  // Write log entries
input long   MagicNumber     = 123456; // Magic number for trades
input int    Deviation       = 20;    // Slippage in points

string g_last_command_id = "";
datetime g_last_command_time = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   // Ensure bridge directory exists
   if(!FolderCreate(BRIDGE_DIR))
   {
      // Directory may already exist - that's ok
   }
   
   if(EnableLogging)
   {
      int handle = FileOpen(LOG_FILE, FILE_WRITE|FILE_TXT|FILE_COMMON);
      if(handle != INVALID_HANDLE && FileSize(handle) > 100000)
      {
         FileClose(handle);
         FileDelete(LOG_FILE, FILE_COMMON);
      }
      WriteLog("ForexTrade Bridge EA loaded on " + _Symbol + " | Account: " + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + " | Server: " + AccountInfoString(ACCOUNT_SERVER));
   }
   
   EventSetMillisecondTimer(PollIntervalMs);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   WriteLog("Bridge EA removed. Reason: " + IntegerToString(reason));
}

//+------------------------------------------------------------------+
//| Timer function - poll for commands                                 |
//+------------------------------------------------------------------+
void OnTimer()
{
   string command = ReadCommand();
   if(command == "")
      return;
   
   string cmd_id = "";
   string cmd = ParseCommandId(command, cmd_id);
   
   // Skip if already processed
   if(cmd_id == g_last_command_id && g_last_command_time + 5 > TimeCurrent())
      return;
   
   g_last_command_id = cmd_id;
   g_last_command_time = TimeCurrent();
   
   string response = ProcessCommand(cmd);
   WriteResponse(cmd_id, response);
}

//+------------------------------------------------------------------+
//| Read command from file                                             |
//+------------------------------------------------------------------+
string ReadCommand()
{
   string content = "";
   
   // Try common folder first
   int handle = FileOpen(COMMAND_FILE, FILE_READ|FILE_TXT|FILE_COMMON);
   if(handle == INVALID_HANDLE)
   {
      return "";
   }
   
   if(handle != INVALID_HANDLE)
   {
      content = FileReadString(handle, (int)FileSize(handle));
      FileClose(handle);
   }
   
   return content;
}

//+------------------------------------------------------------------+
//| Write response to file                                             |
//+------------------------------------------------------------------+
void WriteResponse(string cmd_id, string response)
{
   int handle = FileOpen(RESPONSE_FILE, FILE_WRITE|FILE_TXT|FILE_COMMON);
   if(handle == INVALID_HANDLE)
      return;
   
   FileSeek(handle, 0, SEEK_SET);
   FileWrite(handle, cmd_id + "|" + response);
   FileClose(handle);
}

//+------------------------------------------------------------------+
//| Write to log file                                                  |
//+------------------------------------------------------------------+
void WriteLog(string message)
{
   if(!EnableLogging) return;
   
   int handle = FileOpen(LOG_FILE, FILE_WRITE|FILE_TXT|FILE_COMMON|FILE_READ);
   if(handle != INVALID_HANDLE)
   {
      FileSeek(handle, 0, SEEK_END);
      FileWrite(handle, TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + " | " + message);
      FileClose(handle);
   }
}

//+------------------------------------------------------------------+
//| Parse command ID from raw command line                             |
//+------------------------------------------------------------------+
string ParseCommandId(string raw, string &out_id)
{
   int sep = StringFind(raw, "|");
   if(sep > 0)
   {
      out_id = StringSubstr(raw, 0, sep);
      return StringSubstr(raw, sep + 1);
   }
   out_id = "";
   return raw;
}

//+------------------------------------------------------------------+
//| Process a command and return response                              |
//+------------------------------------------------------------------+
string ProcessCommand(string cmd)
{
   StringToUpper(cmd);
   StringTrimLeft(cmd);
   StringTrimRight(cmd);
   
   if(StringFind(cmd, "PING") == 0)   return HandlePing();
   if(StringFind(cmd, "ACCOUNT") == 0) return HandleAccount();
   if(StringFind(cmd, "POSITIONS") == 0) return HandlePositions();
   if(StringFind(cmd, "TRADE:") == 0) return HandleTrade(cmd);
   if(StringFind(cmd, "CLOSE:") == 0) return HandleClose(cmd);
   if(StringFind(cmd, "MODIFY:") == 0) return HandleModify(cmd);
   if(StringFind(cmd, "LOGIN:") == 0) return HandleLogin(cmd);
   
   return "UNKNOWN:" + cmd;
}

//+------------------------------------------------------------------+
//| Command handlers                                                   |
//+------------------------------------------------------------------+

string HandlePing()
{
   return "PONG|" + _Symbol + "|" + AccountInfoString(ACCOUNT_SERVER) + "|" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
}

string HandleAccount()
{
   string resp = "ACCOUNT|";
   resp += IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "|";
   resp += AccountInfoString(ACCOUNT_SERVER) + "|";
   resp += AccountInfoString(ACCOUNT_COMPANY) + "|";
   resp += DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + "|";
   resp += DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + "|";
   resp += DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN), 2) + "|";
   resp += DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2) + "|";
   resp += IntegerToString(AccountInfoInteger(ACCOUNT_LEVERAGE)) + "|";
   resp += AccountInfoString(ACCOUNT_CURRENCY) + "|";
   resp += DoubleToString(AccountInfoDouble(ACCOUNT_PROFIT), 2) + "|";
   resp += IntegerToString(AccountInfoInteger(ACCOUNT_TRADE_MODE)); // 0=DEMO, 1=CONTEST, 2=REAL
   return resp;
}

string HandlePositions()
{
   string resp = "POSITIONS|";
   int total = PositionsTotal();
   resp += IntegerToString(total);
   
   for(int i = 0; i < total; i++)
   {
      if(PositionSelectByTicket(PositionGetTicket(i)))
      {
         resp += "|" + IntegerToString(PositionGetInteger(POSITION_TICKET));
         resp += "|" + PositionGetString(POSITION_SYMBOL);
         resp += "|" + IntegerToString(PositionGetInteger(POSITION_TYPE)); // 0=BUY, 1=SELL
         resp += "|" + DoubleToString(PositionGetDouble(POSITION_VOLUME), 2);
         resp += "|" + DoubleToString(PositionGetDouble(POSITION_PRICE_OPEN), 5);
         resp += "|" + DoubleToString(PositionGetDouble(POSITION_PRICE_CURRENT), 5);
         resp += "|" + DoubleToString(PositionGetDouble(POSITION_SL), 5);
         resp += "|" + DoubleToString(PositionGetDouble(POSITION_TP), 5);
         resp += "|" + DoubleToString(PositionGetDouble(POSITION_PROFIT), 2);
         resp += "|" + DoubleToString(PositionGetDouble(POSITION_SWAP), 2);
         resp += "|" + DoubleToString(PositionGetDouble(POSITION_COMMISSION), 2);
         resp += "|" + PositionGetString(POSITION_COMMENT);
      }
   }
   
   return resp;
}

string HandleTrade(string cmd)
{
   string parts[];
   StringSplit(cmd, ':', parts);
   // Format: TRADE:SYMBOL:ACTION:LOT:SL:TP
   
   if(ArraySize(parts) < 4)
      return "ERROR:Invalid trade format. Use TRADE:SYMBOL:BUY/SELL:LOT:SL:TP";
   
   string symbol = parts[1];
   string action = parts[2];
   double lot = StringToDouble(parts[3]);
   double sl = (ArraySize(parts) > 4) ? StringToDouble(parts[4]) : 0;
   double tp = (ArraySize(parts) > 5) ? StringToDouble(parts[5]) : 0;
   
   if(lot <= 0) return "ERROR:Lot size must be positive";
   
   double price;
   ENUM_ORDER_TYPE orderType;
   
   if(action == "BUY")
   {
      orderType = ORDER_TYPE_BUY;
      price = SymbolInfoDouble(symbol, SYMBOL_ASK);
   }
   else if(action == "SELL")
   {
      orderType = ORDER_TYPE_SELL;
      price = SymbolInfoDouble(symbol, SYMBOL_BID);
   }
   else
      return "ERROR:Action must be BUY or SELL";
   
   if(price <= 0)
      return "ERROR:Cannot get price for " + symbol;
   
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = symbol;
   request.volume = lot;
   request.type = orderType;
   request.price = price;
   request.sl = sl;
   request.tp = tp;
   request.deviation = Deviation;
   request.magic = MagicNumber;
   request.comment = "ForexTrade Bridge";
   
   if(!OrderSend(request, result))
   {
      WriteLog("TRADE FAILED: " + symbol + " " + action + " lot=" + DoubleToString(lot, 2) + " retcode=" + IntegerToString(result.retcode));
      return "ERROR:Trade rejected. retcode=" + IntegerToString(result.retcode) + " " + result.comment;
   }
   
   if(result.retcode != TRADE_RETCODE_DONE && result.retcode != TRADE_RETCODE_DONE_PARTIAL)
   {
      WriteLog("TRADE REJECTED: " + symbol + " " + action + " retcode=" + IntegerToString(result.retcode));
      return "ERROR:Trade rejected. retcode=" + IntegerToString(result.retcode) + " " + result.comment;
   }
   
   WriteLog("TRADE EXECUTED: " + symbol + " " + action + " ticket=" + IntegerToString(result.order) + " volume=" + DoubleToString(result.volume, 2) + " price=" + DoubleToString(result.price, 5));
   
   return "TRADE_OK|" + IntegerToString(result.order) + "|" + symbol + "|" + action + "|" + DoubleToString(lot, 2) + "|" + DoubleToString(result.price, 5);
}

string HandleClose(string cmd)
{
   // Format: CLOSE:TICKET
   string parts[];
   StringSplit(cmd, ':', parts);
   
   if(ArraySize(parts) < 2)
      return "ERROR:Invalid close format. Use CLOSE:TICKET";
   
   ulong ticket = StringToInteger(parts[1]);
   
   if(!PositionSelectByTicket(ticket))
      return "ERROR:Position " + IntegerToString(ticket) + " not found";
   
   string symbol = PositionGetString(POSITION_SYMBOL);
   double volume = PositionGetDouble(POSITION_VOLUME);
   long posType = PositionGetInteger(POSITION_TYPE);
   
   ENUM_ORDER_TYPE orderType = (posType == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   double price = (posType == POSITION_TYPE_BUY) ? 
                  SymbolInfoDouble(symbol, SYMBOL_BID) : 
                  SymbolInfoDouble(symbol, SYMBOL_ASK);
   
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = symbol;
   request.volume = volume;
   request.type = orderType;
   request.position = ticket;
   request.price = price;
   request.deviation = Deviation;
   request.magic = MagicNumber;
   request.comment = "ForexTrade Close";
   
   if(!OrderSend(request, result))
      return "ERROR:Close failed. retcode=" + IntegerToString(result.retcode);
   
   if(result.retcode != TRADE_RETCODE_DONE)
      return "ERROR:Close rejected. retcode=" + IntegerToString(result.retcode) + " " + result.comment;
   
   WriteLog("POSITION CLOSED: ticket=" + IntegerToString(ticket) + " symbol=" + symbol);
   
   return "CLOSE_OK|" + IntegerToString(ticket) + "|" + DoubleToString(result.price, 5);
}

string HandleModify(string cmd)
{
   // Format: MODIFY:TICKET:SL:TP
   string parts[];
   StringSplit(cmd, ':', parts);
   
   if(ArraySize(parts) < 3)
      return "ERROR:Invalid modify format. Use MODIFY:TICKET:SL:TP";
   
   ulong ticket = StringToInteger(parts[1]);
   double sl = StringToDouble(parts[2]);
   double tp = StringToDouble(parts[3]);
   
   if(!PositionSelectByTicket(ticket))
      return "ERROR:Position " + IntegerToString(ticket) + " not found";
   
   string symbol = PositionGetString(POSITION_SYMBOL);
   
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_SLTP;
   request.symbol = symbol;
   request.position = ticket;
   request.sl = sl;
   request.tp = tp;
   
   if(!OrderSend(request, result))
      return "ERROR:Modify failed. retcode=" + IntegerToString(result.retcode);
   
   if(result.retcode != TRADE_RETCODE_DONE)
      return "ERROR:Modify rejected. retcode=" + IntegerToString(result.retcode);
   
   WriteLog("SL/TP MODIFIED: ticket=" + IntegerToString(ticket) + " sl=" + DoubleToString(sl, 5) + " tp=" + DoubleToString(tp, 5));
   
   return "MODIFY_OK|" + IntegerToString(ticket) + "|" + DoubleToString(sl, 5) + "|" + DoubleToString(tp, 5);
}

string HandleLogin(string cmd)
{
   // Format: LOGIN:LOGIN_ID:PASSWORD:SERVER
   string parts[];
   StringSplit(cmd, ':', parts);
   
   if(ArraySize(parts) < 3)
      return "PONG|" + _Symbol + "|" + AccountInfoString(ACCOUNT_SERVER) + "|" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
   
   // Just return current login info - MT5 is already logged in
   return "LOGIN|" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "|" + AccountInfoString(ACCOUNT_SERVER) + "|" + AccountInfoString(ACCOUNT_COMPANY);
}
//+------------------------------------------------------------------+
