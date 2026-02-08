import { Check, Key, AlertCircle } from "lucide-react";
import { Input } from "@/components/ui/input";
import { type FormData, FOCUS_OPTIONS, WRITING_STYLES } from "@/constants/builder";

interface ConfigStepProps {
  formData: FormData;
  error: string | null;
  onUpdateField: (field: keyof FormData, value: string | string[] | number) => void;
  onToggleFocus: (option: string) => void;
}

export function ConfigStep({ formData, error, onUpdateField, onToggleFocus }: ConfigStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Configure your book</h2>
        <p className="text-slate-600">
          Choose focus areas, style, and provide your API key.
        </p>
      </div>

      {/* Focus Areas */}
      <div>
        <label className="text-sm font-semibold text-slate-700 block mb-2">
          Focus Areas <span className="font-normal text-slate-400">(optional)</span>
        </label>
        <div className="grid grid-cols-2 gap-2">
          {FOCUS_OPTIONS.map((option) => (
            <div
              key={option}
              role="checkbox"
              aria-checked={formData.focus.includes(option)}
              aria-label={option}
              tabIndex={0}
              onClick={() => onToggleFocus(option)}
              onKeyDown={(e) => {
                if (e.key === " " || e.key === "Enter") {
                  e.preventDefault();
                  onToggleFocus(option);
                }
              }}
              className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
                formData.focus.includes(option)
                  ? "border-slate-900 bg-slate-50"
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center gap-2">
                <div
                  className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
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
                <span className="text-sm">{option}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Number of Chapters */}
      <div className="pt-4 border-t border-slate-200">
        <label htmlFor="num-chapters" className="text-sm font-semibold text-slate-700 block mb-2">
          Chapters
        </label>
        <div className="flex items-center gap-4">
          <input
            id="num-chapters"
            type="range"
            min={2}
            max={15}
            value={formData.numChapters}
            onChange={(e) => onUpdateField("numChapters", Number(e.target.value))}
            className="flex-1 accent-slate-900"
          />
          <span className="text-lg font-bold text-slate-900 w-8 text-center">
            {formData.numChapters}
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Fewer chapters = faster generation. 4 chapters takes ~30 min.
        </p>
      </div>

      {/* Writing Style */}
      <div className="pt-4 border-t border-slate-200">
        <label className="text-sm font-semibold text-slate-700 block mb-2">
          Writing Style
        </label>
        <div className="grid grid-cols-1 gap-2">
          {WRITING_STYLES.map((style) => (
            <div
              key={style.key}
              role="radio"
              aria-checked={formData.writingStyle === style.key}
              tabIndex={0}
              onClick={() => onUpdateField("writingStyle", style.key)}
              onKeyDown={(e) => {
                if (e.key === " " || e.key === "Enter") {
                  e.preventDefault();
                  onUpdateField("writingStyle", style.key);
                }
              }}
              className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
                formData.writingStyle === style.key
                  ? "border-slate-900 bg-slate-50"
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center gap-2">
                <div
                  className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                    formData.writingStyle === style.key
                      ? "border-slate-900"
                      : "border-slate-300"
                  }`}
                >
                  {formData.writingStyle === style.key && (
                    <div className="w-2 h-2 rounded-full bg-slate-900" />
                  )}
                </div>
                <span className="text-sm font-medium">{style.label}</span>
                <span className="text-xs text-slate-500">— {style.description}</span>
              </div>
            </div>
          ))}
        </div>
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
          Enter your Google Gemini API key. Get one free at{" "}
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
          onChange={(e) => onUpdateField("geminiApiKey", e.target.value)}
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
  );
}
