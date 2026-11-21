import pytest
from compiler.ast_node import ProteinNode, NotGate, AndGate, OrGate, Circuit
from compiler.gate_mapper import BioGateMapper


def map_circuit(ast):
    mapper = BioGateMapper()
    return mapper.map_circuit(ast)


class TestBioGateMapper:
    def test_simple_circuit_mapping(self):
        ast = Circuit(
            condition=ProteinNode("aTc"),
            output=ProteinNode("GFP")
        )
        cir = map_circuit(ast)
        assert cir is not None
        assert len(cir.nodes) > 0
        assert len(cir.parts_deduplicated()) > 0
        assert cir.output_protein == "GFP"

    def test_not_gate_mapping(self):
        ast = Circuit(
            condition=NotGate(ProteinNode("aTc")),
            output=ProteinNode("GFP")
        )
        cir = map_circuit(ast)
        part_ids = [p["id"] for p in cir.parts_deduplicated()]
        assert "BBa_R0040" in part_ids
        assert "BBa_C0040" in part_ids

    def test_and_gate_mapping(self):
        ast = Circuit(
            condition=AndGate(ProteinNode("aTc"), ProteinNode("AraC")),
            output=ProteinNode("GFP")
        )
        cir = map_circuit(ast)
        part_ids = [p["id"] for p in cir.parts_deduplicated()]
        assert "BBa_K1847000" in part_ids

    def test_or_gate_mapping(self):
        ast = Circuit(
            condition=OrGate(ProteinNode("aTc"), ProteinNode("AraC")),
            output=ProteinNode("RFP")
        )
        cir = map_circuit(ast)
        part_ids = [p["id"] for p in cir.parts_deduplicated()]
        assert "BBa_K1847001" in part_ids
        assert "BBa_E0010" in part_ids

    def test_unknown_output_custom_part(self):
        ast = Circuit(
            condition=ProteinNode("aTc"),
            output=ProteinNode("UnknownR")
        )
        cir = map_circuit(ast)
        part_ids = [p["id"] for p in cir.parts_deduplicated()]
        assert "BBa_CUSTOM_CDS" in part_ids

    def test_none_input_raises_error(self):
        mapper = BioGateMapper()
        with pytest.raises(ValueError, match="null circuit"):
            mapper.map_circuit(None)

    def test_complex_circuit_graph_structure(self):
        ast = Circuit(
            condition=AndGate(
                ProteinNode("aTc"),
                NotGate(ProteinNode("AraC"))
            ),
            output=ProteinNode("GFP")
        )
        cir = map_circuit(ast)
        assert len(cir.nodes) > 0
        assert len(cir.edges) > 0

    def test_duplicate_parts_deduplicated(self):
        ast = Circuit(
            condition=AndGate(
                AndGate(ProteinNode("aTc"), ProteinNode("AraC")),
                ProteinNode("LacI")
            ),
            output=ProteinNode("GFP")
        )
        cir = map_circuit(ast)
        part_ids = [p["id"] for p in cir.parts_deduplicated()]
        assert len(part_ids) == len(set(part_ids))

    def test_to_dict_backward_compat(self):
        ast = Circuit(
            condition=ProteinNode("aTc"),
            output=ProteinNode("GFP")
        )
        cir = map_circuit(ast)
        d = cir.to_dict()
        assert "circuit_structure" in d
        assert "connections" in d
        assert "dna_parts_list" in d
        assert "complexity" in d

    def test_to_api_response(self):
        ast = Circuit(
            condition=ProteinNode("aTc"),
            output=ProteinNode("GFP")
        )
        mapper = BioGateMapper()
        cir = mapper.map_circuit(ast, logic_statement="IF aTc -> GFP")
        resp = cir.to_api_response()
        assert resp["logic"] == "IF aTc -> GFP"
        assert resp["output_protein"] == "GFP"
        assert "graph" in resp
