"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import * as d3 from "d3";
import { buildGraph, getConstellations } from "@/lib/graph";
import { GoenData, StarNode, StarLink } from "@/types";

interface UniverseProps {
  data: GoenData;
  onNodeClick?: (personId: string) => void;
}

export default function Universe({ data, onNodeClick }: UniverseProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<StarNode | null>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };
    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  const getStarBrightness = useCallback((node: StarNode): number => {
    const now = new Date();
    const lastSeen = new Date(node.lastSeen);
    const daysSince = (now.getTime() - lastSeen.getTime()) / (1000 * 60 * 60 * 24);
    // Brightness decays over time: bright within 7 days, dim after 90 days
    return Math.max(0.15, 1 - daysSince / 120);
  }, []);

  const getStarSize = useCallback((node: StarNode): number => {
    // Size based on encounter frequency
    return Math.min(8, 3 + node.encounters * 1.5);
  }, []);

  const getStarColor = useCallback((node: StarNode): string => {
    const brightness = getStarBrightness(node);
    if (brightness > 0.7) return "#f0f0ff"; // Bright white-blue
    if (brightness > 0.4) return "#818cf8"; // Indigo
    return "#4a4a6a"; // Dim
  }, [getStarBrightness]);

  useEffect(() => {
    if (!svgRef.current || data.persons.length === 0) return;

    const { width, height } = dimensions;
    const { nodes, links } = buildGraph(data);
    const constellations = getConstellations(data);

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Background stars (decorative)
    const bgStars = svg.append("g").attr("class", "bg-stars");
    for (let i = 0; i < 150; i++) {
      bgStars
        .append("circle")
        .attr("cx", Math.random() * width)
        .attr("cy", Math.random() * height)
        .attr("r", Math.random() * 1.2)
        .attr("fill", "#ffffff")
        .attr("opacity", Math.random() * 0.3 + 0.05);
    }

    // Defs for glow filter
    const defs = svg.append("defs");
    const glowFilter = defs.append("filter").attr("id", "star-glow");
    glowFilter
      .append("feGaussianBlur")
      .attr("stdDeviation", "3")
      .attr("result", "coloredBlur");
    const feMerge = glowFilter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    // Force simulation
    const simulation = d3
      .forceSimulation<StarNode>(nodes)
      .force(
        "link",
        d3
          .forceLink<StarNode, StarLink>(links)
          .id((d) => d.id)
          .distance(80)
          .strength((d) => Math.min(1, (d as StarLink).strength * 0.3))
      )
      .force("charge", d3.forceManyBody().strength(-150))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30));

    // Constellation labels
    const constellationLabels = svg.append("g").attr("class", "constellation-labels");

    // Links (constellation lines)
    const link = svg
      .append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#6366f1")
      .attr("stroke-opacity", (d) => Math.min(0.4, d.strength * 0.15))
      .attr("stroke-width", (d) => Math.min(2, d.strength * 0.5))
      .attr("stroke-dasharray", "2,4");

    // Node groups
    const nodeGroup = svg
      .append("g")
      .attr("class", "nodes")
      .selectAll<SVGGElement, StarNode>("g")
      .data(nodes)
      .join("g")
      .style("cursor", "pointer")
      .call(
        d3.drag<SVGGElement, StarNode>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    // Star glow (outer)
    nodeGroup
      .append("circle")
      .attr("r", (d) => getStarSize(d) + 4)
      .attr("fill", (d) => getStarColor(d))
      .attr("opacity", (d) => getStarBrightness(d) * 0.2)
      .attr("filter", "url(#star-glow)");

    // Star core
    nodeGroup
      .append("circle")
      .attr("r", (d) => getStarSize(d))
      .attr("fill", (d) => getStarColor(d))
      .attr("opacity", (d) => getStarBrightness(d));

    // Name labels
    nodeGroup
      .append("text")
      .text((d) => d.name)
      .attr("dy", (d) => getStarSize(d) + 16)
      .attr("text-anchor", "middle")
      .attr("fill", "#e0e0f0")
      .attr("font-size", "11px")
      .attr("opacity", (d) => Math.max(0.4, getStarBrightness(d)));

    // Hover and click handlers
    nodeGroup
      .on("mouseenter", (_, d) => setHoveredNode(d))
      .on("mouseleave", () => setHoveredNode(null))
      .on("click", (_, d) => onNodeClick?.(d.id));

    // Tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as StarNode).x!)
        .attr("y1", (d) => (d.source as StarNode).y!)
        .attr("x2", (d) => (d.target as StarNode).x!)
        .attr("y2", (d) => (d.target as StarNode).y!);

      nodeGroup.attr("transform", (d) => `translate(${d.x},${d.y})`);

      // Update constellation labels
      constellationLabels.selectAll("*").remove();
      constellations.forEach((personIds, tag) => {
        const memberNodes = nodes.filter((n) => personIds.includes(n.id));
        if (memberNodes.length < 2) return;
        const cx = memberNodes.reduce((sum, n) => sum + (n.x || 0), 0) / memberNodes.length;
        const cy = memberNodes.reduce((sum, n) => sum + (n.y || 0), 0) / memberNodes.length;
        constellationLabels
          .append("text")
          .attr("x", cx)
          .attr("y", cy - 25)
          .attr("text-anchor", "middle")
          .attr("fill", "#6366f1")
          .attr("font-size", "10px")
          .attr("opacity", 0.4)
          .text(tag);
      });
    });

    return () => {
      simulation.stop();
    };
  }, [data, dimensions, getStarBrightness, getStarColor, getStarSize, onNodeClick]);

  return (
    <div ref={containerRef} className="relative w-full h-full min-h-[500px]">
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="w-full h-full"
      />

      {/* Hover tooltip */}
      {hoveredNode && (
        <div className="absolute top-4 right-4 bg-cosmos-surface/90 backdrop-blur-md border border-cosmos-dim/30 rounded-xl p-4 max-w-xs">
          <h3 className="text-lg font-medium text-cosmos-star">{hoveredNode.name}</h3>
          <p className="text-sm text-cosmos-dim mt-1">
            {hoveredNode.encounters}回の出会い
          </p>
          <p className="text-sm text-cosmos-dim">
            最後: {new Date(hoveredNode.lastSeen).toLocaleDateString("ja-JP")}
          </p>
          {hoveredNode.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {hoveredNode.tags.slice(0, 5).map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 rounded-full bg-cosmos-accent/15 text-cosmos-glow text-xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {data.persons.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-cosmos-dim/60">
            <div className="text-6xl mb-4">✦</div>
            <p className="text-lg">まだ星がありません</p>
            <p className="text-sm mt-1">ご縁を記録して、宇宙を広げましょう</p>
          </div>
        </div>
      )}
    </div>
  );
}
