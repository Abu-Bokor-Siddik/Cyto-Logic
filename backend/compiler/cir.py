class CircuitIR:
    def __init__(self, logic_statement=None, output_protein=None):
        self.logic_statement = logic_statement or ""
        self.output_protein = output_protein or ""
        self._nodes = {}
        self._edges = []
        self._parts = []
        self._metadata = {}

    def add_node(self, node_id, label, node_type, **extra):
        entry = {"label": label, "type": node_type}
        entry.update(extra)
        self._nodes[node_id] = entry

    def set_node(self, node_id, entry):
        self._nodes[node_id] = entry

    def get_node(self, node_id):
        return self._nodes.get(node_id)

    def add_edge(self, source_id, target_id):
        self._edges.append((source_id, target_id))

    def add_part(self, part_id, role, info, strand="+"):
        self._parts.append({"id": part_id, "role": role, "info": info, "strand": strand})

    @property
    def all_parts(self):
        return list(self._parts)

    def parts_deduplicated(self):
        seen = set()
        result = []
        for p in self._parts:
            pid = p.get("id")
            if pid not in seen:
                seen.add(pid)
                result.append(p)
        return result

    @property
    def complexity(self):
        return len(self.parts_deduplicated())

    @property
    def nodes(self):
        return list(self._nodes.items())

    @property
    def edges(self):
        return list(self._edges)

    def to_dict(self):
        return {
            "circuit_structure": dict(self._nodes),
            "connections": list(self._edges),
            "dna_parts_list": self.all_parts,
            "complexity": self.complexity,
        }

    def to_api_response(self):
        return {
            "logic": self.logic_statement,
            "parts": self.all_parts,
            "complexity_score": self.complexity,
            "output_protein": self.output_protein,
            "graph": {
                "nodes": list(self._nodes.items()),
                "edges": list(self._edges),
            },
        }

    @classmethod
    def from_api_payload(cls, payload):
        ir = cls(
            logic_statement=payload.get("logic", ""),
            output_protein=payload.get("output_protein", ""),
        )
        for node_id, data in payload.get("graph", {}).get("nodes", []):
            data = dict(data)
            node_type = data.pop("type", "unknown")
            ir.add_node(node_id, data.pop("label", node_id), node_type, **data)
        for source, target in payload.get("graph", {}).get("edges", []):
            ir.add_edge(source, target)
        for part in payload.get("parts", []):
            ir.add_part(part["id"], part["role"], part["info"],
                        strand=part.get("strand", "+"))
        return ir

    def validate(self):
        errors = []
        if not self._nodes and not self._parts:
            errors.append("CircuitIR is empty: no nodes and no parts.")
        node_ids = set(self._nodes.keys())
        for source, target in self._edges:
            if source not in node_ids:
                errors.append(f"Edge references unknown source node: {source}")
            if target not in node_ids:
                errors.append(f"Edge references unknown target node: {target}")
        return errors

    def __repr__(self):
        return (
            f"CircuitIR(logic={self.logic_statement!r}, "
            f"nodes={len(self._nodes)}, "
            f"parts={self.complexity})"
        )
