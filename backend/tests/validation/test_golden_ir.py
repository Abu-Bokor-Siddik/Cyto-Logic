import pytest
from compiler.pipeline import CompilerPipeline


def _compile(source):
    pipeline = CompilerPipeline()
    cir, messages = pipeline.run(source)
    return cir, messages


class TestGoldenIR:
    def test_simple_not_gate_structure(self):
        cir, msgs = _compile("IF NOT aTc -> GFP")
        assert cir.output_protein == "GFP"
        assert len(cir.nodes) == 2
        labels = [data.get("label") for _, data in cir.nodes]
        assert "NOT" in labels
        assert "aTc" in labels or "GFP" in labels
        assert len(cir.edges) == 1
        parts = cir.parts_deduplicated()
        assert len(parts) >= 2

    def test_and_gate_structure(self):
        cir, msgs = _compile("IF (aTc AND AraC) -> GFP")
        assert cir.output_protein == "GFP"
        assert len(cir.nodes) == 3
        assert len(cir.edges) == 2
        parts = cir.parts_deduplicated()
        assert len(parts) >= 3

    def test_or_gate_structure(self):
        cir, msgs = _compile("IF (aTc OR AraC) -> GFP")
        assert cir.output_protein == "GFP"
        assert len(cir.nodes) == 3
        assert len(cir.edges) == 2
        parts = cir.parts_deduplicated()
        assert len(parts) >= 3

    def test_complex_circuit(self):
        cir, msgs = _compile("IF (aTc AND (NOT AraC OR LacI)) -> RFP")
        assert cir.output_protein == "RFP"
        assert len(cir.nodes) >= 5
        assert len(cir.edges) >= 4
        parts = cir.parts_deduplicated()
        assert len(parts) >= 5

    def test_output_protein_is_correct(self):
        cir, msgs = _compile("IF aTc -> RFP")
        assert cir.output_protein == "RFP"

    def test_logic_statement_preserved(self):
        source = "IF aTc -> GFP"
        cir, msgs = _compile(source)
        assert cir.logic_statement == source

    def test_parts_contain_reporter(self):
        cir, msgs = _compile("IF aTc -> GFP")
        parts = cir.parts_deduplicated()
        part_ids = [p["id"] for p in parts]
        assert "BBa_E0040" in part_ids

    def test_parts_contain_gate_parts(self):
        cir, msgs = _compile("IF NOT aTc -> GFP")
        parts = cir.parts_deduplicated()
        part_ids = [p["id"] for p in parts]
        assert "BBa_B0034" in part_ids

    def test_no_semantic_errors_in_simple_circuit(self):
        cir, msgs = _compile("IF aTc -> GFP")
        errors = [m for m in msgs if m.severity == "error"]
        assert len(errors) == 0
