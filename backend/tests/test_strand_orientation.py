import pytest
from compiler.utils import reverse_complement
from compiler.cir import CircuitIR
from compiler.backends.dna_backend import DNABackend, _get_sequence
from compiler.backends.genbank_backend import GenBankBackend


class TestReverseComplement:
    def test_simple_atgc(self):
        assert reverse_complement("ATGC") == "GCAT"

    def test_palindrome_tata(self):
        assert reverse_complement("TATA") == "TATA"

    def test_empty_string(self):
        assert reverse_complement("") == ""

    def test_lowercase_input(self):
        assert reverse_complement("aatt") == "AATT"

    def test_mixed_case(self):
        assert reverse_complement("AtGc") == "GCAT"

    def test_longer_sequence(self):
        seq = "AGCTTAGCTAG"
        expected = "CTAGCTAAGCT"
        assert reverse_complement(seq) == expected


class TestStrandInCircuitIR:
    def test_add_part_defaults_to_plus(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet")
        part = ir.all_parts[0]
        assert part["strand"] == "+"

    def test_add_part_explicit_minus(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet", strand="-")
        part = ir.all_parts[0]
        assert part["strand"] == "-"

    def test_add_part_explicit_plus(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet", strand="+")
        part = ir.all_parts[0]
        assert part["strand"] == "+"

    def test_mixed_strand_parts(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet", strand="+")
        ir.add_part("BBa_B0034", "RBS", "RBS", strand="-")
        parts = ir.all_parts
        assert parts[0]["strand"] == "+"
        assert parts[1]["strand"] == "-"

    def test_from_api_payload_accepts_strand(self):
        payload = {
            "parts": [
                {"id": "BBa_R0040", "role": "promoter", "info": "pTet", "strand": "-"}
            ]
        }
        ir = CircuitIR.from_api_payload(payload)
        assert ir.all_parts[0]["strand"] == "-"

    def test_from_api_payload_defaults_to_plus(self):
        payload = {
            "parts": [
                {"id": "BBa_R0040", "role": "promoter", "info": "pTet"}
            ]
        }
        ir = CircuitIR.from_api_payload(payload)
        assert ir.all_parts[0]["strand"] == "+"


class TestDNABackendStrand:
    def test_forward_strand_fasta(self):
        ir = CircuitIR()
        ir.add_part("BBa_B0034", "RBS", "strong RBS", strand="+")
        backend = DNABackend()
        fasta = backend.generate(ir)
        fwd_seq = _get_sequence("BBa_B0034")
        assert fwd_seq in fasta

    def test_reverse_strand_has_revcomp(self):
        ir = CircuitIR()
        ir.add_part("BBa_B0034", "RBS", "strong RBS", strand="-")
        backend = DNABackend()
        fasta = backend.generate(ir)
        fwd_seq = _get_sequence("BBa_B0034")
        rev_seq = reverse_complement(fwd_seq)
        assert rev_seq in fasta
        assert fwd_seq not in fasta

    def test_construct_uses_revcomp_for_minus(self):
        ir = CircuitIR()
        ir.add_part("BBa_B0034", "RBS", "RBS", strand="-")
        backend = DNABackend()
        fasta = backend.generate(ir, circuit_name="test_rev")
        lines = fasta.split("\n")
        construct_line = lines[1]
        expected = reverse_complement(_get_sequence("BBa_B0034"))
        # The construct line (index 1) should be the full assembled sequence
        assert construct_line == expected

    def test_mixed_strand_construct(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet", strand="+")
        ir.add_part("BBa_B0034", "RBS", "RBS", strand="-")
        backend = DNABackend()
        fasta = backend.generate(ir)
        lines = fasta.split("\n")
        construct = lines[1]
        expected = (
            _get_sequence("BBa_R0040")
            + reverse_complement(_get_sequence("BBa_B0034"))
        )
        assert construct == expected

    def test_part_header_shows_strand_tag(self):
        ir = CircuitIR()
        ir.add_part("BBa_B0034", "RBS", "strong RBS", strand="-")
        backend = DNABackend()
        fasta = backend.generate(ir)
        assert "[strand=-]" in fasta


class TestGenBankBackendStrand:
    def test_forward_feature_location(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet", strand="+")
        backend = GenBankBackend()
        output = backend.generate(ir)
        seq_len = len(_get_sequence("BBa_R0040"))
        assert f"1..{seq_len}" in output

    def test_reverse_feature_is_complement(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet", strand="-")
        backend = GenBankBackend()
        output = backend.generate(ir)
        seq_len = len(_get_sequence("BBa_R0040"))
        assert f"complement(1..{seq_len})" in output

    def test_reverse_feature_not_plain_coords(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet", strand="-")
        backend = GenBankBackend()
        output = backend.generate(ir)
        seq_len = len(_get_sequence("BBa_R0040"))
        assert f" 1..{seq_len}" not in output

    def test_mixed_strand_locations(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet", strand="+")
        ir.add_part("BBa_B0034", "RBS", "RBS", strand="-")
        backend = GenBankBackend()
        output = backend.generate(ir)
        p_len = len(_get_sequence("BBa_R0040"))
        r_len = len(_get_sequence("BBa_B0034"))
        assert f"1..{p_len}" in output
        r_start = p_len + 1
        r_end = p_len + r_len
        assert f"complement({r_start}..{r_end})" in output

    def test_reverse_strand_total_length(self):
        ir = CircuitIR()
        ir.add_part("BBa_B0034", "RBS", "RBS", strand="-")
        backend = GenBankBackend()
        output = backend.generate(ir)
        seq_len = len(_get_sequence("BBa_B0034"))
        assert f"{seq_len} bp" in output

    def test_origin_uses_revcomp_for_minus(self):
        ir = CircuitIR()
        seq = _get_sequence("BBa_B0034")
        ir.add_part("BBa_B0034", "RBS", "RBS", strand="-")
        backend = GenBankBackend()
        output = backend.generate(ir)
        rev_seq = reverse_complement(seq)
        origin_start = output.index("ORIGIN") + len("ORIGIN")
        origin_section = output[origin_start:]
        end_slash = origin_section.index("//")
        origin_section = origin_section[:end_slash]
        origin_bases = "".join(c for c in origin_section if c.isalpha())
        assert origin_bases == rev_seq.lower()