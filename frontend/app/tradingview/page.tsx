"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Loader2,
  Copy,
  RefreshCw,
  Key,
  Play,
  CheckCircle,
  Clock,
  ArrowRight,
  Radio,
  Activity,
  Zap,
  Eye,
  EyeOff,
  Webhook,
  AlertCircle,
  XCircle,
} from "lucide-react";
import toast from "react-hot-toast";
import { useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { cn, formatDateTime, copyToClipboard } from "@/lib/utils";
import { useWebhookSettings, useWebhookHistory, useLastSignal, useMT5Status } from "@/hooks/use-data";

const WEBHOOK_URL = "https://api-woad-ten-44.vercel.app/api/webhook/tradingview";

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

const cardBase = "bg-card border border-border rounded-lg p-6";

const stepAnimation = {
  initial: { opacity: 0, x: -20, height: 0 },
  animate: { opacity: 1, x: 0, height: "auto" },
  exit: { opacity: 0, x: 20, height: 0 },
  transition: { duration: 0.35, ease: "easeInOut" },
};

const testSteps = [
  { id: 1, label: "Signal Received" },
  { id: 2, label: "Validating" },
  { id: 3, label: "Sending to MT5" },
  { id: 4, label: "Executing" },
  { id: 5, label: "Trade Opened" },
] as const;

type StepStatus = "idle" | "loading" | "success" | "error";

export default function TradingViewPage() {
  const queryClient = useQueryClient();

  const { data: mt5Status, isLoading: mt5Loading } = useMT5Status();
  const { data: webhookSettings, isLoading: settingsLoading } = useWebhookSettings();
  const { data: lastSignal, isLoading: signalLoading } = useLastSignal();
  const { data: webhookHistory, isLoading: historyLoading } = useWebhookHistory();

  const [showSecret, setShowSecret] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testStepStatuses, setTestStepStatuses] = useState<StepStatus[]>(
    Array(testSteps.length).fill("idle")
  );
  const [testError, setTestError] = useState<string | null>(null);

  const isConnected = mt5Status?.is_connected === true;
  const isLoading = mt5Loading || settingsLoading || signalLoading || historyLoading;

  const webhookUrl = webhookSettings?.webhook_url ?? WEBHOOK_URL;

  const handleCopyUrl = useCallback(async () => {
    try {
      await copyToClipboard(webhookUrl);
      toast.success("Webhook URL copied to clipboard");
    } catch {
      toast.error("Failed to copy URL");
    }
  }, [webhookUrl]);

  const handleRegenerateKey = async () => {
    setRegenerating(true);
    try {
      await api.post("/webhook/regenerate-secret");
      queryClient.invalidateQueries({ queryKey: ["webhook-settings"] });
      toast.success("New secret key generated");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to regenerate key";
      toast.error(message);
    } finally {
      setRegenerating(false);
    }
  };

  const handleTestSignal = async () => {
    setTesting(true);
    setTestError(null);
    setTestStepStatuses(Array(testSteps.length).fill("idle"));

    try {
      for (let i = 0; i < testSteps.length; i++) {
        setTestStepStatuses((prev) => {
          const next = [...prev];
          next[i] = "loading";
          return next;
        });

        await new Promise((resolve) => setTimeout(resolve, 600));
      }

      await api.post("/webhook/test");

      setTestStepStatuses((prev) => prev.map(() => "success" as StepStatus));
      toast.success("Test signal processed successfully");
      queryClient.invalidateQueries({ queryKey: ["last-signal"] });
      queryClient.invalidateQueries({ queryKey: ["webhook-history"] });
      queryClient.invalidateQueries({ queryKey: ["trade-history"] });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Test signal failed";

      const currentStatuses = testStepStatuses;
      for (let i = currentStatuses.length - 1; i >= 0; i--) {
        if (currentStatuses[i] === "loading" || currentStatuses[i] === "idle") {
          setTestStepStatuses((prev) => {
            const next = [...prev];
            next[i] = "error";
            return next;
          });
          break;
        }
      }

      setTestError(message);
      toast.error(message);
    } finally {
      setTesting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const maskedSecret = webhookSettings?.webhook_secret
    ? webhookSettings.webhook_secret.slice(0, 6) + "••••••••••••••••"
    : "Not configured";
  const webhookEnabled = webhookSettings?.webhook_enabled ?? false;

  return (
    <div className="space-y-6 max-w-5xl">
      <motion.div {...fadeIn}>
        <h1 className="text-2xl font-bold tracking-tight">TradingView Integration</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Receive and execute trading signals from TradingView via webhooks
        </p>
      </motion.div>

      {!isConnected && (
        <motion.div
          {...fadeIn}
          className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-4 flex items-start gap-3"
        >
          <AlertCircle className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-amber-400">MT5 Not Connected</p>
            <p className="text-xs text-muted-foreground mt-1">
              Connect MT5 first to test webhook signals
            </p>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <motion.div {...fadeIn} className={cardBase}>
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Webhook className="w-5 h-5 text-primary" />
              <h3 className="font-semibold text-sm">Webhook URL</h3>
            </div>
            <span
              className={cn(
                "px-2 py-0.5 rounded text-xs font-medium border",
                webhookEnabled
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : "bg-muted text-muted-foreground border-border"
              )}
            >
              {webhookEnabled ? "Active" : "Inactive"}
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <p className="text-xs text-muted-foreground mb-1.5">Your Webhook URL</p>
              <div className="flex items-center gap-2">
                <input
                  readOnly
                  value={webhookUrl}
                  className="flex-1 px-3 py-2 bg-muted border border-border rounded-md text-sm font-mono text-foreground focus:outline-none"
                />
                <button
                  onClick={handleCopyUrl}
                  className="shrink-0 p-2 bg-muted border border-border rounded-md text-muted-foreground hover:text-foreground hover:border-primary/50 transition-colors"
                  title="Copy URL"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div {...fadeIn} className={cardBase}>
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Key className="w-5 h-5 text-primary" />
              <h3 className="font-semibold text-sm">Secret Key</h3>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <p className="text-xs text-muted-foreground mb-1.5">Webhook Secret</p>
              <div className="flex items-center gap-2">
                <input
                  readOnly
                  value={showSecret ? (webhookSettings?.webhook_secret ?? "Not configured") : maskedSecret}
                  className="flex-1 px-3 py-2 bg-muted border border-border rounded-md text-sm font-mono text-foreground focus:outline-none"
                />
                <button
                  onClick={() => setShowSecret((prev) => !prev)}
                  className="shrink-0 p-2 bg-muted border border-border rounded-md text-muted-foreground hover:text-foreground hover:border-primary/50 transition-colors"
                  title={showSecret ? "Hide key" : "Show key"}
                >
                  {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              onClick={handleRegenerateKey}
              disabled={regenerating}
              className="flex items-center gap-2 px-4 py-2 bg-muted border border-border rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:border-primary/50 disabled:opacity-50 transition-colors"
            >
              {regenerating ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              Generate New Key
            </button>
          </div>
        </motion.div>
      </div>

      <motion.div {...fadeIn} className={cardBase}>
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-sm">Last Signal</h3>
          </div>
        </div>

        {lastSignal ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { label: "Symbol", value: lastSignal.symbol ?? "-", mono: true },
              {
                label: "Action",
                value: lastSignal.action ?? "-",
                badge: true,
                badgeClass:
                  lastSignal.action === "BUY"
                    ? "bg-emerald-500/10 text-emerald-400"
                    : "bg-red-500/10 text-red-400",
              },
              { label: "Lot", value: lastSignal.lot ?? "-", mono: true },
              {
                label: "Status",
                value: lastSignal.status ?? "-",
                badge: true,
                badgeClass:
                  lastSignal.status === "FILLED" || lastSignal.status === "EXECUTED"
                    ? "bg-emerald-500/10 text-emerald-400"
                    : lastSignal.status === "PENDING"
                      ? "bg-amber-500/10 text-amber-400"
                      : lastSignal.status === "ERROR" || lastSignal.status === "REJECTED"
                        ? "bg-red-500/10 text-red-400"
                        : "bg-blue-500/10 text-blue-400",
              },
              {
                label: "Time",
                value: lastSignal.timestamp ? formatDateTime(lastSignal.timestamp) : "-",
              },
              { label: "Ticket", value: lastSignal.ticket ?? "-", mono: true },
            ].map(({ label, value, mono, badge, badgeClass }) => (
              <div
                key={label}
                className="bg-muted/30 border border-border rounded-md p-3"
              >
                <span className="text-xs text-muted-foreground block mb-1">{label}</span>
                {badge ? (
                  <span
                    className={cn(
                      "px-1.5 py-0.5 rounded text-xs font-medium inline-block",
                      badgeClass
                    )}
                  >
                    {value}
                  </span>
                ) : (
                  <p
                    className={cn(
                      "text-sm font-semibold text-foreground",
                      mono && "font-mono"
                    )}
                  >
                    {value}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="py-8 text-center">
            <Clock className="w-8 h-8 text-muted-foreground/40 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">No signals received yet</p>
          </div>
        )}
      </motion.div>

      <motion.div {...fadeIn} className={cardBase}>
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-sm">Test Webhook</h3>
          </div>
        </div>

        <div className="space-y-4">
          <button
            onClick={handleTestSignal}
            disabled={testing || !isConnected}
            className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
          >
            {testing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Test Signal
          </button>

          <AnimatePresence>
            {(testing || testStepStatuses.some((s) => s !== "idle")) && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="bg-muted/30 border border-border rounded-md p-4 space-y-2">
                  <AnimatePresence>
                    {testSteps.map((step, i) => {
                      const status = testStepStatuses[i];
                      if (status === "idle") return null;

                      return (
                        <motion.div
                          key={step.id}
                          {...stepAnimation}
                          className="flex items-center gap-3 py-1.5"
                        >
                          {status === "loading" ? (
                            <Loader2 className="w-4 h-4 animate-spin text-blue-400 shrink-0" />
                          ) : status === "success" ? (
                            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                          ) : status === "error" ? (
                            <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                          ) : null}

                          <span
                            className={cn(
                              "text-sm",
                              status === "loading" && "text-blue-400",
                              status === "success" && "text-emerald-400",
                              status === "error" && "text-red-400"
                            )}
                          >
                            Step {step.id}: {step.label}
                          </span>
                        </motion.div>
                      );
                    })}
                  </AnimatePresence>

                  {testError && (
                    <motion.p
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="text-xs text-red-400 mt-3 pt-3 border-t border-border"
                    >
                      Error: {testError}
                    </motion.p>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>

      <motion.div {...fadeIn} className={cardBase}>
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-sm">Signal History</h3>
          </div>
          <span className="text-xs text-muted-foreground font-mono">
            Last {Math.min((webhookHistory ?? []).length, 20)} signals
          </span>
        </div>

        {!webhookHistory || webhookHistory.length === 0 ? (
          <div className="py-8 text-center">
            <Activity className="w-8 h-8 text-muted-foreground/40 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">No webhook signals received</p>
          </div>
        ) : (
          <div className="overflow-x-auto -mx-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/30 text-left">
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Time</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Symbol</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Action</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Lot</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Status</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {webhookHistory.slice(0, 20).map((entry: { id: number; timestamp?: string; created_at?: string; symbol: string; action: string; lot: number; status: string; message?: string }, i: number) => (
                  <tr key={entry.id ?? i} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-2 text-muted-foreground text-xs whitespace-nowrap">
                      {formatDateTime(entry.timestamp ?? entry.created_at ?? "")}
                    </td>
                    <td className="px-4 py-2 font-mono font-medium whitespace-nowrap">{entry.symbol}</td>
                    <td className="px-4 py-2">
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded text-xs font-medium",
                          entry.action === "BUY"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-red-500/10 text-red-400"
                        )}
                      >
                        {entry.action}
                      </span>
                    </td>
                    <td className="px-4 py-2 font-mono">{entry.lot}</td>
                    <td className="px-4 py-2">
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded text-xs font-medium",
                          entry.status === "FILLED" || entry.status === "EXECUTED" || entry.status === "SUCCESS"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : entry.status === "PENDING"
                              ? "bg-amber-500/10 text-amber-400"
                              : entry.status === "ERROR" || entry.status === "REJECTED" || entry.status === "FAILED"
                                ? "bg-red-500/10 text-red-400"
                                : "bg-blue-500/10 text-blue-400"
                        )}
                      >
                        {entry.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground max-w-[200px] truncate">
                      {entry.message ?? "-"}
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
