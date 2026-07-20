"""
Core responsibility
----------------------------------------------------
Run the complete compilation pipeline from one place.
This file is only used for local testing while
building the compiler. It sends a program through
every stage and prints the intermediate results,
making it easier to check that each module works.

Design note
----------------------------------------------------
I kept this separate from the compiler modules.
The lexer, parser and mapper should never contain
testing code. Keeping the runner outside the compiler
makes it easier to reuse the same modules later in
the web application.
"""
from compiler.lexer import BioLexer
from compiler.parser import BioParser
from compiler.gate_mapper import BioGateMapper

def run_compiler(source_code):
    print(f"--- Compiling Code: '{source_code}' ---\n")
    lexer = BioLexer(source_code)
    try:
        tokens = lexer.tokenize()
        print("[STEP 1] Tokenization Successful!")
        print(f"Tokens: {tokens}\n")
    except Exception as e:
        print(f"[ERROR] Lexing failed: {e}")
        return

    parser = BioParser(tokens)
    try:
        ast_tree = parser.parse()
        print("[STEP 2] Parsing Successful! (AST Generated)")
        print(f"AST Tree structure: {ast_tree}\n")
    except SyntaxError as e:
        print(f"[SYNTAX ERROR] Parsing failed: {e}")
        return
    except Exception as e:
        print(f"[ERROR] Parsing failed: {e}")
        return

    mapper = BioGateMapper()
    try:
        result = mapper.map_circuit(ast_tree)
        print("[STEP 3] Gate Mapping & DNA Synthesis Successful!\n")

        print("==================================================")
        print("          GENERATED BIOLOGICAL PLASMID MAP        ")
        print("==================================================")
        
        print(f"Circuit Complexity Score: {result['complexity']}")
        print("\nSynthesized DNA BioBrick Sequence:")

        # Showing the parts in order makes it easier to compare different compiler outputs.
        for index, part in enumerate(result["dna_parts_list"], 1):
            role_upper = part["role"].upper()
            print(f"  {index}. [{role_upper:<10}] -> ID: {part['id']:<12} | Info: {part['info']}")
            
        print("==================================================")
        
    except Exception as e:
        print(f"[ERROR] Mapping failed: {e}")
        return


if __name__ == "__main__":
    # Simple program that I use while testing the compilation pipeline.
    sample_program = "IF (aTc AND AraC) -> GFP"
    
    run_compiler(sample_program)