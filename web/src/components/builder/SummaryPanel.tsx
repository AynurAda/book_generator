import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { type Step, type FormData } from "@/constants/builder";

interface SummaryPanelProps {
  step: Step;
  formData: FormData;
}

export function SummaryPanel({ step, formData }: SummaryPanelProps) {
  if (step <= 1 || step >= 6) return null;

  const fields = [
    { label: "Topic", value: formData.topic },
    { label: "Domain", value: formData.domain },
    { label: "Goal", value: formData.goal },
    { label: "Background", value: formData.background },
  ].filter((f) => f.value);

  if (fields.length === 0) return null;

  return (
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
            {fields.map((f) => (
              <p key={f.label}>
                <span className="text-slate-500">{f.label}:</span>{" "}
                <span className="font-medium">
                  {f.value.length > 60 ? `${f.value.slice(0, 60)}...` : f.value}
                </span>
              </p>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
