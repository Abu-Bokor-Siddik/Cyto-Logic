import math
import pytest
from compiler.cir import CircuitIR
from compiler.simulation.models import (
    hill_activator,
    hill_repressor,
    or_combine,
    and_combine,
    degradation,
    DEFAULT_VMAX,
    DEFAULT_KD,
    DEFAULT_HILL_N,
)
from compiler.simulation.ode_system import ODESystem
from compiler.simulation.solver import Solver
from compiler.simulation.simulation import simulate_circuit, SimulationResult


class TestHillModels:
    def test_hill_activator_zero(self):
        assert hill_activator(0, 10, 1, 2) == 0.0

    def test_hill_activator_at_kd(self):
        result = hill_activator(1.0, 10, 1, 2)
        assert result == pytest.approx(5.0, rel=1e-3)

    def test_hill_activator_saturates(self):
        result = hill_activator(1000, 10, 1, 2)
        assert result == pytest.approx(10.0, rel=1e-3)

    def test_hill_repressor_zero(self):
        result = hill_repressor(0, 10, 1, 2)
        assert result == pytest.approx(10.0, rel=1e-3)

    def test_hill_repressor_at_kd(self):
        result = hill_repressor(1.0, 10, 1, 2)
        assert result == pytest.approx(5.0, rel=1e-3)

    def test_hill_repressor_saturates(self):
        result = hill_repressor(1000, 10, 1, 2)
        assert result == pytest.approx(0.0, abs=1e-3)

    def test_hill_activator_default_params(self):
        result = hill_activator(1.0)
        assert result == pytest.approx(5.0, rel=1e-3)

    def test_negative_concentration_clamps(self):
        assert hill_activator(-1, 10, 1, 2) == 0.0

    def test_invalid_kd_returns_zero(self):
        assert hill_activator(5, 10, 0, 2) == 0.0

    def test_invalid_n_returns_zero(self):
        assert hill_activator(5, 10, 1, 0) == 0.0


class TestGateCombiners:
    def test_or_both_zero(self):
        assert or_combine(0, 0) == 0.0

    def test_or_one_active(self):
        assert or_combine(10, 0) == 10.0
        assert or_combine(0, 10) == 10.0

    def test_or_both_active(self):
        result = or_combine(0.5, 0.5)
        assert result == pytest.approx(0.75, rel=1e-3)

    def test_or_never_negative(self):
        for vmax in [1, 5, 10, 20, 100]:
            for a1 in [0, vmax/2, vmax, vmax*2]:
                for a2 in [0, vmax/2, vmax, vmax*2]:
                    assert or_combine(a1, a2) >= 0.0

    def test_and_both_zero(self):
        assert and_combine(0, 0) == 0.0

    def test_and_one_zero(self):
        assert and_combine(10, 0) == 0.0

    def test_and_both_active(self):
        assert and_combine(5, 3) == 15.0


class TestDegradation:
    def test_degradation_zero(self):
        assert degradation(0, 0.5) == 0.0

    def test_degradation_linear(self):
        assert degradation(10, 0.5) == 5.0

    def test_negative_concentration_clamps(self):
        assert degradation(-5, 0.5) == 0.0

    def test_negative_delta_clamps(self):
        assert degradation(10, -1) == 0.0


class TestODESystem:
    def test_build_simple_not(self):
        ir = CircuitIR(logic_statement="IF aTc -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "NOT", "gate")
        ir.add_node("n3", "GFP", "output")
        ir.add_edge("n1", "n2")
        ir.add_edge("n2", "n3")
        ode = ODESystem(ir)
        assert ode.num_species == 3
        assert "aTc" in ode.species
        assert "NOT" in ode.species
        assert "GFP" in ode.species

    def test_simple_not_eval(self):
        ir = CircuitIR(logic_statement="IF aTc -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "NOT", "gate")
        ir.add_node("n3", "GFP", "output")
        ir.add_edge("n1", "n2")
        ir.add_edge("n2", "n3")
        ode = ODESystem(ir, inputs={"aTc": 10.0})
        y0 = [0.0] * ode.num_species
        dydt = ode.eval(0, y0)
        assert len(dydt) == 3

    def test_build_and_gate(self):
        ir = CircuitIR(logic_statement="IF (aTc AND AraC) -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "AraC", "input")
        ir.add_node("n3", "AND", "gate")
        ir.add_node("n4", "GFP", "output")
        ir.add_edge("n1", "n3")
        ir.add_edge("n2", "n3")
        ir.add_edge("n3", "n4")
        ode = ODESystem(ir)
        assert ode.num_species == 4

    def test_build_or_gate(self):
        ir = CircuitIR(logic_statement="IF (aTc OR AraC) -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "AraC", "input")
        ir.add_node("n3", "OR", "gate")
        ir.add_node("n4", "GFP", "output")
        ir.add_edge("n1", "n3")
        ir.add_edge("n2", "n3")
        ir.add_edge("n3", "n4")
        ode = ODESystem(ir)
        assert ode.num_species == 4


class TestSolver:
    def test_rk4_simple(self):
        def ode(t, y):
            return [-y[0]]
        solver = Solver(dt=0.01)
        t, y = solver.run(ode, [1.0], (0, 1))
        assert len(t) == 101
        assert abs(y[-1][0] - math.exp(-1)) < 0.01

    def test_dt_must_be_positive(self):
        with pytest.raises(ValueError):
            Solver(dt=0)

    def test_t_span_must_be_valid(self):
        solver = Solver(dt=0.01)
        with pytest.raises(ValueError):
            solver.run(lambda t, y: [0], [0], (5, 0))


class TestSimulation:
    def test_simulate_simple_not(self):
        ir = CircuitIR(logic_statement="IF aTc -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "NOT", "gate")
        ir.add_node("n3", "GFP", "output")
        ir.add_edge("n1", "n2")
        ir.add_edge("n2", "n3")
        result = simulate_circuit(ir, inputs={"aTc": 10.0},
                                  t_span=(0, 10), dt=0.1)
        assert result.num_points == 101
        assert result.num_species == 3

    def test_simulation_result_to_dict(self):
        ir = CircuitIR(logic_statement="IF aTc -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "NOT", "gate")
        ir.add_node("n3", "GFP", "output")
        ir.add_edge("n1", "n2")
        ir.add_edge("n2", "n3")
        result = simulate_circuit(ir, inputs={"aTc": 10.0},
                                  t_span=(0, 5), dt=0.5)
        d = result.to_dict()
        assert "times" in d
        assert "species" in d
        assert "trajectories" in d
        assert len(d["times"]) == 11

    def test_trajectory_access(self):
        ir = CircuitIR(logic_statement="IF aTc -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "NOT", "gate")
        ir.add_node("n3", "GFP", "output")
        ir.add_edge("n1", "n2")
        ir.add_edge("n2", "n3")
        result = simulate_circuit(ir, inputs={"aTc": 10.0},
                                  t_span=(0, 1), dt=0.5)
        traj = result.trajectory("GFP")
        assert len(traj) == 3

    def test_trajectory_unknown_species(self):
        result = SimulationResult([0], [[0]], ["X"])
        with pytest.raises(ValueError):
            result.trajectory("Y")

    def test_final_concentration(self):
        result = SimulationResult([0, 1], [[0, 0], [0, 5]], ["X", "Y"])
        assert result.final_concentration("Y") == 5.0

    def test_simulate_with_and_gate(self):
        ir = CircuitIR(logic_statement="IF (aTc AND AraC) -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "AraC", "input")
        ir.add_node("n3", "AND", "gate")
        ir.add_node("n4", "GFP", "output")
        ir.add_edge("n1", "n3")
        ir.add_edge("n2", "n3")
        ir.add_edge("n3", "n4")
        result = simulate_circuit(ir, inputs={"aTc": 10.0, "AraC": 10.0},
                                  t_span=(0, 10), dt=0.1)
        assert result.num_points == 101

    def test_simulate_with_or_gate(self):
        ir = CircuitIR(logic_statement="IF (aTc OR AraC) -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "AraC", "input")
        ir.add_node("n3", "OR", "gate")
        ir.add_node("n4", "GFP", "output")
        ir.add_edge("n1", "n3")
        ir.add_edge("n2", "n3")
        ir.add_edge("n3", "n4")
        result = simulate_circuit(ir, inputs={"aTc": 0.0, "AraC": 10.0},
                                  t_span=(0, 10), dt=0.1)
        assert result.num_points == 101

    def test_simulation_backend_now_returns_data(self):
        from compiler.backends.simulation_backend import SimulationBackend
        ir = CircuitIR(logic_statement="IF aTc -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "NOT", "gate")
        ir.add_node("n3", "GFP", "output")
        ir.add_edge("n1", "n2")
        ir.add_edge("n2", "n3")
        backend = SimulationBackend(t_span=(0, 5), dt=0.5)
        result = backend.generate(ir, inputs={"aTc": 10.0})
        assert "times" in result
        assert "trajectories" in result
        assert "GFP" in result["trajectories"]
