"use client";

import { useState, useEffect, useCallback } from "react";
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
} from "lucide-react";
import Link from "next/link";

type Step = 1 | 2 | 3 | 4 | 5 | 6;

interface FormData {
  topic: string;
  domain: string;
  goal: string;
  background: string;
  focus: string[];
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

export default function BuilderPage() {
  const [step, setStep] = useState<Step>(1);
  const [formData, setFormData] = useState<FormData>({
    topic: "",
    domain: "",
    goal: "",
    background: "",
    focus: [],
  });
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        return true; // Focus is optional
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

  // Poll for job status
  const pollJobStatus = useCallback(async () => {
    if (!jobId) return;

    try {
      const response = await fetch(`/api/generate/${jobId}`);
      if (!response.ok) {
        throw new Error("Failed to get job status");
      }
      const data: JobStatus = await response.json();
      setJobStatus(data);

      // Stop polling if completed or failed
      if (data.status === "completed" || data.status === "failed") {
        return false;
      }
      return true;
    } catch (err) {
      console.error("Error polling status:", err);
      return true; // Continue polling on error
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId || step !== 6) return;

    // Initial poll
    pollJobStatus();

    // Set up polling interval
    const interval = setInterval(async () => {
      const shouldContinue = await pollJobStatus();
      if (!shouldContinue) {
        clearInterval(interval);
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(interval);
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
          tier: "deep_dive", // Default tier for now
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
            <BookOpen className="h-6 w-6 text-slate-900" />
            <span className="font-semibold text-lg">Learner</span>
          </Link>
          <Badge variant="secondary">Book Builder</Badge>
        </div>
      </nav>

      <div className="pt-32 pb-20 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Progress Steps - hide on step 6 */}
          {step < 6 && (
            <div className="flex justify-between mb-12">
              {stepInfo.map((s, index) => {
                const StepIcon = s.icon;
                const isActive = index + 1 === step;
                const isComplete = index + 1 < step;
                return (
                  <div
                    key={index}
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
                        <Check className="h-5 w-5" />
                      ) : (
                        <StepIcon className="h-5 w-5" />
                      )}
                    </div>
                    <span className="text-xs font-medium hidden sm:block">
                      {s.label}
                    </span>
                  </div>
                );
              })}
            </div>
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
                            onClick={() => toggleFocus(option)}
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
                          <div className="w-full bg-slate-200 rounded-full h-3">
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
                          <div className="grid grid-cols-4 gap-2 text-xs text-slate-500">
                            {[
                              "Vision",
                              "Planning",
                              "Writing",
                              "Assembly",
                            ].map((stage, i) => (
                              <div
                                key={stage}
                                className={`${
                                  (jobStatus?.progress || 0) > i * 25
                                    ? "text-slate-900 font-medium"
                                    : ""
                                }`}
                              >
                                {stage}
                              </div>
                            ))}
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
