import { Check } from "lucide-react";
import { type Step, STEP_INFO } from "@/constants/builder";

interface StepProgressProps {
  currentStep: Step;
}

export function StepProgress({ currentStep }: StepProgressProps) {
  if (currentStep >= 6) return null;

  return (
    <nav aria-label="Book builder progress" className="flex justify-between mb-12">
      {STEP_INFO.map((s, index) => {
        const StepIcon = s.icon;
        const isActive = index + 1 === currentStep;
        const isComplete = index + 1 < currentStep;
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
            <span className="text-xs font-medium hidden sm:block">{s.label}</span>
          </div>
        );
      })}
    </nav>
  );
}
