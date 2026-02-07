"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Brain, Target, Zap, ArrowRight } from "lucide-react";

export function SynthesisSection() {
  return (
    <section className="py-20 px-6">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Synthesis, not{" "}
            <span className="bg-gradient-to-r from-amber-400 via-yellow-400 to-amber-300 bg-clip-text text-transparent">
              summarization.
            </span>
          </h2>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto">
            Summarization makes things shorter. Synthesis creates something new —
            coherent knowledge built for exactly one person.
          </p>
        </motion.div>

        {/* Before/After Comparison */}
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <div className="bg-slate-800/80 rounded-2xl border border-red-500/20 p-6 h-full">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center">
                  <span className="text-red-400 text-lg">{"\u2717"}</span>
                </div>
                <h3 className="text-lg font-semibold text-red-400">Generic Book</h3>
              </div>
              <div className="space-y-3 font-mono text-sm">
                <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                  <div className="text-slate-400 text-xs mb-2">Chapter 5: Knowledge Graphs</div>
                  <ul className="space-y-2 text-slate-300">
                    <li className="flex items-start gap-2">
                      <span className="text-red-400/60">{"\u2022"}</span>
                      <span>Nodes represent entities</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-red-400/60">{"\u2022"}</span>
                      <span>Edges represent relationships</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-red-400/60">{"\u2022"}</span>
                      <span className="text-slate-500">Example: Social network with users...</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-red-400/60">{"\u2022"}</span>
                      <span className="text-slate-500">Example: Movie database...</span>
                    </li>
                  </ul>
                </div>
                <div className="text-slate-500 text-xs italic px-2">
                  Same content for everyone. Irrelevant examples. Covers everything equally.
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <div className="bg-gradient-to-br from-amber-900/20 to-indigo-900/30 rounded-2xl border border-amber-500/30 p-6 h-full">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
                  <span className="text-amber-400 text-lg">{"\u2713"}</span>
                </div>
                <h3 className="text-lg font-semibold text-amber-400">YOUR Book</h3>
                <Badge className="ml-2 bg-indigo-500/20 text-indigo-300 border-indigo-500/30 text-xs">
                  Enterprise AI Engineer
                </Badge>
              </div>
              <div className="space-y-3 font-mono text-sm">
                <div className="bg-slate-900/50 rounded-lg p-4 border border-amber-500/20">
                  <div className="text-amber-400 text-xs mb-2">Chapter 5: Knowledge Graphs for Enterprise Reasoning</div>
                  <ul className="space-y-2 text-slate-200">
                    <li className="flex items-start gap-2">
                      <span className="text-amber-400">{"\u2022"}</span>
                      <span>Modeling SAP hierarchies as queryable graphs</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-amber-400">{"\u2022"}</span>
                      <span>Compliance rules as graph constraints</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-amber-400">{"\u2022"}</span>
                      <span className="text-yellow-300">Code: LangChain + Neo4j for agent memory</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-amber-400">{"\u2022"}</span>
                      <span>Deep dive: RAG retrieval patterns</span>
                    </li>
                  </ul>
                </div>
                <div className="text-amber-300 text-xs italic px-2">
                  YOUR domain. YOUR goals. Skips what you know. Deep where you need it.
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* What Synthesis Means */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="grid md:grid-cols-3 gap-6"
        >
          {[
            {
              icon: Brain,
              title: "Integration",
              description: "Connects scattered ideas from papers, docs, and blogs into a coherent whole.",
              colorClasses: { bg: "bg-indigo-500/20", text: "text-indigo-400" },
            },
            {
              icon: Target,
              title: "Calibration",
              description: "Adjusts depth based on what you already know. No wasted pages.",
              colorClasses: { bg: "bg-amber-500/20", text: "text-amber-400" },
            },
            {
              icon: Zap,
              title: "Prioritization",
              description: "Emphasizes what matters to YOUR goal, not equal coverage of everything.",
              colorClasses: { bg: "bg-yellow-500/20", text: "text-yellow-400" },
            },
          ].map((item) => (
            <div
              key={item.title}
              className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-5 hover:border-amber-500/30 transition-all"
            >
              <div className={`w-10 h-10 rounded-lg ${item.colorClasses.bg} flex items-center justify-center mb-3`}>
                <item.icon className={`w-5 h-5 ${item.colorClasses.text}`} />
              </div>
              <h4 className="font-semibold text-white mb-2">{item.title}</h4>
              <p className="text-slate-400 text-sm">{item.description}</p>
            </div>
          ))}
        </motion.div>

        <div className="text-center mt-10">
          <Button
            size="lg"
            className="bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 shadow-lg shadow-amber-500/25"
            asChild
          >
            <a href="/builder">
              Build Your Book <ArrowRight className="ml-2 h-5 w-5" />
            </a>
          </Button>
        </div>
      </div>
    </section>
  );
}
