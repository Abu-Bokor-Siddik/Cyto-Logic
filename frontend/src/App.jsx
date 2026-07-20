/*
Core responsibility
---------------------------------------------------------
Assemble the main application layout and connect the
major frontend components. This file keeps the shared
compiler result in one place so different panels stay
synchronized without talking to each other directly.

Design note
-------------------------------------------------------
I chose to keep the application state at the top level.
Only the compilation result is shared across components,
which keeps the data flow simple and avoids unnecessary
state management.
*/
import { useState } from 'react';
import CircuitCanvas from './components/CircuitCanvas';
import PartsPanel from './components/PartsPanel';
import OutputPanel from './components/OutputPanel';

export default function App() {
  // The compiler output is shared between the canvas and result panel.
  const [result, setResult] = useState(null);

  return (
    <div style={{ 
      display: 'flex', 
      height: '100vh', 
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      background: '#1c222e', 
      color: '#fff' 
    }}>
       {/* Fixed sidebar keeps the toolbox visible while editing larger circuits. */}
      <div style={{ width: 180, flexShrink: 0, borderRight: '1px solid #2d3b55' }}>
      <div style={{ padding: '16px', borderBottom: '1px solid #333', fontSize: 20, fontWeight: 600, color: '#FFFFFF', fontFamily: "'Audiowide', sans-serif" }}>
          Cyto Logic
        </div>
        <PartsPanel />
      </div>
      
      {/* The canvas grows to fill any remaining workspace. */}
      <div style={{ flex: 1, position: 'relative', background: '#181818' }}>
        <CircuitCanvas onResult={setResult} />
      </div>

      {/* Results are isolated from the editor so they update independently. */}
      <div style={{ width: 260, flexShrink: 0, borderLeft: '1px solid #333' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid #333', fontSize: 13, fontWeight: 600, color: '#aaa' }}>
          Compilation Results
        </div>
        <OutputPanel result={result} />
      </div>
    </div>
  );
}