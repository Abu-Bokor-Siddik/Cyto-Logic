/*
Core responsibility
---------------------------------------------------------
Display the available logic gates that can be added
to the circuit editor. This panel acts as the entry
point for building a visual genetic circuit through
drag-and-drop interactions.

Design note
-------------------------------------------------------
I kept the gate definitions in a single array so new
gate types can be added without changing the UI logic.
The component only starts the drag operation; node
creation is handled by the canvas.
*/
const GATE_TYPES = [
    { type: 'INPUT',  desc: 'Input signal',      color: '#365571', border: '#5992c6' },
    { type: 'AND',    desc: 'AND logic gate',    color: '#9d6070', border: '#e4b6b6' },
    { type: 'OR',     desc: 'OR logic gate',     color: '#9d6070', border: '#e4b6b6' },
    { type: 'NOT',    desc: 'Signal inverter',   color: '#9d6070', border: '#e4b6b6' },
    { type: 'OUTPUT', desc: 'Output reporter',   color: '#ca2f57', border: '#f4819f' },
  ];

  export default function PartsPanel() {
    // React Flow reads this value after the item is dropped onto the canvas.
    const onDragStart = (event, type) => {
      event.dataTransfer.setData('application/reactflow', type);
      event.dataTransfer.effectAllowed = 'move';
    };
  
    return (
      <div style={{ padding: 16, background: '#23313e', height: '100%' }}>
        <p style={{ fontSize: 12, color: '#aaa', marginBottom: 16 }}>
          Drag gates onto the canvas
        </p>
        
        {GATE_TYPES.map(({ type, desc, color, border }) => (
          <div
            key={type}
            draggable
            onDragStart={(e) => onDragStart(e, type)}
            style={{
              padding: '10px',
              marginBottom: 10,
              borderRadius: 8,
              background: color,
              border: `2px solid ${border}`,
              cursor: 'grab',
              fontSize: 13,
              fontWeight: 600,
              transition: 'transform 0.1s ease'
            }}
            // A small hover effect makes draggable items feel more interactive.
            onMouseEnter={(e) => e.target.style.transform = 'scale(1.02)'}
            onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
          >
            <div style={{ color: '#FFFFFF' }}>{type}</div>
            <div style={{ fontSize: 11, fontWeight: 400, marginTop: 4, color: '#FFFFFF' }}>
              {desc}
            </div>
          </div>
        ))}
      </div>
    );
  }