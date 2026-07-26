//+------------------------------------------------------------------+
//|                                                  installer.mq5    |
//|                Auto-attaches bridge EA to EURUSD chart            |
//+------------------------------------------------------------------+
#property script_show_inputs

void OnStart()
{
   long chartId = 0;
   
   // Find or create EURUSD chart
   chartId = ChartFirst();
   while(chartId != -1)
   {
      if(ChartSymbol(chartId) == "EURUSD")
         break;
      chartId = ChartNext(chartId);
   }
   
   if(chartId == -1)
   {
      chartId = ChartOpen("EURUSD", PERIOD_H1);
      if(chartId == 0)
      {
         Print("Failed to open EURUSD chart");
         return;
      }
      ChartRedraw(chartId);
      Sleep(3000);
   }
   
   // Remove any existing expert
   if(ChartGetInteger(chartId, CHART_EXPERT_ENABLED))
   {
      // Expert is already attached - check if it's bridge
      long expertHandle = ChartGetInteger(chartId, CHART_EXPERT_HANDLE);
   }
   
   // Try to attach bridge EA
   // Note: ChartIndicatorAdd doesn't work for experts.
   // We need to write to the chart's .chr file instead.
   
   // Alternative: Use the Expert Advisor setup via chart properties
   // The chart's expert is stored in its .chr file
   
   Print("Attempting to attach bridge EA...");
   
   // Open the Chart Expert Advisor properties dialog  
   // and programmatically select bridge
   // This is done by modifying the chart template
   
   // Write a .tpl file with the EA embedded
   string tplPath = TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Profiles\\bridge_setup.tpl";
   
   int handle = FileOpen("bridge_setup.tpl", FILE_WRITE|FILE_TXT|FILE_COMMON);
   if(handle != INVALID_HANDLE)
   {
      FileWrite(handle, "<chart>");
      FileWrite(handle, "symbol=EURUSD");
      FileWrite(handle, "period=60");
      FileWrite(handle, "<expert>");
      FileWrite(handle, "name=bridge");
      FileWrite(handle, "</expert>");
      FileWrite(handle, "</chart>");
      FileClose(handle);
      
      // Apply template
      ChartApplyTemplate(chartId, "bridge_setup.tpl");
      Print("Bridge EA should now be attached to EURUSD H1 chart");
   }
   else
   {
      Print("Could not create template file");
   }
}
