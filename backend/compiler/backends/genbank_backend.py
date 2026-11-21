from datetime import date

from .base import Backend
from .dna_backend import _resolve_sequence

ROLE_FEATURE_KEY = {
    "promoter": "promoter",
    "RBS": "misc_binding",
    "CDS": "CDS",
    "reporter": "CDS",
    "terminator": "terminator",
}


def _format_origin(sequence):
    lines = []
    for offset in range(0, len(sequence), 60):
        chunk = sequence[offset : offset + 60]
        groups = [chunk[i : i + 10] for i in range(0, len(chunk), 10)]
        lines.append(f"{offset + 1:>9} {' '.join(groups)}")
    return "\n".join(lines)


def _build_features(parts):
    features = []
    running_length = 0
    for part in parts:
        pid = part.get("id", "unknown")
        role = part.get("role", "unknown")
        info = part.get("info", "")
        strand = part.get("strand", "+")
        seq = _resolve_sequence(part)
        start = running_length + 1
        end = running_length + len(seq)
        features.append({
            "role": role,
            "start": start,
            "end": end,
            "pid": pid,
            "info": info,
            "strand": strand,
        })
        running_length += len(seq)
    return features, running_length


class GenBankBackend(Backend):
    @property
    def name(self):
        return "GenBank"

    def generate(self, cir, circuit_name="circuit", **kwargs):
        parts = cir.all_parts
        features, total_length = _build_features(parts)

        full_sequence = ""
        for part in parts:
            full_sequence += _resolve_sequence(part)

        today = date.today().strftime("%d-%b-%Y").upper()

        locus_line = (
            f"LOCUS       {circuit_name:<16s}"
            f"{total_length} bp    ds-DNA    linear   SYN {today}"
        )
        definition = "DEFINITION  Synthetic genetic circuit generated via compiler."

        feature_lines = ["FEATURES             Location/Qualifiers"]
        for f in features:
            key = ROLE_FEATURE_KEY.get(f["role"], "misc_feature")
            if f["strand"] == "-":
                loc = f"complement({f['start']}..{f['end']})"
            else:
                loc = f"{f['start']}..{f['end']}"
            feature_lines.append(f"     {key:<16s}{loc}")
            feature_lines.append(f'                     /label="{f["pid"]}"')
            feature_lines.append(f'                     /note="{f["info"]}"')
            feature_lines.append(f'                     /gene="{f["pid"]}"')

        origin = "ORIGIN"
        if full_sequence:
            origin += "\n" + _format_origin(full_sequence.lower())

        sections = [
            locus_line,
            definition,
            "",
            "\n".join(feature_lines),
            "",
            origin,
            "",
            "//",
        ]
        return "\n".join(sections)

    def generate_genbank(self, cir, circuit_name="circuit", **kwargs):
        return self.generate(cir, circuit_name=circuit_name, **kwargs)
