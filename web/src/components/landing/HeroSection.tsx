"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  BookOpen,
  ArrowRight,
  ChevronDown,
  FileText,
  Video,
  Newspaper,
  Code,
  Search,
  Users,
  Star,
  Sparkles,
} from "lucide-react";

export function HeroSection() {
  return (
    <section className="relative pt-32 pb-16 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left: The Pain */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <Badge className="mb-6 bg-amber-500/20 text-amber-300 border-amber-500/30">
              <Star className="w-3 h-3 mr-1" />
              Your north star to the cutting edge
            </Badge>

            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-[1.1]">
              <span className="text-white">The book you need</span>
              <br />
              <span className="bg-gradient-to-r from-amber-400 via-yellow-400 to-amber-300 bg-clip-text text-transparent">
                doesn&apos;t exist.
              </span>
            </h1>

            <p className="text-xl text-slate-300 mb-8 leading-relaxed">
              The cutting edge is locked in research silos.
              <span className="text-amber-400 font-medium"> We collapse the pipeline</span> so you can
              learn breakthroughs <span className="text-yellow-300 font-medium">in time to build something that matters</span>.
            </p>

            <div className="flex flex-wrap gap-4">
              <Button
                size="lg"
                className="bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-white shadow-lg shadow-amber-500/30"
                asChild
              >
                <a href="/builder">
                  Try the Builder <ArrowRight className="ml-2 h-5 w-5" />
                </a>
              </Button>
              <Button
                size="lg"
                className="bg-white/10 border border-amber-500/20 text-white hover:bg-white/20"
                asChild
              >
                <a href="#stories">
                  See Who It&apos;s For <ChevronDown className="ml-2 h-5 w-5" />
                </a>
              </Button>
            </div>
          </motion.div>

          {/* Right: The Chaos -> Order visualization */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative"
          >
            <div className="relative h-[450px] flex items-center justify-center">
              {[
                { text: "arxiv:2401.xxxxx", rotate: -15, x: -120, y: -100, icon: FileText },
                { text: "3hr lecture series", rotate: 10, x: 100, y: -110, icon: Video },
                { text: "Blog post (2019)", rotate: -8, x: -140, y: 30, icon: Newspaper },
                { text: "Docs v2.3", rotate: 12, x: 130, y: 50, icon: Code },
                { text: "Research paper", rotate: -5, x: -90, y: 130, icon: Search },
                { text: "Forum discussion", rotate: 8, x: 90, y: -20, icon: Users },
                { text: "Textbook Ch. 14", rotate: -12, x: 50, y: 110, icon: BookOpen },
              ].map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{
                    opacity: [0, 0.7, 0.7, 0.3],
                    scale: 1,
                    x: [0, item.x],
                    y: [0, item.y],
                    rotate: item.rotate,
                  }}
                  transition={{
                    delay: 0.5 + i * 0.12,
                    duration: 1.5,
                    repeat: Infinity,
                    repeatType: "reverse",
                    repeatDelay: 3,
                  }}
                  className="absolute px-3 py-2 bg-slate-800/90 border border-slate-600/30 rounded-lg text-xs text-slate-400 font-mono flex items-center gap-2"
                >
                  <item.icon className="w-3 h-3 text-slate-500" />
                  {item.text}
                </motion.div>
              ))}

              <motion.div
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="relative z-10"
              >
                <div className="absolute inset-0 w-32 h-32 rounded-full bg-gradient-to-br from-amber-500/20 to-yellow-500/20 blur-xl" />
                <div className="relative w-32 h-32 rounded-2xl bg-gradient-to-br from-slate-800 to-indigo-950 border border-amber-500/30 flex items-center justify-center shadow-2xl shadow-amber-500/20">
                  <div className="text-center">
                    <BookOpen className="w-10 h-10 text-amber-400 mx-auto mb-2" />
                    <span className="text-xs font-medium text-slate-300">Your Book</span>
                  </div>
                </div>
              </motion.div>

              <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
                <defs>
                  <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#06b6d4" stopOpacity="0" />
                    <stop offset="50%" stopColor="#14b8a6" stopOpacity="0.5" />
                    <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
