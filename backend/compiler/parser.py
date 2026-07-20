"""
Core responsibility
----------------------------------------------------
Convert the token stream into an Abstract Syntax Tree(AST).
This module validates the language grammar and produces
the intermediate tree used by the mapping stage.

Design note
----------------------------------------------------
I kept parsing separate from biological mapping.
The parser only understands the language syntax.
Details such as BioBrick selection or DNA assembly
are handled later in the compilation pipeline.
"""
from .ast_node import ProteinNode, NotGate, AndGate, OrGate, Circuit
class BioParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.idx = 0
        self.token = self.tokens[self.idx] if len(tokens) > 0 else None

    def move(self):
        # Single place for advancing the parser state.
        # It keeps the rest of the parser a little cleaner.
        self.idx += 1
        if self.idx < len(self.tokens):
            self.token = self.tokens[self.idx]
        else:
            self.token = None

    def check_and_move(self, expected_type):
        # Every grammar rule eventually comes through here.
        # It makes syntax errors more consistent.
        if self.token is None:
            raise SyntaxError(f"Expected {expected_type} but reached end of tokens")
            
        if self.token.type != expected_type:
            raise SyntaxError(f"Expected token type {expected_type}, but got {self.token.type}")
        
        current = self.token
        self.move()
        return current

    def parse(self):
        # The language always starts with IF.
        # Making this explicit avoids multiple entry points.
        self.check_and_move('IF')

        condition = self.parse_expression()

        self.check_and_move('Arrow')

        output_token = self.check_and_move('IDENTIFIER')

        return Circuit(condition, ProteinNode(output_token.value))

    def parse_expression(self):
        # OR stays at the top level because it has the lowest precedence in this language.
        left = self.parse_term()
        
        while self.token is not None and self.token.type == 'OR':
            self.move() 
            right = self.parse_term()
            left = OrGate(left, right)
            
        return left

    def parse_term(self):
        # AND binds tighter than OR, matching the precedence used in most logic languages.
        left = self.parse_factor()
        
        while self.token is not None and self.token.type == 'AND':
            self.move()
            right = self.parse_factor()
            left = AndGate(left, right)
            
        return left

    def parse_factor(self):
        current = self.token

        if current is None:
            raise SyntaxError("Unexpected end of input while parsing factor")

        # NOT is handled recursively so expressions like NOT NOT A work naturally.
        if current.type == 'NOT':
            self.move()
            operand = self.parse_factor()
            return NotGate(operand)
        # Parentheses simply restart expression parsing. This keeps precedence handling simple.
        elif current.type == 'L_Paren':
            self.move()
            expr = self.parse_expression()
            self.check_and_move('R_Paren')
            return expr
        # Protein names become leaf nodes. They are interpreted later during mapping.
        elif current.type == 'IDENTIFIER':
            self.move()
            return ProteinNode(current.value)

        else:
            raise SyntaxError(f"Invalid syntax near token: {current}")