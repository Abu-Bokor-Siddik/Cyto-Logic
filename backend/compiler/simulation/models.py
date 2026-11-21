import math


DEFAULT_VMAX = 10.0
DEFAULT_KD = 1.0
DEFAULT_HILL_N = 2.0
DEFAULT_DELTA = 0.5


def hill_activator(concentration, vmax=DEFAULT_VMAX, kd=DEFAULT_KD, n=DEFAULT_HILL_N):
    if concentration < 0:
        concentration = 0.0
    if kd <= 0 or n <= 0:
        return 0.0
    if vmax < 0:
        vmax = 0.0
    return vmax * (concentration ** n) / (kd ** n + concentration ** n)


def hill_repressor(concentration, vmax=DEFAULT_VMAX, kd=DEFAULT_KD, n=DEFAULT_HILL_N):
    if concentration < 0:
        concentration = 0.0
    if kd <= 0 or n <= 0:
        return vmax if vmax > 0 else 0.0
    if vmax < 0:
        vmax = 0.0
    return vmax * (kd ** n) / (kd ** n + concentration ** n)


def or_combine(act1, act2, vmax=None):
    if vmax is not None and vmax > 0:
        p1 = max(0.0, min(act1, vmax)) / vmax
        p2 = max(0.0, min(act2, vmax)) / vmax
        return vmax * (p1 + p2 - p1 * p2)
    val = act1 + act2 - act1 * act2
    return max(0.0, val)


def and_combine(act1, act2):
    return act1 * act2


def degradation(concentration, delta=DEFAULT_DELTA):
    if concentration < 0:
        concentration = 0.0
    if delta < 0:
        delta = 0.0
    return delta * concentration
