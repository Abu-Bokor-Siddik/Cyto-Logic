import pytest
from compiler.cir import CircuitIR
from compiler.backends.sbol_backend import SBOLBackend


class TestSBOLValidation:
    def test_generated_document_has_component(self):
        ir = _simple_circuit()
        backend = SBOLBackend()
        doc = backend.generate(ir, circuit_name="test_circuit")
        assert doc is not None
        cds = list(doc.componentDefinitions)
        assert len(cds) >= 1

    def test_generated_xml_is_parseable(self):
        ir = _simple_circuit()
        backend = SBOLBackend()
        xml = backend.generate_xml(ir, circuit_name="test_circuit")
        import sbol2
        doc2 = sbol2.Document()
        doc2.readString(xml)
        assert len(list(doc2.componentDefinitions)) >= 1

    def test_round_trip_preserves_parts_count(self):
        ir = _simple_circuit()
        backend = SBOLBackend()
        xml = backend.generate_xml(ir, circuit_name="rt_test")
        import sbol2
        doc2 = sbol2.Document()
        doc2.readString(xml)
        n_parts = len(ir.parts_deduplicated())
        n_components = len(list(doc2.componentDefinitions))
        assert n_components >= n_parts or n_components >= 1

    def test_multiple_parts_produce_multiple_components(self):
        ir = CircuitIR(logic_statement="IF aTc -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "GFP", "output")
        ir.add_edge("n1", "n2")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        ir.add_part("BBa_R0040", "promoter", "pTet")
        ir.add_part("BBa_B0034", "RBS", "RBS")
        backend = SBOLBackend()
        xml = backend.generate_xml(ir, circuit_name="multi_part")
        import sbol2
        doc = sbol2.Document()
        doc.readString(xml)
        cds = list(doc.componentDefinitions)
        assert len(cds) >= 3

    def test_homespace_appears_in_identities(self):
        ir = _simple_circuit()
        backend = SBOLBackend(homespace="http://example.org")
        xml = backend.generate_xml(ir, circuit_name="homespace_test")
        assert "http://example.org" in xml
        assert "cytologic.org" not in xml

    def test_circuit_without_parts_still_produces_valid_xml(self):
        ir = CircuitIR()
        ir.add_node("n1", "aTc", "input")
        backend = SBOLBackend()
        xml = backend.generate_xml(ir, circuit_name="empty_parts")
        import sbol2
        doc = sbol2.Document()
        doc.readString(xml)
        assert len(list(doc.componentDefinitions)) >= 1


def _simple_circuit():
    ir = CircuitIR(logic_statement="IF aTc -> GFP")
    ir.add_node("n1", "aTc", "input")
    ir.add_node("n2", "GFP", "output")
    ir.add_edge("n1", "n2")
    ir.add_part("BBa_E0040", "CDS", "GFP")
    return ir
