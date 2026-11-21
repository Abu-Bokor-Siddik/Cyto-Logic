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
import os
import re
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from compiler.parts_db import GATES_DB, BIOMOLECULES, REPORTERS
from compiler.backends.registry import get as get_backend
from compiler.pipeline import CompilerPipeline
from compiler.middleware import setup_logging, rate_limit, validate_input

app = Flask(__name__)
CORS(app, origins=os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:4173,http://127.0.0.1:5173"
).split(","))
setup_logging(app)


def sanitize_filename(name, default="export"):
    """Strip unsafe characters from a filename component."""
    cleaned = re.sub(r'[^\w.-]', '_', name)
    return cleaned if cleaned else default


def graph_to_logic(nodes, edges):
    if not nodes:
        return ""

    node_registry = {n['id']: n['data'] for n in nodes}
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
        app.logger.warning(
            "Multiple output nodes detected (%s); using first one.",
            [e['data'].get('label') for e in endpoints]
        )

    final_node = endpoints[0]
    protein_output = final_node['data']['label']

    orphan_inputs = [
        n['data'].get('label') for n in nodes
        if n['data'].get('type') == 'INPUT'
           and n['id'] not in active_targets
           and n['id'] not in active_sources
    ]
    if orphan_inputs:
        app.logger.warning(
            "Unconnected input nodes detected: %s", orphan_inputs
        )

    def trace_back(current_id, visited=None):
        if visited is None:
            visited = set()
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

        if kind == 'NAND':
            elements = [trace_back(p, visited) for p in parent_links]
            return f"(NOT ({' AND '.join(elements)}))"

        if kind == 'NOR':
            elements = [trace_back(p, visited) for p in parent_links]
            return f"(NOT ({' OR '.join(elements)}))"

        if kind == 'OUTPUT':
            return trace_back(parent_links[0], visited)

        return node_info.get('label', 'Unknown')

    gate_logic = trace_back(final_node['id'])
    return f"IF {gate_logic} -> {protein_output}"


@app.route('/api/compile', methods=['POST'])
@rate_limit
def process_circuit_compilation():
    payload = request.get_json() or {}
    validation_errors = validate_input(payload)
    if validation_errors:
        return jsonify({"success": False, "error": validation_errors[0]}), 400

    statement = payload.get('logic')

    if not statement:
        if len(payload.get('nodes', [])) > 500 or len(payload.get('edges', [])) > 500:
            return jsonify({
                "success": False,
                "error": "Circuit graph too large (max 500 nodes or edges)."
            }), 400
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

    if len(statement) > 10000:
        return jsonify({
            "success": False,
            "error": "Input too long (max 10000 characters)."
        }), 400

    try:
        pipeline = CompilerPipeline()
        cir, messages = pipeline.run(statement)

        api_response = cir.to_api_response()
        api_response["success"] = True
        api_response["semantic_messages"] = [m.to_dict() for m in messages]

        return jsonify(api_response)

    except SyntaxError as syn_ex:
        return jsonify({
            "success": False,
            "error": f"Syntax error: {str(syn_ex)}"
        }), 400
    except Exception as general_ex:
        app.logger.exception("Internal compilation failure")
        return jsonify({
            "success": False,
            "error": f"Internal compilation error: {str(general_ex)}"
        }), 500


@app.route('/api/export/sbol', methods=['POST'])
@rate_limit
def handle_sbol_download():
    payload = request.get_json() or {}
    target_parts = payload.get('parts', [])
    project_title = sanitize_filename(payload.get('name', 'untitled'))

    if not isinstance(target_parts, list) or len(target_parts) > 500:
        return jsonify({
            "success": False,
            "error": "Parts list must be an array of at most 500 items."
        }), 400

    try:
        from compiler.cir import CircuitIR
        cir = CircuitIR()
        for p in target_parts:
            cir.add_part(p["id"], p["role"], p["info"])

        backend = get_backend("SBOL")
        xml_data = backend.generate_xml(cir, circuit_name=project_title)

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


@app.route('/api/export/genbank', methods=['POST'])
@rate_limit
def handle_genbank_export():
    payload = request.get_json() or {}
    statement = payload.get('logic')
    project_title = sanitize_filename(payload.get('name', 'circuit'), 'circuit')

    try:
        if statement:
            pipeline = CompilerPipeline()
            cir, _ = pipeline.run(statement)
        else:
            target_parts = payload.get('parts', [])
            if not isinstance(target_parts, list) or len(target_parts) > 500:
                return jsonify({
                    "success": False,
                    "error": "Parts list must be an array of at most 500 items."
                }), 400
            from compiler.cir import CircuitIR
            cir = CircuitIR()
            for p in target_parts:
                cir.add_part(p["id"], p["role"], p["info"])

        backend = get_backend("GenBank")
        genbank_data = backend.generate(cir, circuit_name=project_title)

        return Response(
            genbank_data,
            mimetype='text/plain',
            headers={
                "Content-Disposition":
                    f"attachment; filename={project_title}.gb"
            }
        )

    except Exception as e:
        app.logger.exception("GenBank export failed")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/export/dna', methods=['POST'])
@rate_limit
def handle_dna_export():
    payload = request.get_json() or {}
    statement = payload.get('logic')
    project_title = sanitize_filename(payload.get('name', 'circuit'), 'circuit')

    try:
        if statement:
            pipeline = CompilerPipeline()
            cir, _ = pipeline.run(statement)
        else:
            target_parts = payload.get('parts', [])
            if not isinstance(target_parts, list) or len(target_parts) > 500:
                return jsonify({
                    "success": False,
                    "error": "Parts list must be an array of at most 500 items."
                }), 400
            from compiler.cir import CircuitIR
            cir = CircuitIR()
            for p in target_parts:
                cir.add_part(p["id"], p["role"], p["info"])

        backend = get_backend("DNA")
        fasta = backend.generate_fasta(cir, circuit_name=project_title)

        return Response(
            fasta,
            mimetype='text/plain',
            headers={
                "Content-Disposition":
                    f"attachment; filename={project_title}.fa"
            }
        )

    except Exception as e:
        app.logger.exception("DNA export failed")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/export/svg', methods=['POST'])
@rate_limit
def handle_svg_export():
    payload = request.get_json() or {}
    statement = payload.get('logic')
    project_title = sanitize_filename(payload.get('name', 'Circuit_Diagram'), 'Circuit_Diagram')

    try:
        if statement:
            pipeline = CompilerPipeline()
            cir, _ = pipeline.run(statement)
        else:
            target_parts = payload.get('parts', [])
            if not isinstance(target_parts, list) or len(target_parts) > 500:
                return jsonify({
                    "success": False,
                    "error": "Parts list must be an array of at most 500 items."
                }), 400
            from compiler.cir import CircuitIR
            cir = CircuitIR()
            for p in target_parts:
                cir.add_part(p["id"], p["role"], p["info"])

        backend = get_backend("SVG")
        svg = backend.generate_svg(cir, title=project_title)

        return Response(
            svg,
            mimetype='image/svg+xml',
            headers={
                "Content-Disposition":
                    f"attachment; filename={project_title}.svg"
            }
        )

    except Exception as e:
        app.logger.exception("SVG export failed")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/parts', methods=['GET'])
def fetch_parts_inventory():
    combined_keys = (
        list(GATES_DB.keys())
        + list(BIOMOLECULES.keys())
        + list(REPORTERS.keys())
    )
    return jsonify({
        "gates": combined_keys,
        "count": len(combined_keys)
    })


@app.route('/api/simulate', methods=['POST'])
@rate_limit
def handle_simulation():
    payload = request.get_json() or {}
    validation_errors = validate_input(payload)
    if validation_errors:
        return jsonify({"success": False, "error": validation_errors[0]}), 400
    statement = payload.get('logic')
    inputs = payload.get('inputs', {})
    t_span = payload.get('t_span', [0, 100])
    dt = payload.get('dt', 0.01)
    params = payload.get('params', {})

    if not statement:
        return jsonify({
            "success": False,
            "error": "Missing 'logic' field."
        }), 400

    try:
        from compiler.backends.simulation_backend import SimulationBackend
        pipeline = CompilerPipeline()
        cir, _ = pipeline.run(statement)
        backend = SimulationBackend(t_span=tuple(t_span), dt=dt)
        result = backend.generate(cir, inputs=inputs, params=params)
        result["success"] = True
        return jsonify(result)
    except SyntaxError as syn_ex:
        return jsonify({
            "success": False,
            "error": f"Syntax error: {str(syn_ex)}"
        }), 400
    except Exception as general_ex:
        app.logger.exception("Simulation failed")
        return jsonify({
            "success": False,
            "error": f"Simulation error: {str(general_ex)}"
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "cyto-logic-backend",
        "version": "0.1.0",
    })


@app.route('/api/optimize', methods=['POST'])
@rate_limit
def handle_optimization():
    payload = request.get_json() or {}
    validation_errors = validate_input(payload)
    if validation_errors:
        return jsonify({"success": False, "error": validation_errors[0]}), 400
    statement = payload.get('logic')
    inputs = payload.get('inputs', {})
    t_span = payload.get('t_span', [0, 100])
    dt = payload.get('dt', 1.0)
    pop_size = payload.get('pop_size', 50)
    generations = payload.get('generations', 20)
    target_output = payload.get('target_output', 10.0)

    if not statement:
        return jsonify({
            "success": False,
            "error": "Missing 'logic' field."
        }), 400

    try:
        from compiler.optimization import OptimizationRunner
        pipeline = CompilerPipeline()
        cir, _ = pipeline.run(statement)
        runner = OptimizationRunner(
            target_output=target_output,
            output_species=cir.output_protein,
            pop_size=pop_size,
            generations=generations,
        )
        result = runner.run(cir, inputs=inputs,
                            t_span=tuple(t_span), dt=dt)
        response = result.to_dict()
        response["success"] = True
        return jsonify(response)
    except SyntaxError as syn_ex:
        return jsonify({
            "success": False,
            "error": f"Syntax error: {str(syn_ex)}"
        }), 400
    except Exception as general_ex:
        app.logger.exception("Optimization failed")
        return jsonify({
            "success": False,
            "error": f"Optimization error: {str(general_ex)}"
        }), 500


if __name__ == '__main__':
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=int(os.environ.get("PORT", 5000)))
