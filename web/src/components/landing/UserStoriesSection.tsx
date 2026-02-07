"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, Quote } from "lucide-react";
import { userStories } from "@/constants/userStories";

export function UserStoriesSection() {
  const [activeStory, setActiveStory] = useState(0);

  return (
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
              <Image
                src={story.avatar}
                alt={story.name}
                width={28}
                height={28}
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
                <div className="flex items-start gap-4 mb-6">
                  <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${userStories[activeStory].color} p-0.5 shadow-lg overflow-hidden`}>
                    <Image
                      src={userStories[activeStory].avatar}
                      alt={userStories[activeStory].name}
                      width={80}
                      height={80}
                      className="w-full h-full rounded-xl object-cover"
                    />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white">{userStories[activeStory].name}</h3>
                    <p className="text-slate-400">{userStories[activeStory].role} • {userStories[activeStory].location}</p>
                  </div>
                </div>

                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-red-400 uppercase tracking-wide mb-2">The Challenge</h4>
                  <p className="text-lg text-slate-300 leading-relaxed">
                    {userStories[activeStory].problem}
                  </p>
                </div>

                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-green-400 uppercase tracking-wide mb-2">Their Book</h4>
                  <p className="text-lg text-white leading-relaxed">
                    {userStories[activeStory].solution}
                  </p>
                </div>

                <div className={`${userStories[activeStory].bgColor} rounded-xl p-4 mb-6 border ${userStories[activeStory].borderColor}`}>
                  <div className="flex items-start gap-3">
                    <Quote className="w-6 h-6 text-amber-400 flex-shrink-0 mt-1" />
                    <p className="text-lg italic text-white">
                      &ldquo;{userStories[activeStory].quote}&rdquo;
                    </p>
                  </div>
                </div>

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
        <div className="flex justify-center gap-2 mt-8" role="tablist" aria-label="User stories">
          {userStories.map((story, index) => (
            <button
              key={index}
              role="tab"
              aria-selected={activeStory === index}
              aria-label={`Story ${index + 1}: ${story.name}`}
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
  );
}
