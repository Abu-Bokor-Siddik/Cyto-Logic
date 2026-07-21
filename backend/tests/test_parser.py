import pytest
from compiler.lexer import BioLexer
from compiler.parser import BioParser
from compiler.ast_node import (
    ProteinNode, NotGate, AndGate, OrGate, Circuit
)


def parse(source):
    tokens = BioLexer(source).tokenize()
    return BioParser(tokens).parse()


class TestBioParser:
    def test_simple_input(self):
        ast = parse("IF aTc -> GFP")
        assert isinstance(ast, Circuit)
        assert isinstance(ast.condition, ProteinNode)
        assert ast.condition.name == "aTc"
        assert ast.output.name == "GFP"

    def test_not_gate(self):
        ast = parse("IF NOT aTc -> GFP")
        assert isinstance(ast.condition, NotGate)
        assert isinstance(ast.condition.input, ProteinNode)
        assert ast.condition.input.name == "aTc"

    def test_and_gate(self):
        ast = parse("IF aTc AND AraC -> GFP")
        assert isinstance(ast.condition, AndGate)
        assert isinstance(ast.condition.left, ProteinNode)
        assert ast.condition.left.name == "aTc"
        assert isinstance(ast.condition.right, ProteinNode)
        assert ast.condition.right.name == "AraC"

    def test_or_gate(self):
        ast = parse("IF aTc OR AraC -> GFP")
        assert isinstance(ast.condition, OrGate)
        assert ast.condition.left.name == "aTc"
        assert ast.condition.right.name == "AraC"

    def test_precedence_and_over_or(self):
        ast = parse("IF aTc OR AraC AND LacI -> GFP")
        assert isinstance(ast.condition, OrGate)
        assert isinstance(ast.condition.left, ProteinNode)
        assert ast.condition.left.name == "aTc"
        assert isinstance(ast.condition.right, AndGate)
        assert ast.condition.right.left.name == "AraC"
        assert ast.condition.right.right.name == "LacI"

    def test_parentheses_override_precedence(self):
        ast = parse("IF (aTc OR AraC) AND LacI -> GFP")
        assert isinstance(ast.condition, AndGate)
        assert isinstance(ast.condition.left, OrGate)
        assert ast.condition.left.left.name == "aTc"
        assert ast.condition.left.right.name == "AraC"
        assert isinstance(ast.condition.right, ProteinNode)
        assert ast.condition.right.name == "LacI"

    def test_nested_not(self):
        ast = parse("IF NOT NOT aTc -> GFP")
        assert isinstance(ast.condition, NotGate)
        assert isinstance(ast.condition.input, NotGate)
        assert isinstance(ast.condition.input.input, ProteinNode)
        assert ast.condition.input.input.name == "aTc"

    def test_complex_nested(self):
        ast = parse("IF (aTc AND (NOT AraC OR LacI)) -> GFP")
        assert isinstance(ast.condition, AndGate)
        assert ast.condition.left.name == "aTc"
        assert isinstance(ast.condition.right, OrGate)
        assert isinstance(ast.condition.right.left, NotGate)
        assert ast.condition.right.left.input.name == "AraC"
        assert ast.condition.right.right.name == "LacI"

    def test_missing_if_raises_error(self):
        with pytest.raises(SyntaxError, match="Expected token type IF"):
            parse("aTc -> GFP")

    def test_missing_arrow_raises_error(self):
        with pytest.raises(SyntaxError, match="Expected token type Arrow"):
            parse("IF aTc GFP")

    def test_missing_output_raises_error(self):
        with pytest.raises(SyntaxError, match="Expected token type IDENTIFIER"):
            parse("IF aTc ->")

    def test_unclosed_paren_raises_error(self):
        with pytest.raises(SyntaxError, match="Expected token type R_Paren"):
            parse("IF (aTc AND AraC -> GFP")

    def test_empty_tokens_raises_error(self):
        from compiler.lexer import BioLexer
        tokens = BioLexer("").tokenize()
        parser = BioParser(tokens)
        with pytest.raises(SyntaxError):
            parser.parse()

    def test_invalid_syntax_raises_error(self):
        with pytest.raises(SyntaxError):
            parse("IF AND -> GFP")
