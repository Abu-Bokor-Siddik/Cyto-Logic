"""
Core responsibility
-----------------------------------------------
Store the biological parts used by the compiler.
The mapper looks up this file whenever it needs
to translate a logic gate into real genetic parts.
For now I only included a small collection of
commonly used BioBrick components. More parts
can be added without changing the compiler itself.

Design note
----------------------------------------------------
I wanted all biological data in one place instead
of mixing it with compiler code.
This file is only a reference database.
It does not contain any compilation logic.
Keeping the data separate made it easier to update
part information without touching the mapper.
"""

from .knowledge_base import (
    get_biomolecules,
    get_gates,
    get_reporters,
    get_additional_parts,
    get_regulatory_map,
    get_part,
    reload,
)

BIOMOLECULES = get_biomolecules()
GATES_DB = get_gates()
REPORTERS = get_reporters()
ADDITIONAL_PARTS = get_additional_parts()
REGULATORY_MAP = get_regulatory_map()


def refresh():
    reload()
    global BIOMOLECULES, GATES_DB, REPORTERS, ADDITIONAL_PARTS, REGULATORY_MAP
    BIOMOLECULES = get_biomolecules()
    GATES_DB = get_gates()
    REPORTERS = get_reporters()
    ADDITIONAL_PARTS = get_additional_parts()
    REGULATORY_MAP = get_regulatory_map()


if __name__ == "__main__":
    print("--- BioBrick Parts Database Test (from Knowledge Base) ---")
    repressor_name = "TetR"
    if repressor_name in BIOMOLECULES:
        part_info = BIOMOLECULES[repressor_name]
        print(f"Intermediate Repressor [{repressor_name}] -> iGEM ID: {part_info['id']} ({part_info['info']})")
    print("\nNOT Gate Backbone Parts:")
    for part in GATES_DB["NOT"]:
        print(f"  Role: {part['role']:<12} -> iGEM ID: {part['id']}")
