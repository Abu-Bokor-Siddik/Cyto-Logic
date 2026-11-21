_COMPLEMENT = str.maketrans("ACGTacgt", "TGCATGCA")


def reverse_complement(sequence: str) -> str:
    return sequence.translate(_COMPLEMENT)[::-1]