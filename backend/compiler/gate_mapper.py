"""
Core responsibility
------------------------------------------------------------
Translate the validated AST into a biological circuit.
This mapper converts logic gates into BioBrick parts,
builds the circuit graph, selects compatible genetic
implementations, and prepares the final design for
SBOL export.

Design note
-------------------------------------------------------
I separated biological mapping from parsing so the
compiler stays independent of any specific genetic
implementation. New gate designs or BioBrick libraries
can be added by updating the mapping tables instead of
changing the compiler itself.
"""
from .ir_builder import IRBuilder


class BioGateMapper:
    def __init__(self):
        self._builder = None

    def map_circuit(self, circuit_ast, logic_statement=None):
        if circuit_ast is None:
            raise ValueError("Cannot map a null circuit AST.")

        self._builder = IRBuilder(logic_statement=logic_statement)
        return self._builder.build(circuit_ast)
            self.final_parts.extend(GATES_DB["OR"])
            return current_id

        return None
