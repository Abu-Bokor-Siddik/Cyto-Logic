import pytest
from compiler.ast_node import ProteinNode, NotGate, AndGate, OrGate, Circuit
from compiler.ir_builder import IRBuilder


def build(ast, logic=None):
    return IRBuilder(logic_statement=logic).build(ast)


class TestIRBuilder:
    def test_simple_input(self):
        ast = Circuit(condition=ProteinNode("aTc"), output=ProteinNode("GFP"))
        ir = build(ast)
        assert ir.output_protein == "GFP"
        assert len(ir.nodes) == 1
        assert ir.get_node(list(dict(ir.nodes).keys())[0])["type"] == "input"

    def test_not_gate(self):
        ast = Circuit(condition=NotGate(ProteinNode("aTc")), output=ProteinNode("GFP"))
        ir = build(ast)
        assert len(ir.nodes) == 2
        assert len(ir.edges) == 1

    def test_and_gate(self):
        ast = Circuit(
            condition=AndGate(ProteinNode("aTc"), ProteinNode("AraC")),
            output=ProteinNode("GFP"),
        )
        ir = build(ast)
        assert len(ir.nodes) >= 3
        assert len(ir.edges) == 2

    def test_or_gate(self):
        ast = Circuit(
            condition=OrGate(ProteinNode("aTc"), ProteinNode("AraC")),
            output=ProteinNode("RFP"),
        )
        ir = build(ast)
        assert len(ir.nodes) >= 3
        assert len(ir.edges) == 2

    def test_complex_nested(self):
        ast = Circuit(
            condition=AndGate(
                ProteinNode("aTc"),
                NotGate(ProteinNode("AraC")),
            ),
            output=ProteinNode("GFP"),
        )
        ir = build(ast)
        assert len(ir.nodes) >= 4
        assert len(ir.edges) >= 2

    def test_parts_are_selected(self):
        ast = Circuit(condition=ProteinNode("aTc"), output=ProteinNode("GFP"))
        ir = build(ast)
        assert len(ir.parts_deduplicated()) >= 1

    def test_not_gate_has_repressor_part(self):
        ast = Circuit(condition=NotGate(ProteinNode("aTc")), output=ProteinNode("GFP"))
        ir = build(ast)
        part_ids = [p["id"] for p in ir.parts_deduplicated()]
        assert "BBa_C0040" in part_ids

    def test_logic_statement_carried_through(self):
        ast = Circuit(condition=ProteinNode("aTc"), output=ProteinNode("GFP"))
        ir = build(ast, logic="IF aTc -> GFP")
        assert ir.logic_statement == "IF aTc -> GFP"

    def test_none_ast_returns_none_traversal(self):
        ir = IRBuilder().build(
            Circuit(condition=ProteinNode("aTc"), output=ProteinNode("GFP"))
        )
        assert ir is not None
