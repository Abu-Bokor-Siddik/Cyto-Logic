import pytest
from compiler.cir import CircuitIR
from compiler.backends.sbol_backend import SBOLBackend


class TestSBOLBackend:
    def test_name(self):
        b = SBOLBackend()
        assert b.name == "SBOL"

    def test_generate_returns_document(self):
        ir = CircuitIR()
        ir.add_node("n1", "aTc", "input")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        b = SBOLBackend()
        doc = b.generate(ir)
        assert doc is not None

    def test_generate_xml_returns_string(self):
        ir = CircuitIR()
        ir.add_node("n1", "aTc", "input")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        b = SBOLBackend()
        xml = b.generate_xml(ir)
        assert isinstance(xml, str)
        assert len(xml) > 0

    def test_custom_homespace(self):
        b = SBOLBackend(homespace="http://example.com")
        assert b._homespace == "http://example.com"

    def test_empty_cir_produces_xml(self):
        ir = CircuitIR()
        b = SBOLBackend()
        xml = b.generate_xml(ir, circuit_name="empty_test")
        assert isinstance(xml, str)
        assert "empty_test" in xml

    def test_circuit_name_sanitized(self):
        ir = CircuitIR()
        ir.add_node("n1", "aTc", "input")
        b = SBOLBackend()
        xml = b.generate_xml(ir, circuit_name="My Circuit v2")
        assert "My_Circuit_v2" in xml
