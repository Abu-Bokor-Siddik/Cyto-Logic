"""
Core responsibility
-----------------------------------------------------------
Expose the compiler through a REST API.
This layer accepts either a logic expression or a
visual circuit from the frontend, runs the compiler,
and returns the generated biological design. It also
handles SBOL export and provides the available parts
database.

Design note
--------------------------------------------------------
The API only coordinates requests. I kept the compiler,
mapper and SBOL exporter in separate modules so the web
layer stays small and easier to maintain.
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import sbol2
from compiler.lexer import BioLexer
from compiler.parser import BioParser
from compiler.gate_mapper import BioGateMapper
from compiler.sbol_exporter import SBOLExporter
from compiler.parts_db import GATES_DB, BIOMOLECULES, REPORTERS

app = Flask(__name__)
CORS(app)
# The frontend runs on a different port during development. CORS keeps the browser from blocking those requests.
def graph_to_logic(nodes, edges):
    if not nodes:
        return ""
    # The lookup table avoids scanning the node list every time the traversal needs node information.
    node_registry = {n['id']: n['data'] for n in nodes}
    # An output node has incoming edges but no outgoing edge.
    active_sources = {e['source'] for e in edges}
    active_targets = {e['target'] for e in edges}

    endpoints = [
        n for n in nodes
        if n['id'] not in active_sources
           and n['data'].get('type') == 'OUTPUT'
    ]

    if not endpoints:
        raise ValueError("Circuit design error: missing an output reporter gene node.")

    if len(endpoints) > 1:
        # If more than one output exists, I continue with the first one instead of stopping the whole compilation.
        app.logger.warning(
            "Multiple output nodes detected (%s); using first one.",
            [e['data'].get('label') for e in endpoints]
        )

    final_node = endpoints[0]
    protein_output = final_node['data']['label']
    # This helps catch inputs that were placed but never connected.
    orphan_inputs = [
        n['data'].get('label') for n in nodes
        if n['data'].get('type') == 'INPUT'
           and n['id'] not in active_targets
           and n['id'] in active_sources
    ]
    if orphan_inputs:
        app.logger.warning(
            "Unconnected input nodes detected: %s", orphan_inputs
        )
    # Walk backward through the circuit until every input has been translated into a logic expression.
    def trace_back(current_id, visited=None):
        if visited is None:
            visited = set()
        # A visited set prevents infinite recursion if the graph accidentally contains a cycle.    
        if current_id in visited:
            app.logger.warning(
                "Cycle detected at node %s; breaking to prevent infinite recursion.",
                current_id
            )
            return f"...(cycle at {current_id})..."
        visited.add(current_id)

        node_info = node_registry.get(current_id, {})
        kind = node_info.get('type', 'INPUT')

        parent_links = [e['source'] for e in edges if e['target'] == current_id]

        if kind == 'INPUT' or not parent_links:
            return node_info.get('label', 'Unknown')

        if kind == 'NOT':
            # NOT is defined as a single-input gate. If more connections exist, only the first is used.
            if len(parent_links) > 1:
                app.logger.warning(
                    "NOT gate at %s has %d inputs; using first one.",
                    current_id, len(parent_links)
                )
            return f"NOT {trace_back(parent_links[0], visited)}"

        if kind == 'AND':
            elements = [trace_back(p, visited) for p in parent_links]
            return f"({' AND '.join(elements)})"

        if kind == 'OR':
            elements = [trace_back(p, visited) for p in parent_links]
            return f"({' OR '.join(elements)})"

        if kind == 'OUTPUT':
            return trace_back(parent_links[0], visited)

        return node_info.get('label', 'Unknown')

    gate_logic = trace_back(final_node['id'])
    return f"IF {gate_logic} -> {protein_output}"


@app.route('/api/compile', methods=['POST'])
def process_circuit_compilation():
    payload = request.get_json() or {}
    statement = payload.get('logic')
    # The frontend may send either text or a visual circuit. If no logic string exists, generate one from the graph.
    if not statement:
        try:
            statement = graph_to_logic(
                payload.get('nodes', []),
                payload.get('edges', [])
            )
        except (ValueError, KeyError) as err:
            return jsonify({
                "success": False,
                "error": f"Graph conversion failed: {str(err)}"
            }), 400
    # A simple size limit avoids unusually large requests from consuming unnecessary resources.
    if len(statement) > 10000:
        return jsonify({
            "success": False,
            "error": "Input too long (max 10000 characters)."
        }), 400

    try:
        # The compiler always runs in the same order: Lexer → Parser → Gate Mapper.
        lexer_engine = BioLexer(statement)
        generated_tokens = lexer_engine.tokenize()

        parser_engine = BioParser(generated_tokens)
        syntax_tree = parser_engine.parse()

        mapping_engine = BioGateMapper()
        synthesis_result = mapping_engine.map_circuit(syntax_tree)
        # Nothing meaningful can be returned if mapping fails.
        if synthesis_result is None:
            return jsonify({
                "success": False,
                "error": "Compiler produced no output from the given input."
            }), 400

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
        return jsonify({
            "success": False,
            "error": f"Syntax error: {str(syn_ex)}"
        }), 400
    except Exception as general_ex:
        # Unexpected failures are logged so debugging doesn't depend on browser error messages.
        app.logger.exception("Internal compilation failure")
        return jsonify({
            "success": False,
            "error": f"Internal compilation error: {str(general_ex)}"
        }), 500


@app.route('/api/export/sbol', methods=['POST'])
def handle_sbol_download():
    payload = request.get_json()
    target_parts = payload.get('parts', [])
    project_title = payload.get('name', 'untitled')
    # Export only accepts a reasonable number of parts. This keeps malformed requests under control.
    if not isinstance(target_parts, list) or len(target_parts) > 500:
        return jsonify({
            "success": False,
            "error": "Parts list must be an array of at most 500 items."
        }), 400

    try:
        # The exporter builds the SBOL document. Flask only streams the generated XML back.
        exporter_tool = SBOLExporter()
        doc = exporter_tool.create_document(target_parts, project_title)

        xml_data = doc.writeString()

        return Response(
            xml_data,
            mimetype='application/xml',
            headers={
                "Content-Disposition":
                    f"attachment; filename={project_title}.xml"
            }
        )

    except Exception as e:
        app.logger.exception("SBOL export failed")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/parts', methods=['GET'])
def fetch_parts_inventory():
    # The frontend only needs the available names, not the full database entries.
    combined_keys = (
        list(GATES_DB.keys())
        + list(BIOMOLECULES.keys())
        + list(REPORTERS.keys())
    )
    return jsonify({
        "gates": combined_keys,
        "count": len(combined_keys)
    })


if __name__ == '__main__':
    # Useful during local development. Production should run behind a WSGI server.
    app.run(debug=True, port=5000)
