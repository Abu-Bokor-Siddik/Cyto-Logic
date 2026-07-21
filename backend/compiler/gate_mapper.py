from .ast_node import ProteinNode, NotGate, AndGate, OrGate, Circuit
from .parts_db import GATES_DB, BIOMOLECULES, REPORTERS

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

    def _repressor_for_input(self, input_name):
        return GATE_IMPL_MAP.get("NOT", {}).get(input_name, "TetR")

    def traverse(self, node):
        if node is None:
            return None
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
