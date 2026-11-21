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
from compiler.pipeline import CompilerPipeline
from compiler.backends.dna_backend import DNABackend
from compiler.backends.simulation_backend import SimulationBackend


def run_compiler(source_code):
    print(f"=== Compiling: '{source_code}' ===\n")

    pipeline = CompilerPipeline()
    try:
        cir, messages = pipeline.run(source_code)
    except SyntaxError as e:
        print(f"[SYNTAX ERROR] {e}")
        return
    except Exception as e:
        print(f"[ERROR] Compilation failed: {e}")
        return

    print("[STEP 1] Tokenization + Parsing + Semantic Analysis + IR Build — OK")
    print(f"  Output protein: {cir.output_protein}")
    print(f"  Complexity score: {cir.complexity}")

    for msg in messages:
        print(f"  [{msg.severity.upper()}] {msg.message}")

    print("\n[STEP 2] Circuit IR — parts list (5' → 3'):")
    for i, part in enumerate(cir.all_parts, 1):
        strand = part.get("strand", "+")
        s = f" [-] strand" if strand == "-" else ""
        print(f"  {i}. [{part['role']:<10}] {part['id']:<12} | {part['info']}{s}")
    print()

    print("[DEMO] DNA Backend (FASTA):")
    dna = DNABackend()
    print(dna.generate(cir))
    print()

    print("[DEMO] Simulation Backend (Hill ODE, RK4):")
    sim = SimulationBackend(t_span=(0, 20), dt=0.5)
    try:
        result = sim.generate(cir, inputs={"aTc": 10.0, "AraC": 10.0})
        print(f"  Species: {result['species']}")
        print(f"  Time points: {result['num_points']}")
        for sp in result["species"]:
            final = result["trajectories"][sp][-1]
            print(f"  {sp} final concentration: {final:.4f}")
    except Exception as e:
        print(f"  Simulation failed: {e}")
    print()


if __name__ == "__main__":
    for expr in [
        "IF (aTc AND AraC) -> GFP",
        "IF (NOT aTc) -> RFP",
        "IF (aTc OR AraC) -> BFP",
    ]:
        run_compiler(expr)
        print("---\n")
