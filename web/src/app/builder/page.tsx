"use client";

import { useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, ArrowLeft, Sparkles, Loader2, Star } from "lucide-react";
import Link from "next/link";

import { useBuilderForm } from "@/hooks/useBuilderForm";
import { useJobPolling } from "@/hooks/useJobPolling";

import { StepProgress } from "@/components/builder/StepProgress";
import { SummaryPanel } from "@/components/builder/SummaryPanel";
import { GenerationStatus } from "@/components/builder/GenerationStatus";
import { TopicStep } from "@/components/builder/steps/TopicStep";
import { DomainStep } from "@/components/builder/steps/DomainStep";
import { GoalStep } from "@/components/builder/steps/GoalStep";
import { BackgroundStep } from "@/components/builder/steps/BackgroundStep";
import { ConfigStep } from "@/components/builder/steps/ConfigStep";

export default function BuilderPage() {
  const {
    step,
    formData,
    jobId,
    jobStatus,
    isSubmitting,
    error,
    setJobStatus,
    setError,
    updateField,
    toggleFocus,
    canProceed,
    nextStep,
    prevStep,
    handleSubmit,
    handleDownload,
    handleRetry,
    resetForm,
  } = useBuilderForm();

  // Poll for job status when on generation step
  const onPollStatus = useCallback((s: typeof jobStatus) => { if (s) setJobStatus(s); }, [setJobStatus]);
  const onPollError = useCallback((msg: string) => setError(msg), [setError]);
  useJobPolling({ jobId, active: step === 6, onStatus: onPollStatus, onError: onPollError });

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
          <StepProgress currentStep={step} />

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
                  {/* Form steps */}
                  {step === 1 && (
                    <TopicStep
                      value={formData.topic}
                      onChange={(v) => updateField("topic", v)}
                    />
                  )}
                  {step === 2 && (
                    <DomainStep
                      value={formData.domain}
                      onChange={(v) => updateField("domain", v)}
                    />
                  )}
                  {step === 3 && (
                    <GoalStep
                      value={formData.goal}
                      onChange={(v) => updateField("goal", v)}
                    />
                  )}
                  {step === 4 && (
                    <BackgroundStep
                      value={formData.background}
                      onChange={(v) => updateField("background", v)}
                    />
                  )}
                  {step === 5 && (
                    <ConfigStep
                      formData={formData}
                      error={error}
                      onUpdateField={updateField}
                      onToggleFocus={toggleFocus}
                    />
                  )}

                  {/* Generation status */}
                  {step === 6 && (
                    <GenerationStatus
                      jobId={jobId}
                      jobStatus={jobStatus}
                      onDownload={handleDownload}
                      onRetry={handleRetry}
                      onReset={resetForm}
                    />
                  )}

                  {/* Navigation buttons */}
                  {step < 6 && (
                    <div className="flex justify-between mt-8 pt-6 border-t">
                      <Button variant="outline" onClick={prevStep} disabled={step === 1}>
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Back
                      </Button>

                      {step < 5 ? (
                        <Button onClick={nextStep} disabled={!canProceed()}>
                          Continue
                          <ArrowRight className="h-4 w-4 ml-2" />
                        </Button>
                      ) : (
                        <Button onClick={handleSubmit} disabled={isSubmitting || !canProceed()}>
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

          <SummaryPanel step={step} formData={formData} />
        </div>
      </div>
    </div>
  );
}
