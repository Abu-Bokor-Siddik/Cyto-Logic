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
    def create_document(self, parts, name):
        # Every generated document belongs to the same project namespace.
        sbol2.setHomespace('http://cytologic.org')
        sbol2.Config.setOption('validate', False)
        
        doc = sbol2.Document()
        # SBOL identifiers should not contain spaces.
        safe_name = name.replace(" ", "_")

        # The whole circuit is stored as one engineered genetic region.
        main_region = sbol2.ComponentDefinition(safe_name)
        main_region.roles = ["http://identifiers.org/so/SO:0000804"]
        doc.addComponentDefinition(main_region)

        # Only a few part types are needed in the current compiler.
        so_mapping = {
            'promoter': sbol2.SO_PROMOTER,
            'RBS': 'http://identifiers.org/SO:0000139',
            'CDS': sbol2.SO_CDS,
            'terminator': 'http://identifiers.org/SO:0000141'
        }

        for idx, item in enumerate(parts):
            # The index keeps every component id unique, even if the same BioBrick appears twice.
            unique_id = f"{safe_name}_{item.get('id', 'part')}_{idx}".replace("-", "_")
            sub_part = sbol2.ComponentDefinition(unique_id)
            
            part_role = so_mapping.get(item.get('role'), sbol2.SO_MISC)
            sub_part.roles = [part_role]
            doc.addComponentDefinition(sub_part)

            sub_component = sbol2.Component(f"element_{idx}")
            sub_component.definition = sub_part.identity 
            main_region.components.add(sub_component)

        return doc