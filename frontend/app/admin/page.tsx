"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Loader2,
  RefreshCw,
  Users,
  Code2,
  BarChart3,
  Activity,
  ChevronLeft,
  ChevronRight,
  Shield,
} from "lucide-react";
import toast from "react-hot-toast";
import api from "@/lib/api";
import { cn, formatNumber, formatDateTime } from "@/lib/utils";
import { useAuth } from "@/providers/auth-provider";
import { useQuery } from "@tanstack/react-query";

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

const cardBase = "rounded-lg border border-border bg-card p-5";

const actionBadge = (action: string) =>
  cn(
    "px-1.5 py-0.5 rounded text-xs font-medium",
    action === "BUY"
      ? "bg-emerald-500/10 text-emerald-400"
      : action === "SELL"
        ? "bg-red-500/10 text-red-400"
        : "bg-muted text-muted-foreground"
  );

const statusBadge = (status: string) =>
  cn(
    "px-1.5 py-0.5 rounded text-xs font-medium",
    status === "OPEN" || status === "ACTIVE"
      ? "bg-blue-500/10 text-blue-400"
      : status === "CLOSED" || status === "WIN"
        ? "bg-emerald-500/10 text-emerald-400"
        : status === "LOSS" || status === "CANCELLED"
          ? "bg-red-500/10 text-red-400"
          : status === "PENDING"
            ? "bg-amber-500/10 text-amber-400"
            : "bg-muted text-muted-foreground"
  );

function Spinner() {
  return (
    <div className="flex items-center justify-center h-96">
      <Loader2 className="w-8 h-8 animate-spin text-primary" />
    </div>
  );
}

function RefreshButton({ onClick, loading }: { onClick: () => void; loading?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-muted border border-border text-muted-foreground hover:text-foreground hover:bg-muted/70 transition-colors disabled:opacity-50"
    >
      <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
      Refresh
    </button>
  );
}

export default function AdminPage() {
  const { user } = useAuth();

  const {
    data: stats,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: async () => {
      const { data } = await api.get("/scripts/admin/stats");
      return data;
    },
  });

  const {
    data: users,
    isLoading: usersLoading,
    refetch: refetchUsers,
  } = useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => {
      const { data } = await api.get("/scripts/admin/users");
      return data;
    },
  });

  const [tradesPage, setTradesPage] = useState(1);
  const {
    data: tradesData,
    isLoading: tradesLoading,
    refetch: refetchTrades,
  } = useQuery({
    queryKey: ["admin-trades", tradesPage],
    queryFn: async () => {
      const { data } = await api.get("/scripts/admin/trades", {
        params: { page: tradesPage, limit: 15 },
      });
      return data;
    },
    placeholderData: (prev) => prev,
  });

  const {
    data: signals,
    isLoading: signalsLoading,
    refetch: refetchSignals,
  } = useQuery({
    queryKey: ["admin-signals"],
    queryFn: async () => {
      const { data } = await api.get("/scripts/signals");
      return data;
    },
  });

  const {
    data: scripts,
    isLoading: scriptsLoading,
    refetch: refetchScripts,
  } = useQuery({
    queryKey: ["admin-scripts"],
    queryFn: async () => {
      const { data } = await api.get("/scripts");
      return data;
    },
  });

  const [togglingScriptId, setTogglingScriptId] = useState<number | null>(null);

  const handleToggleScript = useCallback(
    async (id: number, currentActive: boolean) => {
      setTogglingScriptId(id);
      try {
        await api.put(`/scripts/${id}`, { is_active: currentActive ? 0 : 1 });
        toast.success(`Script ${currentActive ? "deactivated" : "activated"}`);
        refetchScripts();
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to toggle script";
        toast.error(message);
      } finally {
        setTogglingScriptId(null);
      }
    },
    [refetchScripts]
  );

  const statsCards = [
    { label: "Total Users", value: stats?.total_users ?? "-", icon: Users, color: "text-blue-400" },
    { label: "Active Scripts", value: stats?.active_scripts ?? "-", icon: Code2, color: "text-emerald-400" },
    { label: "Total Trades", value: stats?.total_trades ?? "-", icon: BarChart3, color: "text-amber-400" },
    { label: "Total Signals", value: stats?.total_signals ?? "-", icon: Activity, color: "text-purple-400" },
  ];

  if (statsLoading && usersLoading && tradesLoading && signalsLoading && scriptsLoading) {
    return <Spinner />;
  }

  const tradesList = Array.isArray(tradesData) ? tradesData : tradesData?.trades ?? [];
  const totalTrades = tradesData?.total ?? tradesList.length;
  const hasNextPage = tradesData?.has_next ?? false;

  return (
    <div className="space-y-6 max-w-7xl">
      <motion.div {...fadeIn}>
        <h1 className="text-2xl font-bold tracking-tight">Admin Panel</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Manage users, scripts, and monitor all trading activity
        </p>
      </motion.div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsCards.map(({ label, value, icon: Icon, color }) => (
          <motion.div key={label} {...fadeIn} className={cardBase}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className={cn("text-2xl font-bold font-mono mt-1", color)}>{value}</p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-muted/50 flex items-center justify-center">
                <Icon className={cn("w-5 h-5", color)} />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Users Table */}
      <motion.div {...fadeIn} className={cardBase}>
        <div className="flex items-center justify-between mb-3 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-sm">Users</h3>
          </div>
          <RefreshButton onClick={() => refetchUsers()} loading={usersLoading} />
        </div>
        {usersLoading ? (
          <Spinner />
        ) : !Array.isArray(users) || users.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm text-muted-foreground">No users found</p>
          </div>
        ) : (
          <div className="overflow-x-auto -mx-5">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/30 text-left">
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">ID</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Username</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Email</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Scripts</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Trades</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Signals</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Joined</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {users.map((u: { id: number; username: string; email: string; scripts_count?: number; trades_count?: number; signals_count?: number; created_at?: string; joined_at?: string }) => {
                  const isAdmin = u.id === user?.id;
                  const joined = u.created_at || u.joined_at;
                  return (
                    <tr
                      key={u.id}
                      className={cn(
                        "hover:bg-muted/30 transition-colors",
                        isAdmin && "bg-primary/5"
                      )}
                    >
                      <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                        {u.id}
                        {isAdmin && (
                          <span className="ml-2 inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-medium bg-primary/10 text-primary">
                            <Shield className="w-3 h-3" />
                            Admin
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2 font-medium">{u.username}</td>
                      <td className="px-4 py-2 text-muted-foreground text-xs">{u.email}</td>
                      <td className="px-4 py-2 font-mono text-xs">{u.scripts_count ?? "-"}</td>
                      <td className="px-4 py-2 font-mono text-xs">{u.trades_count ?? "-"}</td>
                      <td className="px-4 py-2 font-mono text-xs">{u.signals_count ?? "-"}</td>
                      <td className="px-4 py-2 text-muted-foreground text-xs">
                        {joined ? new Date(joined).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "-"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {/* All Trades Table */}
      <motion.div {...fadeIn} className={cardBase}>
        <div className="flex items-center justify-between mb-3 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-sm">All Trades</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground font-mono">
              {tradesPage > 1 ? `Page ${tradesPage}` : ""} {totalTrades ? `${totalTrades} trades` : ""}
            </span>
            <RefreshButton onClick={() => refetchTrades()} loading={tradesLoading} />
          </div>
        </div>
        {tradesLoading ? (
          <Spinner />
        ) : tradesList.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm text-muted-foreground">No trades found</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto -mx-5">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-muted/30 text-left">
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Time</th>
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">User</th>
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Symbol</th>
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Action</th>
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Lot</th>
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Price</th>
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">SL / TP</th>
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Status</th>
                    <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Ticket</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {tradesList.map((trade: { id?: number; ticket?: number; created_at?: string; time?: string; username?: string; user_id?: number; symbol: string; action: string; lot?: number; volume?: number; open_price?: number; price?: number; sl?: number; tp?: number; status: string; ticket_num?: number }) => (
                    <tr key={trade.id ?? trade.ticket} className="hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-2 text-muted-foreground text-xs">
                        {formatDateTime(trade.created_at || trade.time || "")}
                      </td>
                       <td className="px-4 py-2 text-xs">{trade.username || `#${trade.user_id}` || "-"}</td>
                      <td className="px-4 py-2 font-mono font-medium">{trade.symbol}</td>
                      <td className="px-4 py-2">
                        <span className={actionBadge(trade.action)}>{trade.action}</span>
                      </td>
                      <td className="px-4 py-2 font-mono text-xs">{trade.lot ?? trade.volume ?? "-"}</td>
                      <td className="px-4 py-2 font-mono text-xs">{trade.open_price?.toFixed(5) ?? trade.price?.toFixed(5) ?? "-"}</td>
                      <td className="px-4 py-2 font-mono text-xs">
                        {(trade.sl != null && trade.sl > 0) ? trade.sl.toFixed(5) : "-"} /{" "}
                        {(trade.tp != null && trade.tp > 0) ? trade.tp.toFixed(5) : "-"}
                      </td>
                      <td className="px-4 py-2">
                        <span className={statusBadge(trade.status)}>{trade.status}</span>
                      </td>
                      <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                        {trade.ticket ?? trade.ticket_num ?? "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex items-center justify-between mt-4 pt-3 border-t border-border">
              <span className="text-xs text-muted-foreground">
                Showing page {tradesPage}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setTradesPage((p) => Math.max(1, p - 1))}
                  disabled={tradesPage <= 1 || tradesLoading}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium bg-muted border border-border text-muted-foreground hover:text-foreground disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  Prev
                </button>
                <button
                  onClick={() => setTradesPage((p) => p + 1)}
                  disabled={!hasNextPage || tradesLoading}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium bg-muted border border-border text-muted-foreground hover:text-foreground disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </>
        )}
      </motion.div>

      {/* All Signals Table */}
      <motion.div {...fadeIn} className={cardBase}>
        <div className="flex items-center justify-between mb-3 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-sm">All Signals</h3>
          </div>
          <RefreshButton onClick={() => refetchSignals()} loading={signalsLoading} />
        </div>
        {signalsLoading ? (
          <Spinner />
        ) : !Array.isArray(signals) || signals.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm text-muted-foreground">No signals found</p>
          </div>
        ) : (
          <div className="overflow-x-auto -mx-5">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/30 text-left">
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Time</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">User ID</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Symbol</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Action</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Signal Type</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Status</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {signals.map((s: { id: number; created_at?: string; time?: string; user_id: number; symbol: string; action: string; signal_type?: string; type?: string; status: string; message?: string }) => (
                  <tr key={s.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-2 text-muted-foreground text-xs">
                      {formatDateTime(s.created_at || s.time || "")}
                    </td>
                    <td className="px-4 py-2 font-mono text-xs">{s.user_id}</td>
                    <td className="px-4 py-2 font-mono font-medium">{s.symbol}</td>
                    <td className="px-4 py-2">
                      <span className={actionBadge(s.action)}>{s.action}</span>
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground">
                      {s.signal_type || s.type || "-"}
                    </td>
                    <td className="px-4 py-2">
                      <span className={statusBadge(s.status)}>{s.status}</span>
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground max-w-[200px] truncate">
                      {s.message || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {/* Scripts Management */}
      <motion.div {...fadeIn} className={cardBase}>
        <div className="flex items-center justify-between mb-3 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Code2 className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-sm">Scripts Management</h3>
          </div>
          <RefreshButton onClick={() => refetchScripts()} loading={scriptsLoading} />
        </div>
        {scriptsLoading ? (
          <Spinner />
        ) : !Array.isArray(scripts) || scripts.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm text-muted-foreground">No scripts found</p>
          </div>
        ) : (
          <div className="overflow-x-auto -mx-5">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/30 text-left">
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">ID</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Name</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Symbol</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Timeframe</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Status</th>
                  <th className="px-4 py-2 text-xs font-medium text-muted-foreground">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {scripts.map((script: { id: number; name: string; symbol: string; timeframe: string; is_active: boolean | number }) => {
                  const isActive = script.is_active === true || script.is_active === 1;
                  const isToggling = togglingScriptId === script.id;
                  return (
                    <tr key={script.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{script.id}</td>
                      <td className="px-4 py-2 font-medium">{script.name}</td>
                      <td className="px-4 py-2 font-mono text-xs">{script.symbol}</td>
                      <td className="px-4 py-2 text-xs text-muted-foreground">{script.timeframe}</td>
                      <td className="px-4 py-2">
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded text-xs font-medium",
                            isActive
                              ? "bg-emerald-500/10 text-emerald-400"
                              : "bg-muted text-muted-foreground"
                          )}
                        >
                          {isActive ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-4 py-2">
                        <button
                          onClick={() => handleToggleScript(script.id, isActive)}
                          disabled={isToggling}
                          className={cn(
                            "px-3 py-1 rounded-md text-xs font-medium transition-colors disabled:opacity-50",
                            isActive
                              ? "bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20"
                              : "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/20"
                          )}
                        >
                          {isToggling ? (
                            <span className="flex items-center gap-1">
                              <Loader2 className="w-3 h-3 animate-spin" />
                              ...
                            </span>
                          ) : isActive ? (
                            "Deactivate"
                          ) : (
                            "Activate"
                          )}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>
    </div>
  );
}
