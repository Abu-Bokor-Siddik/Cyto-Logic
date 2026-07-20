/*
Core responsibility
------------------------------------------------------------
Render a single logic gate inside the visual circuit editor.
Each node provides the connection points needed to build
a circuit while keeping the visual appearance independent
from the compiler itself.

Design note
----------------------------------------------------------------
I kept rendering separate from circuit logic. This component
only draws a node based on the data it receives. It does not
know anything about compilation or biological mapping.
*/
import { Handle, Position } from 'reactflow';

const gateColors = {
  AND:    { bg: '#9d6070', border: '#e4b6b6', text: '#FFFFFF' },
  OR:     { bg: '#9d6070', border: '#e4b6b6', text: '#FFFFFF' },
  NOT:    { bg: '#9d6070', border: '#e4b6b6', text: '#FFFFFF' },
  INPUT:  { bg: '#365571', border: '#5992c6', text: '#FFFFFF' }, 
  OUTPUT: { bg: '#ca2f57', border: '#f4819f', text: '#FFFFFF' },
}; 

export default function GateNode({ data }) {
   // A fallback keeps custom or incomplete nodes from breaking the UI.
  const style = gateColors[data.type] || gateColors.INPUT;
  
  const isNot = data.type === 'NOT';
  const isOutput = data.type === 'OUTPUT';
  const isInput = data.type === 'INPUT';

  return (
    <div style={{
      background: style.bg,
      border: `2px solid ${style.border}`,
      borderRadius: '8px',
      padding: '12px 20px',
      minWidth: 130,
      textAlign: 'center',
      cursor: 'grab',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      fontFamily: '"Segoe UI", sans-serif'
    }}>
      {!isInput && (
        /* NOT only accepts one incoming signal, so its connector stays centered. */
        <>
          <Handle type="target" position={Position.Left} id="a" 
            style={{ top: isNot ? '50%' : '30%', background: '#E5E7EB', border: 'none', width: 8, height: 8 }} />
          {!isNot && (
            <Handle type="target" position={Position.Left} id="b" 
              style={{ top: '70%', background: '#E5E7EB', border: 'none', width: 8, height: 8 }} />
          )}
        </>
      )}

      <div style={{ fontWeight: 600, fontSize: 14, color: style.text, letterSpacing: '0.5px' }}>
        {data.type}
      </div>
      <div style={{ fontSize: 11, color: style.text, opacity: 0.8, marginTop: 4 }}>
        {data.label}
      </div>

      {/* Output is the end of the circuit, so it does not expose another source handle. */}
      {!isOutput && (
        <Handle type="source" position={Position.Right} 
          style={{ background: '#E5E7EB', border: 'none', width: 8, height: 8 }} />
      )}
    </div>
  );
}