import pytest
from compiler.pipeline import CompilerPipeline


class TestCompilerPipeline:
    def test_simple_program(self):
        pipeline = CompilerPipeline()
        cir, messages = pipeline.run("IF aTc -> GFP")
        assert cir is not None
        assert cir.output_protein == "GFP"
        assert len(cir.nodes) >= 1
        assert len(cir.parts_deduplicated()) >= 1
        assert messages == []

    def test_not_gate(self):
        pipeline = CompilerPipeline()
        cir, messages = pipeline.run("IF NOT aTc -> RFP")
        assert cir.output_protein == "RFP"
        assert len(cir.nodes) == 2

    def test_and_gate(self):
        pipeline = CompilerPipeline()
        cir, messages = pipeline.run("IF (aTc AND AraC) -> GFP")
        assert len(cir.nodes) == 3
        assert len(cir.edges) == 2

    def test_or_gate(self):
        pipeline = CompilerPipeline()
        cir, messages = pipeline.run("IF (aTc OR AraC) -> GFP")
        assert len(cir.nodes) == 3
        assert len(cir.edges) == 2

    def test_complex(self):
        pipeline = CompilerPipeline()
        cir, messages = pipeline.run("IF (aTc AND (NOT AraC OR LacI)) -> GFP")
        assert len(cir.nodes) >= 5
        assert len(cir.edges) >= 4

    def test_unknown_output_generates_warning(self):
        pipeline = CompilerPipeline()
        cir, messages = pipeline.run("IF aTc -> UnknownR")
        warning_msgs = [m for m in messages if m.severity == "warning"]
        assert len(warning_msgs) >= 1
        assert any("UnknownR" in m.message for m in warning_msgs)

    def test_syntax_error(self):
        pipeline = CompilerPipeline()
        with pytest.raises(SyntaxError):
            pipeline.run("aTc -> GFP")

    def test_logic_statement_carried_through(self):
        pipeline = CompilerPipeline()
        cir, _ = pipeline.run("IF aTc -> GFP")
        assert cir.logic_statement == "IF aTc -> GFP"

    def test_undefined_protein_warning(self):
        pipeline = CompilerPipeline()
        cir, messages = pipeline.run("IF UnknownX -> GFP")
        warning_msgs = [m for m in messages if m.severity == "warning"]
        assert any("UnknownX" in m.message for m in warning_msgs)
