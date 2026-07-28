//+------------------------------------------------------------------+
//|                                                bridge_simple.mq5  |
//|                                  Minimal MT5 <-> Python Bridge    |
//+------------------------------------------------------------------+
#property strict

#define CMD_FILE "bridge_cmd.txt"
#define RESP_FILE "bridge_resp.txt"

int OnInit()
{
   EventSetMillisecondTimer(500);
   Print("Bridge EA started - polling every 500ms");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("Bridge EA removed");
}

void OnTimer()
{
   // Read command - use FILE_ANSI to read ASCII from Python
   int h = FileOpen(CMD_FILE, FILE_READ|FILE_ANSI|FILE_COMMON);
   if(h == INVALID_HANDLE) return;
   
   string cmd = FileReadString(h, (int)FileSize(h));
   FileClose(h);
   
   if(cmd == "") return;
   
   // Trim whitespace and convert to uppercase
   StringTrimLeft(cmd);
   StringTrimRight(cmd);
   cmd = StringSubstr(cmd, 0);  // Force copy to clear any encoding issues
   
   string upper = cmd;
   StringToUpper(upper);
   
   string response;
   
   if(StringFind(upper, "PING") == 0)
      response = "PONG|" + Symbol() + "|" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "|" + AccountInfoString(ACCOUNT_SERVER) + "|" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE),2) + "|" + AccountInfoString(ACCOUNT_CURRENCY);
   else if(StringFind(upper, "ACCOUNT") == 0)
   {
      double bal = AccountInfoDouble(ACCOUNT_BALANCE);
      double eq = AccountInfoDouble(ACCOUNT_EQUITY);
      double mar = AccountInfoDouble(ACCOUNT_MARGIN);
      double fm = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
      long lev = AccountInfoInteger(ACCOUNT_LEVERAGE);
      
      response = "ACCOUNT|";
      response += IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "|";
      response += AccountInfoString(ACCOUNT_SERVER) + "|";
      response += AccountInfoString(ACCOUNT_COMPANY) + "|";
      response += DoubleToString(bal, 2) + "|";
      response += DoubleToString(eq, 2) + "|";
      response += DoubleToString(mar, 2) + "|";
      response += DoubleToString(fm, 2) + "|";
      response += IntegerToString(lev) + "|";
      response += AccountInfoString(ACCOUNT_CURRENCY) + "|";
      response += IntegerToString(AccountInfoInteger(ACCOUNT_TRADE_MODE)) + "|";
      response += DoubleToString(AccountInfoDouble(ACCOUNT_PROFIT), 2);
      
      Print("Bridge ACCT: login=", AccountInfoInteger(ACCOUNT_LOGIN),
            " bal=", DoubleToString(bal,2),
            " eq=", DoubleToString(eq,2),
            " lev=", lev,
            " cur=", AccountInfoString(ACCOUNT_CURRENCY));
   }
   else if(StringFind(upper, "POSITIONS") == 0)
   {
      response = "POSITIONS|";
      int total = PositionsTotal();
      response += IntegerToString(total);
      for(int i = 0; i < total; i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(PositionSelectByTicket(ticket))
         {
            response += "|" + IntegerToString(ticket);
            response += "|" + PositionGetString(POSITION_SYMBOL);
            response += "|" + IntegerToString(PositionGetInteger(POSITION_TYPE));
            response += "|" + DoubleToString(PositionGetDouble(POSITION_VOLUME), 2);
            response += "|" + DoubleToString(PositionGetDouble(POSITION_PRICE_OPEN), 5);
            response += "|" + DoubleToString(PositionGetDouble(POSITION_PRICE_CURRENT), 5);
            response += "|" + DoubleToString(PositionGetDouble(POSITION_SL), 5);
            response += "|" + DoubleToString(PositionGetDouble(POSITION_TP), 5);
            response += "|" + DoubleToString(PositionGetDouble(POSITION_PROFIT), 2);
         }
      }
   }
   else if(StringFind(upper, "TRADE:") == 0)
   {
      string parts[];
      StringSplit(cmd, ':', parts);
      if(ArraySize(parts) >= 4)
      {
         string sym = parts[1];
         string act = parts[2];
         double lot = StringToDouble(parts[3]);
         double sl = (ArraySize(parts) > 4) ? StringToDouble(parts[4]) : 0;
         double tp = (ArraySize(parts) > 5) ? StringToDouble(parts[5]) : 0;
         
         double price;
         ENUM_ORDER_TYPE ot;
         if(act == "BUY") { ot = ORDER_TYPE_BUY; price = SymbolInfoDouble(sym, SYMBOL_ASK); }
         else { ot = ORDER_TYPE_SELL; price = SymbolInfoDouble(sym, SYMBOL_BID); }
         
         MqlTradeRequest req = {};
         MqlTradeResult res = {};
         req.action = TRADE_ACTION_DEAL;
         req.symbol = sym;
         req.volume = lot;
         req.type = ot;
         req.price = price;
         req.sl = sl;
         req.tp = tp;
         req.deviation = 20;
         req.magic = 123456;
         req.comment = "ForexTrade";
         
         if(OrderSend(req, res) && res.retcode == TRADE_RETCODE_DONE)
            response = "TRADE_OK|" + IntegerToString(res.order) + "|" + sym + "|" + act + "|" + DoubleToString(lot,2) + "|" + DoubleToString(res.price,5);
         else
            response = "TRADE_ERR|" + IntegerToString(res.retcode) + "|" + res.comment;
      }
      else
         response = "ERROR|Invalid trade format";
   }
   else if(StringFind(upper, "CLOSE:") == 0)
   {
      string parts[];
      StringSplit(cmd, ':', parts);
      if(ArraySize(parts) >= 2)
      {
         ulong ticket = StringToInteger(parts[1]);
         if(PositionSelectByTicket(ticket))
         {
            string sym = PositionGetString(POSITION_SYMBOL);
            double vol = PositionGetDouble(POSITION_VOLUME);
            long pt = PositionGetInteger(POSITION_TYPE);
            ENUM_ORDER_TYPE ot = (pt == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
            double price = (pt == POSITION_TYPE_BUY) ? SymbolInfoDouble(sym, SYMBOL_BID) : SymbolInfoDouble(sym, SYMBOL_ASK);
            
            MqlTradeRequest req = {};
            MqlTradeResult res = {};
            req.action = TRADE_ACTION_DEAL;
            req.symbol = sym;
            req.volume = vol;
            req.type = ot;
            req.position = ticket;
            req.price = price;
            req.deviation = 20;
            req.magic = 123456;
            req.comment = "ForexTrade Close";
            
            if(OrderSend(req, res) && res.retcode == TRADE_RETCODE_DONE)
               response = "CLOSE_OK|" + IntegerToString(ticket) + "|" + DoubleToString(res.price, 5);
            else
               response = "CLOSE_ERR|" + IntegerToString(res.retcode);
         }
         else
            response = "ERROR|Position not found";
      }
   }
   else
      response = "UNKNOWN|" + cmd;
   
   // Write response - use FILE_ANSI for Python compatibility
   h = FileOpen(RESP_FILE, FILE_WRITE|FILE_ANSI|FILE_COMMON);
   if(h != INVALID_HANDLE)
   {
      FileSeek(h, 0, SEEK_SET);
      FileWriteString(h, response);
      FileClose(h);
   }
}
//+------------------------------------------------------------------+
