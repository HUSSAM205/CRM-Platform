"use client";

import { useEffect, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const WS_URL = API_URL.replace(/^http/, "ws");

export interface RealtimeEvent {
  kind: "notification" | "message";
  [key: string]: unknown;
}

/** Opens one WebSocket connection to the backend and forwards every parsed frame to onEvent. */
export function useRealtimeSocket(onEvent: (event: RealtimeEvent) => void) {
  const handlerRef = useRef(onEvent);
  handlerRef.current = onEvent;

  useEffect(() => {
    const socket = new WebSocket(`${WS_URL}/api/v1/ws`);
    socket.onmessage = (event) => {
      try {
        handlerRef.current(JSON.parse(event.data) as RealtimeEvent);
      } catch {
        // ignore malformed frames
      }
    };
    return () => socket.close();
  }, []);
}
