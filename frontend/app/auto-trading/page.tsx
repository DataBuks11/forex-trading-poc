"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Radio,
  Play,
  Square,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Settings,
  TrendingUp,
  Loader2,
  ArrowLeft,
  Zap,
} from "lucide-react";
import toast from "react-hot-toast";
import { useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { cn } from "@/lib/utils";
import { useSettings, useMT5Status } from "@/hooks/use-data";

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

const inputClass =
  "w-full px-3 py-2 bg-muted border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all";

const statusConfig: Record<string, { label: string; color: string; badge: string; icon: React.ElementType; pulse: boolean }> = {
  running: {
    label: "Running",
    color: "text-emerald-400",
    badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    icon: Play,
    pulse: true,
  },
  stopped: {
    label: "Stopped",
    color: "text-muted-foreground",
    badge: "bg-muted text-muted-foreground border-border",
    icon: Square,
    pulse: false,
  },
  waiting_for_signal: {
    label: "Waiting for Signal",
    color: "text-blue-400",
    badge: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    icon: Radio,
    pulse: true,
  },
  executing_trade: {
    label: "Executing Trade",
    color: "text-amber-400",
    badge: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    icon: TrendingUp,
    pulse: true,
  },
  error: {
    label: "Error",
    color: "text-red-400",
    badge: "bg-red-500/10 text-red-400 border-red-500/20",
    icon: AlertCircle,
    pulse: false,
  },
};

const sessionOptions = [
  { value: "ALL", label: "All Sessions" },
  { value: "ASIAN", label: "Asian" },
  { value: "LONDON", label: "London" },
  { value: "NEW_YORK", label: "New York" },
];

export default function AutoTradingPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: settings, isLoading: settingsLoading } = useSettings();
  const { data: mt5Status, isLoading: mt5Loading } = useMT5Status();

  const isConnected = mt5Status?.is_connected === true;

  const [defaultLotSize, setDefaultLotSize] = useState("0.01");
  const [riskPercent, setRiskPercent] = useState("2");
  const [defaultSl, setDefaultSl] = useState("30");
  const [defaultTp, setDefaultTp] = useState("60");
  const [maxOpenTrades, setMaxOpenTrades] = useState("5");
  const [tradingPairs, setTradingPairs] = useState("");
  const [tradingSession, setTradingSession] = useState("ALL");
  const [autoTradingEnabled, setAutoTradingEnabled] = useState(false);

  const [botActionLoading, setBotActionLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (settings) {
      if (settings.default_lot_size != null) setDefaultLotSize(String(settings.default_lot_size));
      if (settings.risk_percent != null) setRiskPercent(String(settings.risk_percent));
      if (settings.default_sl != null) setDefaultSl(String(settings.default_sl));
      if (settings.default_tp != null) setDefaultTp(String(settings.default_tp));
      if (settings.max_open_trades != null) setMaxOpenTrades(String(settings.max_open_trades));
      if (settings.trading_pairs != null) setTradingPairs(String(settings.trading_pairs));
      if (settings.trading_session != null) setTradingSession(settings.trading_session);
      if (settings.auto_trading_enabled != null) setAutoTradingEnabled(settings.auto_trading_enabled);
    }
  }, [settings]);

  const botStatus: string = settings?.bot_status ?? "stopped";
  const status = statusConfig[botStatus] ?? statusConfig.stopped;
  const StatusIcon = status.icon;

  const handleBotAction = async (action: "running" | "stopped") => {
    setBotActionLoading(true);
    try {
      await api.put("/settings/auto-trading", { bot_status: action });
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      toast.success(`Bot ${action === "running" ? "started" : "stopped"} successfully`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update bot status";
      toast.error(message);
    } finally {
      setBotActionLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      const payload = {
        default_lot_size: parseFloat(defaultLotSize) || 0.01,
        risk_percent: parseFloat(riskPercent) || 2,
        default_sl: parseInt(defaultSl) || 30,
        default_tp: parseInt(defaultTp) || 60,
        max_open_trades: parseInt(maxOpenTrades) || 5,
        trading_pairs: tradingPairs,
        trading_session: tradingSession,
        auto_trading_enabled: autoTradingEnabled,
      };
      await api.put("/settings/auto-trading", payload);
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      toast.success("Trading settings saved successfully");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save settings";
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  if (settingsLoading || mt5Loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <motion.div {...fadeIn}>
        <h1 className="text-2xl font-bold tracking-tight">Auto Trading</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Configure and control automated trading bot
        </p>
      </motion.div>

      {!isConnected && (
        <motion.div
          {...fadeIn}
          className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-4 flex items-start gap-3"
        >
          <AlertCircle className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-amber-400">MT5 Not Connected</p>
            <p className="text-xs text-muted-foreground mt-1">
              Please connect your MT5 account in MT5 Connection page before enabling auto trading
            </p>
          </div>
          <button
            onClick={() => router.push("/mt5-connect")}
            className="shrink-0 px-3 py-1.5 bg-amber-500/10 border border-amber-500/20 rounded-md text-xs font-medium text-amber-400 hover:bg-amber-500/20 transition-colors flex items-center gap-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Connect MT5
          </button>
        </motion.div>
      )}

      <motion.div
        {...fadeIn}
        className="bg-card border border-border rounded-lg p-6"
      >
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-sm">Bot Status</h3>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative flex items-center justify-center">
              <AnimatePresence mode="wait">
                <motion.div
                  key={botStatus}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.8, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <StatusIcon className={cn("w-12 h-12", status.color)} />
                </motion.div>
              </AnimatePresence>
              {status.pulse && (
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500" />
                </span>
              )}
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Current Status</p>
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 mt-1 px-2.5 py-1 rounded-full text-xs font-medium border",
                  status.badge
                )}
              >
                {status.label}
              </span>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => handleBotAction("running")}
              disabled={botActionLoading || !isConnected || botStatus === "running"}
              className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {botActionLoading && botStatus !== "running" ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              Start Bot
            </button>
            <button
              onClick={() => handleBotAction("stopped")}
              disabled={botActionLoading || botStatus === "stopped"}
              className="flex items-center gap-2 px-4 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {botActionLoading && botStatus === "stopped" ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Square className="w-4 h-4" />
              )}
              Stop Bot
            </button>
          </div>
        </div>
      </motion.div>

      <motion.div
        {...fadeIn}
        className="bg-card border border-border rounded-lg p-6"
      >
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-sm">Trading Settings</h3>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Default Lot Size
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={defaultLotSize}
              onChange={(e) => setDefaultLotSize(e.target.value)}
              className={inputClass}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Risk %
            </label>
            <input
              type="number"
              min="0.1"
              max="100"
              step="0.1"
              value={riskPercent}
              onChange={(e) => setRiskPercent(e.target.value)}
              className={inputClass}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Default Stop Loss (pips)
            </label>
            <input
              type="number"
              value={defaultSl}
              onChange={(e) => setDefaultSl(e.target.value)}
              className={inputClass}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Default Take Profit (pips)
            </label>
            <input
              type="number"
              value={defaultTp}
              onChange={(e) => setDefaultTp(e.target.value)}
              className={inputClass}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Max Open Trades
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={maxOpenTrades}
              onChange={(e) => setMaxOpenTrades(e.target.value)}
              className={inputClass}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Trading Pairs
            </label>
            <input
              type="text"
              placeholder="EURUSD,GBPUSD,USDJPY"
              value={tradingPairs}
              onChange={(e) => setTradingPairs(e.target.value)}
              className={inputClass}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Trading Session
            </label>
            <select
              value={tradingSession}
              onChange={(e) => setTradingSession(e.target.value)}
              className={cn(inputClass, "cursor-pointer")}
            >
              {sessionOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Enable Auto Trading
            </label>
            <label className="flex items-center gap-3 cursor-pointer select-none group mt-1">
              <input
                type="checkbox"
                checked={autoTradingEnabled}
                onChange={(e) => setAutoTradingEnabled(e.target.checked)}
                className="sr-only"
              />
              <div
                className={cn(
                  "relative w-10 h-5 rounded-full transition-colors",
                  autoTradingEnabled ? "bg-primary" : "bg-muted border border-border"
                )}
              >
                <div
                  className={cn(
                    "absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform",
                    autoTradingEnabled ? "translate-x-5" : "translate-x-0.5"
                  )}
                />
              </div>
              <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">
                {autoTradingEnabled ? "Enabled" : "Disabled"}
              </span>
            </label>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-border">
          <button
            onClick={handleSaveSettings}
            disabled={saving}
            className="w-full md:w-auto px-6 py-2.5 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center justify-center gap-2"
          >
            {saving && <Loader2 className="w-4 h-4 animate-spin" />}
            {saving ? "Saving..." : "Save Settings"}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
