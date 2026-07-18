"use client";

import { motion } from "framer-motion";
import {
  Loader2,
  Wallet,
  PiggyBank,
  TrendingUp,
  Shield,
  Activity,
  Zap,
  Percent,
  Target,
  DollarSign,
} from "lucide-react";
import { useDashboard, useMT5Status } from "@/hooks/use-data";
import { cn, formatCurrency, formatNumber, timeAgo, formatDateTime } from "@/lib/utils";

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

const cardBase = "rounded-lg border border-border bg-card p-5";

export default function DashboardPage() {
  const { data: dashboard, isLoading: dashLoading } = useDashboard();
  const { data: mt5Status, isLoading: mt5Loading } = useMT5Status();

  if (dashLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const account = dashboard?.account;
  const positions = dashboard?.open_positions ?? [];
  const activity = dashboard?.recent_activity ?? [];
  const trades = dashboard?.trade_history ?? [];
  const stats = dashboard?.stats;

  return (
    <div className="space-y-6 max-w-7xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Trading Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Overview of your trading activity and account performance
        </p>
      </div>

      {/* Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Connection Status Card */}
        <motion.div {...fadeIn} className={cardBase}>
          <div className="flex items-center justify-between mb-3 pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary" />
              <h3 className="font-semibold text-sm">Connection Status</h3>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "w-2.5 h-2.5 rounded-full",
                  mt5Status?.is_connected
                    ? "bg-emerald-500 animate-pulse"
                    : "bg-red-500"
                )}
              />
              <span
                className={cn(
                  "text-sm font-medium",
                  mt5Status?.is_connected ? "text-emerald-400" : "text-red-400"
                )}
              >
                {mt5Status?.is_connected ? "Connected" : "Disconnected"}
              </span>
            </div>
            {mt5Status?.is_connected && (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Broker</span>
                  <span className="text-sm font-medium">{mt5Status?.broker ?? account?.broker ?? "-"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Account</span>
                  <span className="text-sm font-mono">{mt5Status?.account_number ?? account?.account_number ?? "-"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Type</span>
                  <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-blue-500/10 text-blue-400">
                    {mt5Status?.account_type || "N/A"}
                  </span>
                </div>
              </>
            )}
          </div>
        </motion.div>

        {/* Account Balance Card */}
        <motion.div {...fadeIn} className={cardBase}>
          <div className="flex items-center justify-between mb-3 pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Wallet className="w-5 h-5 text-primary" />
              <h3 className="font-semibold text-sm">Account Balance</h3>
            </div>
          </div>
          {account ? (
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Balance", value: formatCurrency(account.balance, account.currency), icon: Wallet, color: "text-emerald-400" },
                { label: "Equity", value: formatCurrency(account.equity, account.currency), icon: PiggyBank, color: "text-blue-400" },
                { label: "Margin", value: formatCurrency(account.margin, account.currency), icon: TrendingUp, color: "text-amber-400" },
                { label: "Free Margin", value: formatCurrency(account.free_margin ?? (account.balance - account.margin), account.currency), icon: Shield, color: "text-purple-400" },
              ].map(({ label, value, icon: Icon, color }) => (
                <div
                  key={label}
                  className="bg-muted/30 border border-border rounded-md p-3"
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <Icon className={cn("w-3.5 h-3.5", color)} />
                    <span className="text-xs text-muted-foreground">{label}</span>
                  </div>
                  <p className="text-sm font-mono font-semibold text-foreground">
                    {value}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No account data available</p>
          )}
        </motion.div>

        {/* Quick Stats Card */}
        <motion.div {...fadeIn} className={cardBase}>
          <div className="flex items-center justify-between mb-3 pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-primary" />
              <h3 className="font-semibold text-sm">Quick Stats</h3>
            </div>
          </div>
          {stats ? (
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Total Trades", value: formatNumber(stats.total_trades ?? 0, 0), icon: TrendingUp, color: "text-blue-400" },
                { label: "Open Positions", value: formatNumber(stats.open_positions ?? 0, 0), icon: Target, color: "text-amber-400" },
                { label: "Today's Profit", value: ((stats.profit_today ?? 0) >= 0 ? "+" : "") + formatCurrency(stats.profit_today ?? 0), icon: DollarSign, color: (stats.profit_today ?? 0) >= 0 ? "text-emerald-400" : "text-red-400" },
                { label: "Floating P/L", value: ((stats.floating_pl ?? 0) >= 0 ? "+" : "") + formatCurrency(stats.floating_pl ?? 0), icon: Activity, color: (stats.floating_pl ?? 0) >= 0 ? "text-emerald-400" : "text-red-400" },
                { label: "Win Rate", value: stats.win_rate != null ? formatNumber(stats.win_rate, 1) + "%" : "-", icon: Percent, color: "text-purple-400" },
              ].map(({ label, value, icon: Icon, color }) => (
                <div
                  key={label}
                  className="bg-muted/30 border border-border rounded-md p-3"
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <Icon className={cn("w-3.5 h-3.5", color)} />
                    <span className="text-xs text-muted-foreground">{label}</span>
                  </div>
                  <p className={cn("text-sm font-mono font-semibold", color)}>
                    {value}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No stats available</p>
          )}
        </motion.div>
      </div>

      {/* Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Open Positions Card */}
        <motion.div {...fadeIn} className={cardBase}>
          <div className="flex items-center justify-between mb-3 pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              <h3 className="font-semibold text-sm">Open Positions</h3>
            </div>
            <span className="text-xs text-muted-foreground font-mono">
              {positions.length} active
            </span>
          </div>
          {positions.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-sm text-muted-foreground">No open positions</p>
            </div>
          ) : (
            <div className="overflow-x-auto -mx-5">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-muted/30 text-left">
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Symbol</th>
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Type</th>
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Volume</th>
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Profit</th>
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">SL</th>
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">TP</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {positions.map((pos: { ticket: number; symbol: string; type: string; volume: number; profit: number; sl: number; tp: number }) => (
                    <tr key={pos.ticket} className="hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-2 font-mono font-medium">{pos.symbol}</td>
                      <td className="px-4 py-2">
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
                      <td className="px-4 py-2 font-mono">{pos.volume}</td>
                      <td className="px-4 py-2 font-mono">
                        <span
                          className={cn(
                            pos.profit >= 0 ? "text-emerald-400" : "text-red-400"
                          )}
                        >
                          {pos.profit >= 0 ? "+" : ""}
                          {pos.profit.toFixed(2)}
                        </span>
                      </td>
                      <td className="px-4 py-2 font-mono text-xs">
                        {pos.sl > 0 ? pos.sl.toFixed(5) : "-"}
                      </td>
                      <td className="px-4 py-2 font-mono text-xs">
                        {pos.tp > 0 ? pos.tp.toFixed(5) : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </motion.div>

        {/* Recent Activity Card */}
        <motion.div {...fadeIn} className={cardBase}>
          <div className="flex items-center justify-between mb-3 pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-primary" />
              <h3 className="font-semibold text-sm">Recent Activity</h3>
            </div>
          </div>
          {activity.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-sm text-muted-foreground">No recent activity</p>
            </div>
          ) : (
            <div className="space-y-3">
              {activity.slice(0, 8).map((entry: { event_type: string; description: string; created_at: string }, i: number) => (
                <div
                  key={i}
                  className="flex items-start gap-3 pb-3 border-b border-border last:border-0 last:pb-0"
                >
                  <div className="w-2 h-2 rounded-full bg-primary/60 mt-1.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium">{entry.event_type}</span>
                      <span className="text-xs text-muted-foreground shrink-0">
                        {timeAgo(entry.created_at)}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5 truncate">
                      {entry.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>

      {/* Row 3 */}
      <motion.div {...fadeIn} className={cardBase}>
        <div className="flex items-center justify-between mb-3 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-sm">Trade History</h3>
          </div>
          <span className="text-xs text-muted-foreground font-mono">
            Last {Math.min(trades.length, 10)} trades
          </span>
        </div>
        {trades.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm text-muted-foreground">No trades yet</p>
          </div>
        ) : (
          <div className="overflow-x-auto -mx-5">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/30 text-left">
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Time</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Symbol</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Action</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Lot</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Price</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">SL / TP</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {trades.slice(0, 10).map((trade: { id: number; symbol: string; action: string; lot: number; open_price: number; sl: number; tp: number; status: string; created_at: string }) => (
                  <tr key={trade.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-2 text-muted-foreground text-xs">
                      {formatDateTime(trade.created_at)}
                    </td>
                    <td className="px-4 py-2 font-mono font-medium">{trade.symbol}</td>
                    <td className="px-4 py-2">
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
                    <td className="px-4 py-2 font-mono">{trade.lot}</td>
                    <td className="px-4 py-2 font-mono">{trade.open_price?.toFixed(5) ?? "-"}</td>
                    <td className="px-4 py-2 font-mono text-xs">
                      {trade.sl > 0 ? trade.sl.toFixed(5) : "-"} /{" "}
                      {trade.tp > 0 ? trade.tp.toFixed(5) : "-"}
                    </td>
                    <td className="px-4 py-2">
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded text-xs font-medium",
                          trade.status === "OPEN"
                            ? "bg-blue-500/10 text-blue-400"
                            : trade.status === "CLOSED"
                              ? "bg-emerald-500/10 text-emerald-400"
                              : "bg-muted text-muted-foreground"
                        )}
                      >
                        {trade.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>
    </div>
  );
}
