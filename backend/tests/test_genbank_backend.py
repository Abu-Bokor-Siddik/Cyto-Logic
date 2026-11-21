import pytest
from compiler.cir import CircuitIR
from compiler.backends.genbank_backend import GenBankBackend, _format_origin, ROLE_FEATURE_KEY
from compiler.backends.registry import get, list_backends
from compiler.backends.dna_backend import PART_SEQUENCES, FALLBACK_SEQUENCE


class TestGenBankBackend:
    def setup_method(self):
        self.backend = GenBankBackend()

    def test_name(self):
        assert self.backend.name == "GenBank"

    def test_empty_circuit(self):
        ir = CircuitIR()
        result = self.backend.generate(ir)
        assert "LOCUS" in result
        assert "0 bp" in result
        assert "//" in result

    def test_single_part(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP")
        result = self.backend.generate(ir, circuit_name="test_construct")
        assert "LOCUS" in result
        assert "test_construct" in result
        expected = len(PART_SEQUENCES["BBa_E0040"])
        assert f"{expected} bp" in result

    def test_locus_contains_length(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet")
        ir.add_part("BBa_B0034", "RBS", "Strong RBS")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        result = self.backend.generate(ir, circuit_name="circuit")
        expected_len = (
            len(PART_SEQUENCES["BBa_R0040"])
            + len(PART_SEQUENCES["BBa_B0034"])
            + len(PART_SEQUENCES["BBa_E0040"])
        )
        assert f"{expected_len} bp" in result

    def test_locus_contains_date(self):
        import re
        from datetime import date
        ir = CircuitIR()
        ir.add_part("BBa_B0034", "RBS", "Strong RBS")
        result = self.backend.generate(ir)
        today = date.today().strftime("%d-%b-%Y").upper()
        assert today in result

    def test_locus_contains_ds_dna_linear(self):
        ir = CircuitIR()
        ir.add_part("BBa_B0034", "RBS", "Strong RBS")
        result = self.backend.generate(ir)
        assert "ds-DNA" in result
        assert "linear" in result

    def test_definition_line(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP")
        result = self.backend.generate(ir)
        assert "DEFINITION" in result
        assert "Synthetic genetic circuit" in result

    def test_feature_coordinates_promoter(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet")
        result = self.backend.generate(ir)
        seq_len = len(PART_SEQUENCES["BBa_R0040"])
        assert f"1..{seq_len}" in result
        assert "promoter" in result

    def test_feature_coordinates_cumulative(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet")
        ir.add_part("BBa_B0034", "RBS", "Strong RBS")
        result = self.backend.generate(ir)
        p_len = len(PART_SEQUENCES["BBa_R0040"])
        r_len = len(PART_SEQUENCES["BBa_B0034"])
        assert f"1..{p_len}" in result
        assert f"{p_len + 1}..{p_len + r_len}" in result

    def test_feature_keys_role_mapping(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet")
        ir.add_part("BBa_B0034", "RBS", "Strong RBS")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        ir.add_part("BBa_B0015", "terminator", "terminator")
        result = self.backend.generate(ir)
        assert "promoter" in result
        assert "misc_binding" in result
        assert "CDS" in result
        assert "terminator" in result

    def test_feature_qualifiers(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet promoter")
        result = self.backend.generate(ir)
        assert '/label="BBa_R0040"' in result
        assert '/note="pTet promoter"' in result
        assert '/gene="BBa_R0040"' in result

    def test_origin_section_exists(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP")
        result = self.backend.generate(ir)
        assert "ORIGIN" in result

    def test_origin_formatting_60bp_lines(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP")
        result = self.backend.generate(ir)
        origin_start = result.index("ORIGIN")
        origin_section = result[origin_start:]
        lines = origin_section.split("\n")
        data_lines = [
            l for l in lines[1:] if l.strip() and not l.startswith("//")
        ]
        for line in data_lines:
            parts_after_num = line.strip().split(None, 1)
            if len(parts_after_num) == 2:
                seq_part = parts_after_num[1]
                bases = seq_part.replace(" ", "")
                assert len(bases) <= 60

    def test_origin_groups_of_10(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet")
        result = self.backend.generate(ir)
        origin_start = result.index("ORIGIN")
        origin_lines = result[origin_start:].split("\n")[1:-1]
        for line in origin_lines:
            if not line.strip() or line.startswith("//"):
                continue
            stripped = line.strip()
            parts_after_num = stripped.split(None, 1)
            if len(parts_after_num) < 2:
                continue
            groups = parts_after_num[1].split(" ")
            for g in groups[:-1]:
                assert len(g) == 10

    def test_record_ends_with_double_slash(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP")
        result = self.backend.generate(ir)
        assert result.rstrip().endswith("//")

    def test_all_parts_preserved_in_order(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet")
        ir.add_part("BBa_B0034", "RBS", "Strong RBS")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        ir.add_part("BBa_B0015", "terminator", "terminator")
        result = self.backend.generate(ir)
        parts = ir.all_parts
        for part in parts:
            assert f'/label="{part["id"]}"' in result
        positions = [result.index(f'/label="{p["id"]}"') for p in parts]
        assert positions == sorted(positions)

    def test_duplicate_parts_both_appear(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        result = self.backend.generate(ir)
        assert result.count('/label="BBa_E0040"') == 2
        total_len = len(PART_SEQUENCES["BBa_E0040"]) * 2
        assert f"{total_len} bp" in result

    def test_unknown_part_uses_fallback_sequence(self):
        ir = CircuitIR()
        ir.add_part("BBa_FAKE", "CDS", "fake part")
        result = self.backend.generate(ir)
        assert f"{len(FALLBACK_SEQUENCE)} bp" in result
        assert "BBa_FAKE" in result

    def test_unknown_role_uses_misc_feature(self):
        ir = CircuitIR()
        ir.add_part("BBa_B0034", "unknown_role", "test")
        result = self.backend.generate(ir)
        assert "misc_feature" in result

    def test_registry_contains_genbank(self):
        assert "GenBank" in list_backends()
        backend = get("GenBank")
        assert backend is not None
        assert backend.name == "GenBank"

    def test_generate_genbank_alias(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP")
        result = self.backend.generate_genbank(ir, circuit_name="alias_test")
        assert "LOCUS" in result
        assert "alias_test" in result

    def test_circuit_name_in_locus(self):
        ir = CircuitIR()
        ir.add_part("BBa_E0040", "CDS", "GFP")
        result = self.backend.generate(ir, circuit_name="my_circuit_v3")
        assert "my_circuit_v3" in result


class TestFormatOrigin:
    def test_empty_sequence(self):
        assert _format_origin("") == ""

    def test_short_sequence_single_line(self):
        result = _format_origin("atgcgtaaag")
        assert result.strip().startswith("1")
        assert "atgcgtaaag" in result

    def test_exact_60bp(self):
        seq = "a" * 60
        result = _format_origin(seq)
        lines = result.split("\n")
        assert len(lines) == 1
        groups = lines[0].strip().split()
        assert groups[0] == "1"
        seq_groups = groups[1:]
        assert len(seq_groups) == 6

    def test_61bp_wraps_to_two_lines(self):
        seq = "a" * 61
        result = _format_origin(seq)
        lines = result.split("\n")
        assert len(lines) == 2
        assert "1" in lines[0]
        assert "61" in lines[1]

    def test_line_number_right_justified(self):
        result = _format_origin("a" * 120)
        lines = result.split("\n")
        for line in lines:
            # First 9 chars are the right-justified position number
            num = int(line[:9].strip())
            assert line[:9] == str(num).rjust(9)


class TestRoleFeatureKeyMapping:
    def test_all_mapped_roles(self):
        assert ROLE_FEATURE_KEY["promoter"] == "promoter"
        assert ROLE_FEATURE_KEY["RBS"] == "misc_binding"
        assert ROLE_FEATURE_KEY["CDS"] == "CDS"
        assert ROLE_FEATURE_KEY["reporter"] == "CDS"
        assert ROLE_FEATURE_KEY["terminator"] == "terminator"

    def test_total_length_matches_concatenated_sequences(self):
        ir = CircuitIR()
        parts = [
            ("BBa_R0040", "promoter", "pTet"),
            ("BBa_B0034", "RBS", "Strong RBS"),
            ("BBa_E0040", "CDS", "GFP"),
            ("BBa_B0015", "terminator", "terminator"),
        ]
        for pid, role, info in parts:
            ir.add_part(pid, role, info)
        result = ir.all_parts
        total = sum(len(PART_SEQUENCES[p["id"]]) for p in result)
        genbank = GenBankBackend()
        output = genbank.generate(ir)
        assert f"{total} bp" in output

    def test_multi_part_cumulative_coordinates(self):
        ir = CircuitIR()
        ir.add_part("BBa_R0040", "promoter", "pTet")
        ir.add_part("BBa_B0034", "RBS", "Strong RBS")
        ir.add_part("BBa_E0040", "CDS", "GFP")
        ir.add_part("BBa_B0015", "terminator", "terminator")
        genbank = GenBankBackend()
        output = genbank.generate(ir)
        p1 = len(PART_SEQUENCES["BBa_R0040"])
        p2 = len(PART_SEQUENCES["BBa_B0034"])
        p3 = len(PART_SEQUENCES["BBa_E0040"])
        assert f"1..{p1}" in output
        assert f"{p1+1}..{p1+p2}" in output
        assert f"{p1+p2+1}..{p1+p2+p3}" in output
