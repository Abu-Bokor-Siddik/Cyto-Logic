import pytest
from compiler.pipeline import CompilerPipeline
from compiler.parts_db import GATES_DB, BIOMOLECULES, REPORTERS


def _compile(source):
    pipeline = CompilerPipeline()
    cir, messages = pipeline.run(source)
    return cir, messages


class TestBiologicalVerification:
    def test_not_gate_uses_correct_repressor(self):
        cir, msgs = _compile("IF NOT aTc -> GFP")
        parts = cir.parts_deduplicated()
        part_ids = [p["id"] for p in parts]
        assert "BBa_C0040" in part_ids, (
            "NOT gate with aTc should include TetR repressor (BBa_C0040)"
        )
        assert "BBa_R0040" in part_ids, (
            "NOT gate should include pTet promoter (BBa_R0040)"
        )

    def test_not_gate_with_araC_uses_lacI_repressor(self):
        cir, msgs = _compile("IF NOT AraC -> RFP")
        parts = cir.parts_deduplicated()
        part_ids = [p["id"] for p in parts]
        assert "BBa_C0012" in part_ids, (
            "NOT gate with AraC should include LacI repressor (BBa_C0012)"
        )

    def test_gfp_reporter_present(self):
        cir, msgs = _compile("IF aTc -> GFP")
        parts = cir.parts_deduplicated()
        part_ids = [p["id"] for p in parts]
        assert "BBa_E0040" in part_ids

    def test_rfp_reporter_present(self):
        cir, msgs = _compile("IF aTc -> RFP")
        parts = cir.parts_deduplicated()
        part_ids = [p["id"] for p in parts]
        assert "BBa_E0010" in part_ids

    def test_and_gate_uses_split_activator(self):
        cir, msgs = _compile("IF (aTc AND AraC) -> GFP")
        parts = cir.parts_deduplicated()
        part_ids = [p["id"] for p in parts]
        assert "BBa_K1847000" in part_ids, (
            "AND gate should use split-activator promoter (BBa_K1847000)"
        )

    def test_or_gate_uses_dual_promoter(self):
        cir, msgs = _compile("IF (aTc OR AraC) -> GFP")
        parts = cir.parts_deduplicated()
        part_ids = [p["id"] for p in parts]
        assert "BBa_K1847001" in part_ids, (
            "OR gate should use dual promoter (BBa_K1847001)"
        )

    def test_known_inputs_are_in_biomolecules(self):
        inputs = ["aTc", "AraC"]
        for inp in inputs:
            assert inp in BIOMOLECULES, (
                f"Expected {inp} in BIOMOLECULES database"
            )

    def test_known_reporters_are_in_database(self):
        reporters = ["GFP", "RFP"]
        for r in reporters:
            assert r in REPORTERS, (
                f"Expected {r} in REPORTERS database"
            )

    def test_gates_have_expected_structure(self):
        for gate_name in ["NOT", "AND", "OR"]:
            assert gate_name in GATES_DB
            parts = GATES_DB[gate_name]
            assert len(parts) >= 2

    def test_ribosome_binding_site_present_in_all_gates(self):
        for gate_name, parts in GATES_DB.items():
            part_ids = [p["id"] for p in parts]
            assert "BBa_B0034" in part_ids, (
                f"{gate_name} gate missing RBS (BBa_B0034)"
            )

    def test_terminator_present_in_final_ir(self):
        from compiler.ir_builder import IRBuilder
        from compiler.ast_node import ProteinNode, AndGate, Circuit
        ast = Circuit(
            condition=AndGate(ProteinNode("aTc"), ProteinNode("AraC")),
            output=ProteinNode("GFP"),
        )
        ir = IRBuilder(logic_statement="aTc AND AraC").build(ast)
        part_ids = [p["id"] for p in ir.parts_deduplicated()]
        assert "BBa_B0015" in part_ids, "Final circuit IR missing terminator (BBa_B0015)"
        assert part_ids[-1] == "BBa_B0015", "Terminator must be the last part in the sequence"

    def test_regulatory_map_has_expected_keys(self):
        from compiler.parts_db import REGULATORY_MAP
        assert "TetR_protein" in REGULATORY_MAP
        assert "aTc_inducer" in REGULATORY_MAP
        assert REGULATORY_MAP["TetR_protein"]["action"] == "repress"
        assert REGULATORY_MAP["aTc_inducer"]["action"] == "inhibit_repressor"
        assert "IPTG_inducer" in REGULATORY_MAP
        assert "LuxR_protein" in REGULATORY_MAP

    def test_nand_gate_defined(self):
        assert "NAND" in GATES_DB

    def test_nor_gate_defined(self):
        assert "NOR" in GATES_DB

    def test_new_reporters_are_in_database(self):
        for r in ["BFP", "YFP", "mCherry", "LacZ"]:
            assert r in REPORTERS, f"Expected {r} in REPORTERS database"

    def test_new_biomolecules_are_in_database(self):
        for b in ["IPTG", "HSL", "AraC_activator", "LuxR"]:
            assert b in BIOMOLECULES, f"Expected {b} in BIOMOLECULES database"
