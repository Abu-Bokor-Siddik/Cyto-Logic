/*
Core responsibility
-------------------------------------------------
Display the compiler output in a readable format.
This panel shows the generated biological parts,
reports compilation errors, and allows the circuit
to be exported as an SBOL document.

Design note
------------------------------------------------------
I kept result presentation separate from compilation.
This component only displays data it receives and
triggers export when requested. All compiler logic
stays inside the backend and API layer.
*/
import {useState} from 'react';
import {exportSBOL} from '../api/compilerApi'; 

export default function OutputPanel({result}) {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await exportSBOL(result.parts, 'my_circuit');
    } catch (error) {
      console.error("Export failed:", error);
      alert("SBOL Export Failed! Please check if your backend server is running.");
    } finally {
      // Always restore the button state, even if export fails.
      setIsExporting(false);
    }
  };
  // Nothing has been compiled yet.
  if (!result) {
    return (
      <div style={{ padding: 20, color: '#888', fontSize: 13, textAlign: 'center' }}>
        Compile a circuit to see the results here!
      </div>
    );
  }
  // Display compiler errors instead of rendering incomplete data.
  if (!result.success) {
    return (
      <div style={{ padding: 20, color: '#ff5f5f', fontSize: 13 }}>
        <strong>Compilation Error:</strong> <br/> 
        {result.error}
      </div>
    );
  }

  return (
    <div style={{ padding: 16, color: '#fff' }}>
      
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <div style={{ flex: 1, background: '#2c2c2c', borderRadius: 8, padding: '12px' }}>
          <div style={{ fontSize: 11, color: '#aaa' }}>Output Protein</div>
          <div style={{ fontSize: 16, fontWeight: 600, marginTop: 4 }}>
            {result.output_protein || 'N/A'}
          </div>
        </div>
        
        <div style={{ flex: 1, background: '#2c2c2c', borderRadius: 8, padding: '12px' }}>
          <div style={{ fontSize: 11, color: '#aaa' }}>Total Parts</div>
          <div style={{ fontSize: 16, fontWeight: 600, marginTop: 4 }}>
            {result.parts?.length || 0}
          </div>
        </div>
      </div>

      <p style={{ fontSize: 12, color: '#aaa', marginBottom: 10 }}>Required BioBricks:</p>
      
      <div style={{ maxHeight: '300px', overflowY: 'auto', paddingRight: '4px' }}>
        
        {/* A scrollable list keeps large circuits from stretching the panel. */}
        {result.parts?.map((part, index) => (
          <div 
            key={index} 
            style={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              background: '#252525',
              border: '1px solid #333',
              borderRadius: 6, 
              padding: '8px', 
              marginBottom: 6,
              fontSize: 12
            }}
          >
            <span style={{ fontFamily: 'monospace', color: '#00ffcc' }}>{part.id}</span>
            <span style={{ color: '#888' }}>{part.role}</span>
          </div>
        ))}
        
        {(!result.parts || result.parts.length === 0) && (
          <div style={{ fontSize: 12, color: '#666', textAlign: 'center', marginTop: 10 }}>
            No parts found in this circuit.
          </div>
        )}
      </div>

      <button
        onClick={handleExport}
        disabled={isExporting}
        style={{ 
          width: '100%', 
          marginTop: 20, 
          padding: '10px',
          background: isExporting ? '#666' : '#c9656d', 
          color: '#fff', 
          border: '1px solid #444',
          borderRadius: 8, 
          fontSize: 13, 
          fontWeight: 600,
          cursor: isExporting ? 'not-allowed' : 'pointer', 
          transition: 'background 0.2s ease-in-out'
        }}
      >
        {isExporting ? 'Generating XML...' : 'Export SBOL (.xml)'}
      </button>
      
    </div>
  );
}