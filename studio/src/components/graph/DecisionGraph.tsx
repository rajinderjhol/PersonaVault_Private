import React, { useEffect, useState } from 'react';
import ReactFlow, { Background, Controls, Node, Edge, NodeMouseHandler } from 'reactflow';
import 'reactflow/dist/style.css';
import { graphService } from '../../services/graphService';
import styles from './DecisionGraph.module.css';

interface DecisionGraphProps {
  decisionId: string;
  onNodeClick?: (node: Node) => void;
}

export const DecisionGraph: React.FC<DecisionGraphProps> = ({ decisionId, onNodeClick }) => {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGraph = async () => {
      setLoading(true);
      try {
        const response = await graphService.getDecisionGraph(decisionId);
        
        // Add positions to nodes for ReactFlow (simple horizontal layout)
        const formattedNodes = response.data.nodes.map((n: any, index: number) => ({
          ...n,
          position: { x: index * 200, y: 100 },
        }));
        
        setNodes(formattedNodes);
        setEdges(response.data.edges);
      } catch (error) {
        console.error('Error fetching graph:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchGraph();
  }, [decisionId]);

  const handleNodeClick: NodeMouseHandler = (event, node) => {
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  if (loading) return <div>Loading Decision Graph...</div>;

  return (
    <div className={styles.graphContainer}>
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        fitView
        onNodeClick={handleNodeClick}
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
};
