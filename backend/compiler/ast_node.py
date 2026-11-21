"""
Core responsibility
------------------------------------------------------------
Define the Abstract Syntax Tree (AST) used by the compiler.
Each node represents the meaning of the source program
after parsing. Later stages never work with raw tokens.
They only read these nodes to build biological circuits.

Design note
-------------------------------------------------------
I chose a small node hierarchy instead of dictionaries
or nested lists because every compiler stage can work
with a consistent structure. Keeping the AST independent
from BioBrick data also allows the parser to stay focused
only on language structure, while biological mapping is
handled later in the pipeline.
"""
class ASTNode:
    pass

class ProteinNode(ASTNode):
    def __init__(self, name, strand="+"):
        self.name = name
        self.strand = strand

    def __repr__(self):
        return f"Protein({self.name}, strand={self.strand!r})"

class NotGate(ASTNode):
    def __init__(self, input_node, strand="+"):
        self.input = input_node
        self.strand = strand

    def __repr__(self):
        return f"NOT({self.input}, strand={self.strand!r})"

class AndGate(ASTNode):
    def __init__(self, left, right, strand="+"):
        self.left = left
        self.right = right
        self.strand = strand

    def __repr__(self):
        return f"({self.left} AND {self.right}, strand={self.strand!r})"

class OrGate(ASTNode):
    def __init__(self, left, right, strand="+"):
        self.left = left
        self.right = right
        self.strand = strand

    def __repr__(self):
        return f"({self.left} OR {self.right}, strand={self.strand!r})"

class Circuit(ASTNode):
    def __init__(self, condition, output):
        self.condition = condition
        self.output = output

    def __repr__(self):
        return f"CIRCUIT: IF {self.condition} -> THEN EXPRESS {self.output}"
