"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Loader2,
  Code2,
  Radio,
  Plus,
  RefreshCw,
  Play,
  Square,
  Zap,
  AlertCircle,
  CheckCircle,
  XCircle,
} from "lucide-react";
import toast from "react-hot-toast";
import api from "@/lib/api";
import { cn, formatCurrency, formatNumber, timeAgo, formatDateTime } from "@/lib/utils";

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

const stagger = {
  animate: { transition: { staggerChildren: 0.06 } },
};

const inputClass =
  "w-full px-3 py-2 bg-muted border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all";

const cardHeaderClass =
  "flex items-center justify-between mb-4 pb-3 border-b border-border";

interface Script {
  id: number;
  name: string;
  description: string;
  symbol: string;
  timeframe: string;
  enabled: boolean;
  lot_size: number;
  risk_percent: number;
  script_config?: Record<string, unknown>;
}

interface Signal {
  id: number;
  created_at: string;
  script_id: string;
  symbol: string;
  action: string;
  signal_type: string;
  status: string;
  ticket: number | null;
  message: string;
}

export default function ScriptsPage() {
  const [scripts, setScripts] = useState<Script[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [scriptsLoading, setScriptsLoading] = useState(true);
  const [signalsLoading, setSignalsLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);

  const [lotSizes, setLotSizes] = useState<Record<number, string>>({});
  const [riskPercents, setRiskPercents] = useState<Record<number, string>>({});
  const [savingScriptId, setSavingScriptId] = useState<number | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newScript, setNewScript] = useState({
    name: "",
    description: "",
    symbol: "",
    timeframe: "",
    script_config: "{}",
  });

  const fetchScripts = useCallback(async () => {
    setScriptsLoading(true);
    try {
      const res = await api.get("/scripts");
      const data = res.data;
      const list = Array.isArray(data) ? data : data.scripts ?? data.results ?? [];
      setScripts(list);
      if (typeof (data as { is_admin?: boolean }).is_admin === "boolean") {
        setIsAdmin((data as { is_admin?: boolean }).is_admin ?? false);
      }
      const lots: Record<number, string> = {};
      const risks: Record<number, string> = {};
      list.forEach((s: Script) => {
        lots[s.id] = String(s.lot_size ?? 0.01);
        risks[s.id] = String(s.risk_percent ?? 1);
      });
      setLotSizes(lots);
      setRiskPercents(risks);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load scripts";
      toast.error(message);
      setIsAdmin(false);
    } finally {
      setScriptsLoading(false);
    }
  }, []);

  const fetchSignals = useCallback(async () => {
    setSignalsLoading(true);
    try {
      const res = await api.get("/scripts/signals");
      const data = res.data;
      const list = Array.isArray(data) ? data : data.signals ?? data.results ?? [];
      setSignals(list);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load signals";
      toast.error(message);
    } finally {
      setSignalsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchScripts();
    fetchSignals();
  }, [fetchScripts, fetchSignals]);

  const handleToggleEnabled = async (script: Script) => {
    try {
      const enabled = !script.enabled;
      await api.post(`/scripts/${script.id}/enable`, {
        enabled,
        lot_size: parseFloat(lotSizes[script.id] ?? String(script.lot_size)) || 0.01,
        risk: parseFloat(riskPercents[script.id] ?? String(script.risk_percent)) || 1,
      });
      setScripts((prev) =>
        prev.map((s) => (s.id === script.id ? { ...s, enabled } : s))
      );
      toast.success(`Script "${script.name}" ${enabled ? "enabled" : "disabled"}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update script";
      toast.error(message);
    }
  };

  const handleSaveSettings = async (script: Script) => {
    setSavingScriptId(script.id);
    try {
      await api.post(`/scripts/${script.id}/enable`, {
        enabled: script.enabled,
        lot_size: parseFloat(lotSizes[script.id] ?? String(script.lot_size)) || 0.01,
        risk: parseFloat(riskPercents[script.id] ?? String(script.risk_percent)) || 1,
      });
      toast.success(`Settings saved for "${script.name}"`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save settings";
      toast.error(message);
    } finally {
      setSavingScriptId(null);
    }
  };

  const handleCreateScript = async () => {
    if (!newScript.name.trim() || !newScript.symbol.trim()) {
      toast.error("Name and Symbol are required");
      return;
    }
    setCreating(true);
    try {
      let parsedConfig: Record<string, unknown> = {};
      try {
        parsedConfig = JSON.parse(newScript.script_config || "{}");
      } catch {
        toast.error("Invalid JSON in script config");
        setCreating(false);
        return;
      }
      await api.post("/scripts", {
        name: newScript.name,
        description: newScript.description,
        symbol: newScript.symbol,
        timeframe: newScript.timeframe,
        script_config: parsedConfig,
      });
      toast.success("Script created successfully");
      setShowCreate(false);
      setNewScript({ name: "", description: "", symbol: "", timeframe: "", script_config: "{}" });
      fetchScripts();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to create script";
      toast.error(message);
    } finally {
      setCreating(false);
    }
  };

  const signalTypeBadge = (type: string) => {
    const config: Record<string, string> = {
      ENTRY: "bg-blue-500/10 text-blue-400 border-blue-500/20",
      EXIT: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      MODIFY: "bg-amber-500/10 text-amber-400 border-amber-500/20",
      CLOSE: "bg-red-500/10 text-red-400 border-red-500/20",
    };
    return config[type?.toUpperCase()] ?? "bg-muted text-muted-foreground border-border";
  };

  const statusBadge = (status: string) => {
    const config: Record<string, string> = {
      PENDING: "bg-amber-500/10 text-amber-400 border-amber-500/20",
      EXECUTED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      REJECTED: "bg-red-500/10 text-red-400 border-red-500/20",
      EXPIRED: "bg-muted text-muted-foreground border-border",
      CANCELLED: "bg-muted text-muted-foreground border-border",
    };
    return config[status?.toUpperCase()] ?? "bg-muted text-muted-foreground border-border";
  };

  const actionBadge = (action: string) => {
    return action?.toUpperCase() === "BUY"
      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
      : action?.toUpperCase() === "SELL"
        ? "bg-red-500/10 text-red-400 border-red-500/20"
        : "bg-muted text-muted-foreground border-border";
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <motion.div {...fadeIn} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Trading Scripts</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Automated trading strategies running on your account
          </p>
        </div>
        <button
          onClick={() => {
            fetchScripts();
            fetchSignals();
            toast.success("Refreshed");
          }}
          className="flex items-center gap-2 px-3 py-2 bg-muted border border-border rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-muted/70 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </motion.div>

      {/* Available Scripts */}
      <motion.div
        {...fadeIn}
        className="bg-card border border-border rounded-lg p-6"
      >
        <div className={cardHeaderClass}>
          <div className="flex items-center gap-2">
            <Code2 className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-sm">Available Scripts</h3>
          </div>
          <span className="text-xs text-muted-foreground font-mono">
            {scripts.length} scripts
          </span>
        </div>

        {scriptsLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
          </div>
        ) : scripts.length === 0 ? (
          <div className="py-12 text-center">
            <Code2 className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">No trading scripts available</p>
          </div>
        ) : (
          <motion.div className="space-y-4" {...stagger}>
            {scripts.map((script) => (
              <motion.div
                key={script.id}
                variants={{
                  initial: { opacity: 0, y: 12 },
                  animate: { opacity: 1, y: 0 },
                }}
                className="bg-muted/30 border border-border rounded-lg p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <h4 className="font-semibold text-sm">{script.name}</h4>
                      <span
                        className={cn(
                          "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border",
                          script.enabled
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : "bg-muted text-muted-foreground border-border"
                        )}
                      >
                        {script.enabled ? (
                          <>
                            <Play className="w-3 h-3" />
                            Active
                          </>
                        ) : (
                          <>
                            <Square className="w-3 h-3" />
                            Disabled
                          </>
                        )}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mb-3">
                      {script.description}
                    </p>
                    <div className="flex items-center gap-2 mb-4">
                      <span className="px-2 py-0.5 rounded text-xs font-mono font-medium bg-primary/10 text-primary border border-primary/20">
                        {script.symbol}
                      </span>
                      <span className="px-2 py-0.5 rounded text-xs font-mono bg-muted text-muted-foreground border border-border">
                        {script.timeframe}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">
                          Lot Size
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0.01"
                          value={lotSizes[script.id] ?? "0.01"}
                          onChange={(e) =>
                            setLotSizes((prev) => ({
                              ...prev,
                              [script.id]: e.target.value,
                            }))
                          }
                          className={inputClass}
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">
                          Risk %
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          min="0.1"
                          max="100"
                          value={riskPercents[script.id] ?? "1"}
                          onChange={(e) =>
                            setRiskPercents((prev) => ({
                              ...prev,
                              [script.id]: e.target.value,
                            }))
                          }
                          className={inputClass}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-3 shrink-0">
                    <label className="flex items-center gap-3 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={script.enabled}
                        onChange={() => handleToggleEnabled(script)}
                        className="sr-only"
                      />
                      <div
                        className={cn(
                          "relative w-10 h-5 rounded-full transition-colors",
                          script.enabled
                            ? "bg-primary"
                            : "bg-muted border border-border"
                        )}
                      >
                        <div
                          className={cn(
                            "absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform",
                            script.enabled ? "translate-x-5" : "translate-x-0.5"
                          )}
                        />
                      </div>
                    </label>
                    <button
                      onClick={() => handleSaveSettings(script)}
                      disabled={savingScriptId === script.id}
                      className="px-4 py-1.5 bg-primary text-primary-foreground rounded-md text-xs font-medium hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center gap-1.5 whitespace-nowrap"
                    >
                      {savingScriptId === script.id && (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      )}
                      {savingScriptId === script.id ? "Saving..." : "Save Settings"}
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </motion.div>

      {/* My Signals */}
      <motion.div
        {...fadeIn}
        className="bg-card border border-border rounded-lg p-6"
      >
        <div className={cardHeaderClass}>
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-sm">My Signals</h3>
          </div>
          <span className="text-xs text-muted-foreground font-mono">
            {signals.length} signals
          </span>
        </div>

        {signalsLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
          </div>
        ) : signals.length === 0 ? (
          <div className="py-12 text-center">
            <Radio className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">No signals yet</p>
          </div>
        ) : (
          <div className="overflow-x-auto -mx-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/30 text-left">
                  <th className="px-4 py-2.5 text-xs font-medium text-muted-foreground">Time</th>
                  <th className="px-4 py-2.5 text-xs font-medium text-muted-foreground">Script</th>
                  <th className="px-4 py-2.5 text-xs font-medium text-muted-foreground">Symbol</th>
                  <th className="px-4 py-2.5 text-xs font-medium text-muted-foreground">Action</th>
                  <th className="px-4 py-2.5 text-xs font-medium text-muted-foreground">Signal Type</th>
                  <th className="px-4 py-2.5 text-xs font-medium text-muted-foreground">Status</th>
                  <th className="px-4 py-2.5 text-xs font-medium text-muted-foreground">Ticket</th>
                  <th className="px-4 py-2.5 text-xs font-medium text-muted-foreground">Message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {signals.map((signal) => (
                  <tr key={signal.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-2.5 text-muted-foreground text-xs whitespace-nowrap">
                      {formatDateTime(signal.created_at)}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">{signal.script_id}</td>
                    <td className="px-4 py-2.5 font-mono font-medium text-xs">{signal.symbol}</td>
                    <td className="px-4 py-2.5">
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded text-xs font-medium border",
                          actionBadge(signal.action)
                        )}
                      >
                        {signal.action}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded text-xs font-medium border",
                          signalTypeBadge(signal.signal_type)
                        )}
                      >
                        {signal.signal_type}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded text-xs font-medium border",
                          statusBadge(signal.status)
                        )}
                      >
                        {signal.status}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs">
                      {signal.ticket != null ? signal.ticket : "-"}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-muted-foreground max-w-[200px] truncate">
                      {signal.message}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {/* Quick Create Script (Admin) */}
      {isAdmin && (
        <motion.div
          {...fadeIn}
          className="bg-card border border-primary/20 rounded-lg p-6"
        >
          <div className={cardHeaderClass}>
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-primary" />
              <h3 className="font-semibold text-sm">Quick Create Script</h3>
            </div>
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-primary-foreground rounded-md text-xs font-medium hover:opacity-90 transition-opacity"
            >
              {showCreate ? null : <Plus className="w-3.5 h-3.5" />}
              {showCreate ? "Cancel" : "Create Script"}
            </button>
          </div>

          <AnimatePresence>
            {showCreate && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="overflow-hidden"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-muted-foreground">
                      Script Name
                    </label>
                    <input
                      type="text"
                      placeholder="My Strategy"
                      value={newScript.name}
                      onChange={(e) =>
                        setNewScript((prev) => ({ ...prev, name: e.target.value }))
                      }
                      className={inputClass}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-muted-foreground">
                      Description
                    </label>
                    <input
                      type="text"
                      placeholder="Brief description"
                      value={newScript.description}
                      onChange={(e) =>
                        setNewScript((prev) => ({ ...prev, description: e.target.value }))
                      }
                      className={inputClass}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-muted-foreground">
                      Symbol
                    </label>
                    <input
                      type="text"
                      placeholder="EURUSD"
                      value={newScript.symbol}
                      onChange={(e) =>
                        setNewScript((prev) => ({ ...prev, symbol: e.target.value }))
                      }
                      className={inputClass}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-muted-foreground">
                      Timeframe
                    </label>
                    <input
                      type="text"
                      placeholder="M5, M15, H1, D1"
                      value={newScript.timeframe}
                      onChange={(e) =>
                        setNewScript((prev) => ({ ...prev, timeframe: e.target.value }))
                      }
                      className={inputClass}
                    />
                  </div>
                </div>
                <div className="space-y-1.5 mb-4">
                  <label className="text-xs font-medium text-muted-foreground">
                    Script Config (JSON)
                  </label>
                  <textarea
                    rows={4}
                    placeholder='{"indicators": ["RSI", "MACD"], ...}'
                    value={newScript.script_config}
                    onChange={(e) =>
                      setNewScript((prev) => ({ ...prev, script_config: e.target.value }))
                    }
                    className={cn(inputClass, "font-mono text-xs resize-y")}
                  />
                </div>
                <button
                  onClick={handleCreateScript}
                  disabled={creating}
                  className="px-6 py-2.5 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center gap-2"
                >
                  {creating && <Loader2 className="w-4 h-4 animate-spin" />}
                  {creating ? "Creating..." : "Create Script"}
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}
    </div>
  );
}
