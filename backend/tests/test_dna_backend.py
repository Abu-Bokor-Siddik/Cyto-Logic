import pytest
from compiler.cir import CircuitIR
from compiler.backends.dna_backend import DNABackend


class TestDNABackend:
    def test_name(self):
        assert DNABackend().name == "DNA"

    def test_empty_circuit_returns_fasta(self):
        ir = CircuitIR()
        backend = DNABackend()
        fasta = backend.generate(ir)
        assert fasta.startswith(">")

    def test_single_part(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP")
        backend = DNABackend()
        fasta = backend.generate(ir, circuit_name="test")
        assert ">test" in fasta
        assert ">BBa_E0040" in fasta
        assert "ATGCGT" in fasta

    def test_multiple_parts_concatenated(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet")
        ir.add_part("BBa_B0034", "RBS", "RBS")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        ir.add_part("BBa_B0015", "terminator", "terminator")
        backend = DNABackend()
        fasta = backend.generate(ir, circuit_name="construct")
        assert ">construct" in fasta
        assert ">BBa_R0040" in fasta
        assert ">BBa_B0034" in fasta
        assert ">BBa_E0040" in fasta
        assert ">BBa_B0015" in fasta

    def test_unknown_part_uses_placeholder(self):
        ir = CircuitIR()
        ir.add_part("BBa_UNKNOWN", "CDS", "Unknown")
        backend = DNABackend()
        fasta = backend.generate(ir)
        assert "N" in fasta

    def test_generate_fasta_alias(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP")
        backend = DNABackend()
        fasta = backend.generate_fasta(ir)
        assert fasta.startswith(">")

    def test_registry_contains_dna(self):
        from compiler.backends.registry import get, list_backends
        assert "DNA" in list_backends()
        backend = get("DNA")
        assert backend is not None
        assert backend.name == "DNA"

    def test_duplicate_parts_preserved_in_order(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        backend = DNABackend()
        fasta = backend.generate(ir)
        assert fasta.count(">BBa_E0040") == 2

    def test_circuit_name_in_construct_header(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP")
        backend = DNABackend()
        fasta = backend.generate(ir, circuit_name="my_circuit_v2")
        assert ">my_circuit_v2" in fasta

    def test_new_reporter_bfp_has_sequence(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0020", "CDS", "BFP")
        backend = DNABackend()
        fasta = backend.generate(ir)
        assert "BBa_E0020" in fasta
        assert len(fasta) > 100

    def test_new_reporter_yfp_has_sequence(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0030", "CDS", "YFP")
        backend = DNABackend()
        fasta = backend.generate(ir)
        assert "BBa_E0030" in fasta

    def test_new_promoter_plac_has_sequence(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0010", "promoter", "pLac")
        backend = DNABackend()
        fasta = backend.generate(ir)
        assert "BBa_R0010" in fasta

    def test_new_rbs_medium_has_sequence(self):
        ir = CircuitIR()
        ir.add_part("BBa_B0032", "RBS", "medium RBS")
        backend = DNABackend()
        fasta = backend.generate(ir)
        assert "BBa_B0032" in fasta
        assert "AAAGGAGGAAAA" in fasta
