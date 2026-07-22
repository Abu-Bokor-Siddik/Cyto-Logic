/*
Core responsibility
----------------------------------------------------
Provide a single communication layer between the
React frontend and the Flask backend.This module 
sends compiler requests, graph data,and SBOL export 
requests to the backend.

Design note
----------------------------------------------------
I kept all API calls in one place so React
components never deal with backend URLs or
request details directly.If the API changes 
later, only this file needs to be updated.
*/
import axios from 'axios';

const API_BASE = '/api';

export const compileCircuit = async (logicString) => {
  const response = await axios.post(`${API_BASE}/compile`, {
    logic: logicString
    // A timeout prevents the UI from waiting forever if the backend stops responding.
  }, { timeout: 30000 });
  return response.data;
};

export const compileFromGraph = async (nodes, edges) => {
  const response = await axios.post(`${API_BASE}/compile`, {
    nodes,
    edges
  }, { timeout: 30000 });
  return response.data;
};

export const exportSBOL = async (parts, circuitName) => {
  const response = await axios.post(`${API_BASE}/export/sbol`, {
    parts,
    name: circuitName
  }, {
    responseType: 'blob',
    timeout: 30000
  });
  // The backend returns JSON instead of XML whenever an export error occurs.
  const contentType = response.headers['content-type'] || '';
  if (contentType.includes('application/json')) {
    const text = await new Response(response.data).text();
    const err = JSON.parse(text);
    throw new Error(err.error || 'Export failed');
  }

  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;

  const fileName = circuitName || 'my_circuit';
  link.setAttribute('download', `${fileName}.xml`);

  document.body.appendChild(link);
  link.click();
   // The object URL is no longer needed after the download starts.
  setTimeout(() => {
    link.remove();
    window.URL.revokeObjectURL(url);
  }, 100);
};
