"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "./api";

interface AsyncState<T> {
  data: T | null;
  error: string | null;
  isLoading: boolean;
}

/** Runs `fn` on mount and whenever `deps` change; exposes a `refetch` to re-run manually. */
export function useAsync<T>(fn: () => Promise<T>, deps: React.DependencyList): AsyncState<T> & { refetch: () => void } {
  const [state, setState] = useState<AsyncState<T>>({ data: null, error: null, isLoading: true });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    // Data-fetching effect: reset to loading, then resolve into data/error.
    // This is the documented shape for a fetch-in-effect (react.dev "Fetching data").
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setState((s) => ({ ...s, isLoading: true, error: null }));

    fn()
      .then((data) => {
        if (!cancelled) setState({ data, error: null, isLoading: false });
      })
      .catch((err) => {
        if (cancelled) return;
        const message = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
        setState({ data: null, error: message, isLoading: false });
      });

    return () => {
      cancelled = true;
    };
    // fn is intentionally excluded: callers pass a fresh inline function each render,
    // and `deps` already lists its real reactive inputs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  return { ...state, refetch };
}
