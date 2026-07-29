"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Loader2,
  History,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  Download,
} from "lucide-react";
import { useTradeHistory } from "@/hooks/use-data";
import { cn, formatCurrency, formatNumber, formatDateTime } from "@/lib/utils";
import toast from "react-hot-toast";

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

const LIMIT = 20;

export default function TradeHistoryPage() {
  const [symbol, setSymbol] = useState("");
  const [action, setAction] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(0);

  const queryParams: Record<string, string> = {};
  if (symbol) queryParams.symbol = symbol;
  if (action) queryParams.action = action;
  if (status) queryParams.status = status;
  queryParams.offset = String(page * LIMIT);
  queryParams.limit = String(LIMIT);

  const { data, isLoading } = useTradeHistory(queryParams);

  const trades = data?.trades ?? [];
  const total = data?.total ?? 0;

  const totalPages = Math.ceil(total / LIMIT);

  const handleSearch = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSymbol(e.target.value);
    setPage(0);
  }, []);

  const handleActionChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      setAction(e.target.value);
      setPage(0);
    },
    []
  );

  const handleStatusChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      setStatus(e.target.value);
      setPage(0);
    },
    []
  );

  const handleExport = () => {
    toast("Export feature coming soon", { icon: "📦" });
  };

  return (
    <div className="space-y-6 max-w-7xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Trade History</h1>
        <p className="text-sm text-muted-foreground mt-1">
          View and filter your complete trading history
        </p>
      </div>

      {/* Filter Bar */}
      <motion.div
        {...fadeIn}
        className="rounded-lg border border-border bg-card p-3 flex gap-3 flex-wrap items-center"
      >
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search symbol..."
            value={symbol}
            onChange={handleSearch}
            className="w-full h-9 pl-9 pr-3 rounded-md border border-border bg-background text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <select
            value={action}
            onChange={handleActionChange}
            className="h-9 px-3 rounded-md border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Actions</option>
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
          </select>

          <select
            value={status}
            onChange={handleStatusChange}
            className="h-9 px-3 rounded-md border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Status</option>
            <option value="OPEN">OPEN</option>
            <option value="CLOSED">CLOSED</option>
          </select>
        </div>

        <button
          onClick={handleExport}
          className="h-9 px-3 rounded-md border border-border bg-background text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Export
        </button>
      </motion.div>

      {/* Trade History Table */}
      <motion.div
        {...fadeIn}
        className="rounded-lg border border-border bg-card overflow-hidden"
      >
        {isLoading ? (
          <div className="flex items-center justify-center h-96">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : trades.length === 0 ? (
          <div className="py-16 text-center">
            <History className="w-10 h-10 text-muted-foreground/40 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">
              No trades found matching your filters
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/50 text-left">
                  <th className="px-4 py-3 text-xs font-medium text-muted-foreground">
                    Time
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-muted-foreground">
                    Symbol
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-muted-foreground">
                    Action
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-muted-foreground">
                    Lot
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-muted-foreground">
                    Entry Price
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-muted-foreground">
                    SL
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-muted-foreground">
                    TP
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-muted-foreground">
                    Close Price
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-muted-foreground">
                    Profit
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-muted-foreground">
                    Status
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-muted-foreground">
                    Source
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-muted-foreground">
                    Broker
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-muted-foreground">
                    Ticket
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {trades.map(
                  (trade: {
                    id: number;
                    created_at: string;
                    symbol: string;
                    action: string;
                    lot: number;
                    open_price: number;
                    sl: number;
                    tp: number;
                    close_price: number;
                    profit: number;
                    status: string;
                    source?: string;
                    broker?: string;
                    ticket: number;
                  }) => (
                    <tr
                      key={trade.id}
                      className="hover:bg-muted/30 transition-colors"
                    >
                      <td className="px-4 py-2.5 text-muted-foreground text-xs whitespace-nowrap">
                        {formatDateTime(trade.created_at)}
                      </td>
                      <td className="px-4 py-2.5 font-mono font-medium whitespace-nowrap">
                        {trade.symbol}
                      </td>
                      <td className="px-4 py-2.5">
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded text-xs font-medium whitespace-nowrap",
                            trade.action === "BUY"
                              ? "bg-emerald-500/10 text-emerald-400"
                              : "bg-red-500/10 text-red-400"
                          )}
                        >
                          {trade.action}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 font-mono whitespace-nowrap">
                        {trade.lot}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs whitespace-nowrap">
                        {trade.open_price != null && trade.open_price > 0
                          ? trade.open_price.toFixed(5)
                          : "-"}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs whitespace-nowrap">
                        {trade.sl != null && trade.sl > 0
                          ? trade.sl.toFixed(5)
                          : "-"}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs whitespace-nowrap">
                        {trade.tp != null && trade.tp > 0
                          ? trade.tp.toFixed(5)
                          : "-"}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs whitespace-nowrap">
                        {trade.close_price != null && trade.close_price > 0
                          ? trade.close_price.toFixed(5)
                          : "-"}
                      </td>
                      <td className="px-4 py-2.5 font-mono whitespace-nowrap">
                        {trade.profit != null ? (
                          <span
                            className={cn(
                              trade.profit >= 0
                                ? "text-emerald-400"
                                : "text-red-400"
                            )}
                          >
                            {trade.profit >= 0 ? "+" : ""}
                            {trade.profit.toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5">
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded text-xs font-medium whitespace-nowrap",
                            trade.status === "OPEN"
                              ? "bg-blue-500/10 text-blue-400"
                              : "bg-muted text-muted-foreground"
                          )}
                        >
                          {trade.status}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-xs text-muted-foreground whitespace-nowrap">
                        {trade.source ?? "-"}
                      </td>
                      <td className="px-4 py-2.5 text-xs text-muted-foreground whitespace-nowrap">
                        {trade.broker ?? "-"}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs whitespace-nowrap">
                        {trade.ticket}
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {/* Pagination */}
      {!isLoading && trades.length > 0 && (
        <motion.div
          {...fadeIn}
          className="flex justify-between items-center"
        >
          <span className="text-sm text-muted-foreground">
            Showing {page * LIMIT + 1}–{Math.min((page + 1) * LIMIT, total)}{" "}
            of {total} trades
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="h-9 w-9 rounded-md border border-border bg-card flex items-center justify-center hover:bg-muted/50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() =>
                setPage((p) => Math.min(totalPages - 1, p + 1))
              }
              disabled={page >= totalPages - 1}
              className="h-9 w-9 rounded-md border border-border bg-card flex items-center justify-center hover:bg-muted/50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
}
