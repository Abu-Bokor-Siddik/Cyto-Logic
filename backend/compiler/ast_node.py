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
    # Shared parent so every compiler stage can treat all node types through a common interface.
    pass

class ProteinNode(ASTNode):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Protein({self.name})"

class NotGate(ASTNode):
    # NOT always operates on a single operand, so storing exactly one child keeps the tree structure simple.
    def __init__(self, input_node):
        self.input = input_node

    def __repr__(self):
        return f"NOT({self.input})"

class AndGate(ASTNode):
    # Binary gates keep explicit left/right children.
    # This makes recursive tree traversal predictable.
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left} AND {self.right})"

class OrGate(ASTNode):
    # Uses the same structure as AND so later compiler stages can process both gate types consistently.
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left} OR {self.right})"

class Circuit(ASTNode):
    # The root node represents one complete program.
    # Separating the condition from the output keeps the entire circuit under a single entry point.
    def __init__(self, condition, output):
        self.condition = condition  
        self.output = output        

    def __repr__(self):
        return f"CIRCUIT: IF {self.condition} -> THEN EXPRESS {self.output}"