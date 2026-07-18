"use client";

import { useCallback } from "react";
import { motion } from "framer-motion";
import { Loader2, RefreshCw } from "lucide-react";
import { useOpenTrades, useMT5Positions } from "@/hooks/use-data";
import { useQueryClient } from "@tanstack/react-query";
import { cn, formatCurrency, formatNumber, timeAgo } from "@/lib/utils";
import toast from "react-hot-toast";

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

const cardBase = "rounded-lg border border-border bg-card p-6";

interface MT5Position {
  ticket: number;
  symbol: string;
  type: string;
  volume: number;
  open_price: number;
  current_price: number;
  sl: number;
  tp: number;
  profit: number;
  swap: number;
  commission: number;
}

interface OpenTrade {
  id: number;
  symbol: string;
  action: string;
  lot: number;
  open_price: number;
  sl: number;
  tp: number;
  ticket: number;
  created_at: string;
  source?: string;
  status: string;
}

export default function OpenPositionsPage() {
  const queryClient = useQueryClient();
  const { data: mt5Data, isLoading: mt5Loading } = useMT5Positions();
  const { data: tradesData, isLoading: tradesLoading } = useOpenTrades();

  const mt5Positions: MT5Position[] = mt5Data?.positions ?? mt5Data ?? [];
  const openTrades: OpenTrade[] = tradesData?.trades ?? tradesData ?? [];

  const isLoading = mt5Loading || tradesLoading;

  const handleRefresh = useCallback(async () => {
    try {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["mt5-positions"] }),
        queryClient.invalidateQueries({ queryKey: ["open-trades"] }),
      ]);
      toast.success("Positions refreshed");
    } catch {
      toast.error("Failed to refresh positions");
    }
  }, [queryClient]);

  const totalOpenCount = mt5Positions.length + openTrades.filter((t) => t.status === "OPEN").length;
  const totalFloatingPL = mt5Positions.reduce((sum, p) => sum + (p.profit ?? 0), 0);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Open Positions</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Monitor your live MT5 positions and webhook-created trades
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="h-9 px-3 rounded-md border border-border bg-card text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* MT5 Live Positions */}
      <motion.div {...fadeIn} className={cardBase}>
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
          <h3 className="font-semibold text-sm">Live Positions (MT5)</h3>
          <span className="px-2 py-0.5 rounded text-xs font-mono font-medium bg-primary/10 text-primary">
            {mt5Positions.length}
          </span>
        </div>

        {mt5Positions.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-sm text-muted-foreground">
              No live positions. Connect MT5 and execute trades to see live data.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto -mx-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/30 text-left">
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Ticket</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Symbol</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Type</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Volume</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Open Price</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Current</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">SL</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">TP</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Profit</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Swap</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Commission</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {mt5Positions.map((pos) => (
                  <tr key={pos.ticket} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-2.5 font-mono text-xs">{pos.ticket}</td>
                    <td className="px-4 py-2.5 font-mono font-medium">{pos.symbol}</td>
                    <td className="px-4 py-2.5">
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded text-xs font-medium",
                          pos.type === "BUY"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-red-500/10 text-red-400"
                        )}
                      >
                        {pos.type}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-mono">{pos.volume}</td>
                    <td className="px-4 py-2.5 font-mono text-xs">
                      {pos.open_price != null && pos.open_price > 0 ? pos.open_price.toFixed(5) : "-"}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">
                      {pos.current_price != null && pos.current_price > 0 ? pos.current_price.toFixed(5) : "-"}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">
                      {pos.sl != null && pos.sl > 0 ? pos.sl.toFixed(5) : "-"}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">
                      {pos.tp != null && pos.tp > 0 ? pos.tp.toFixed(5) : "-"}
                    </td>
                    <td className="px-4 py-2.5 font-mono">
                      <span
                        className={cn(
                          (pos.profit ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                        )}
                      >
                        {(pos.profit ?? 0) >= 0 ? "+" : ""}
                        {(pos.profit ?? 0).toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">
                      {pos.swap != null ? pos.swap.toFixed(2) : "-"}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">
                      {pos.commission != null ? pos.commission.toFixed(2) : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {/* Webhook Positions */}
      <motion.div {...fadeIn} className={cardBase}>
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
          <h3 className="font-semibold text-sm">Webhook Positions</h3>
          <span className="px-2 py-0.5 rounded text-xs font-mono font-medium bg-primary/10 text-primary">
            {openTrades.length}
          </span>
        </div>

        {openTrades.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-sm text-muted-foreground">
              No webhook positions yet
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto -mx-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/30 text-left">
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">ID</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Symbol</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Action</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Lot</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Open Price</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">SL</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">TP</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Ticket</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Time</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Source</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {openTrades.map((trade) => (
                  <tr key={trade.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-2.5 font-mono text-xs">{trade.id}</td>
                    <td className="px-4 py-2.5 font-mono font-medium">{trade.symbol}</td>
                    <td className="px-4 py-2.5">
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded text-xs font-medium",
                          trade.action === "BUY"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-red-500/10 text-red-400"
                        )}
                      >
                        {trade.action}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-mono">{trade.lot}</td>
                    <td className="px-4 py-2.5 font-mono text-xs">
                      {trade.open_price != null && trade.open_price > 0 ? trade.open_price.toFixed(5) : "-"}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">
                      {trade.sl != null && trade.sl > 0 ? trade.sl.toFixed(5) : "-"}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">
                      {trade.tp != null && trade.tp > 0 ? trade.tp.toFixed(5) : "-"}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">{trade.ticket}</td>
                    <td className="px-4 py-2.5 text-muted-foreground text-xs whitespace-nowrap">
                      {timeAgo(trade.created_at)}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-muted-foreground">
                      {trade.source ?? "-"}
                    </td>
                    <td className="px-4 py-2.5">
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded text-xs font-medium",
                          trade.status === "OPEN"
                            ? "bg-blue-500/10 text-blue-400"
                            : "bg-muted text-muted-foreground"
                        )}
                      >
                        {trade.status === "OPEN" ? "Active" : "Closed"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {/* Combined Summary */}
      <motion.div
        {...fadeIn}
        className="rounded-lg border border-border bg-card p-5 flex items-center gap-6"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Total Open Positions</span>
          <span className="px-2 py-0.5 rounded text-sm font-mono font-semibold bg-primary/10 text-primary">
            {totalOpenCount}
          </span>
        </div>
        <div className="w-px h-8 bg-border" />
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Total Floating P/L</span>
          <span
            className={cn(
              "text-sm font-mono font-semibold",
              totalFloatingPL >= 0 ? "text-emerald-400" : "text-red-400"
            )}
          >
            {totalFloatingPL >= 0 ? "+" : ""}
            {formatCurrency(totalFloatingPL)}
          </span>
        </div>
      </motion.div>
    </div>
  );
}
