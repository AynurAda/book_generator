"use client";

import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Play, Route, GraduationCap } from "lucide-react";

export function RoadmapSection() {
  const items = [
    {
      icon: BookOpen,
      label: "Personalized Books",
      status: "Live now",
      statusColor: "text-emerald-400",
      dotColor: "bg-emerald-400",
      description: "Deep-dive books synthesized for your exact background",
    },
    {
      icon: Play,
      label: "Interactive Courses",
      status: "Coming soon",
      statusColor: "text-amber-400",
      dotColor: "bg-amber-400",
      description: "Learn-by-doing modules with exercises tailored to your level",
    },
    {
      icon: Route,
      label: "Learning Paths",
      status: "Coming soon",
      statusColor: "text-amber-400",
      dotColor: "bg-amber-400",
      description: "Multi-step curricula that adapt as you grow",
    },
    {
      icon: GraduationCap,
      label: "Assessments",
      status: "On the horizon",
      statusColor: "text-slate-400",
      dotColor: "bg-slate-400",
      description: "Prove mastery with personalized evaluations",
    },
  ];

  return (
    <section className="py-20 px-6 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-indigo-950/30 to-transparent" />
      <div className="max-w-4xl mx-auto relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <Badge className="bg-indigo-500/20 text-indigo-300 border-indigo-500/30 mb-4">
            The bigger picture
          </Badge>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Beyond books. A learning platform built for{" "}
            <span className="bg-gradient-to-r from-amber-400 to-yellow-300 bg-clip-text text-transparent">you</span>.
          </h2>
          <p className="text-lg text-slate-300 max-w-2xl mx-auto">
            Polaris is growing into a fully personalized learning experience — where every course,
            every path, and every exercise adapts to who you are and what you need.
          </p>
        </motion.div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {items.map((item, index) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              viewport={{ once: true }}
              className="bg-white/5 border border-white/10 rounded-xl p-5 hover:bg-white/[0.07] transition-colors"
            >
              <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center mb-3">
                <item.icon className="w-5 h-5 text-amber-400" />
              </div>
              <h3 className="font-semibold text-white text-sm mb-1">{item.label}</h3>
              <p className="text-xs text-slate-400 mb-3">{item.description}</p>
              <div className="flex items-center gap-1.5">
                <div className={`w-1.5 h-1.5 rounded-full ${item.dotColor}`} />
                <span className={`text-xs font-medium ${item.statusColor}`}>{item.status}</span>
              </div>
            </motion.div>
          ))}
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center text-sm text-slate-400 mt-8"
        >
          Not one-size-fits-all. Not pre-recorded lectures.{" "}
          <span className="text-slate-300">Every piece of content generated for exactly one learner — you.</span>
        </motion.p>
      </div>
    </section>
  );
}
