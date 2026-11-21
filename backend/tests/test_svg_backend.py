import pytest
from compiler.cir import CircuitIR
from compiler.backends.svg_backend import SVGBackend


class TestSVGBackend:
    def test_name(self):
        assert SVGBackend().name == "SVG"

    def test_empty_circuit_produces_svg(self):
        ir = CircuitIR()
        backend = SVGBackend()
        svg = backend.generate(ir)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")

    def test_simple_not_circuit(self):
        ir = CircuitIR(logic_statement="IF NOT aTc -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "NOT", "gate")
        ir.add_node("n3", "GFP", "output")
        ir.add_edge("n1", "n2")
        ir.add_edge("n2", "n3")
        ir.add_part("BBa_R0040", "promoter", "pTet")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        backend = SVGBackend()
        svg = backend.generate(ir, title="NOT Gate Test")
        assert "<svg" in svg
        assert "aTc" in svg
        assert "NOT" in svg
        assert "GFP" in svg
        assert "NOT Gate Test" in svg

    def test_and_circuit(self):
        ir = CircuitIR(logic_statement="IF (aTc AND AraC) -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "AraC", "input")
        ir.add_node("n3", "AND", "gate")
        ir.add_node("n4", "GFP", "output")
        ir.add_edge("n1", "n3")
        ir.add_edge("n2", "n3")
        ir.add_edge("n3", "n4")
        backend = SVGBackend()
        svg = backend.generate(ir)
        assert "AND" in svg

    def test_or_circuit(self):
        ir = CircuitIR(logic_statement="IF (aTc OR AraC) -> RFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "AraC", "input")
        ir.add_node("n3", "OR", "gate")
        ir.add_node("n4", "RFP", "output")
        ir.add_edge("n1", "n3")
        ir.add_edge("n2", "n3")
        ir.add_edge("n3", "n4")
        backend = SVGBackend()
        svg = backend.generate(ir)
        assert "OR" in svg
        assert "RFP" in svg

    def test_parts_table_rendered(self):
        ir = CircuitIR()
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "GFP", "output")
        ir.add_edge("n1", "n2")
        ir.add_part("BBa_E0040", "CDS", "GFP reporter")
        ir.add_part("BBa_B0034", "RBS", "Ribosome binding site")
        backend = SVGBackend()
        svg = backend.generate(ir)
        assert "DNA Parts" in svg
        assert "BBa_E0040" in svg
        assert "BBa_B0034" in svg
        assert "CDS" in svg
        assert "RBS" in svg

    def test_generate_svg_alias(self):
        ir = CircuitIR()
        ir.add_node("n1", "aTc", "input")
        backend = SVGBackend()
        svg = backend.generate_svg(ir, title="Test")
        assert "<svg" in svg

    def test_registry_contains_svg(self):
        from compiler.backends.registry import get, list_backends
        assert "SVG" in list_backends()
        backend = get("SVG")
        assert backend is not None
        assert backend.name == "SVG"

    def test_xml_escaping(self):
        ir = CircuitIR()
        ir.add_node("n1", "a<Tc", "input")
        backend = SVGBackend()
        svg = backend.generate(ir)
        assert "&lt;" in svg
        assert "a&lt;Tc" in svg

    def test_defs_has_arrowhead(self):
        ir = CircuitIR()
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "GFP", "output")
        ir.add_edge("n1", "n2")
        backend = SVGBackend()
        svg = backend.generate(ir)
        assert "arrowhead" in svg

    def test_complex_circuit_svg(self):
        ir = CircuitIR(logic_statement="IF (aTc AND (NOT AraC OR LacI)) -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "AraC", "input")
        ir.add_node("n3", "NOT", "gate")
        ir.add_node("n4", "OR", "gate")
        ir.add_node("n5", "AND", "gate")
        ir.add_node("n6", "GFP", "output")
        ir.add_edge("n1", "n5")
        ir.add_edge("n2", "n3")
        ir.add_edge("n3", "n4")
        ir.add_edge("n4", "n5")
        ir.add_edge("n5", "n6")
        backend = SVGBackend()
        svg = backend.generate(ir, title="Complex Circuit")
        assert "GGT;" not in svg
        assert "Complex Circuit" in svg
