"use client";
import { useEffect, useRef } from "react";

/**
 * Generic polling hook — runs `fn` every `interval` ms.
 * Stops when component unmounts or `enabled` is false.
 */
export function usePolling(
  fn: () => void | Promise<void>,
  interval: number,
  enabled = true
) {
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => {
    if (!enabled) return;
    const timer = setInterval(() => {
      fnRef.current();
    }, interval);
    return () => clearInterval(timer);
  }, [interval, enabled]);
}
