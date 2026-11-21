"""
Core responsibility
----------------------------------------------------
Export the compiled circuit as an SBOL document.
This module takes the parts selected by the compiler
and writes them into a standard SBOL file. The output
can be opened by other synthetic biology tools.

Design note
----------------------------------------------------
I kept exporting separate from compilation.
The compiler decides what the circuit contains.
This file only describes how that circuit is saved
in a standard exchange format.
"""
import sbol2

class SBOLExporter:
    def create_document(self, parts, name, homespace='http://cytologic.org'):
        sbol2.setHomespace(homespace)
        doc = sbol2.Document()
        safe_name = name.replace(" ", "_")

        main_region = sbol2.ComponentDefinition(safe_name)
        main_region.roles = ["http://identifiers.org/so/SO:0000804"]

        so_mapping = {
            'promoter': sbol2.SO_PROMOTER,
            'RBS': 'http://identifiers.org/SO:0000139',
            'CDS': sbol2.SO_CDS,
            'terminator': 'http://identifiers.org/SO:0000141'
        }

        # idx ensures unique IDs even if same BioBrick appears twice
        for idx, item in enumerate(parts):
            unique_id = f"{safe_name}_{item.get('id', 'part')}_{idx}".replace("-", "_")
            sub_part = sbol2.ComponentDefinition(unique_id)
            part_role = so_mapping.get(item.get('role'), sbol2.SO_MISC)
            sub_part.roles = [part_role]

            sub_component = sbol2.Component(f"element_{idx}")
            sub_component.definition = sub_part.identity
            main_region.components.add(sub_component)

            doc.addComponentDefinition(sub_part)
        doc.addComponentDefinition(main_region)
        return doc
