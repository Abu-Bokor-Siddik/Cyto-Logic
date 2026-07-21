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
        result = map_circuit(ast)
        assert result is not None
        assert "circuit_structure" in result
        assert "connections" in result
        assert "dna_parts_list" in result
        assert len(result["dna_parts_list"]) > 0

    def test_not_gate_mapping(self):
        ast = Circuit(
            condition=NotGate(ProteinNode("aTc")),
            output=ProteinNode("GFP")
        )
        result = map_circuit(ast)
        part_ids = [p["id"] for p in result["dna_parts_list"]]
        assert "BBa_R0040" in part_ids
        assert "BBa_C0040" in part_ids

    def test_and_gate_mapping(self):
        ast = Circuit(
            condition=AndGate(ProteinNode("aTc"), ProteinNode("AraC")),
            output=ProteinNode("GFP")
        )
        result = map_circuit(ast)
        part_ids = [p["id"] for p in result["dna_parts_list"]]
        assert "BBa_K1847000" in part_ids

    def test_or_gate_mapping(self):
        ast = Circuit(
            condition=OrGate(ProteinNode("aTc"), ProteinNode("AraC")),
            output=ProteinNode("RFP")
        )
        result = map_circuit(ast)
        part_ids = [p["id"] for p in result["dna_parts_list"]]
        assert "BBa_K1847001" in part_ids
        assert "BBa_E0010" in part_ids

    def test_unknown_output_gets_custom_part(self):
        ast = Circuit(
            condition=ProteinNode("aTc"),
            output=ProteinNode("YFP")
        )
        result = map_circuit(ast)
        part_ids = [p["id"] for p in result["dna_parts_list"]]
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
        result = map_circuit(ast)
        assert len(result["circuit_structure"]) > 0
        assert len(result["connections"]) > 0

    def test_duplicate_parts_deduplicated(self):
        ast = Circuit(
            condition=AndGate(
                AndGate(ProteinNode("aTc"), ProteinNode("AraC")),
                ProteinNode("LacI")
            ),
            output=ProteinNode("GFP")
        )
        result = map_circuit(ast)
        part_ids = [p["id"] for p in result["dna_parts_list"]]
        assert len(part_ids) == len(set(part_ids))
