"use client";

import { useEffect, useCallback, useRef } from "react";
import {
  type JobStatus,
  POLL_INITIAL_MS,
  POLL_MAX_MS,
  POLL_BACKOFF,
  POLL_MAX_ERRORS,
} from "@/constants/builder";

interface UseJobPollingOptions {
  jobId: string | null;
  active: boolean;
  onStatus: (status: JobStatus) => void;
  onError: (message: string) => void;
}

export function useJobPolling({ jobId, active, onStatus, onError }: UseJobPollingOptions) {
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const errorCountRef = useRef(0);
  const intervalRef = useRef(POLL_INITIAL_MS);

  const poll = useCallback(async () => {
    if (!jobId) return;

    try {
      const response = await fetch(`/api/generate/${jobId}`);
      if (!response.ok) throw new Error("Failed to get job status");

      const data: JobStatus = await response.json();
      onStatus(data);
      errorCountRef.current = 0;

      if (data.status === "completed" || data.status === "failed") {
        return; // done
      }
    } catch {
      errorCountRef.current += 1;
      if (errorCountRef.current >= POLL_MAX_ERRORS) {
        onError("Lost connection to the server. Your job is still running — refresh to check.");
        return;
      }
    }

    intervalRef.current = Math.min(intervalRef.current * POLL_BACKOFF, POLL_MAX_MS);
    pollRef.current = setTimeout(poll, intervalRef.current);
  }, [jobId, onStatus, onError]);

  useEffect(() => {
    if (!jobId || !active) return;

    intervalRef.current = POLL_INITIAL_MS;
    errorCountRef.current = 0;
    poll();

    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, [jobId, active, poll]);
}
