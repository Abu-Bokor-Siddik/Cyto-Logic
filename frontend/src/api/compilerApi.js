import axios from 'axios';

const API_BASE = '/api';

export const compileCircuit = async (logicString) => {
  const response = await axios.post(`${API_BASE}/compile`, {
    logic: logicString
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

  setTimeout(() => {
    link.remove();
    window.URL.revokeObjectURL(url);
  }, 100);
};
