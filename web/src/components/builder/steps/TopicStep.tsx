import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { TOPIC_SUGGESTIONS } from "@/constants/builder";

interface TopicStepProps {
  value: string;
  onChange: (value: string) => void;
}

export function TopicStep({ value, onChange }: TopicStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">What do you want to learn?</h2>
        <p className="text-slate-600">
          Enter the field or topic you want to deeply understand.
        </p>
      </div>
      <Input
        placeholder="e.g., Neuro-symbolic AI, Quantum Computing, Knowledge Graphs"
        aria-label="Topic you want to learn"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="text-lg py-6"
        autoFocus
      />
      <div className="flex flex-wrap gap-2">
        {TOPIC_SUGGESTIONS.map((suggestion) => (
          <Badge
            key={suggestion}
            variant="outline"
            className="cursor-pointer hover:bg-slate-100"
            onClick={() => onChange(suggestion)}
          >
            {suggestion}
          </Badge>
        ))}
      </div>
    </div>
  );
}
