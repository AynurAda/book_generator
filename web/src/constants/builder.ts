import { BookOpen, Layers, Target, User, Compass } from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────

export type Step = 1 | 2 | 3 | 4 | 5 | 6;

export interface FormData {
  topic: string;
  domain: string;
  goal: string;
  background: string;
  focus: string[];
  geminiApiKey: string;
  numChapters: number;
  writingStyle: string;
}

export interface LogEntry {
  t: string;
  msg: string;
}

export interface JobStatus {
  job_id: string;
  status: string;
  progress: number;
  current_stage: string;
  message: string;
  book_name?: string;
  error?: string;
  logs?: LogEntry[];
}

export const INITIAL_FORM_DATA: FormData = {
  topic: "",
  domain: "",
  goal: "",
  background: "",
  focus: [],
  geminiApiKey: "",
  numChapters: 4,
  writingStyle: "waitbutwhy",
};

// ── Constants ──────────────────────────────────────────────────────

export const STORAGE_KEY = "polaris-builder";
export const POLL_INITIAL_MS = 3_000;
export const POLL_MAX_MS = 30_000;
export const POLL_BACKOFF = 1.5;
export const POLL_MAX_ERRORS = 10;

export const WRITING_STYLES = [
  { key: "waitbutwhy", label: "WaitButWhy", description: "Conversational, curious, humor from the ideas" },
  { key: "for_dummies", label: "For Dummies", description: "Accessible, step-by-step, analogy-driven" },
  { key: "oreilly", label: "O'Reilly", description: "Practical, clear, for practitioners" },
  { key: "textbook", label: "Textbook", description: "Rigorous, structured, formal academic" },
  { key: "practical", label: "Practical Guide", description: "Application-focused, minimal theory" },
];

export const FOCUS_OPTIONS = [
  "Theoretical foundations",
  "Practical implementation",
  "Code examples",
  "Case studies",
  "Industry applications",
  "Research frontiers",
  "Historical context",
  "Comparative analysis",
];

export const TOPIC_SUGGESTIONS = [
  "Neuro-symbolic AI",
  "Knowledge Graphs",
  "Quantum Computing",
  "Causal Inference",
];

export const DOMAIN_SUGGESTIONS = [
  "Enterprise software",
  "Healthcare",
  "Legal tech",
  "Fintech",
  "Robotics",
  "Education",
];

export const STATUS_MESSAGES: Record<string, { stage: string; description: string }> = {
  pending: { stage: "Queued", description: "Your book is in the queue..." },
  researching: { stage: "Research", description: "Researching cutting-edge papers and breakthroughs..." },
  generating_vision: { stage: "Vision", description: "Crafting the book's core thesis and themes..." },
  generating_outline: { stage: "Outline", description: "Designing chapter structure for your domain..." },
  planning: { stage: "Planning", description: "Creating detailed plans for each chapter..." },
  quality_review: { stage: "Quality Review", description: "Reviewing plans for coherence and completeness..." },
  writing_content: { stage: "Writing", description: "Synthesizing content tailored to your background..." },
  generating_illustrations: { stage: "Illustrating", description: "Creating diagrams and visualizations..." },
  generating_cover: { stage: "Cover", description: "Designing your book cover..." },
  assembling_pdf: { stage: "Assembly", description: "Assembling the final PDF..." },
  completed: { stage: "Complete", description: "Your book is ready!" },
  failed: { stage: "Failed", description: "Something went wrong." },
};

export const PIPELINE_STAGES = [
  { key: "researching", label: "Research" },
  { key: "generating_vision", label: "Vision" },
  { key: "generating_outline", label: "Outline" },
  { key: "planning", label: "Planning" },
  { key: "quality_review", label: "QA" },
  { key: "writing_content", label: "Writing" },
  { key: "generating_illustrations", label: "Illustrate" },
  { key: "generating_cover", label: "Cover" },
  { key: "assembling_pdf", label: "Assembly" },
];

export const STAGE_ORDER = [
  "pending", "researching", "generating_vision", "generating_outline",
  "planning", "quality_review", "writing_content",
  "generating_illustrations", "generating_cover", "assembling_pdf",
];

export const STEP_INFO = [
  { icon: BookOpen, label: "Topic" },
  { icon: Layers, label: "Domain" },
  { icon: Target, label: "Goal" },
  { icon: User, label: "Background" },
  { icon: Compass, label: "Configure" },
];
