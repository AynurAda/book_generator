interface GoalStepProps {
  value: string;
  onChange: (value: string) => void;
}

export function GoalStep({ value, onChange }: GoalStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">
          What do you want to be able to DO?
        </h2>
        <p className="text-slate-600">
          Describe your goal. The book will be structured around this outcome.
        </p>
      </div>
      <textarea
        placeholder="e.g., Design and build hybrid LLM + knowledge graph systems for enterprise reasoning..."
        aria-label="What you want to be able to do"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full min-h-[120px] px-4 py-3 text-lg border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-slate-900"
        autoFocus
      />
    </div>
  );
}
