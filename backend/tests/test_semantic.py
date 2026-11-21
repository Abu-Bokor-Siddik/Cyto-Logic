import pytest
from compiler.ast_node import ProteinNode, NotGate, AndGate, OrGate, Circuit
from compiler.semantic import SemanticAnalyzer, SemanticMessage


def analyze(ast):
    return SemanticAnalyzer().analyze(ast)


def errors(msgs):
    return [m for m in msgs if m.severity == "error"]


def warnings(msgs):
    return [m for m in msgs if m.severity == "warning"]


class TestSemanticAnalyzer:
    def test_null_ast(self):
        msgs = analyze(None)
        assert len(errors(msgs)) == 1
        assert "empty" in errors(msgs)[0].message.lower()

    def test_valid_simple_circuit(self):
        ast = Circuit(
            condition=ProteinNode("aTc"),
            output=ProteinNode("GFP"),
        )
        msgs = analyze(ast)
        assert len(msgs) == 0

    def test_valid_complex_circuit(self):
        ast = Circuit(
            condition=AndGate(
                ProteinNode("aTc"),
                NotGate(ProteinNode("AraC")),
            ),
            output=ProteinNode("GFP"),
        )
        msgs = analyze(ast)
        assert len(msgs) == 0

    def test_unknown_output_warning(self):
        ast = Circuit(
            condition=ProteinNode("aTc"),
            output=ProteinNode("UnknownR"),
        )
        msgs = analyze(ast)
        assert any("UnknownR" in w.message for w in warnings(msgs))

    def test_undefined_protein_warning(self):
        ast = Circuit(
            condition=ProteinNode("UnknownProtein"),
            output=ProteinNode("GFP"),
        )
        msgs = analyze(ast)
        assert len(warnings(msgs)) >= 1
        assert any("UnknownProtein" in w.message for w in warnings(msgs))

    def test_empty_output_name_error(self):
        ast = Circuit(
            condition=ProteinNode("aTc"),
            output=ProteinNode(""),
        )
        msgs = analyze(ast)
        assert len(errors(msgs)) >= 1
        assert any("no name" in e.message.lower() for e in errors(msgs))

    def test_not_gate_with_null_input(self):
        ast = Circuit(
            condition=NotGate(None),
            output=ProteinNode("GFP"),
        )
        msgs = analyze(ast)
        assert len(errors(msgs)) >= 1
        assert any("no input" in e.message.lower() for e in errors(msgs))

    def test_and_gate_with_null_input(self):
        ast = Circuit(
            condition=AndGate(None, ProteinNode("aTc")),
            output=ProteinNode("GFP"),
        )
        msgs = analyze(ast)
        assert len(errors(msgs)) >= 1

    def test_or_gate_with_null_input(self):
        ast = Circuit(
            condition=OrGate(ProteinNode("aTc"), None),
            output=ProteinNode("GFP"),
        )
        msgs = analyze(ast)
        assert len(errors(msgs)) >= 1

    def test_deeply_nested_circuit(self):
        node = ProteinNode("aTc")
        for _ in range(60):
            node = NotGate(node)
        ast = Circuit(condition=node, output=ProteinNode("GFP"))
        msgs = analyze(ast)
        assert len(errors(msgs)) >= 1
        assert any("depth" in e.message.lower() for e in errors(msgs))

    def test_duplicate_protein_only_reported_once(self):
        ast = Circuit(
            condition=AndGate(
                ProteinNode("aTc"),
                ProteinNode("aTc"),
            ),
            output=ProteinNode("GFP"),
        )
        msgs = analyze(ast)
        msgs_about_atc = [
            m for m in msgs if m.node_name == "aTc"
        ]
        assert len(msgs_about_atc) <= 1

    def test_semantic_message_to_dict(self):
        msg = SemanticMessage("test error", "error", "X")
        d = msg.to_dict()
        assert d["message"] == "test error"
        assert d["severity"] == "error"
        assert d["node"] == "X"

    def test_semantic_message_equality(self):
        a = SemanticMessage("msg", "error", "X")
        b = SemanticMessage("msg", "error", "X")
        assert a == b
