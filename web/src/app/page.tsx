"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  BookOpen,
  Check,
  ArrowRight,
  ChevronRight,
  Mail,
  Sparkles,
  Brain,
  Code,
  FileText,
  Video,
  Newspaper,
  Search,
  Target,
  Quote,
  Zap,
  Users,
  ChevronDown,
  Star,
  GraduationCap,
  Layers,
  Play,
  Route,
} from "lucide-react";


const userStories = [
  {
    name: "Aynur",
    role: "Quantitative Researcher",
    location: "London",
    avatar: "/avatars/aynur.png",
    color: "from-sky-500 to-blue-500",
    borderColor: "border-sky-500/30",
    bgColor: "bg-sky-500/10",
    problem: "Wants to build an intelligent trading bot using neuro-symbolic AI. But all the literature is scattered across papers about visual reasoning and medical diagnosis — nothing about finance and LLMs.",
    solution: "A book that covers neuro-symbolic AI specifically through the lens of quantitative finance, with examples using market data, and deep dives into LLM integration for trading strategies.",
    quote: "Finally, a resource that speaks my language — literally about MY use case.",
    tags: ["Neuro-symbolic AI", "Finance", "LLM Integration"],
  },
  {
    name: "Marina",
    role: "Fighting for her life",
    location: "São Paulo",
    avatar: "/avatars/marina.png",
    color: "from-amber-500 to-orange-500",
    borderColor: "border-amber-500/30",
    bgColor: "bg-amber-500/10",
    problem: "Diagnosed with stage 4 pancreatic cancer. 3% survival rate with standard treatment. She wants to understand cutting-edge research on innovative treatments and supplements — but papers are impenetrable and she has no time.",
    solution: "A comprehensive, accessible guide synthesizing the latest research on emerging treatments, clinical trials, and evidence-based supplements — written in plain language she can actually understand.",
    quote: "Knowledge is power. This gave me hope and a plan to discuss with my doctors.",
    tags: ["Oncology Research", "Accessible Language", "Life-saving"],
  },
  {
    name: "James",
    role: "Career Changer",
    location: "Detroit",
    avatar: "/avatars/james.png",
    color: "from-slate-500 to-zinc-600",
    borderColor: "border-slate-500/30",
    bgColor: "bg-slate-500/10",
    problem: "Lost his manufacturing job after 28 years. Trying to transition to tech but every bootcamp assumes you're young, have endless time, and already speak tech. He has mechanical intuition, not coding intuition.",
    solution: "Programming fundamentals explained for someone who thinks in physical systems — variables as containers, functions as assembly lines, debugging as troubleshooting. His experience is an asset, not a liability.",
    quote: "I built cars for 28 years. They said I couldn't learn to build software. Watch me.",
    tags: ["Career Change", "Practical Approach", "No Assumptions"],
  },
  {
    name: "Amir",
    role: "Gifted Student",
    location: "Dhaka, Bangladesh",
    avatar: "/avatars/amir.png",
    color: "from-amber-500 to-orange-500",
    borderColor: "border-amber-500/30",
    bgColor: "bg-amber-500/10",
    problem: "Mathematically gifted and dreams of cutting-edge research. But no access to elite institutions, world-class labs, or expensive resources. Also struggles with English-language materials.",
    solution: "Advanced mathematics and ML textbooks in Bangla, starting exactly where he is, building toward research-level understanding — unlocking his potential without geographic or financial barriers.",
    quote: "The best education in my language. I can finally reach my potential.",
    tags: ["Native Language", "Advanced Math", "Democratized Access"],
  },
  {
    name: "Marcus",
    role: "Dyslexic Entrepreneur",
    location: "Austin",
    avatar: "/avatars/marcus.png",
    color: "from-cyan-500 to-sky-600",
    borderColor: "border-cyan-500/30",
    bgColor: "bg-cyan-500/10",
    problem: "Brilliant business mind but traditional textbooks are torture. Dense walls of text make learning new skills — marketing analytics, finance — nearly impossible. He's built companies but can't read a textbook.",
    solution: "Concepts broken into digestible chunks, heavy use of diagrams and analogies, structured for how his brain actually works. Business knowledge without the wall-of-text barrier.",
    quote: "I've built a company. But I still can't read a textbook without wanting to throw it across the room.",
    tags: ["Dyslexia-Friendly", "Visual Learning", "Business"],
  },
  {
    name: "Priya",
    role: "Climate Journalist",
    location: "Mumbai",
    avatar: "/avatars/priya.png",
    color: "from-green-500 to-emerald-600",
    borderColor: "border-green-500/30",
    bgColor: "bg-green-500/10",
    problem: "Needs to understand complex climate science, economics, and policy to write accurate stories. She's not a scientist — she's a storyteller who needs to get it right. Millions read what she writes.",
    solution: "Climate science distilled for a smart non-scientist — the physics, the economics, the politics, with India-specific context and guidance on communicating findings accurately.",
    quote: "Millions read what I write. I can't afford to get the science wrong.",
    tags: ["Climate Science", "Journalism", "India Context"],
  },
  {
    name: "Anna",
    role: "Computational Biologist",
    location: "Boston",
    avatar: "/avatars/anna.png",
    color: "from-emerald-500 to-teal-500",
    borderColor: "border-emerald-500/30",
    bgColor: "bg-emerald-500/10",
    problem: "Needs to learn Python for work, but generic tutorials use boring examples about calculators and todo apps. She falls asleep. Nothing connects to what she actually does.",
    solution: "A hands-on Python book where every example analyzes genomic data, processes protein sequences, and visualizes biological pathways — her actual work.",
    quote: "I learned more in one week than three months of generic courses.",
    tags: ["Python", "Bioinformatics", "Hands-on"],
  },
  {
    name: "Sofia",
    role: "First-Gen College Student",
    location: "Phoenix",
    avatar: "/avatars/sofia.png",
    color: "from-orange-500 to-amber-600",
    borderColor: "border-orange-500/30",
    bgColor: "bg-orange-500/10",
    problem: "First in her family to attend university. No one at home can explain organic chemistry or academic writing. Tutoring is expensive. She feels like everyone else got a secret manual she never received.",
    solution: "Organic chemistry with extra scaffolding — explains the 'obvious' things professors assume you know, with study strategies built in, written like a patient mentor who remembers what it's like to struggle.",
    quote: "Everyone else seems to just... know things. I'm always three steps behind.",
    tags: ["First-Generation", "Extra Support", "Mentorship"],
  },
  {
    name: "Kofi",
    role: "Small Business Owner",
    location: "Accra, Ghana",
    avatar: "/avatars/kofi.png",
    color: "from-yellow-500 to-amber-600",
    borderColor: "border-yellow-500/30",
    bgColor: "bg-yellow-500/10",
    problem: "Runs a successful tailoring business, wants to expand online. But every e-commerce guide assumes US/EU payment systems, logistics, and infrastructure. None of it applies to his reality.",
    solution: "E-commerce and digital marketing for West African markets — mobile money integration, local logistics solutions, WhatsApp and Facebook selling strategies that actually work in Ghana.",
    quote: "The internet was supposed to level the playing field. But all the playbooks are written for Silicon Valley.",
    tags: ["African Markets", "E-commerce", "Local Context"],
  },
  {
    name: "Rachel",
    role: "Living with Chronic Fatigue",
    location: "Melbourne",
    avatar: "/avatars/rachel.png",
    color: "from-teal-500 to-cyan-600",
    borderColor: "border-teal-500/30",
    bgColor: "bg-teal-500/10",
    problem: "Brilliant mind but can only focus for 20-30 minutes before crashing. Traditional courses assume 3-hour study sessions. She wants to learn UX design but every resource is built for people with unlimited energy.",
    solution: "UX design in micro-chapters — each self-contained, with clear stopping points and recaps. Designed for interrupted learning. Progress even on bad days.",
    quote: "My brain works fine. It's my body that won't cooperate. Why does every course assume unlimited energy?",
    tags: ["Chronic Illness", "Micro-Learning", "Accessible Pace"],
  },
  {
    name: "David",
    role: "Deaf Entrepreneur",
    location: "London",
    avatar: "/avatars/david.png",
    color: "from-sky-500 to-blue-600",
    borderColor: "border-sky-500/30",
    bgColor: "bg-sky-500/10",
    problem: "Most learning content is video-based now. YouTube tutorials, online courses — all assume you can hear. Auto-generated captions are garbage. He's been excluded from the learning economy.",
    solution: "Comprehensive written content with detailed visual diagrams. Everything a video would teach, in a format he can actually use. No dependence on audio explanations.",
    quote: "The shift to video killed my ability to self-educate. Everyone forgot people like me exist.",
    tags: ["Deaf Accessible", "Visual-First", "Written Content"],
  },
  {
    name: "Mira",
    role: "Accounting Student",
    location: "Toronto",
    avatar: "/avatars/mira.png",
    color: "from-cyan-500 to-blue-500",
    borderColor: "border-cyan-500/30",
    bgColor: "bg-cyan-500/10",
    problem: "Has to pass her CPA exam but the material is soul-crushingly dry. She's falling behind because she can't stay engaged with traditional textbooks.",
    solution: "An accounting prep book with Rick and Morty-style humor woven throughout. Debits and credits explained through interdimensional adventures. Actually fun to read.",
    quote: "I never thought I'd laugh while studying depreciation methods. Wubba lubba dub dub!",
    tags: ["Accounting", "Rick & Morty Style", "Actually Fun"],
  },
];

export default function LandingPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeStory, setActiveStory] = useState(0);

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

      {/* Hero Section - The Problem */}
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

            {/* Right: The Chaos → Order visualization */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative"
            >
              <div className="relative h-[450px] flex items-center justify-center">
                {/* Scattered sources - floating around */}
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

                {/* Center - convergence point with book icon */}
                <motion.div
                  animate={{ scale: [1, 1.05, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="relative z-10"
                >
                  {/* Glowing rings */}
                  <div className="absolute inset-0 w-32 h-32 rounded-full bg-gradient-to-br from-amber-500/20 to-yellow-500/20 blur-xl" />
                  <div className="relative w-32 h-32 rounded-2xl bg-gradient-to-br from-slate-800 to-indigo-950 border border-amber-500/30 flex items-center justify-center shadow-2xl shadow-amber-500/20">
                    <div className="text-center">
                      <BookOpen className="w-10 h-10 text-amber-400 mx-auto mb-2" />
                      <span className="text-xs font-medium text-slate-300">Your Book</span>
                    </div>
                  </div>
                </motion.div>

                {/* Connection lines (decorative) */}
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

      {/* User Stories Section */}
      <section id="stories" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <Badge className="mb-4 bg-amber-500/20 text-amber-300 border-amber-500/30">
              <Users className="w-3 h-3 mr-1" />
              Breaking All Barriers
            </Badge>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Knowledge for{" "}
              <span className="bg-gradient-to-r from-amber-400 via-yellow-400 to-amber-300 bg-clip-text text-transparent">
                everyone
              </span>
            </h2>
            <p className="text-xl text-slate-300 max-w-2xl mx-auto">
              Geographic, economic, linguistic, cognitive — we break all barriers to learning.
            </p>
          </motion.div>

          {/* Story Selector */}
          <div className="flex flex-wrap justify-center gap-3 mb-12">
            {userStories.map((story, index) => (
              <motion.button
                key={story.name}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setActiveStory(index)}
                className={`flex items-center gap-2 px-4 py-2 rounded-full font-medium transition-all ${
                  activeStory === index
                    ? `bg-gradient-to-r ${story.color} text-white shadow-lg`
                    : "bg-white/5 text-slate-300 hover:bg-white/10 border border-white/10"
                }`}
              >
                <img
                  src={story.avatar}
                  alt={story.name}
                  className="w-7 h-7 rounded-full object-cover"
                />
                <span>{story.name}</span>
              </motion.button>
            ))}
          </div>

          {/* Active Story Card */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeStory}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="max-w-4xl mx-auto"
            >
              <Card className={`${userStories[activeStory].bgColor} ${userStories[activeStory].borderColor} border-2`}>
                <CardContent className="p-8 md:p-10">
                  {/* Header */}
                  <div className="flex items-start gap-4 mb-6">
                    <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${userStories[activeStory].color} p-0.5 shadow-lg overflow-hidden`}>
                      <img
                        src={userStories[activeStory].avatar}
                        alt={userStories[activeStory].name}
                        className="w-full h-full rounded-xl object-cover"
                      />
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold text-white">{userStories[activeStory].name}</h3>
                      <p className="text-slate-400">{userStories[activeStory].role} • {userStories[activeStory].location}</p>
                    </div>
                  </div>

                  {/* Problem */}
                  <div className="mb-6">
                    <h4 className="text-sm font-semibold text-red-400 uppercase tracking-wide mb-2">The Challenge</h4>
                    <p className="text-lg text-slate-300 leading-relaxed">
                      {userStories[activeStory].problem}
                    </p>
                  </div>

                  {/* Solution */}
                  <div className="mb-6">
                    <h4 className="text-sm font-semibold text-green-400 uppercase tracking-wide mb-2">Their Book</h4>
                    <p className="text-lg text-white leading-relaxed">
                      {userStories[activeStory].solution}
                    </p>
                  </div>

                  {/* Quote */}
                  <div className={`${userStories[activeStory].bgColor} rounded-xl p-4 mb-6 border ${userStories[activeStory].borderColor}`}>
                    <div className="flex items-start gap-3">
                      <Quote className="w-6 h-6 text-amber-400 flex-shrink-0 mt-1" />
                      <p className="text-lg italic text-white">
                        &ldquo;{userStories[activeStory].quote}&rdquo;
                      </p>
                    </div>
                  </div>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-2">
                    {userStories[activeStory].tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1 bg-white/10 rounded-full text-sm text-slate-300 border border-white/10"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </AnimatePresence>

          {/* Story Navigation Dots */}
          <div className="flex justify-center gap-2 mt-8">
            {userStories.map((_, index) => (
              <button
                key={index}
                onClick={() => setActiveStory(index)}
                className={`w-2 h-2 rounded-full transition-all ${
                  activeStory === index
                    ? "w-8 bg-amber-500"
                    : "bg-white/20 hover:bg-white/40"
                }`}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Synthesis vs Summarization - Before/After */}
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
            {/* Before - Generic Book */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className="bg-slate-800/80 rounded-2xl border border-red-500/20 p-6 h-full">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center">
                    <span className="text-red-400 text-lg">✗</span>
                  </div>
                  <h3 className="text-lg font-semibold text-red-400">Generic Book</h3>
                </div>
                <div className="space-y-3 font-mono text-sm">
                  <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                    <div className="text-slate-400 text-xs mb-2">Chapter 5: Knowledge Graphs</div>
                    <ul className="space-y-2 text-slate-300">
                      <li className="flex items-start gap-2">
                        <span className="text-red-400/60">•</span>
                        <span>Nodes represent entities</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-red-400/60">•</span>
                        <span>Edges represent relationships</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-red-400/60">•</span>
                        <span className="text-slate-500">Example: Social network with users...</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-red-400/60">•</span>
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

            {/* After - Your Book */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className="bg-gradient-to-br from-amber-900/20 to-indigo-900/30 rounded-2xl border border-amber-500/30 p-6 h-full">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
                    <span className="text-amber-400 text-lg">✓</span>
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
                        <span className="text-amber-400">•</span>
                        <span>Modeling SAP hierarchies as queryable graphs</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-amber-400">•</span>
                        <span>Compliance rules as graph constraints</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-amber-400">•</span>
                        <span className="text-yellow-300">Code: LangChain + Neo4j for agent memory</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-amber-400">•</span>
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
                color: "indigo",
              },
              {
                icon: Target,
                title: "Calibration",
                description: "Adjusts depth based on what you already know. No wasted pages.",
                color: "amber",
              },
              {
                icon: Zap,
                title: "Prioritization",
                description: "Emphasizes what matters to YOUR goal, not equal coverage of everything.",
                color: "yellow",
              },
            ].map((item) => (
              <div
                key={item.title}
                className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-5 hover:border-amber-500/30 transition-all"
              >
                <div className={`w-10 h-10 rounded-lg bg-${item.color}-500/20 flex items-center justify-center mb-3`}>
                  <item.icon className={`w-5 h-5 text-${item.color}-400`} />
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

      {/* Vision — Platform Roadmap */}
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
            {[
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
            ].map((item, index) => (
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

      {/* CTA / Waitlist */}
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

      {/* Footer */}
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
    </div>
  );
}
