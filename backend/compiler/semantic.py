from .ast_node import ProteinNode, NotGate, AndGate, OrGate, Circuit
from .parts_db import BIOMOLECULES, REPORTERS

_KNOWN_INPUTS = set(BIOMOLECULES.keys())
_KNOWN_OUTPUTS = set(REPORTERS.keys())
_KNOWN_PROTEINS = _KNOWN_INPUTS | _KNOWN_OUTPUTS


class SemanticMessage:
    def __init__(self, message, severity, node_name=None):
        self.message = message
        self.severity = severity
        self.node_name = node_name

    def to_dict(self):
        return {
            "message": self.message,
            "severity": self.severity,
            "node": self.node_name,
        }

    def __repr__(self):
        return f"[{self.severity.upper()}] {self.message}"

    def __eq__(self, other):
        if not isinstance(other, SemanticMessage):
            return NotImplemented
        return (
            self.message == other.message
            and self.severity == other.severity
            and self.node_name == other.node_name
        )


class SemanticAnalyzer:
    def __init__(self, known_inputs=None, known_outputs=None):
        self.known_inputs = known_inputs or _KNOWN_INPUTS
        self.known_outputs = known_outputs or _KNOWN_OUTPUTS

    def analyze(self, circuit_ast):
        if circuit_ast is None:
            return [
                SemanticMessage(
                    "Circuit is empty (null AST).",
                    "error",
                )
            ]

        messages = []
        self._check_output(circuit_ast, messages)
        self._walk_condition(circuit_ast.condition, messages, seen_proteins=set())
        return messages

    def _check_output(self, circuit, messages):
        out_name = circuit.output.name
        if not out_name:
            messages.append(
                SemanticMessage(
                    "Output protein has no name.",
                    "error",
                    out_name,
                )
            )
        elif out_name not in self.known_outputs:
            messages.append(
                SemanticMessage(
                    f"Output '{out_name}' is not in the reporter database. "
                    f"Known reporters: {sorted(self.known_outputs)}.",
                    "warning",
                    out_name,
                )
            )

    def _walk_condition(self, node, messages, seen_proteins, depth=0):
        if depth > 50:
            messages.append(
                SemanticMessage(
                    "Circuit exceeds maximum depth (50). Possible infinite recursion.",
                    "error",
                )
            )
            return

        if isinstance(node, ProteinNode):
            self._check_protein(node, messages, seen_proteins)

        elif isinstance(node, NotGate):
            if node.input is None:
                messages.append(
                    SemanticMessage(
                        "NOT gate has no input.",
                        "error",
                        "NOT",
                    )
                )
            else:
                self._walk_condition(
                    node.input, messages, seen_proteins, depth + 1
                )

        elif isinstance(node, AndGate):
            if node.left is None or node.right is None:
                messages.append(
                    SemanticMessage(
                        "AND gate is missing one or both inputs.",
                        "error",
                        "AND",
                    )
                )
            else:
                self._walk_condition(
                    node.left, messages, seen_proteins, depth + 1
                )
                self._walk_condition(
                    node.right, messages, seen_proteins, depth + 1
                )

        elif isinstance(node, OrGate):
            if node.left is None or node.right is None:
                messages.append(
                    SemanticMessage(
                        "OR gate is missing one or both inputs.",
                        "error",
                        "OR",
                    )
                )
            else:
                self._walk_condition(
                    node.left, messages, seen_proteins, depth + 1
                )
                self._walk_condition(
                    node.right, messages, seen_proteins, depth + 1
                )

    def _check_protein(self, node, messages, seen_proteins):
        if node.name in seen_proteins:
            return
        seen_proteins.add(node.name)

        if node.name not in self.known_inputs:
            messages.append(
                SemanticMessage(
                    f"Undefined protein '{node.name}'. "
                    f"Known inputs: {sorted(self.known_inputs)}.",
                    "warning",
                    node.name,
                )
            )
