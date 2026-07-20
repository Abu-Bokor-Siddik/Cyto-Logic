/*
Core responsibility
----------------------------------------------------
Provide a small API layer for the frontend.
Every compiler request goes through this file so the UI
doesn't need to know how the backend is called.

Design note
----------------------------------------------------
I kept all HTTP requests together instead of placing
Axios calls inside React components. If an endpoint
changes later, only this file needs to be updated.
*/
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

export const compileCircuit = async (logicString) => {
  const response = await axios.post(`${API_BASE}/compile`, {
    logic: logicString
  });
  return response.data;
};

export const compileFromGraph = async (nodes, edges) => {
  // I left this log here while testing the visual editor.
  // It makes it easy to verify that the current graph is actually being sent.
  console.log("Sending visual graph to backend...");
  
  const response = await axios.post(`${API_BASE}/compile`, {
    nodes,
    edges
  });
  return response.data;
};

export const exportSBOL = async (parts, circuitName) => {
  const response = await axios.post(`${API_BASE}/export/sbol`, {
    parts,
    name: circuitName
  }, 
  { 
    // SBOL is returned as XML, so the browser should treat it as a downloadable file instead of text.
    responseType: 'blob' }); 

  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;

  const fileName = circuitName ? circuitName : "my_circuit";
  link.setAttribute('download', `${fileName}.xml`);
  
  document.body.appendChild(link);
  link.click();
  link.remove();

  // Free the temporary object after the download starts.
  window.URL.revokeObjectURL(url);
};