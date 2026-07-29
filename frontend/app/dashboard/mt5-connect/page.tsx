"use client";

import { useState, useEffect, useCallback } from "react";
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
  CircleDot,
  CheckCircle2,
} from "lucide-react";
import toast from "react-hot-toast";
import { bridgeApi } from "@/lib/api";
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

interface AccountData {
  account_number?: number;
  account_type?: string;
  broker?: string;
  company?: string;
  server?: string;
  balance?: number;
  equity?: number;
  margin?: number;
  free_margin?: number;
  leverage?: number;
  currency?: string;
  terminal_build?: number;
  connected_at?: string;
}

export default function MT5ConnectPage() {
  const [brokerName, setBrokerName] = useState("");
  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [serverName, setServerName] = useState("");
  const [remember, setRemember] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [bridgeOnline, setBridgeOnline] = useState<boolean | null>(null);
  const [account, setAccount] = useState<AccountData | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Check bridge on mount
  useEffect(() => {
    bridgeApi.get("/health").then(() => setBridgeOnline(true)).catch(() => setBridgeOnline(false));
    // Restore saved account
    const saved = localStorage.getItem("mt5_account");
    if (saved) {
      try { setAccount(JSON.parse(saved)); } catch {}
    }
  }, []);

  const fetchAccount = useCallback(async () => {
    try {
      const res = await bridgeApi.get("/account");
      const data = res.data;
      const acct: AccountData = {
        account_number: data.account_number,
        account_type: data.account_type || "live",
        company: data.company || brokerName,
        server: data.server || serverName,
        balance: data.balance,
        equity: data.equity,
        margin: data.margin,
        free_margin: data.free_margin,
        leverage: data.leverage,
        currency: data.currency || "USD",
      };
      localStorage.setItem("mt5_account", JSON.stringify(acct));
      setAccount(acct);
      return acct;
    } catch {
      return null;
    }
  }, [brokerName, serverName]);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!brokerName || !loginId || !password || !serverName) {
      toast.error("All fields are required");
      return;
    }
    setConnecting(true);
    try {
      const res = await bridgeApi.post("/connect", {
        broker_name: brokerName,
        login_id: parseInt(loginId) || 0,
        password,
        server_name: serverName,
      });
      toast.success("Connected to MT5!");
      // Fetch full account info after connect
      setTimeout(() => fetchAccount(), 1000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Connection failed";
      if (msg.includes("Network Error") || msg.includes("ERR_CONNECTION")) {
        toast.error("Bridge not running. Start: python bridge.py", { duration: 8000 });
      } else {
        toast.error(msg);
      }
    } finally {
      setConnecting(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAccount();
    setRefreshing(false);
    toast.success("Account refreshed");
  };

  const handleDisconnect = async () => {
    setDisconnecting(true);
    try {
      await bridgeApi.post("/disconnect");
      toast.success("Disconnected");
    } catch {
      // bridge might be offline, just clear locally
    }
    localStorage.removeItem("mt5_account");
    setAccount(null);
    setDisconnecting(false);
  };

  const isConnected = account !== null;

  return (
    <div className="space-y-6 max-w-2xl">
      <motion.div {...fadeIn}>
        <h1 className="text-2xl font-bold tracking-tight">MT5 Connection</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Connect your MetaTrader 5 trading account
        </p>
      </motion.div>

      {/* Bridge Status */}
      <motion.div {...fadeIn} className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <CircleDot className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">Bridge Status</h3>
          </div>
          <span className={cn(
            "px-2 py-1 rounded text-xs font-medium",
            bridgeOnline === true ? "bg-emerald-500/10 text-emerald-400" : 
            bridgeOnline === false ? "bg-red-500/10 text-red-400" :
            "bg-muted text-muted-foreground"
          )}>
            {bridgeOnline === true ? "Online" : bridgeOnline === false ? "Offline" : "Checking..."}
          </span>
        </div>
        {bridgeOnline === false && (
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-md p-3 text-sm text-amber-400">
            Bridge not detected. Run: <code className="bg-muted px-1.5 py-0.5 rounded text-xs">python bridge.py</code>
          </div>
        )}
      </motion.div>

      {/* Connection Form */}
      <motion.div {...fadeIn} className="bg-card border border-border rounded-lg p-6">
        <form onSubmit={handleConnect} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Broker Name
            </label>
            <input type="text" placeholder="e.g. CXM, ICMarkets, FXPro" value={brokerName}
              onChange={(e) => setBrokerName(e.target.value)} required className={inputClass} />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              MT5 Login ID
            </label>
            <input type="number" placeholder="732959" value={loginId}
              onChange={(e) => setLoginId(e.target.value)} required className={inputClass} />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Password
            </label>
            <input type="password" placeholder="Your MT5 password" value={password}
              onChange={(e) => setPassword(e.target.value)} required className={inputClass} />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Server Name
            </label>
            <input type="text" placeholder="e.g. CXMDirect-Live" value={serverName}
              onChange={(e) => setServerName(e.target.value)} required className={inputClass} />
          </div>

          <label className="flex items-center gap-2.5 cursor-pointer select-none group">
            <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="sr-only" />
            <div className={cn(
              "w-4 h-4 rounded border-2 flex items-center justify-center shrink-0 transition-colors",
              remember ? "bg-primary border-primary" : "border-muted-foreground/40 bg-transparent group-hover:border-muted-foreground/60"
            )}>
              {remember && (
                <svg className="w-2.5 h-2.5 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              )}
            </div>
            <span className="text-sm text-muted-foreground">Remember Credentials</span>
          </label>

          <div className="flex gap-3 pt-1">
            <button type="submit" disabled={connecting}
              className="flex-1 py-2.5 px-4 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center justify-center gap-2">
              {connecting && <Loader2 className="w-4 h-4 animate-spin" />}
              {connecting ? "Connecting..." : "Connect"}
            </button>
            <button type="button" onClick={handleDisconnect} disabled={disconnecting || !isConnected}
              className="py-2.5 px-4 border border-destructive/30 text-destructive rounded-md text-sm font-medium hover:bg-destructive/10 disabled:opacity-50 transition-colors">
              Disconnect
            </button>
          </div>
        </form>
      </motion.div>

      {/* Account Info Card */}
      {isConnected && account && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
            <div className="flex items-center gap-2.5">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
              </span>
              <span className="text-sm font-semibold text-emerald-400">Connected</span>
            </div>
            <button onClick={handleRefresh} disabled={refreshing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors">
              <RefreshCw className={cn("w-3.5 h-3.5", refreshing && "animate-spin")} />
              Refresh
            </button>
          </div>

          <motion.div variants={staggerChildren} initial="initial" animate="animate"
            className="grid grid-cols-2 lg:grid-cols-3 gap-3">
            {[
              { label: "Account #", value: account.account_number ? `#${account.account_number}` : "-", icon: User },
              { label: "Balance", value: account.balance != null ? formatCurrency(account.balance, account.currency || "USD") : "-", icon: Wallet },
              { label: "Equity", value: account.equity != null ? formatCurrency(account.equity, account.currency || "USD") : "-", icon: PiggyBank },
              { label: "Margin", value: account.margin != null ? formatCurrency(account.margin, account.currency || "USD") : "-", icon: TrendingUp },
              { label: "Free Margin", value: account.free_margin != null ? formatCurrency(account.free_margin, account.currency || "USD") : "-", icon: Shield },
              { label: "Leverage", value: account.leverage ? `1:${account.leverage}` : "-", icon: Activity },
              { label: "Server", value: account.server ?? "-", icon: Server },
              { label: "Company", value: account.company ?? "-", icon: Building2 },
              { label: "Currency", value: account.currency ?? "-", icon: ExternalLink },
            ].map(({ label, value, icon: Icon }) => (
              <motion.div key={label} variants={childVariant}
                className="bg-muted/50 rounded-md p-3 border border-border">
                <div className="flex items-center gap-1.5 mb-1">
                  <Icon className="w-3.5 h-3.5 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">{label}</span>
                </div>
                <p className="text-sm font-mono font-semibold text-foreground truncate">{value}</p>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
