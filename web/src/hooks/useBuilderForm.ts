"use client";

import { useState, useEffect, useCallback } from "react";
import {
  type Step,
  type FormData,
  type JobStatus,
  INITIAL_FORM_DATA,
  STORAGE_KEY,
} from "@/constants/builder";

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
    // localStorage full or unavailable
  }
}

function clearPersisted() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

export function useBuilderForm() {
  const [step, setStep] = useState<Step>(1);
  const [formData, setFormData] = useState<FormData>(INITIAL_FORM_DATA);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Restore from localStorage on mount
  useEffect(() => {
    const saved = loadSaved();
    if (saved.formData) setFormData(saved.formData);
    if (saved.jobId) setJobId(saved.jobId);
    if (saved.step) setStep(saved.step);
  }, []);

  // Persist on every meaningful change
  useEffect(() => {
    persist({ formData, jobId, step });
  }, [formData, jobId, step]);

  const updateField = useCallback((field: keyof FormData, value: string | string[] | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }, []);

  const toggleFocus = useCallback((option: string) => {
    setFormData((prev) => ({
      ...prev,
      focus: prev.focus.includes(option)
        ? prev.focus.filter((f) => f !== option)
        : [...prev.focus, option],
    }));
  }, []);

  const canProceed = useCallback((): boolean => {
    switch (step) {
      case 1: return formData.topic.trim().length > 0;
      case 2: return formData.domain.trim().length > 0;
      case 3: return formData.goal.trim().length > 0;
      case 4: return formData.background.trim().length > 0;
      case 5: return formData.geminiApiKey.trim().length > 0;
      default: return false;
    }
  }, [step, formData]);

  const nextStep = useCallback(() => {
    if (step < 5 && canProceed()) {
      setStep((prev) => (prev + 1) as Step);
    }
  }, [step, canProceed]);

  const prevStep = useCallback(() => {
    if (step > 1 && step < 6) {
      setStep((prev) => (prev - 1) as Step);
    }
  }, [step]);

  const handleSubmit = useCallback(async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: formData.topic,
          domain: formData.domain,
          goal: formData.goal,
          background: formData.background,
          focus: formData.focus.length > 0 ? formData.focus.join(", ") : undefined,
          num_chapters: formData.numChapters,
          writing_style: formData.writingStyle,
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
  }, [formData]);

  const handleDownload = useCallback(async (format: "pdf" | "markdown") => {
    if (!jobId) return;

    try {
      const response = await fetch(`/api/generate/${jobId}/download?format=${format}`);
      if (!response.ok) throw new Error("Download failed");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${jobStatus?.book_name || "book"}.${format === "pdf" ? "pdf" : "md"}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch {
      setError("Failed to download file");
    }
  }, [jobId, jobStatus]);

  const handleRetry = useCallback(() => {
    setJobId(null);
    setJobStatus(null);
    setError(null);
    setStep(5);
  }, []);

  const resetForm = useCallback(() => {
    setStep(1);
    setJobId(null);
    setJobStatus(null);
    setFormData(INITIAL_FORM_DATA);
    clearPersisted();
  }, []);

  return {
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
  };
}
