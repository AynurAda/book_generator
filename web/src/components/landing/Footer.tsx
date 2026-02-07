import { Star, Sparkles } from "lucide-react";

export function Footer() {
  return (
    <footer className="py-12 px-6 border-t border-amber-500/10">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <Star className="h-6 w-6 text-amber-400 fill-amber-400/30" />
          <span className="font-bold text-lg text-white">Polaris</span>
        </div>

        <div className="flex items-center gap-2 text-sm text-slate-400">
          <span>Built with</span>
          <Sparkles className="w-4 h-4 text-amber-400" />
          <span className="bg-gradient-to-r from-amber-400 to-yellow-300 bg-clip-text text-transparent font-medium">
            Gemini AI
          </span>
        </div>

        <p className="text-sm text-slate-400">
          &copy; {new Date().getFullYear()} Polaris. Your north star to the cutting edge.
        </p>
      </div>
    </footer>
  );
}
