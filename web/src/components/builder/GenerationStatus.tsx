import { useRef, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  Check,
  Loader2,
  Download,
  FileText,
  AlertCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  type JobStatus,
  STATUS_MESSAGES,
  PIPELINE_STAGES,
  STAGE_ORDER,
} from "@/constants/builder";

interface GenerationStatusProps {
  jobId: string | null;
  jobStatus: JobStatus | null;
  onDownload: (format: "pdf" | "markdown") => void;
  onRetry: () => void;
  onReset: () => void;
}

export function GenerationStatus({
  jobId,
  jobStatus,
  onDownload,
  onRetry,
  onReset,
}: GenerationStatusProps) {
  if (jobStatus?.status === "completed") {
    return <CompletedState jobStatus={jobStatus} onDownload={onDownload} onReset={onReset} />;
  }

  if (jobStatus?.status === "failed") {
    return <FailedState jobStatus={jobStatus} onRetry={onRetry} />;
  }

  return <InProgressState jobId={jobId} jobStatus={jobStatus} />;
}

// ── Completed ────────────────────────────────────────────────────

function CompletedState({
  jobStatus,
  onDownload,
  onReset,
}: {
  jobStatus: JobStatus;
  onDownload: (format: "pdf" | "markdown") => void;
  onReset: () => void;
}) {
  return (
    <div className="text-center space-y-6">
      <div className="w-20 h-20 mx-auto bg-green-100 rounded-full flex items-center justify-center">
        <Check className="h-10 w-10 text-green-600" />
      </div>
      <div>
        <h2 className="text-2xl font-bold mb-2">Your Book is Ready!</h2>
        <p className="text-slate-600">{jobStatus.book_name}</p>
      </div>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Button size="lg" onClick={() => onDownload("pdf")} className="bg-slate-900">
          <Download className="h-5 w-5 mr-2" />
          Download PDF
        </Button>
        <Button size="lg" variant="outline" onClick={() => onDownload("markdown")}>
          <FileText className="h-5 w-5 mr-2" />
          Download Markdown
        </Button>
      </div>
      <Button variant="ghost" onClick={onReset}>
        Create Another Book
      </Button>
    </div>
  );
}

// ── Failed ───────────────────────────────────────────────────────

function FailedState({
  jobStatus,
  onRetry,
}: {
  jobStatus: JobStatus;
  onRetry: () => void;
}) {
  return (
    <div className="text-center space-y-6">
      <div className="w-20 h-20 mx-auto bg-red-100 rounded-full flex items-center justify-center">
        <AlertCircle className="h-10 w-10 text-red-600" />
      </div>
      <div>
        <h2 className="text-2xl font-bold mb-2">Generation Failed</h2>
        <p className="text-slate-600">{jobStatus.error || "Something went wrong"}</p>
      </div>
      <Button onClick={onRetry}>
        <RefreshCw className="h-4 w-4 mr-2" />
        Try Again
      </Button>
    </div>
  );
}

// ── In Progress ──────────────────────────────────────────────────

function InProgressState({
  jobId,
  jobStatus,
}: {
  jobId: string | null;
  jobStatus: JobStatus | null;
}) {
  const currentStatusInfo = jobStatus
    ? STATUS_MESSAGES[jobStatus.status] || { stage: "Processing", description: jobStatus.message }
    : null;

  return (
    <div className="text-center space-y-6">
      <div className="w-20 h-20 mx-auto bg-slate-100 rounded-full flex items-center justify-center">
        <Loader2 className="h-10 w-10 text-slate-600 animate-spin" />
      </div>
      <div>
        <h2 className="text-2xl font-bold mb-2">Synthesizing Your Book</h2>
        <p className="text-slate-600">
          {currentStatusInfo?.description || "Starting generation..."}
        </p>
      </div>

      {/* Progress bar */}
      <div
        className="w-full bg-slate-200 rounded-full h-3"
        role="progressbar"
        aria-valuenow={jobStatus?.progress || 5}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Book generation progress"
      >
        <motion.div
          className="bg-gradient-to-r from-cyan-600 to-teal-600 h-3 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${jobStatus?.progress || 5}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>

      {/* Stage indicators */}
      <div className="grid grid-cols-9 gap-1 text-xs text-slate-400">
        {PIPELINE_STAGES.map((stage) => {
          const currentIdx = STAGE_ORDER.indexOf(jobStatus?.status || "");
          const stageIdx = STAGE_ORDER.indexOf(stage.key);
          const isActive = jobStatus?.status === stage.key;
          const isDone = currentIdx > stageIdx;

          return (
            <div
              key={stage.key}
              className={`flex flex-col items-center gap-1 ${
                isActive
                  ? "text-teal-600 font-semibold"
                  : isDone
                    ? "text-slate-900 font-medium"
                    : ""
              }`}
            >
              <div
                className={`w-2 h-2 rounded-full ${
                  isActive
                    ? "bg-teal-500 animate-pulse"
                    : isDone
                      ? "bg-slate-900"
                      : "bg-slate-300"
                }`}
              />
              {stage.label}
            </div>
          );
        })}
      </div>

      <p className="text-sm text-slate-500">
        This typically takes 30-60 minutes. You can leave this page and come back.
      </p>

      {/* Log trail */}
      {jobStatus?.logs && jobStatus.logs.length > 0 && (
        <LogPanel logs={jobStatus.logs} />
      )}

      {jobId && (
        <p className="text-xs text-slate-400">Job ID: {jobId}</p>
      )}
    </div>
  );
}

// ── Log Panel ─────────────────────────────────────────────────────

function LogPanel({ logs }: { logs: { t: string; msg: string }[] }) {
  const [expanded, setExpanded] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const visibleLogs = expanded ? logs : logs.slice(-3);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs.length]);

  return (
    <div className="w-full text-left">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 mb-2"
      >
        {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        {expanded ? "Collapse" : "Show"} activity log ({logs.length})
      </button>
      <div className={`bg-slate-950 rounded-lg p-3 font-mono text-xs ${expanded ? "max-h-60" : "max-h-24"} overflow-y-auto`}>
        {visibleLogs.map((log, i) => {
          const time = new Date(log.t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
          return (
            <div key={`${log.t}-${i}`} className="flex gap-2 py-0.5">
              <span className="text-slate-500 shrink-0">{time}</span>
              <span className="text-green-400">{log.msg}</span>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
