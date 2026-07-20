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

# Input molecules and regulatory proteins that can appear inside a logic program.
BIOMOLECULES = {
    "aTc": {
        "id": "BBa_K145001", 
        "role": "inducer", 
        "info": "Anhydrotetracycline - induces TetR promoter"
    },
    "AraC": {
        "id": "BBa_I13458", 
        "role": "regulatory_protein", 
        "info": "Arabinose regulatory protein"
    },
    
    "TetR": {
        "id": "BBa_C0040", 
        "role": "CDS", 
        "info": "TetR repressor protein coding sequence"
    },
    "LacI": {
        "id": "BBa_C0012", 
        "role": "CDS", 
        "info": "LacI repressor protein coding sequence"
    },
    "cI": {
        "id": "BBa_C0051", 
        "role": "CDS", 
        "info": "Lambda cI repressor protein coding sequence"
    }
}

# Each logical gate currently maps to one predefined biological implementation.
# This is only the first version of the compiler.
# Different implementations can be added later.
GATES_DB = {
    "NOT": [
        {"id": "BBa_R0040", "role": "promoter", "info": "TetR repressible promoter (pTet)"},
        {"id": "BBa_B0034", "role": "RBS",      "info": "Strong RBS"},
        {"id": "BBa_B0015", "role": "terminator", "info": "Double terminator"}
    ],
    "AND": [
        {"id": "BBa_K1847000", "role": "promoter", "info": "AND gate promoter (Split-activator responsive)"},
        {"id": "BBa_B0034",    "role": "RBS",      "info": "Strong RBS"},
        {"id": "BBa_B0015",    "role": "terminator", "info": "Double terminator"}
    ],
    "OR": [
        {"id": "BBa_K1847001", "role": "promoter", "info": "OR gate dual promoter"},
        {"id": "BBa_B0034",    "role": "RBS",      "info": "Strong RBS"},
        {"id": "BBa_B0015",    "role": "terminator", "info": "Double terminator"}
    ]
}
# Reporter proteins are treated separately because they represent the final observable output.
REPORTERS = {
    "GFP": {
        "id": "BBa_E0040", 
        "role": "CDS", 
        "info": "Green Fluorescent Protein reporter"
    },
    "RFP": {
        "id": "BBa_E0010", 
        "role": "CDS", 
        "info": "Red Fluorescent Protein reporter"
    }
}

"""
Small lookup table describing a few known
regulatory relationships. It is not used by
the parser and is only biological knowledge.
"""

REGULATORY_MAP = {
    "TetR_protein": {"target_promoter": "BBa_R0040", "action": "repress"},
    "aTc_inducer": {"target_protein": "TetR", "action": "inhibit_repressor"},
    "LacI_protein": {"target_promoter": "BBa_R0010", "action": "repress"}
}

if __name__ == "__main__":
    # Quick check to make sure the database contains the expected records.
    print("--- BioBrick Parts Database Test ---")

    repressor_name = "TetR"
    if repressor_name in BIOMOLECULES:
        part_info = BIOMOLECULES[repressor_name]
        print(f"Intermediate Repressor [{repressor_name}] -> iGEM ID: {part_info['id']} ({part_info['info']})")

    print("\nNOT Gate Backbone Parts:")
    for part in GATES_DB["NOT"]:
        print(f"  Role: {part['role']:<12} -> iGEM ID: {part['id']}")