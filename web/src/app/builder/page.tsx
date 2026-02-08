"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  BookOpen,
  ArrowRight,
  ArrowLeft,
  Layers,
  Target,
  User,
  Compass,
  Sparkles,
  Check,
  Loader2,
  Download,
  FileText,
  AlertCircle,
  RefreshCw,
  Star,
  Key,
} from "lucide-react";
import Link from "next/link";

type Step = 1 | 2 | 3 | 4 | 5 | 6;

interface FormData {
  topic: string;
  domain: string;
  goal: string;
  background: string;
  focus: string[];
  geminiApiKey: string;
}

interface JobStatus {
  job_id: string;
  status: string;
  progress: number;
  current_stage: string;
  message: string;
  book_name?: string;
  error?: string;
}

const STORAGE_KEY = "polaris-builder";
const POLL_INITIAL_MS = 3_000;
const POLL_MAX_MS = 30_000;
const POLL_BACKOFF = 1.5;
const POLL_MAX_ERRORS = 10;

const focusOptions = [
  "Theoretical foundations",
  "Practical implementation",
  "Code examples",
  "Case studies",
  "Industry applications",
  "Research frontiers",
  "Historical context",
  "Comparative analysis",
];

const statusMessages: Record<string, { stage: string; description: string }> = {
  pending: { stage: "Queued", description: "Your book is in the queue..." },
  researching: {
    stage: "Research",
    description: "Researching cutting-edge papers and breakthroughs...",
  },
  generating_vision: {
    stage: "Vision",
    description: "Crafting the book's core thesis and themes...",
  },
  generating_outline: {
    stage: "Outline",
    description: "Designing chapter structure for your domain...",
  },
  planning: {
    stage: "Planning",
    description: "Creating detailed plans for each chapter...",
  },
  quality_review: {
    stage: "Quality Review",
    description: "Reviewing plans for coherence and completeness...",
  },
  writing_content: {
    stage: "Writing",
    description: "Synthesizing content tailored to your background...",
  },
  generating_illustrations: {
    stage: "Illustrating",
    description: "Creating diagrams and visualizations...",
  },
  generating_cover: {
    stage: "Cover",
    description: "Designing your book cover...",
  },
  assembling_pdf: {
    stage: "Assembly",
    description: "Assembling the final PDF...",
  },
  completed: {
    stage: "Complete",
    description: "Your book is ready!",
  },
  failed: {
    stage: "Failed",
    description: "Something went wrong.",
  },
};

function loadSaved(): { formData?: FormData; jobId?: string; step?: Step } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function persist(data: { formData: FormData; jobId: string | null; step: Step }) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // localStorage full or unavailable — ignore
  }
}

function clearPersisted() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

export default function BuilderPage() {
  const [step, setStep] = useState<Step>(1);
  const [formData, setFormData] = useState<FormData>({
    topic: "",
    domain: "",
    goal: "",
    background: "",
    focus: [],
    geminiApiKey: "",
  });
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // --- Restore from localStorage on mount ---
  useEffect(() => {
    const saved = loadSaved();
    if (saved.formData) setFormData(saved.formData);
    if (saved.jobId) setJobId(saved.jobId);
    if (saved.step) setStep(saved.step);
  }, []);

  // --- Persist on every meaningful change ---
  useEffect(() => {
    persist({ formData, jobId, step });
  }, [formData, jobId, step]);

  const updateField = (field: keyof FormData, value: string | string[]) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleFocus = (option: string) => {
    setFormData((prev) => ({
      ...prev,
      focus: prev.focus.includes(option)
        ? prev.focus.filter((f) => f !== option)
        : [...prev.focus, option],
    }));
  };

  const canProceed = () => {
    switch (step) {
      case 1:
        return formData.topic.trim().length > 0;
      case 2:
        return formData.domain.trim().length > 0;
      case 3:
        return formData.goal.trim().length > 0;
      case 4:
        return formData.background.trim().length > 0;
      case 5:
        return formData.geminiApiKey.trim().length > 0;
      default:
        return false;
    }
  };

  const nextStep = () => {
    if (step < 5 && canProceed()) {
      setStep((prev) => (prev + 1) as Step);
    }
  };

  const prevStep = () => {
    if (step > 1 && step < 6) {
      setStep((prev) => (prev - 1) as Step);
    }
  };

  // --- Exponential-backoff polling ---
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const errorCountRef = useRef(0);
  const intervalRef = useRef(POLL_INITIAL_MS);

  const pollJobStatus = useCallback(async () => {
    if (!jobId) return;

    try {
      const response = await fetch(`/api/generate/${jobId}`);
      if (!response.ok) throw new Error("Failed to get job status");

      const data: JobStatus = await response.json();
      setJobStatus(data);
      errorCountRef.current = 0; // reset on success

      if (data.status === "completed" || data.status === "failed") {
        return; // done — don't schedule next poll
      }
    } catch (err) {
      console.error("Error polling status:", err);
      errorCountRef.current += 1;
      if (errorCountRef.current >= POLL_MAX_ERRORS) {
        setError("Lost connection to the server. Your job is still running — refresh to check.");
        return;
      }
    }

    // Schedule next poll with backoff
    intervalRef.current = Math.min(intervalRef.current * POLL_BACKOFF, POLL_MAX_MS);
    pollRef.current = setTimeout(pollJobStatus, intervalRef.current);
  }, [jobId]);

  useEffect(() => {
    if (!jobId || step !== 6) return;

    // Reset backoff state
    intervalRef.current = POLL_INITIAL_MS;
    errorCountRef.current = 0;

    // Start first poll immediately
    pollJobStatus();

    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, [jobId, step, pollJobStatus]);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: formData.topic,
          domain: formData.domain,
          goal: formData.goal,
          background: formData.background,
          focus: formData.focus.length > 0 ? formData.focus.join(", ") : undefined,
          tier: "primer", // Demo mode: primer only (4 chapters)
          api_key: formData.geminiApiKey || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to start generation");
      }

      const data = await response.json();
      setJobId(data.job_id);
      setStep(6);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownload = async (format: "pdf" | "markdown") => {
    if (!jobId) return;

    try {
      const response = await fetch(
        `/api/generate/${jobId}/download?format=${format}`
      );
      if (!response.ok) {
        throw new Error("Download failed");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${jobStatus?.book_name || "book"}.${format === "pdf" ? "pdf" : "md"}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error("Download error:", err);
      setError("Failed to download file");
    }
  };

  const handleRetry = () => {
    setJobId(null);
    setJobStatus(null);
    setError(null);
    setStep(5);
  };

  const stepInfo = [
    { icon: BookOpen, label: "Topic", color: "blue" },
    { icon: Layers, label: "Domain", color: "purple" },
    { icon: Target, label: "Goal", color: "green" },
    { icon: User, label: "Background", color: "amber" },
    { icon: Compass, label: "Focus", color: "rose" },
  ];

  const currentStatusInfo = jobStatus
    ? statusMessages[jobStatus.status] || {
        stage: "Processing",
        description: jobStatus.message,
      }
    : null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md z-50 border-b border-slate-100">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-2">
            <Star className="h-6 w-6 text-amber-500 fill-amber-500/30" />
            <span className="font-semibold text-lg">Polaris</span>
          </Link>
          <Badge variant="secondary">Book Builder</Badge>
        </div>
      </nav>

      <div className="pt-32 pb-20 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Progress Steps - hide on step 6 */}
          {step < 6 && (
            <nav aria-label="Book builder progress" className="flex justify-between mb-12">
              {stepInfo.map((s, index) => {
                const StepIcon = s.icon;
                const isActive = index + 1 === step;
                const isComplete = index + 1 < step;
                return (
                  <div
                    key={index}
                    aria-current={isActive ? "step" : undefined}
                    className={`flex flex-col items-center gap-2 ${
                      isActive
                        ? "text-slate-900"
                        : isComplete
                          ? "text-green-600"
                          : "text-slate-300"
                    }`}
                  >
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        isActive
                          ? "bg-slate-900 text-white"
                          : isComplete
                            ? "bg-green-100 text-green-600"
                            : "bg-slate-100"
                      }`}
                    >
                      {isComplete ? (
                        <Check className="h-5 w-5" aria-label={`${s.label} complete`} />
                      ) : (
                        <StepIcon className="h-5 w-5" aria-hidden="true" />
                      )}
                    </div>
                    <span className="text-xs font-medium hidden sm:block">
                      {s.label}
                    </span>
                  </div>
                );
              })}
            </nav>
          )}

          {/* Step Content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Card className="border-0 shadow-xl">
                <CardContent className="p-8">
                  {step === 1 && (
                    <div className="space-y-6">
                      <div>
                        <h2 className="text-2xl font-bold mb-2">
                          What do you want to learn?
                        </h2>
                        <p className="text-slate-600">
                          Enter the field or topic you want to deeply understand.
                        </p>
                      </div>
                      <Input
                        placeholder="e.g., Neuro-symbolic AI, Quantum Computing, Knowledge Graphs"
                        aria-label="Topic you want to learn"
                        value={formData.topic}
                        onChange={(e) => updateField("topic", e.target.value)}
                        className="text-lg py-6"
                        autoFocus
                      />
                      <div className="flex flex-wrap gap-2">
                        {[
                          "Neuro-symbolic AI",
                          "Knowledge Graphs",
                          "Quantum Computing",
                          "Causal Inference",
                        ].map((suggestion) => (
                          <Badge
                            key={suggestion}
                            variant="outline"
                            className="cursor-pointer hover:bg-slate-100"
                            onClick={() => updateField("topic", suggestion)}
                          >
                            {suggestion}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {step === 2 && (
                    <div className="space-y-6">
                      <div>
                        <h2 className="text-2xl font-bold mb-2">
                          What&apos;s your professional domain?
                        </h2>
                        <p className="text-slate-600">
                          Every example and case study will be drawn from YOUR
                          world.
                        </p>
                      </div>
                      <Input
                        placeholder="e.g., Enterprise AI agents, Healthcare diagnostics, Legal tech"
                        aria-label="Your professional domain"
                        value={formData.domain}
                        onChange={(e) => updateField("domain", e.target.value)}
                        className="text-lg py-6"
                        autoFocus
                      />
                      <div className="flex flex-wrap gap-2">
                        {[
                          "Enterprise software",
                          "Healthcare",
                          "Legal tech",
                          "Fintech",
                          "Robotics",
                          "Education",
                        ].map((suggestion) => (
                          <Badge
                            key={suggestion}
                            variant="outline"
                            className="cursor-pointer hover:bg-slate-100"
                            onClick={() => updateField("domain", suggestion)}
                          >
                            {suggestion}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {step === 3 && (
                    <div className="space-y-6">
                      <div>
                        <h2 className="text-2xl font-bold mb-2">
                          What do you want to be able to DO?
                        </h2>
                        <p className="text-slate-600">
                          Describe your goal. The book will be structured around
                          this outcome.
                        </p>
                      </div>
                      <textarea
                        placeholder="e.g., Design and build hybrid LLM + knowledge graph systems for enterprise reasoning..."
                        aria-label="What you want to be able to do"
                        value={formData.goal}
                        onChange={(e) => updateField("goal", e.target.value)}
                        className="w-full min-h-[120px] px-4 py-3 text-lg border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-slate-900"
                        autoFocus
                      />
                    </div>
                  )}

                  {step === 4 && (
                    <div className="space-y-6">
                      <div>
                        <h2 className="text-2xl font-bold mb-2">
                          What&apos;s your background?
                        </h2>
                        <p className="text-slate-600">
                          We&apos;ll skip what you know and go deep where you
                          need it.
                        </p>
                      </div>
                      <textarea
                        placeholder="e.g., ML engineer with 3 years experience, familiar with transformers and Python. New to symbolic AI and knowledge graphs."
                        aria-label="Your background and experience"
                        value={formData.background}
                        onChange={(e) =>
                          updateField("background", e.target.value)
                        }
                        className="w-full min-h-[120px] px-4 py-3 text-lg border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-slate-900"
                        autoFocus
                      />
                    </div>
                  )}

                  {step === 5 && (
                    <div className="space-y-6">
                      <div>
                        <h2 className="text-2xl font-bold mb-2">
                          What aspects interest you most?
                        </h2>
                        <p className="text-slate-600">
                          Select focus areas for extra depth. (Optional)
                        </p>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        {focusOptions.map((option) => (
                          <div
                            key={option}
                            role="checkbox"
                            aria-checked={formData.focus.includes(option)}
                            aria-label={option}
                            tabIndex={0}
                            onClick={() => toggleFocus(option)}
                            onKeyDown={(e) => {
                              if (e.key === " " || e.key === "Enter") {
                                e.preventDefault();
                                toggleFocus(option);
                              }
                            }}
                            className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                              formData.focus.includes(option)
                                ? "border-slate-900 bg-slate-50"
                                : "border-slate-200 hover:border-slate-300"
                            }`}
                          >
                            <div className="flex items-center gap-2">
                              <div
                                className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                                  formData.focus.includes(option)
                                    ? "border-slate-900 bg-slate-900"
                                    : "border-slate-300"
                                }`}
                                aria-hidden="true"
                              >
                                {formData.focus.includes(option) && (
                                  <Check className="h-3 w-3 text-white" />
                                )}
                              </div>
                              <span className="text-sm font-medium">
                                {option}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Gemini API Key */}
                      <div className="pt-4 border-t border-slate-200">
                        <div className="flex items-center gap-2 mb-2">
                          <Key className="h-4 w-4 text-slate-500" />
                          <label htmlFor="gemini-api-key" className="text-sm font-semibold text-slate-700">
                            Gemini API Key
                          </label>
                        </div>
                        <p className="text-xs text-slate-500 mb-2">
                          Enter your own Google Gemini API key. Get one free at{" "}
                          <a
                            href="https://aistudio.google.com/apikey"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            aistudio.google.com
                          </a>
                        </p>
                        <Input
                          id="gemini-api-key"
                          type="password"
                          placeholder="AIza..."
                          aria-label="Gemini API Key"
                          value={formData.geminiApiKey}
                          onChange={(e) => updateField("geminiApiKey", e.target.value)}
                          className="font-mono text-sm"
                        />
                      </div>

                      {error && (
                        <div className="flex items-center gap-2 text-red-600 bg-red-50 p-4 rounded-lg">
                          <AlertCircle className="h-5 w-5" />
                          <span>{error}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Step 6: Generation Progress */}
                  {step === 6 && (
                    <div className="space-y-6">
                      {jobStatus?.status === "completed" ? (
                        // Completed state
                        <div className="text-center space-y-6">
                          <div className="w-20 h-20 mx-auto bg-green-100 rounded-full flex items-center justify-center">
                            <Check className="h-10 w-10 text-green-600" />
                          </div>
                          <div>
                            <h2 className="text-2xl font-bold mb-2">
                              Your Book is Ready!
                            </h2>
                            <p className="text-slate-600">
                              {jobStatus.book_name}
                            </p>
                          </div>
                          <div className="flex flex-col sm:flex-row gap-3 justify-center">
                            <Button
                              size="lg"
                              onClick={() => handleDownload("pdf")}
                              className="bg-slate-900"
                            >
                              <Download className="h-5 w-5 mr-2" />
                              Download PDF
                            </Button>
                            <Button
                              size="lg"
                              variant="outline"
                              onClick={() => handleDownload("markdown")}
                            >
                              <FileText className="h-5 w-5 mr-2" />
                              Download Markdown
                            </Button>
                          </div>
                          <Button
                            variant="ghost"
                            onClick={() => {
                              setStep(1);
                              setJobId(null);
                              setJobStatus(null);
                              setFormData({
                                topic: "",
                                domain: "",
                                goal: "",
                                background: "",
                                focus: [],
                                geminiApiKey: "",
                              });
                            }}
                          >
                            Create Another Book
                          </Button>
                        </div>
                      ) : jobStatus?.status === "failed" ? (
                        // Failed state
                        <div className="text-center space-y-6">
                          <div className="w-20 h-20 mx-auto bg-red-100 rounded-full flex items-center justify-center">
                            <AlertCircle className="h-10 w-10 text-red-600" />
                          </div>
                          <div>
                            <h2 className="text-2xl font-bold mb-2">
                              Generation Failed
                            </h2>
                            <p className="text-slate-600">
                              {jobStatus.error || "Something went wrong"}
                            </p>
                          </div>
                          <Button onClick={handleRetry}>
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Try Again
                          </Button>
                        </div>
                      ) : (
                        // In progress state
                        <div className="text-center space-y-6">
                          <div className="w-20 h-20 mx-auto bg-slate-100 rounded-full flex items-center justify-center">
                            <Loader2 className="h-10 w-10 text-slate-600 animate-spin" />
                          </div>
                          <div>
                            <h2 className="text-2xl font-bold mb-2">
                              Synthesizing Your Book
                            </h2>
                            <p className="text-slate-600">
                              {currentStatusInfo?.description ||
                                "Starting generation..."}
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
                              animate={{
                                width: `${jobStatus?.progress || 5}%`,
                              }}
                              transition={{ duration: 0.5 }}
                            />
                          </div>

                          {/* Stage indicators */}
                          <div className="grid grid-cols-9 gap-1 text-xs text-slate-400">
                            {[
                              { key: "researching", label: "Research" },
                              { key: "generating_vision", label: "Vision" },
                              { key: "generating_outline", label: "Outline" },
                              { key: "planning", label: "Planning" },
                              { key: "quality_review", label: "QA" },
                              { key: "writing_content", label: "Writing" },
                              { key: "generating_illustrations", label: "Illustrate" },
                              { key: "generating_cover", label: "Cover" },
                              { key: "assembling_pdf", label: "Assembly" },
                            ].map((stage, i) => {
                              const current = jobStatus?.status;
                              const stageOrder = [
                                "pending", "researching", "generating_vision", "generating_outline",
                                "planning", "quality_review", "writing_content",
                                "generating_illustrations", "generating_cover", "assembling_pdf",
                              ];
                              const currentIdx = stageOrder.indexOf(current || "");
                              const stageIdx = stageOrder.indexOf(stage.key);
                              const isActive = current === stage.key;
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
                            This typically takes 30-60 minutes. You can leave
                            this page and come back.
                          </p>

                          {jobId && (
                            <p className="text-xs text-slate-400">
                              Job ID: {jobId}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Navigation Buttons - hide on step 6 */}
                  {step < 6 && (
                    <div className="flex justify-between mt-8 pt-6 border-t">
                      <Button
                        variant="outline"
                        onClick={prevStep}
                        disabled={step === 1}
                      >
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Back
                      </Button>

                      {step < 5 ? (
                        <Button onClick={nextStep} disabled={!canProceed()}>
                          Continue
                          <ArrowRight className="h-4 w-4 ml-2" />
                        </Button>
                      ) : (
                        <Button onClick={handleSubmit} disabled={isSubmitting}>
                          {isSubmitting ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Starting...
                            </>
                          ) : (
                            <>
                              <Sparkles className="h-4 w-4 mr-2" />
                              Generate Book
                            </>
                          )}
                        </Button>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </AnimatePresence>

          {/* Summary Panel - hide on step 6 */}
          {step > 1 && step < 6 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-8"
            >
              <Card className="border-slate-200 bg-slate-50">
                <CardContent className="p-4">
                  <h3 className="text-sm font-semibold text-slate-500 mb-3">
                    Your Synthesis
                  </h3>
                  <div className="space-y-2 text-sm">
                    {formData.topic && (
                      <p>
                        <span className="text-slate-500">Topic:</span>{" "}
                        <span className="font-medium">{formData.topic}</span>
                      </p>
                    )}
                    {formData.domain && (
                      <p>
                        <span className="text-slate-500">Domain:</span>{" "}
                        <span className="font-medium">{formData.domain}</span>
                      </p>
                    )}
                    {formData.goal && (
                      <p>
                        <span className="text-slate-500">Goal:</span>{" "}
                        <span className="font-medium">
                          {formData.goal.slice(0, 60)}
                          {formData.goal.length > 60 ? "..." : ""}
                        </span>
                      </p>
                    )}
                    {formData.background && (
                      <p>
                        <span className="text-slate-500">Background:</span>{" "}
                        <span className="font-medium">
                          {formData.background.slice(0, 60)}
                          {formData.background.length > 60 ? "..." : ""}
                        </span>
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
