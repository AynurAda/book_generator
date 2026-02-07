"use client";

import { useRef, useCallback, useEffect, useState } from "react";
import dynamic from "next/dynamic";

const ForceGraph3D = dynamic(() => import("react-force-graph-3d"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center">
      <div className="animate-pulse text-purple-400">Loading visualization...</div>
    </div>
  ),
});

interface GraphNode {
  id: string;
  name: string;
  type: "topic" | "concept" | "chapter" | "project" | "skill";
  val?: number;
  color?: string;
  description?: string;
}

interface GraphLink {
  source: string;
  target: string;
  type?: "requires" | "enables" | "includes" | "applies_to";
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// Pre-built graph data for different topics
const graphDatasets: Record<string, GraphData> = {
  webdev: {
    nodes: [
      { id: "topic", name: "Web Development", type: "topic", val: 30 },
      { id: "html", name: "HTML & Structure", type: "concept", val: 15 },
      { id: "css", name: "CSS & Styling", type: "concept", val: 15 },
      { id: "js", name: "JavaScript", type: "concept", val: 20 },
      { id: "react", name: "React", type: "chapter", val: 18 },
      { id: "state", name: "State Management", type: "chapter", val: 12 },
      { id: "api", name: "API Integration", type: "chapter", val: 14 },
      { id: "deploy", name: "Deployment", type: "skill", val: 10 },
      { id: "project", name: "Your Startup MVP", type: "project", val: 25 },
    ],
    links: [
      { source: "topic", target: "html", type: "includes" },
      { source: "topic", target: "css", type: "includes" },
      { source: "topic", target: "js", type: "includes" },
      { source: "html", target: "react", type: "enables" },
      { source: "css", target: "react", type: "enables" },
      { source: "js", target: "react", type: "requires" },
      { source: "react", target: "state", type: "enables" },
      { source: "js", target: "api", type: "requires" },
      { source: "react", target: "api", type: "enables" },
      { source: "state", target: "project", type: "applies_to" },
      { source: "api", target: "project", type: "applies_to" },
      { source: "deploy", target: "project", type: "applies_to" },
      { source: "react", target: "deploy", type: "enables" },
    ],
  },
  ml: {
    nodes: [
      { id: "topic", name: "Machine Learning", type: "topic", val: 30 },
      { id: "math", name: "Math Foundations", type: "concept", val: 12 },
      { id: "python", name: "Python & NumPy", type: "concept", val: 15 },
      { id: "data", name: "Data Processing", type: "concept", val: 14 },
      { id: "models", name: "ML Models", type: "chapter", val: 18 },
      { id: "training", name: "Training & Tuning", type: "chapter", val: 15 },
      { id: "eval", name: "Evaluation", type: "chapter", val: 12 },
      { id: "deploy", name: "Model Deployment", type: "skill", val: 10 },
      { id: "project", name: "Movie Recommender", type: "project", val: 25 },
    ],
    links: [
      { source: "topic", target: "math", type: "includes" },
      { source: "topic", target: "python", type: "includes" },
      { source: "topic", target: "data", type: "includes" },
      { source: "math", target: "models", type: "enables" },
      { source: "python", target: "models", type: "requires" },
      { source: "data", target: "models", type: "requires" },
      { source: "models", target: "training", type: "enables" },
      { source: "training", target: "eval", type: "enables" },
      { source: "eval", target: "deploy", type: "enables" },
      { source: "models", target: "project", type: "applies_to" },
      { source: "training", target: "project", type: "applies_to" },
      { source: "deploy", target: "project", type: "applies_to" },
    ],
  },
  gamedev: {
    nodes: [
      { id: "topic", name: "Game Development", type: "topic", val: 30 },
      { id: "physics", name: "Game Physics", type: "concept", val: 14 },
      { id: "graphics", name: "2D Graphics", type: "concept", val: 15 },
      { id: "input", name: "Input Handling", type: "concept", val: 12 },
      { id: "loop", name: "Game Loop", type: "chapter", val: 16 },
      { id: "collision", name: "Collision Detection", type: "chapter", val: 14 },
      { id: "animation", name: "Sprite Animation", type: "chapter", val: 12 },
      { id: "audio", name: "Sound & Music", type: "skill", val: 10 },
      { id: "project", name: "2D Platformer", type: "project", val: 25 },
    ],
    links: [
      { source: "topic", target: "physics", type: "includes" },
      { source: "topic", target: "graphics", type: "includes" },
      { source: "topic", target: "input", type: "includes" },
      { source: "physics", target: "loop", type: "enables" },
      { source: "graphics", target: "loop", type: "enables" },
      { source: "physics", target: "collision", type: "requires" },
      { source: "graphics", target: "animation", type: "enables" },
      { source: "loop", target: "collision", type: "enables" },
      { source: "collision", target: "project", type: "applies_to" },
      { source: "animation", target: "project", type: "applies_to" },
      { source: "input", target: "project", type: "applies_to" },
      { source: "audio", target: "project", type: "applies_to" },
    ],
  },
  data: {
    nodes: [
      { id: "topic", name: "Data Analysis", type: "topic", val: 30 },
      { id: "stats", name: "Statistics", type: "concept", val: 14 },
      { id: "pandas", name: "Pandas & DataFrames", type: "concept", val: 16 },
      { id: "viz", name: "Data Visualization", type: "concept", val: 15 },
      { id: "clean", name: "Data Cleaning", type: "chapter", val: 12 },
      { id: "explore", name: "Exploratory Analysis", type: "chapter", val: 14 },
      { id: "insight", name: "Drawing Insights", type: "chapter", val: 13 },
      { id: "present", name: "Presentation", type: "skill", val: 10 },
      { id: "project", name: "Spotify Analysis", type: "project", val: 25 },
    ],
    links: [
      { source: "topic", target: "stats", type: "includes" },
      { source: "topic", target: "pandas", type: "includes" },
      { source: "topic", target: "viz", type: "includes" },
      { source: "pandas", target: "clean", type: "enables" },
      { source: "stats", target: "explore", type: "enables" },
      { source: "clean", target: "explore", type: "requires" },
      { source: "viz", target: "explore", type: "enables" },
      { source: "explore", target: "insight", type: "enables" },
      { source: "insight", target: "present", type: "enables" },
      { source: "clean", target: "project", type: "applies_to" },
      { source: "explore", target: "project", type: "applies_to" },
      { source: "insight", target: "project", type: "applies_to" },
    ],
  },
  aiagents: {
    nodes: [
      { id: "topic", name: "AI Agents", type: "topic", val: 30 },
      { id: "llm", name: "LLM Fundamentals", type: "concept", val: 16 },
      { id: "prompt", name: "Prompt Engineering", type: "concept", val: 14 },
      { id: "tools", name: "Tool Integration", type: "concept", val: 15 },
      { id: "memory", name: "Agent Memory", type: "chapter", val: 14 },
      { id: "reasoning", name: "Chain of Thought", type: "chapter", val: 15 },
      { id: "rag", name: "RAG Systems", type: "chapter", val: 14 },
      { id: "orchestrate", name: "Orchestration", type: "skill", val: 12 },
      { id: "project", name: "Research Assistant", type: "project", val: 25 },
    ],
    links: [
      { source: "topic", target: "llm", type: "includes" },
      { source: "topic", target: "prompt", type: "includes" },
      { source: "topic", target: "tools", type: "includes" },
      { source: "llm", target: "memory", type: "enables" },
      { source: "prompt", target: "reasoning", type: "enables" },
      { source: "tools", target: "rag", type: "enables" },
      { source: "memory", target: "orchestrate", type: "enables" },
      { source: "reasoning", target: "orchestrate", type: "enables" },
      { source: "rag", target: "project", type: "applies_to" },
      { source: "memory", target: "project", type: "applies_to" },
      { source: "reasoning", target: "project", type: "applies_to" },
      { source: "orchestrate", target: "project", type: "applies_to" },
    ],
  },
};

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

const nodeColors: Record<string, string> = {
  topic: "#a855f7", // Purple
  concept: "#3b82f6", // Blue
  chapter: "#06b6d4", // Cyan
  skill: "#22c55e", // Green
  project: "#f59e0b", // Amber/Gold
};

interface ConceptGraph3DProps {
  topic?: string;
  autoRotate?: boolean;
  className?: string;
}

export function ConceptGraph3D({
  topic = "ml",
  autoRotate = true,
  className = "",
}: ConceptGraph3DProps) {
  const fgRef = useRef<any>(null);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [dimensions, setDimensions] = useState({ width: 600, height: 500 });

  useEffect(() => {
    const handleResize = () => {
      const container = document.getElementById("graph-container");
      if (container) {
        setDimensions({
          width: container.clientWidth,
          height: container.clientHeight,
        });
      }
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    // Animate nodes appearing one by one
    const data = graphDatasets[topic] || graphDatasets.ml;
    const nodes = [...data.nodes];
    const links = [...data.links];

    // Start with empty graph
    setGraphData({ nodes: [], links: [] });

    // Add nodes progressively
    let nodeIndex = 0;
    const nodeInterval = setInterval(() => {
      if (nodeIndex < nodes.length) {
        setGraphData((prev) => ({
          nodes: [...prev.nodes, nodes[nodeIndex]],
          links: prev.links,
        }));
        nodeIndex++;
      } else {
        clearInterval(nodeInterval);

        // After all nodes added, add links progressively
        let linkIndex = 0;
        const linkInterval = setInterval(() => {
          if (linkIndex < links.length) {
            setGraphData((prev) => ({
              nodes: prev.nodes,
              links: [...prev.links, links[linkIndex]],
            }));
            linkIndex++;
          } else {
            clearInterval(linkInterval);
          }
        }, 100);
      }
    }, 150);

    return () => clearInterval(nodeInterval);
  }, [topic]);

  useEffect(() => {
    if (fgRef.current && autoRotate && graphData.nodes.length > 0) {
      // Auto-rotate camera - wait for graph to initialize
      const timeout = setTimeout(() => {
        let angle = 0;
        const distance = 300;
        const interval = setInterval(() => {
          angle += 0.005;
          try {
            if (fgRef.current?.cameraPosition) {
              fgRef.current.cameraPosition({
                x: distance * Math.sin(angle),
                y: 50,
                z: distance * Math.cos(angle),
              });
            }
          } catch (e) {
            // Ignore errors during initialization
          }
        }, 30);
        return () => clearInterval(interval);
      }, 500);
      return () => clearTimeout(timeout);
    }
  }, [autoRotate, graphData.nodes.length]);

  const handleNodeClick = useCallback((node: any) => {
    if (fgRef.current) {
      const distance = 120;
      const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
      fgRef.current.cameraPosition(
        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
        node,
        1000
      );
    }
  }, []);

  return (
    <div
      id="graph-container"
      className={`relative ${className}`}
      role="img"
      aria-label={`Interactive 3D knowledge graph showing concepts and relationships for ${topic}`}
    >
      <div className="sr-only">
        Knowledge graph with {graphData.nodes.length} concepts connected by {graphData.links.length} relationships.
        Node types: topic, concept, chapter, skill, project.
      </div>
      <ForceGraph3D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeLabel={(node: any) => `<div class="bg-slate-900/90 px-3 py-2 rounded-lg text-sm">
          <div class="font-semibold text-white">${escapeHtml(String(node.name))}</div>
          <div class="text-slate-400 text-xs capitalize">${escapeHtml(String(node.type))}</div>
        </div>`}
        nodeColor={(node: any) => nodeColors[node.type] || "#ffffff"}
        nodeVal={(node: any) => node.val || 10}
        nodeOpacity={0.9}
        linkColor={() => "rgba(147, 51, 234, 0.4)"}
        linkWidth={2}
        linkOpacity={0.6}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={2}
        linkDirectionalParticleColor={() => "#a855f7"}
        backgroundColor="rgba(0,0,0,0)"
        onNodeClick={handleNodeClick}
        enableNodeDrag={true}
        enableNavigationControls={true}
        showNavInfo={false}
      />

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-slate-900/80 backdrop-blur-sm rounded-lg p-3 text-xs">
        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
          {Object.entries(nodeColors).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: color }}
                aria-hidden="true"
              />
              <span className="text-slate-300 capitalize">{type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default ConceptGraph3D;
