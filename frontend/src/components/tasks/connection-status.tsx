"use client";

/**
 * Connection Status Indicator Component.
 *
 * Per T046: Shows real-time sync connection status to users.
 */

import { ConnectionStatus, getStatusColor, getStatusText } from "@/hooks/useRealTimeSync";

interface ConnectionStatusIndicatorProps {
  status: ConnectionStatus;
  showText?: boolean;
  className?: string;
}

/**
 * Visual indicator for WebSocket connection status.
 *
 * Displays a colored dot and optional text showing:
 * - Green "Live" when connected
 * - Yellow pulsing "Connecting..." when connecting
 * - Gray "Offline" when disconnected
 * - Red "Connection error" on error
 */
export function ConnectionStatusIndicator({
  status,
  showText = true,
  className = "",
}: ConnectionStatusIndicatorProps) {
  const colorClass = getStatusColor(status);
  const text = getStatusText(status);

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="relative">
        <div className={`w-2 h-2 rounded-full ${colorClass}`} />
        {status === "connected" && (
          <div className="absolute inset-0 w-2 h-2 rounded-full bg-green-500 animate-ping opacity-75" />
        )}
      </div>
      {showText && (
        <span
          className={`text-xs font-medium ${
            status === "connected"
              ? "text-green-600"
              : status === "error"
              ? "text-red-600"
              : "text-gray-500"
          }`}
        >
          {text}
        </span>
      )}
    </div>
  );
}

/**
 * Compact connection status for navbar/header.
 */
export function ConnectionStatusBadge({
  status,
  className = "",
}: {
  status: ConnectionStatus;
  className?: string;
}) {
  if (status === "connected") {
    return (
      <div
        className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-green-50 border border-green-200 ${className}`}
        title="Real-time sync active"
      >
        <div className="relative">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
          <div className="absolute inset-0 w-1.5 h-1.5 rounded-full bg-green-500 animate-ping opacity-75" />
        </div>
        <span className="text-[10px] font-semibold text-green-700 uppercase tracking-wide">
          Live
        </span>
      </div>
    );
  }

  if (status === "connecting") {
    return (
      <div
        className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-yellow-50 border border-yellow-200 ${className}`}
        title="Connecting to real-time sync..."
      >
        <div className="w-1.5 h-1.5 rounded-full bg-yellow-500 animate-pulse" />
        <span className="text-[10px] font-semibold text-yellow-700 uppercase tracking-wide">
          Syncing
        </span>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div
        className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-red-50 border border-red-200 ${className}`}
        title="Connection error - click to retry"
      >
        <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
        <span className="text-[10px] font-semibold text-red-700 uppercase tracking-wide">
          Error
        </span>
      </div>
    );
  }

  // Disconnected - show nothing or subtle indicator
  return null;
}
