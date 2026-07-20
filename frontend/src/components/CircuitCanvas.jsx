/*
Core responsibility
-------------------------------------------------------
Provide the visual editor used to build logic circuits.
Users can connect gates, edit proteins, and send the
finished graph to the compiler. This component only
handles interaction on the canvas. The actual compiler
runs on the backend.

Design note
-------------------------------------------------------------
I decided to keep the visual editor independent from the
compiler itself. The frontend only manages nodes and edges,
then sends the graph to the backend. That keeps the UI
simple and avoids duplicating compiler logic in JavaScript.
*/
import { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
  addEdge, 
  useNodesState, 
  useEdgesState,
  Controls, 
  Background, 
  MiniMap,
} from 'reactflow';
import '@reactflow/core/dist/style.css';
import GateNode from './GateNode';
import { compileFromGraph } from '../api/compilerApi';

const nodeTypes = { gateNode: GateNode };
// A small starter circuit makes the editor usable immediately.
const initialNodes = [
  { id: '1', type: 'gateNode', position: { x: 80,  y: 120 }, data: { type: 'INPUT',  label: 'aTc' } },
  { id: '2', type: 'gateNode', position: { x: 80,  y: 240 }, data: { type: 'INPUT',  label: 'AraC' } },
  { id: '3', type: 'gateNode', position: { x: 280, y: 180 }, data: { type: 'AND',    label: 'AND gate' } },
  { id: '4', type: 'gateNode', position: { x: 480, y: 180 }, data: { type: 'OUTPUT', label: 'GFP' } },
];

const initialEdges = [
  { id: 'e1-3', source: '1', target: '3', targetHandle: 'a', animated: true },
  { id: 'e2-3', source: '2', target: '3', targetHandle: 'b', animated: true },
  { id: 'e3-4', source: '3', target: '4', animated: true },
];

export default function CircuitCanvas({ onResult }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [isCompiling, setIsCompiling] = useState(false);

  useEffect(() => {
    // Remove default browser spacing so the editor fills the entire page.
    document.body.style.margin = "0";
    document.body.style.padding = "0";
    document.body.style.overflow = "hidden";
    document.body.style.backgroundColor = "#f8f9fa";
  }, []);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({ ...params, animated: true }, eds)),
    [setEdges]
  );

  const onNodeDoubleClick = useCallback((event, node) => {
    const currentLabel = node.data.label;
    const newLabel = prompt(`Modify label/protein name for this ${node.data.type} node:`, currentLabel);
    
    /*Protein names change frequently while testing circuits, so editing
    them directly is faster than opening a separate settings panel.*/
    if (newLabel && newLabel.trim() !== "") {
      setNodes((nds) =>
        nds.map((n) => {
          if (n.id === node.id) {
            return {
              ...n,
              data: { ...n.data, label: newLabel.trim() }
            };
          }
          return n;
        })
      );
    }
  }, [setNodes]);

  const handleClearCanvas = () => {
    if (window.confirm("Are you sure you want to delete the whole circuit and start fresh?")) {
      setNodes([]);
      setEdges([]);
    }
  };

  const handleCompile = async () => {
    setIsCompiling(true);
    // Keeping this log helped while checking the request flow between React and the Flask backend.
    console.log("Initiating compiler request...");
    try {
      const result = await compileFromGraph(nodes, edges);
      onResult(result);
    } catch (err) {
      console.error("Oops! Compilation crashed:", err);
      onResult({ success: false, error: err.message });
    } finally {
      setIsCompiling(false);
    }
  };

  const onDrop = useCallback((event) => {
    event.preventDefault();
    const type = event.dataTransfer.getData('application/reactflow');
    if (!type) return;

    const reactFlowBounds = event.target.getBoundingClientRect();
    const position = {
    /*A small offset keeps the cursor near the center of the new node
    instead of placing it from the top-left corner.*/
      x: event.clientX - reactFlowBounds.left - 75,
      y: event.clientY - reactFlowBounds.top - 40
    };

    const newNode = {
      id: `node_${Date.now()}`,
      type: 'gateNode',
      position,
      data: { 
        type, 
        label: type === 'INPUT' ? 'Input' : type === 'OUTPUT' ? 'Output' : `${type} Gate` 
      }
    };
    
    setNodes((nds) => nds.concat(newNode));
  }, [setNodes]);

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', background: '#0e2439' }}>
      
      <div style={{ position: 'absolute', top: 15, left: 15, zIndex: 10 }}>
        <button
          onClick={handleClearCanvas}
          style={{
            background: '#ff4d4d', color: 'white', border: 'none',
            padding: '8px 16px', borderRadius: 6, cursor: 'pointer',
            fontSize: 15, fontWeight: 600, boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
            transition: 'background 0.2s'
          }}
          onMouseOver={(e) => e.target.style.background = '#e03b3b'}
          onMouseOut={(e) => e.target.style.background = '#ff4d4d'}
        >
          Create New Logic
        </button>
      </div>

      <ReactFlow
        nodes={nodes} 
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDrop={onDrop}
        onDragOver={onDragOver}
        nodeTypes={nodeTypes}
        onNodeDoubleClick={onNodeDoubleClick}
        deleteKeyCode={["Delete", "Backspace"]}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <MiniMap 
      style={{ 
        background: '#1A202C',
        border: '1px solid #3B5B75',
        borderRadius: '16px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)', 
        overflow: 'hidden'
      }}
      nodeColor={(node) => {
        switch (node.data.type) {
          case 'INPUT': 
            return '#3B5B75';
          case 'OUTPUT': 
            return '#ca2f57';
          case 'AND':
          case 'OR':
          case 'NOT': 
            return '#8A5B73';
          default: 
            return '#4B5563';
        }
      }}
      nodeBorderRadius={6}
      maskColor="rgba(15, 20, 30, 0.75)"
      pannable={true}
      zoomable={true}
      onClick={(event) => {
        console.log("Navigating to selected area...");
      }}
    />
        <Background variant="dots" gap={20} size={2} />
      </ReactFlow>

      <button
        onClick={handleCompile}
        disabled={isCompiling}
        style={{
          position: 'absolute', 
          bottom: 20,
          left: '50%',
          transform: 'translateX(-50%)', 
          zIndex: 10,
          padding: '12px 24px', 
          borderRadius: 8, 
          cursor: isCompiling ? 'not-allowed' : 'pointer',
          background: '#1D9E75',
          color: 'white', 
          border: 'none', 
          fontWeight: 'bold', 
          fontSize: 14,
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
          transition: 'all 0.2s'
        }}
      >
        {isCompiling ? 'Compiling...' : 'Compile Circuit'}
      </button>
    </div>
  );
}