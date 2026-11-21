from .ast_node import ProteinNode, NotGate, AndGate, OrGate, Circuit
from .parts_db import GATES_DB, BIOMOLECULES, REPORTERS, REGULATORY_MAP
from .cir import CircuitIR

_GATE_IMPL_MAP = None


def _build_gate_map():
    map_data = {"NOT": {}}
    regulatory_rules = {
        k.lower(): v for k, v in REGULATORY_MAP.items()
    }
    for entry_name, rule in regulatory_rules.items():
        target_protein = rule.get("target_protein", "")
        action = rule.get("action", "")
        if action == "inhibit_repressor" and target_protein:
            inducer_name = entry_name.replace("_inducer", "")
            for bio_name, bio_info in BIOMOLECULES.items():
                if bio_name.lower() == inducer_name:
                    map_data["NOT"][bio_name] = target_protein
    if "AraC" not in map_data["NOT"]:
        map_data["NOT"]["AraC"] = "LacI"
    return map_data


def get_gate_map():
    global _GATE_IMPL_MAP
    if _GATE_IMPL_MAP is None:
        _GATE_IMPL_MAP = _build_gate_map()
    return _GATE_IMPL_MAP


class IRBuilder:
    def __init__(self, logic_statement=None):
        self.logic_statement = logic_statement or ""
        self._counter = 0

    def build(self, circuit_ast):
        ir = CircuitIR(
            logic_statement=self.logic_statement,
            output_protein=circuit_ast.output.name,
        )

        self._traverse(circuit_ast.condition, ir)

        out_name = circuit_ast.output.name
        ir.add_part(
            "BBa_B0034", "RBS", "Strong RBS"
        )
        if out_name in REPORTERS:
            ir.add_part(
                REPORTERS[out_name]["id"],
                REPORTERS[out_name]["role"],
                REPORTERS[out_name]["info"],
            )
        else:
            ir.add_part(
                "BBa_CUSTOM_CDS",
                "CDS",
                f"Custom CDS for {out_name}",
            )

        ir.add_part(
            "BBa_B0015",
            "terminator",
            "Double terminator",
        )

        return ir

    def _next_id(self):
        nid = f"gate_{self._counter}"
        self._counter += 1
        return nid

    def _traverse(self, node, ir):
        if node is None:
            return None

        current_id = self._next_id()

        if isinstance(node, ProteinNode):
            node_info = {"label": node.name, "type": "input"}
            if node.name in BIOMOLECULES:
                node_info["biopart_id"] = BIOMOLECULES[node.name]["id"]
            ir.set_node(current_id, node_info)
            return current_id

        elif isinstance(node, NotGate):
            child_id = self._traverse(node.input, ir)
            ir.set_node(current_id, {"label": "NOT", "type": "gate"})
            if child_id:
                ir.add_edge(child_id, current_id)
            for part in GATES_DB["NOT"]:
                ir.add_part(part["id"], part["role"], part["info"])
            input_name = (
                node.input.name
                if isinstance(node.input, ProteinNode)
                else None
            )
            gate_map = get_gate_map()
            repressor_key = gate_map.get("NOT", {}).get(input_name, "TetR")
            if repressor_key in BIOMOLECULES:
                r = BIOMOLECULES[repressor_key]
                ir.add_part(r["id"], r["role"], r["info"])
            return current_id

        elif isinstance(node, AndGate):
            left_id = self._traverse(node.left, ir)
            right_id = self._traverse(node.right, ir)
            ir.add_node(current_id, "AND", "gate")
            if left_id:
                ir.add_edge(left_id, current_id)
            if right_id:
                ir.add_edge(right_id, current_id)
            for part in GATES_DB["AND"]:
                ir.add_part(part["id"], part["role"], part["info"])
            return current_id

        elif isinstance(node, OrGate):
            left_id = self._traverse(node.left, ir)
            right_id = self._traverse(node.right, ir)
            ir.add_node(current_id, "OR", "gate")
            if left_id:
                ir.add_edge(left_id, current_id)
            if right_id:
                ir.add_edge(right_id, current_id)
            for part in GATES_DB["OR"]:
                ir.add_part(part["id"], part["role"], part["info"])
            return current_id

        return None

    def traverse_graph_node(self, gate_type, input_ids, ir):
        current_id = self._next_id()
        ir.add_node(current_id, gate_type, "gate")
        for in_id in input_ids:
            if in_id:
                ir.add_edge(in_id, current_id)
        gate_key = gate_type if isinstance(gate_type, str) else gate_type.upper()
        if gate_key in GATES_DB:
            for part in GATES_DB[gate_key]:
                ir.add_part(part["id"], part["role"], part["info"])
        return current_id
