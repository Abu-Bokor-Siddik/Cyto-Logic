import pytest
from compiler.cir import CircuitIR


class TestCircuitIR:
    def test_empty_cir(self):
        ir = CircuitIR()
        assert ir.logic_statement == ""
        assert ir.output_protein == ""
        assert ir.nodes == []
        assert ir.edges == []
        assert ir.parts_deduplicated() == []
        assert ir.complexity == 0

    def test_add_node(self):
        ir = CircuitIR()
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "AND", "gate")
        assert len(ir.nodes) == 2
        assert ir.get_node("n1") == {"label": "aTc", "type": "input"}

    def test_add_node_with_extra(self):
        ir = CircuitIR()
        ir.add_node("n1", "aTc", "input", biopart_id="BBa_K145001")
        assert ir.get_node("n1")["biopart_id"] == "BBa_K145001"

    def test_add_edge(self):
        ir = CircuitIR()
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "AND", "gate")
        ir.add_edge("n1", "n2")
        assert ir.edges == [("n1", "n2")]

    def test_add_part(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP reporter")
        ir.add_part("BBa_B0034", "RBS", "Strong RBS")
        assert len(ir.parts_deduplicated()) == 2

    def test_parts_deduplication(self):
        ir = CircuitIR()
        ir.add_part("BBa_B0034", "RBS", "Strong RBS")
        ir.add_part("BBa_B0034", "RBS", "Strong RBS")
        assert len(ir.parts_deduplicated()) == 1

    def test_complexity(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP")
        ir.add_part("BBa_B0034", "RBS", "RBS")
        assert ir.complexity == 2

    def test_to_dict(self):
        ir = CircuitIR(logic_statement="IF aTc -> GFP", output_protein="GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_edge("n1", "n2")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        d = ir.to_dict()
        assert "circuit_structure" in d
        assert "connections" in d
        assert "dna_parts_list" in d
        assert "complexity" in d
        assert d["complexity"] == 1

    def test_to_api_response(self):
        ir = CircuitIR(logic_statement="IF aTc -> GFP", output_protein="GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        resp = ir.to_api_response()
        assert resp["logic"] == "IF aTc -> GFP"
        assert resp["output_protein"] == "GFP"
        assert resp["complexity_score"] == 1
        assert "graph" in resp
        assert "nodes" in resp["graph"]
        assert "edges" in resp["graph"]

    def test_from_api_payload(self):
        payload = {
            "logic": "IF aTc -> GFP",
            "output_protein": "GFP",
            "graph": {
                "nodes": [["n1", {"label": "aTc", "type": "input"}]],
                "edges": [["n1", "n2"]],
            },
            "parts": [
                {"id": "BBa_E0040", "role": "CDS", "info": "GFP"}
            ],
        }
        ir = CircuitIR.from_api_payload(payload)
        assert ir.logic_statement == "IF aTc -> GFP"
        assert ir.output_protein == "GFP"
        assert len(ir.nodes) == 1
        assert ir.get_node("n1")["label"] == "aTc"

    def test_validate_empty(self):
        ir = CircuitIR()
        errors = ir.validate()
        assert len(errors) == 1
        assert "empty" in errors[0]

    def test_validate_orphan_edge(self):
        ir = CircuitIR()
        ir.add_edge("missing_source", "missing_target")
        errors = ir.validate()
        assert len(errors) == 3
        assert any("empty" in e for e in errors)
        assert any("missing_source" in e for e in errors)
        assert any("missing_target" in e for e in errors)

    def test_validate_clean(self):
        ir = CircuitIR()
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "GFP", "output")
        ir.add_edge("n1", "n2")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        assert ir.validate() == []

    def test_repr(self):
        ir = CircuitIR(logic_statement="IF aTc -> GFP")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        assert "CircuitIR" in repr(ir)
        assert "IF aTc -> GFP" in repr(ir)
