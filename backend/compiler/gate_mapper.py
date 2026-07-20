"""
Core responsibility
--------------------------------------------------------------------
Convert the parsed AST into a biological circuit.
This stage walks through every logic node and
builds a graph that represents the circuit.
At the same time it selects the BioBrick parts
needed to implement the logic.The final result is simple enough 
for the next stage to export as SBOL or other formats.

Design note
-------------------------------------------------------
I decided to keep the mapping logic in one place.
The parser only builds the logic tree.
It should not know anything about promoters,
repressors or DNA parts.If I want to support different 
biological libraries later, I only need to change this
mapping layer without touching the parser.
"""
from .ast_node import ProteinNode, NotGate, AndGate, OrGate, Circuit
from .parts_db import GATES_DB, BIOMOLECULES, REPORTERS

class BioGateMapper:
    def __init__(self):
        self.graph_nodes = {}
        self.graph_edges = []
        # I collect parts while walking the tree once.
        # No need for another traversal later.
        self.final_parts = []
        # Simple counter is enough to keep every node unique.
        self.counter = 0

    def map_circuit(self, circuit_ast):
        # Nothing to map if parsing failed.
        if circuit_ast is None:
            return None
        # Start from the logical condition.
        # The traversal builds both the graph and the required biological parts.
        self.traverse(circuit_ast.condition)
        
        out_name = circuit_ast.output.name

        # Reporter genes are always attached at the end.
        if out_name in REPORTERS:
            self.final_parts.append(REPORTERS[out_name])
        else:
            # Unknown outputs are still accepted.
            # A placeholder lets the pipeline continue.
            self.final_parts.append({
                "id": "BBa_CUSTOM_CDS", 
                "role": "CDS", 
                "info": f"Custom CDS for {out_name}"
            })

        return {
            "circuit_structure": self.graph_nodes,
            "connections": self.graph_edges,
            "dna_parts_list": self.final_parts,
            "complexity": len(self.final_parts)
        }

    def traverse(self, node):
        if node is None:
            return None
        # Every graph node gets its own unique id.
        current_id = f"gate_{self.counter}"
        self.counter += 1

        if isinstance(node, ProteinNode):
            # Input proteins become leaf nodes in the graph.
            node_info = {"label": node.name, "type": "input"}
            # Keep the BioBrick id if this molecule already exists in the database.
            if node.name in BIOMOLECULES:
                node_info["biopart_id"] = BIOMOLECULES[node.name]["id"]
                
            self.graph_nodes[current_id] = node_info
            return current_id

        elif isinstance(node, NotGate):
            # Visit the child before creating the gate.
            child_id = self.traverse(node.input)
            # This prototype uses one predefined implementation of a NOT gate.
            self.graph_nodes[current_id] = {"label": "NOT", "type": "gate"}
            if child_id:
                self.graph_edges.append((child_id, current_id))
            
            self.final_parts.extend(GATES_DB["NOT"])
            self.final_parts.append(BIOMOLECULES["TetR"])
            
            return current_id

        elif isinstance(node, AndGate):
            # Both branches must exist before the gate can be connected.
            left_id = self.traverse(node.left)
            right_id = self.traverse(node.right)
            
            self.graph_nodes[current_id] = {"label": "AND", "type": "gate"}
            if left_id: self.graph_edges.append((left_id, current_id))
            if right_id: self.graph_edges.append((right_id, current_id))
            # Right now every AND gate maps to the same predefined biological design.
            self.final_parts.extend(GATES_DB["AND"])
            return current_id

        elif isinstance(node, OrGate):
            left_id = self.traverse(node.left)
            right_id = self.traverse(node.right)
            
            self.graph_nodes[current_id] = {"label": "OR", "type": "gate"}
            if left_id: self.graph_edges.append((left_id, current_id))
            if right_id: self.graph_edges.append((right_id, current_id))
            # OR uses its own backbone stored in the parts database.
            self.final_parts.extend(GATES_DB["OR"])
            return current_id

        return None

if __name__ == "__main__":
    # Small manual test that I use while changing the mapper implementation.
    test_ast = Circuit(
        condition=NotGate(ProteinNode("aTc")),
        output=ProteinNode("GFP")
    )
    
    mapper = BioGateMapper()
    result = mapper.map_circuit(test_ast)
    
    print("--- Generated DNA BioBrick Sequence ---")
    for part in result["dna_parts_list"]:
        print(f"[{part['role'].upper()}] -> {part['id']}: {part['info']}")