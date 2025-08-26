
import React, { useEffect, useState, useMemo } from 'react';
import type { InvestigationData, Entity } from '../types';
import { EntityType } from '../types';

interface GraphViewProps {
    data: InvestigationData | null;
    highlightedEntity: Entity | null;
    onNodeClick: (entity: Entity) => void;
}

interface Node extends Entity {
    x: number;
    y: number;
}

interface Link {
    source: Node;
    target: Node;
    label: string;
}

const typeColors: Record<EntityType, string> = {
    [EntityType.Domain]: '#34d399', // emerald-400
    [EntityType.Email]: '#fbbf24', // amber-400
    [EntityType.IP]: '#60a5fa', // blue-400
    [EntityType.Username]: '#a78bfa', // violet-400
    [EntityType.Breach]: '#f87171', // red-400
    [EntityType.File]: '#a3a3a3', // neutral-400
    [EntityType.Organization]: '#22d3ee', // cyan-400
    [EntityType.Person]: '#f472b6', // pink-400
    [EntityType.SourceFile]: '#ffffff', // white
    [EntityType.Password]: '#fca5a5', // red-300
    [EntityType.PasswordHash]: '#fdba74', // orange-300
    [EntityType.SessionInfo]: '#818cf8', // indigo-300
    [EntityType.APIKey]: '#c084fc', // purple-300
    [EntityType.Cookie]: '#f9a8d4', // pink-300
    [EntityType.Unknown]: '#9ca3af', // gray-400
};

export const GraphView: React.FC<GraphViewProps> = ({ data, highlightedEntity, onNodeClick }) => {
    const [nodes, setNodes] = useState<Node[]>([]);
    const [links, setLinks] = useState<Link[]>([]);
    const [viewBox, setViewBox] = useState('0 0 1000 600');
    const width = 1000;
    const height = 600;

    useEffect(() => {
        if (data && data.entities.length > 0) {
            // Simple force-directed layout simulation
            const newNodes: Node[] = data.entities.map(e => ({
                ...e,
                x: Math.random() * width,
                y: Math.random() * height,
            }));

            // A basic physics simulation for layout
            for (let i = 0; i < 60; i++) { // iterations
                 // Repulsion force
                newNodes.forEach(nodeA => {
                    newNodes.forEach(nodeB => {
                        if (nodeA.id === nodeB.id) return;
                        const dx = nodeB.x - nodeA.x;
                        const dy = nodeB.y - nodeA.y;
                        const distance = Math.sqrt(dx * dx + dy * dy) || 1;
                        const force = -100 / (distance * distance);
                        const forceX = force * (dx / distance);
                        const forceY = force * (dy / distance);
                        nodeA.x += forceX;
                        nodeA.y += forceY;
                    });
                });
                 // Attraction force for links
                const nodeMap = new Map(newNodes.map(n => [n.id, n]));
                 data.relations.forEach(rel => {
                    const source = nodeMap.get(rel.from);
                    const target = nodeMap.get(rel.to);
                    if (!source || !target) return;
                     const dx = target.x - source.x;
                     const dy = target.y - source.y;
                     const distance = Math.sqrt(dx * dx + dy * dy);
                     const force = 0.05 * (distance - 150);
                     const forceX = force * (dx / distance);
                     const forceY = force * (dy / distance);
                     source.x += forceX;
                     source.y += forceY;
                     target.x -= forceX;
                     target.y -= forceY;
                });
            }

            // Center the graph
            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
            newNodes.forEach(n => {
                minX = Math.min(minX, n.x);
                maxX = Math.max(maxX, n.x);
                minY = Math.min(minY, n.y);
                maxY = Math.max(maxY, n.y);
            });
            const graphWidth = maxX - minX;
            const graphHeight = maxY - minY;
            const offsetX = (width - graphWidth) / 2 - minX;
            const offsetY = (height - graphHeight) / 2 - minY;

            const finalNodes = newNodes.map(n => ({
                ...n,
                x: n.x + offsetX,
                y: n.y + offsetY
            }));

            setNodes(finalNodes);

            const nodeMap = new Map(finalNodes.map(n => [n.id, n]));
            const newLinks = data.relations
                .map(r => ({
                    source: nodeMap.get(r.from),
                    target: nodeMap.get(r.to),
                    label: r.label,
                }))
                .filter(l => l.source && l.target) as Link[];
            setLinks(newLinks);
        } else {
            setNodes([]);
            setLinks([]);
        }
    }, [data]);

    const highlightedIds = useMemo(() => {
        if (!highlightedEntity || !data) return new Set();

        const ids = new Set<number>([highlightedEntity.id]);
        data.relations.forEach(rel => {
            if (rel.from === highlightedEntity.id) ids.add(rel.to);
            if (rel.to === highlightedEntity.id) ids.add(rel.from);
        });
        return ids;
    }, [highlightedEntity, data]);

    if (!data) {
        return <div className="absolute inset-0 flex items-center justify-center text-gray-500">Graph will be displayed here.</div>;
    }

    return (
        <svg viewBox={viewBox} className="w-full h-full">
            <defs>
                <marker id="arrowhead" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280" />
                </marker>
            </defs>
            {links.map((link, i) => (
                <g key={`link-group-${i}`}>
                    <line
                        x1={link.source.x}
                        y1={link.source.y}
                        x2={link.target.x}
                        y2={link.target.y}
                        stroke="#4b5563"
                        strokeWidth="1"
                        markerEnd="url(#arrowhead)"
                        opacity={highlightedEntity ? (highlightedIds.has(link.source.id) && highlightedIds.has(link.target.id) ? 1 : 0.2) : 1}
                        style={{ transition: "opacity 0.3s" }}
                    />
                </g>
            ))}
             {links.map((link, i) => (
                 <text
                        key={`label-${i}`}
                        x={(link.source.x + link.target.x) / 2}
                        y={(link.source.y + link.target.y) / 2}
                        fill="#9ca3af"
                        fontSize="8"
                        textAnchor="middle"
                        dy="-4"
                        opacity={highlightedEntity ? (highlightedIds.has(link.source.id) && highlightedIds.has(link.target.id) ? 0.9 : 0.1) : 0.7}
                        className="pointer-events-none transition-opacity duration-300"
                    >
                        {link.label}
                    </text>
             ))}
            {nodes.map(node => (
                <g 
                  key={node.id} 
                  transform={`translate(${node.x},${node.y})`}
                  style={{ transition: 'opacity 0.3s' }}
                  opacity={highlightedEntity ? (highlightedIds.has(node.id) ? 1 : 0.3) : 1}
                  onClick={() => onNodeClick(node)}
                  className="cursor-pointer"
                  >
                    <circle
                        r={node.type === EntityType.SourceFile ? 10 : 8}
                        fill={typeColors[node.type] || '#9ca3af'}
                        stroke={node.type === EntityType.SourceFile ? typeColors[EntityType.Organization] : "#1f2937"}
                        strokeWidth="2"
                    />
                    <text
                        y="20"
                        fill="#d1d5db"
                        fontSize="10"
                        textAnchor="middle"
                        className="pointer-events-none"
                    >
                        {node.label}
                    </text>
                </g>
            ))}
        </svg>
    );
};