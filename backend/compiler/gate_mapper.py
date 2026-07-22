"""
Core responsibility
------------------------------------------------------------
Translate the validated AST into a biological circuit.
This mapper converts logic gates into BioBrick parts,
builds the circuit graph, selects compatible genetic
implementations, and prepares the final design for
SBOL export.

Design note
-------------------------------------------------------
I separated biological mapping from parsing so the
compiler stays independent of any specific genetic
implementation. New gate designs or BioBrick libraries
can be added by updating the mapping tables instead of
changing the compiler itself.
"""
from .ast_node import ProteinNode, NotGate, AndGate, OrGate, Circuit
from .parts_db import GATES_DB, BIOMOLECULES, REPORTERS
# Different inputs can use different biological implementations of the same logic gate.
GATE_IMPL_MAP = {
    "NOT": {
        "aTc": "TetR",
        "AraC": "LacI",
    },
}

class BioGateMapper:
    def __init__(self):
        self.graph_nodes = {}
        self.graph_edges = []
        self.final_parts = []
        self.counter = 0

    def map_circuit(self, circuit_ast):
        if circuit_ast is None:
            raise ValueError("Cannot map a null circuit AST.")

        self.traverse(circuit_ast.condition)

        out_name = circuit_ast.output.name

        if out_name in REPORTERS:
            self.final_parts.append(REPORTERS[out_name])
        else:
            self.final_parts.append({
                "id": "BBa_CUSTOM_CDS",
                "role": "CDS",
                "info": f"Custom CDS for {out_name}"
            })
        # The same BioBrick may appear more than once while traversing the circuit.
        # I remove duplicates before returning the final design.
        seen = set()
        deduplicated_parts = []
        for part in self.final_parts:
            part_id = part.get("id")
            if part_id not in seen:
                seen.add(part_id)
                deduplicated_parts.append(part)
        self.final_parts = deduplicated_parts

        return {
            "circuit_structure": self.graph_nodes,
            "connections": self.graph_edges,
            "dna_parts_list": self.final_parts,
            "complexity": len(self.final_parts)
        }
    # Fall back to TetR if no input-specific implementation has been defined.
    def _repressor_for_input(self, input_name):
        return GATE_IMPL_MAP.get("NOT", {}).get(input_name, "TetR")

    def traverse(self, node):
        if node is None:
            return None
        # Every AST node becomes a graph node so the frontend can rebuild the compiled circuit structure.
        current_id = f"gate_{self.counter}"
        self.counter += 1

        if isinstance(node, ProteinNode):
            node_info = {"label": node.name, "type": "input"}
            if node.name in BIOMOLECULES:
                node_info["biopart_id"] = BIOMOLECULES[node.name]["id"]

            self.graph_nodes[current_id] = node_info
            return current_id

        elif isinstance(node, NotGate):
            child_id = self.traverse(node.input)
            self.graph_nodes[current_id] = {"label": "NOT", "type": "gate"}
            if child_id:
                self.graph_edges.append((child_id, current_id))

            self.final_parts.extend(GATES_DB["NOT"])

            input_name = (
                node.input.name
                if isinstance(node.input, ProteinNode)
                else None
            )
            # Pick the repressor that matches the incoming biological signal.
            repressor_key = self._repressor_for_input(input_name)
            if repressor_key in BIOMOLECULES:
                self.final_parts.append(BIOMOLECULES[repressor_key])

            return current_id

        elif isinstance(node, AndGate):
            left_id = self.traverse(node.left)
            right_id = self.traverse(node.right)

            self.graph_nodes[current_id] = {"label": "AND", "type": "gate"}
            if left_id:
                self.graph_edges.append((left_id, current_id))
            if right_id:
                self.graph_edges.append((right_id, current_id))

            self.final_parts.extend(GATES_DB["AND"])
            return current_id

        elif isinstance(node, OrGate):
            left_id = self.traverse(node.left)
            right_id = self.traverse(node.right)

            self.graph_nodes[current_id] = {"label": "OR", "type": "gate"}
            if left_id:
                self.graph_edges.append((left_id, current_id))
            if right_id:
                self.graph_edges.append((right_id, current_id))

            self.final_parts.extend(GATES_DB["OR"])
            return current_id

        return None
