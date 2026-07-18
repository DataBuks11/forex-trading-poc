"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Plug,
  Loader2,
  RefreshCw,
  Shield,
  Wallet,
  PiggyBank,
  TrendingUp,
  Activity,
  Server,
  Key,
  User,
  Building2,
  ExternalLink,
} from "lucide-react";
import toast from "react-hot-toast";
import api from "@/lib/api";
import { useMT5Status } from "@/hooks/use-data";
import { cn, formatCurrency, formatNumber } from "@/lib/utils";

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

const staggerChildren = {
  animate: { transition: { staggerChildren: 0.05 } },
};

const childVariant = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
};

const inputClass =
  "w-full px-3 py-2 bg-muted border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all";

export default function MT5ConnectPage() {
  const { data, isLoading, refetch } = useMT5Status();
  const [brokerName, setBrokerName] = useState("");
  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [serverName, setServerName] = useState("");
  const [remember, setRemember] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  const isConnected = data?.is_connected;
  const account = data;

  const getPayload = () => ({
    broker_name: brokerName,
    login_id: parseInt(loginId) || 0,
    password,
    server_name: serverName,
    remember,
  });

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!brokerName || !loginId || !password || !serverName) {
      toast.error("All fields are required");
      return;
    }
    setConnecting(true);
    try {
      await api.post("/mt5/connect", getPayload());
      toast.success("Connected successfully");
      setTestResult(null);
      refetch();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Connection failed";
      toast.error(message);
    } finally {
      setConnecting(false);
    }
  };

  const handleTest = async () => {
    if (!brokerName || !loginId || !password || !serverName) {
      toast.error("All fields are required to test connection");
      return;
    }
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.post("/mt5/test", getPayload());
      const msg =
        res.data?.message || res.data?.detail || "Test connection successful";
      setTestResult({ success: true, message: msg });
      toast.success("Test connection successful");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Test connection failed";
      setTestResult({ success: false, message });
      toast.error(message);
    } finally {
      setTesting(false);
    }
  };

  const handleDisconnect = async () => {
    setDisconnecting(true);
    try {
      await api.post("/mt5/disconnect");
      toast.success("Disconnected");
      setTestResult(null);
      refetch();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Disconnect failed";
      toast.error(message);
    } finally {
      setDisconnecting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <motion.div {...fadeIn}>
        <h1 className="text-2xl font-bold tracking-tight">MT5 Connection</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Connect your MetaTrader 5 trading account
        </p>
      </motion.div>

      <motion.div
        {...fadeIn}
        className="bg-card border border-border rounded-lg p-6"
      >
        <form onSubmit={handleConnect} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <Building2 className="w-3.5 h-3.5" />
              Broker Name
            </label>
            <input
              type="text"
              placeholder="e.g. ICMarkets, FXPro, Exness, Pepperstone"
              value={brokerName}
              onChange={(e) => setBrokerName(e.target.value)}
              required
              className={inputClass}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <User className="w-3.5 h-3.5" />
              MT5 Login ID
            </label>
            <input
              type="number"
              placeholder="Enter your MT5 login ID"
              value={loginId}
              onChange={(e) => setLoginId(e.target.value)}
              required
              className={inputClass}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <Key className="w-3.5 h-3.5" />
              Password
            </label>
            <input
              type="password"
              placeholder="Enter your MT5 password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className={inputClass}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <Server className="w-3.5 h-3.5" />
              Server Name
            </label>
            <input
              type="text"
              placeholder="e.g. ICMarkets-Demo, ICMarkets-Live, Exness-Real"
              value={serverName}
              onChange={(e) => setServerName(e.target.value)}
              required
              className={inputClass}
            />
          </div>

          <label className="flex items-center gap-2.5 cursor-pointer select-none group">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              className="sr-only"
            />
            <div
              className={cn(
                "w-4 h-4 rounded border-2 flex items-center justify-center shrink-0 transition-colors",
                remember
                  ? "bg-primary border-primary"
                  : "border-muted-foreground/40 bg-transparent group-hover:border-muted-foreground/60"
              )}
            >
              {remember && (
                <svg
                  className="w-2.5 h-2.5 text-primary-foreground"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={3}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              )}
            </div>
            <span className="text-sm text-muted-foreground">
              Remember Credentials
            </span>
          </label>

          {testResult && (
            <div
              className={cn(
                "rounded-md p-3 text-sm",
                testResult.success
                  ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                  : "bg-red-500/10 border border-red-500/20 text-red-400"
              )}
            >
              {testResult.message}
            </div>
          )}

          <div className="flex gap-3 pt-1">
            <button
              type="submit"
              disabled={connecting}
              className="flex-1 py-2.5 px-4 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center justify-center gap-2"
            >
              {connecting && <Loader2 className="w-4 h-4 animate-spin" />}
              {connecting ? "Connecting..." : "Connect"}
            </button>
            <button
              type="button"
              onClick={handleTest}
              disabled={testing}
              className="flex-1 py-2.5 px-4 bg-secondary text-secondary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center justify-center gap-2"
            >
              {testing && <Loader2 className="w-4 h-4 animate-spin" />}
              {testing ? "Testing..." : "Test Connection"}
            </button>
            <button
              type="button"
              onClick={handleDisconnect}
              disabled={disconnecting}
              className="py-2.5 px-4 border border-destructive/30 text-destructive rounded-md text-sm font-medium hover:bg-destructive/10 disabled:opacity-50 transition-colors flex items-center justify-center gap-2 shrink-0"
            >
              {disconnecting && <Loader2 className="w-4 h-4 animate-spin" />}
              {disconnecting ? "..." : "Disconnect"}
            </button>
          </div>
        </form>
      </motion.div>

      {isConnected && account && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="bg-card border border-border rounded-lg p-6"
        >
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
            <div className="flex items-center gap-2.5">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
              </span>
              <span className="text-sm font-semibold text-emerald-400">
                Connected
              </span>
            </div>
            <button
              onClick={() => refetch()}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          </div>

          <motion.div
            variants={staggerChildren}
            initial="initial"
            animate="animate"
            className="grid grid-cols-2 lg:grid-cols-3 gap-3"
          >
            {[
              {
                label: "Account Number",
                value: account.account_number
                  ? `#${account.account_number}`
                  : "-",
                icon: User,
              },
              {
                label: "Account Type",
                value: account.account_type ?? "-",
                icon: Building2,
              },
              {
                label: "Broker",
                value: account.broker ?? "-",
                icon: Server,
              },
              {
                label: "Balance",
                value:
                  account.balance != null
                    ? formatCurrency(account.balance, account.currency)
                    : "-",
                icon: Wallet,
              },
              {
                label: "Equity",
                value:
                  account.equity != null
                    ? formatCurrency(account.equity, account.currency)
                    : "-",
                icon: PiggyBank,
              },
              {
                label: "Margin",
                value:
                  account.margin != null
                    ? formatCurrency(account.margin, account.currency)
                    : "-",
                icon: TrendingUp,
              },
              {
                label: "Free Margin",
                value:
                  account.free_margin != null
                    ? formatCurrency(account.free_margin, account.currency)
                    : account.balance != null && account.margin != null
                      ? formatCurrency(
                          account.balance - account.margin,
                          account.currency
                        )
                      : "-",
                icon: Shield,
              },
              {
                label: "Leverage",
                value: account.leverage
                  ? `1:${formatNumber(account.leverage, 0)}`
                  : "-",
                icon: Activity,
              },
              {
                label: "Currency",
                value: account.currency ?? "-",
                icon: ExternalLink,
              },
              {
                label: "Terminal Version",
                value: account.terminal_version ?? "-",
                icon: Server,
              },
              {
                label: "Connection Time",
                value: account.connection_time ?? "-",
                icon: Plug,
              },
              {
                label: "Server",
                value: account.server_name ?? account.server ?? "-",
                icon: Server,
              },
            ].map(({ label, value, icon: Icon }) => (
              <motion.div
                key={label}
                variants={childVariant}
                className="bg-muted/50 rounded-md p-3 border border-border"
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <Icon className="w-3.5 h-3.5 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">{label}</span>
                </div>
                <p className="text-sm font-mono font-semibold text-foreground truncate">
                  {value}
                </p>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
