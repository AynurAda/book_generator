"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Star, Sparkles } from "lucide-react";
import { HeroSection } from "@/components/landing/HeroSection";
import { UserStoriesSection } from "@/components/landing/UserStoriesSection";
import { SynthesisSection } from "@/components/landing/SynthesisSection";
import { RoadmapSection } from "@/components/landing/RoadmapSection";
import { WaitlistSection } from "@/components/landing/WaitlistSection";
import { Footer } from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-indigo-950/80 to-slate-950 text-white overflow-x-hidden">
      {/* Animated background - celestial navy + gold */}
      <div className="fixed inset-0 bg-gradient-to-br from-slate-950 via-indigo-950/50 to-slate-950 pointer-events-none" />
      <div className="fixed inset-0 opacity-30 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/30 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-amber-500/25 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 right-1/3 w-64 h-64 bg-amber-400/20 rounded-full blur-3xl animate-pulse delay-500" />
        <div className="absolute bottom-1/3 left-1/3 w-72 h-72 bg-indigo-400/20 rounded-full blur-3xl animate-pulse delay-700" />
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-slate-950/80 backdrop-blur-xl z-50 border-b border-amber-500/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Star className="h-7 w-7 text-amber-400 fill-amber-400/30" />
              <div className="absolute -top-1 -right-1 w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
            </div>
            <span className="font-bold text-xl bg-gradient-to-r from-white to-amber-200 bg-clip-text text-transparent">
              Polaris
            </span>
          </div>

          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-full border border-amber-500/20">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span className="text-sm text-slate-300">Powered by</span>
            <span className="text-sm font-semibold bg-gradient-to-r from-amber-400 to-yellow-300 bg-clip-text text-transparent">
              Gemini
            </span>
          </div>

          <div className="flex gap-3">
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-300 hover:text-white hover:bg-white/10"
              asChild
            >
              <a href="/builder">Try Demo</a>
            </Button>
            <Button
              size="sm"
              className="bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-white shadow-lg shadow-amber-500/25"
              asChild
            >
              <a href="#waitlist">Get Early Access</a>
            </Button>
          </div>
        </div>
      </nav>

      <HeroSection />

      {/* The Solution - One Liner */}
      <section className="py-12 px-6 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-indigo-950/30 to-transparent" />
        <div className="max-w-4xl mx-auto relative text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
              <span className="text-white">We synthesize</span>{" "}
              <span className="bg-gradient-to-r from-amber-400 via-yellow-400 to-amber-300 bg-clip-text text-transparent">
                the exact book
              </span>
              <br />
              <span className="text-white">you need.</span>
            </h2>
            <p className="text-xl md:text-2xl text-slate-300 max-w-3xl mx-auto">
              Not personalized. Not adapted. <span className="text-amber-400 font-medium">Synthesized from scratch</span> —
              built molecule by molecule for exactly one person.
              <br />
              <span className="text-yellow-300">Take anyone to the cutting edge. No barriers.</span>
            </p>
          </motion.div>
        </div>
      </section>

      <UserStoriesSection />
      <SynthesisSection />
      <RoadmapSection />
      <WaitlistSection />
      <Footer />
    </div>
  );
}
