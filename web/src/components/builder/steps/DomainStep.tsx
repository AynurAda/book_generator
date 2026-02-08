import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { DOMAIN_SUGGESTIONS } from "@/constants/builder";

interface DomainStepProps {
  value: string;
  onChange: (value: string) => void;
}

export function DomainStep({ value, onChange }: DomainStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">
          What&apos;s your professional domain?
        </h2>
        <p className="text-slate-600">
          Every example and case study will be drawn from YOUR world.
        </p>
      </div>
      <Input
        placeholder="e.g., Enterprise AI agents, Healthcare diagnostics, Legal tech"
        aria-label="Your professional domain"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="text-lg py-6"
        autoFocus
      />
      <div className="flex flex-wrap gap-2">
        {DOMAIN_SUGGESTIONS.map((suggestion) => (
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
