interface BackgroundStepProps {
  value: string;
  onChange: (value: string) => void;
}

export function BackgroundStep({ value, onChange }: BackgroundStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">
          What&apos;s your background?
        </h2>
        <p className="text-slate-600">
          We&apos;ll skip what you know and go deep where you need it.
        </p>
      </div>
      <textarea
        placeholder="e.g., ML engineer with 3 years experience, familiar with transformers and Python. New to symbolic AI and knowledge graphs."
        aria-label="Your background and experience"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full min-h-[120px] px-4 py-3 text-lg border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-slate-900"
        autoFocus
      />
    </div>
  );
}
