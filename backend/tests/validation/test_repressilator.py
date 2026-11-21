import pytest
from compiler.cir import CircuitIR
from compiler.simulation import simulate_circuit, SimulationResult


def build_repressilator():
    ir = CircuitIR(logic_statement="(cI -> TetR -> LacI -> cI) -> GFP")
    ir.add_node("tetR_p", "TetR", "gate", kinetics="NOT")
    ir.add_node("lacI_p", "LacI", "gate", kinetics="NOT")
    ir.add_node("cI_p", "cI", "gate", kinetics="NOT")
    ir.add_node("gfp_out", "GFP", "output", kinetics="NOT")
    ir.add_edge("cI_p", "tetR_p")
    ir.add_edge("tetR_p", "lacI_p")
    ir.add_edge("lacI_p", "cI_p")
    ir.add_edge("tetR_p", "gfp_out")
    return ir


def _small_perturbation():
    return {"TetR": 0.1}


class TestRepressilatorBenchmark:
    def test_build_repressilator(self):
        ir = build_repressilator()
        assert ir is not None
        assert len(ir.nodes) >= 4

    def test_simulate_repressilator(self):
        ir = build_repressilator()
        result = simulate_circuit(ir, y0=_small_perturbation(),
                                  t_span=(0, 200), dt=0.5)
        assert result.num_points == 401

    def test_repressilator_oscillates(self):
        ir = build_repressilator()
        result = simulate_circuit(ir, y0=_small_perturbation(),
                                  t_span=(0, 200), dt=0.5)
        gfp = result.trajectory("GFP")
        peaks = _count_peaks(gfp)
        assert peaks >= 2, (
            f"Repressilator should oscillate, but only {peaks} peaks detected"
        )

    def test_repressilator_has_period(self):
        ir = build_repressilator()
        slow_params = {
            "TetR": {"vmax": 2.0, "delta": 0.1},
            "LacI": {"vmax": 2.0, "delta": 0.1},
            "cI": {"vmax": 2.0, "delta": 0.1},
            "GFP": {"vmax": 2.0, "delta": 0.1},
        }
        result = simulate_circuit(ir, y0=_small_perturbation(),
                                  params=slow_params,
                                  t_span=(0, 200), dt=0.5)
        gfp = result.trajectory("GFP")
        period = _estimate_period(gfp, dt=0.5)
        assert 10 < period < 150, (
            f"Expected period between 10-150 time units, got {period}"
        )

    def test_repressilator_steady_state_different_from_zero(self):
        ir = build_repressilator()
        result = simulate_circuit(ir, y0=_small_perturbation(),
                                  t_span=(0, 200), dt=0.5)
        final = result.final_concentration("GFP")
        assert final > 0.01, (
            f"Repressilator final GFP should be > 0, got {final}"
        )

    def test_repressilator_without_perturbation_flatline(self):
        ir = build_repressilator()
        result = simulate_circuit(ir, t_span=(0, 100), dt=0.5)
        gfp = result.trajectory("GFP")
        peaks = _count_peaks(gfp)
        assert peaks < 2, (
            "Without perturbation, repressilator should not oscillate"
        )


def _count_peaks(trajectory, threshold=1e-3):
    """Count number of peaks (local maxima) in a trajectory."""
    if len(trajectory) < 3:
        return 0
    peaks = 0
    for i in range(1, len(trajectory) - 1):
        if (trajectory[i] > trajectory[i - 1] and
            trajectory[i] > trajectory[i + 1] and
            trajectory[i] > threshold):
            peaks += 1
    return peaks


def _estimate_period(trajectory, dt=0.5):
    """Estimate oscillation period from peak-to-peak distance."""
    if len(trajectory) < 3:
        return float("inf")
    peak_indices = []
    for i in range(1, len(trajectory) - 1):
        if (trajectory[i] > trajectory[i - 1] and
            trajectory[i] > trajectory[i + 1] and
            trajectory[i] > 1e-3):
            peak_indices.append(i)
    if len(peak_indices) < 2:
        return float("inf")
    periods = [
        (peak_indices[j + 1] - peak_indices[j]) * dt
        for j in range(len(peak_indices) - 1)
    ]
    return sum(periods) / len(periods)
