"use client";

import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import {
  Activity,
  UserCheck,
  Plug,
  Webhook,
  TrendingUp,
  TrendingDown,
  XCircle,
  RefreshCcw,
  AlertCircle,
  Clock,
  Play,
  Square,
  LogIn,
} from "lucide-react";
import { useActivityLog } from "@/hooks/use-data";
import { cn, timeAgo } from "@/lib/utils";

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

const stagger = {
  animate: { transition: { staggerChildren: 0.05 } },
};

const eventConfig: Record<
  string,
  {
    icon: React.ElementType;
    color: string;
    bgColor: string;
    borderColor: string;
  }
> = {
  user_registered: {
    icon: UserCheck,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/50",
  },
  user_login: {
    icon: LogIn,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/50",
  },
  broker_connected: {
    icon: Plug,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/50",
  },
  broker_disconnected: {
    icon: XCircle,
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/50",
  },
  webhook_received: {
    icon: Webhook,
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/50",
  },
  trade_executed: {
    icon: TrendingUp,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/50",
  },
  trade_closed: {
    icon: TrendingDown,
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/50",
  },
  bot_started: {
    icon: Play,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/50",
  },
  bot_stopped: {
    icon: Square,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/50",
  },
  error: {
    icon: AlertCircle,
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/50",
  },
  connection_lost: {
    icon: AlertCircle,
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/50",
  },
  connection_restored: {
    icon: RefreshCcw,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/50",
  },
};

const defaultConfig = {
  icon: Clock,
  color: "text-gray-400",
  bgColor: "bg-gray-500/10",
  borderColor: "border-gray-500/50",
};

function formatEventType(type: string): string {
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

interface ActivityEntry {
  id: string | number;
  event_type: string;
  description: string;
  created_at: string;
}

export default function ActivityLogPage() {
  const { data: raw, isLoading } = useActivityLog();
  const activities: ActivityEntry[] = Array.isArray(raw)
    ? raw
    : raw?.data ?? raw?.activities ?? [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <motion.div {...fadeIn}>
        <h1 className="text-2xl font-bold tracking-tight">Activity Log</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Track all platform events and actions
        </p>
      </motion.div>

      <motion.div
        {...fadeIn}
        className="rounded-lg border border-border bg-card p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-muted-foreground">
            Showing{" "}
            <span className="font-medium text-foreground">
              {activities.length}
            </span>{" "}
            event{activities.length !== 1 ? "s" : ""}
          </p>
        </div>

        {activities.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <Activity className="w-12 h-12 mb-4 opacity-40" />
            <p className="text-sm">No activity recorded yet</p>
          </div>
        ) : (
          <motion.div className="space-y-0" {...stagger}>
            {activities.map((entry, i) => {
              const config = eventConfig[entry.event_type] ?? defaultConfig;
              const Icon = config.icon;

              return (
                <motion.div
                  key={entry.id ?? i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.04 }}
                  className={cn(
                    "flex items-start gap-4 py-3.5 border-l-2 pl-4",
                    config.borderColor,
                  )}
                >
                  <div
                    className={cn(
                      "flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center",
                      config.bgColor,
                    )}
                  >
                    <Icon className={cn("w-4.5 h-4.5", config.color)} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground">
                      {formatEventType(entry.event_type)}
                    </p>
                    <p className="text-sm text-muted-foreground mt-0.5 truncate">
                      {entry.description}
                    </p>
                  </div>

                  <div className="flex-shrink-0 text-xs text-muted-foreground whitespace-nowrap pt-0.5">
                    {timeAgo(entry.created_at)}
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
