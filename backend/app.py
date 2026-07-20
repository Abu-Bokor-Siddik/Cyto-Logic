"""
Core responsibility
----------------------------------------------------
Expose the compiler as a REST API for the frontend.
This module receives either a logic expression or a
visual circuit, runs the complete compilation pipeline,
and returns the generated biological design. It also
provides SBOL export so the result can be used outside
the application.

Design note
----------------------------------------------------
I kept the Flask routes thin on purpose. The compiler,
parser, mapper and exporter all live in separate modules.
That makes each layer easier to test and change without
touching the web API.
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import io
import sbol2
from compiler.lexer import BioLexer
from compiler.parser import BioParser
from compiler.gate_mapper import BioGateMapper
from compiler.sbol_exporter import SBOLExporter

app = Flask(__name__)
CORS(app) 

def graph_to_logic(nodes, edges):
    #Convert a visual React Flow graph into the compiler's textual language.
    if not nodes:
        return ""
        
    node_registry = {n['id']: n['data'] for n in nodes}
    
    # I identify the output by looking for the node that has no outgoing connection.
    active_sources = {e['source'] for e in edges}
    endpoints = [n for n in nodes if n['id'] not in active_sources and n['data'].get('type') == 'OUTPUT']
    
    if not endpoints:
        raise ValueError("circuit design error: missing an output reporter gene node.")
        
    final_node = endpoints[0]
    protein_output = final_node['data']['label']

    def trace_back(current_id):
        node_info = node_registry.get(current_id, {})
        kind = node_info.get('type', 'INPUT')

        parent_links = [e['source'] for e in edges if e['target'] == current_id]
        
        if kind == 'INPUT' or not parent_links:
            return node_info.get('label', 'Unknown')
            
        if kind == 'NOT':
            return f"NOT {trace_back(parent_links[0])}"
            
        if kind == 'AND':
            elements = [trace_back(p) for p in parent_links]
            return f"({' AND '.join(elements)})"
            
        if kind == 'OR':
            elements = [trace_back(p) for p in parent_links]
            return f"({' OR '.join(elements)})"
            
        return node_info.get('label', 'Unknown')

    gate_logic = trace_back(final_node['id'])
    return f"IF {gate_logic} -> {protein_output}"


@app.route('/api/compile', methods=['POST'])
def process_circuit_compilation():
    payload = request.get_json() or {}
    statement = payload.get('logic')

    if not statement:
        try:
            statement = graph_to_logic(payload.get('nodes', []), payload.get('edges', []))
        except Exception as err:
            return jsonify({"success": False, "error": f"graph conversion failed: {str(err)}"}), 400

    try:
        lexer_engine = BioLexer(statement)
        generated_tokens = lexer_engine.tokenize()
        
        parser_engine = BioParser(generated_tokens)
        syntax_tree = parser_engine.parse()
        
        mapping_engine = BioGateMapper()
        synthesis_result = mapping_engine.map_circuit(syntax_tree)

        nodes_dict = synthesis_result.get("circuit_structure", {})
        edges_list = synthesis_result.get("connections", [])
        
        return jsonify({
            "success": True,
            "logic": statement,
            "parts": synthesis_result.get("dna_parts_list", []),
            "complexity_score": synthesis_result.get("complexity", 0),
            "output_protein": payload.get('output_protein', 'GFP'),
            "graph": {
                "nodes": list(nodes_dict.items()),
                "edges": edges_list
            }
        })
        
    except SyntaxError as syn_ex:
        return jsonify({"success": False, "error": f"bad code syntax: {str(syn_ex)}"}), 400
    except Exception as general_ex:
        return jsonify({"success": False, "error": f"internal compilation breakdown: {str(general_ex)}"}), 500


@app.route('/api/export/sbol', methods=['POST'])
def handle_sbol_download():
    payload = request.get_json()
    target_parts = payload.get('parts', [])
    project_title = payload.get('name', 'untitled')
    
    try:
        sbol2.setHomespace('http://cytologic.org')
        exporter_tool = SBOLExporter()
        
        print(f"DEBUG: Starting export for {project_title} with {len(target_parts)} parts.")
        
        doc = exporter_tool.create_document(target_parts, project_title)
        
        print("DEBUG: Document created successfully. Attempting to write XML...")
        
        xml_data = doc.writeString()
        
        print("DEBUG: XML string generated.")
        
        return Response(
            xml_data,
            mimetype='application/xml',
            headers={"Content-Disposition": f"attachment; filename={project_title}.xml"}
        )
        
    except Exception as e:
        import traceback
        print("--- Find a critical error ---")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/parts', methods=['GET'])
def fetch_parts_inventory():
    from compiler.parts_db import GATES_DB, BIOMOLECULES, REPORTERS
    
    combined_keys = list(GATES_DB.keys()) + list(BIOMOLECULES.keys()) + list(REPORTERS.keys())
    return jsonify({
        "gates": combined_keys,
        "count": len(combined_keys)
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)