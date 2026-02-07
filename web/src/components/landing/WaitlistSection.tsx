"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Check, ChevronRight, Mail, Star } from "lucide-react";

export function WaitlistSection() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (response.ok) {
        setSubmitted(true);
      }
    } catch (error) {
      console.error("Error submitting waitlist:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="waitlist" className="py-20 px-6 relative">
      <div className="absolute inset-0 bg-gradient-to-t from-indigo-950/50 via-amber-950/20 to-transparent" />
      <div className="max-w-2xl mx-auto text-center relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-amber-500 via-yellow-500 to-amber-400 flex items-center justify-center shadow-lg shadow-amber-500/30">
            <Star className="w-10 h-10 text-white fill-white/30" />
          </div>

          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Find your north star.
          </h2>
          <p className="text-xl text-slate-300 mb-8">
            Navigate to the cutting edge with knowledge synthesized for exactly one person — you.
          </p>

          {submitted ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-8"
            >
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-500/20 flex items-center justify-center">
                <Check className="h-8 w-8 text-amber-400" />
              </div>
              <p className="text-xl text-amber-300 font-medium">
                You&apos;re in! We&apos;ll email you when it&apos;s ready.
              </p>
            </motion.div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
              <div className="relative flex-1">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <Input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="pl-12 h-14 bg-white/5 border-amber-500/20 text-white placeholder:text-slate-400 rounded-xl focus:border-amber-500 focus:ring-amber-500/20"
                />
              </div>
              <Button
                type="submit"
                size="lg"
                disabled={loading}
                className="h-14 px-8 bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 rounded-xl shadow-lg shadow-amber-500/25"
              >
                {loading ? "Joining..." : <>Get Early Access <ChevronRight className="ml-1 h-5 w-5" /></>}
              </Button>
            </form>
          )}

          <p className="text-sm text-slate-400 mt-4">No spam. Just one email when we launch.</p>
        </motion.div>
      </div>
    </section>
  );
}
