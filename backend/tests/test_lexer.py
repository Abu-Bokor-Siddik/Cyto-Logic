import pytest
from compiler.lexer import BioLexer


class TestBioLexer:
    def test_empty_input(self):
        tokens = BioLexer("").tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == "EOF"

    def test_whitespace_only(self):
        tokens = BioLexer("   \t\n\r  ").tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == "EOF"

    def test_if_keyword(self):
        tokens = BioLexer("IF").tokenize()
        assert tokens[0].type == "IF"
        assert tokens[0].value == "IF"
        assert tokens[1].type == "EOF"

    def test_if_keyword_case_insensitive(self):
        tokens = BioLexer("if").tokenize()
        assert tokens[0].type == "IF"

    def test_and_keyword(self):
        tokens = BioLexer("AND").tokenize()
        assert tokens[0].type == "AND"
        assert tokens[1].type == "EOF"

    def test_or_keyword(self):
        tokens = BioLexer("OR").tokenize()
        assert tokens[0].type == "OR"
        assert tokens[1].type == "EOF"

    def test_not_keyword(self):
        tokens = BioLexer("NOT").tokenize()
        assert tokens[0].type == "NOT"
        assert tokens[1].type == "EOF"

    def test_identifier(self):
        tokens = BioLexer("aTc").tokenize()
        assert tokens[0].type == "IDENTIFIER"
        assert tokens[0].value == "aTc"
        assert tokens[1].type == "EOF"

    def test_identifier_preserves_case(self):
        tokens = BioLexer("AraC").tokenize()
        assert tokens[0].type == "IDENTIFIER"
        assert tokens[0].value == "AraC"

    def test_left_paren(self):
        tokens = BioLexer("(").tokenize()
        assert tokens[0].type == "L_Paren"
        assert tokens[1].type == "EOF"

    def test_right_paren(self):
        tokens = BioLexer(")").tokenize()
        assert tokens[0].type == "R_Paren"
        assert tokens[1].type == "EOF"

    def test_arrow(self):
        tokens = BioLexer("->").tokenize()
        assert tokens[0].type == "Arrow"
        assert tokens[0].value == "->"
        assert tokens[1].type == "EOF"

    def test_simple_program(self):
        tokens = BioLexer("IF aTc -> GFP").tokenize()
        types = [t.type for t in tokens]
        values = [t.value for t in tokens]
        assert types == ["IF", "IDENTIFIER", "Arrow", "IDENTIFIER", "EOF"]
        assert values == ["IF", "aTc", "->", "GFP", ""]

    def test_complex_expression(self):
        tokens = BioLexer("IF (aTc AND AraC) -> GFP").tokenize()
        types = [t.type for t in tokens]
        assert types == [
            "IF", "L_Paren", "IDENTIFIER", "AND", "IDENTIFIER",
            "R_Paren", "Arrow", "IDENTIFIER", "EOF"
        ]

    def test_not_expression(self):
        tokens = BioLexer("IF NOT aTc -> GFP").tokenize()
        types = [t.type for t in tokens]
        assert types == [
            "IF", "NOT", "IDENTIFIER", "Arrow", "IDENTIFIER", "EOF"
        ]

    def test_expression_with_or(self):
        tokens = BioLexer("IF (aTc OR AraC) -> RFP").tokenize()
        types = [t.type for t in tokens]
        assert types == [
            "IF", "L_Paren", "IDENTIFIER", "OR", "IDENTIFIER",
            "R_Paren", "Arrow", "IDENTIFIER", "EOF"
        ]

    def test_unknown_characters_are_skipped(self):
        tokens = BioLexer("IF aTc @#$ -> GFP").tokenize()
        types = [t.type for t in tokens]
        assert "IF" in types
        assert "IDENTIFIER" in types
        assert "Arrow" in types

    def test_position_tracking(self):
        tokens = BioLexer("IF aTc -> GFP").tokenize()
        if_token = tokens[0]
        assert if_token.position == 0

        identifier_token = tokens[1]
        assert identifier_token.position == 3

        arrow_token = tokens[2]
        assert arrow_token.value == "->"

    def test_multi_char_identifier_with_digits(self):
        tokens = BioLexer("TEST123").tokenize()
        assert tokens[0].type == "IDENTIFIER"
        assert tokens[0].value == "TEST123"
