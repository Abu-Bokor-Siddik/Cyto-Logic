import pytest
from compiler.cir import CircuitIR
from compiler.backends.base import Backend
from compiler.backends.registry import get, list_backends
from compiler.backends.simulation_backend import SimulationBackend


class TestBackendAbstraction:
    def test_base_class_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            Backend()

    def test_simulation_backend_has_name(self):
        b = SimulationBackend()
        assert b.name == "Simulation"

    def test_simulation_backend_returns_trajectory(self):
        ir = CircuitIR(logic_statement="IF aTc -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "GFP", "output")
        ir.add_edge("n1", "n2")
        b = SimulationBackend(t_span=(0, 1), dt=0.5)
        result = b.generate(ir, inputs={"aTc": 10.0})
        assert "times" in result
        assert "trajectories" in result

    def test_registry_has_expected_backends(self):
        names = list_backends()
        assert "SBOL" in names
        assert "Simulation" in names
        assert "DNA" in names
        assert "SVG" in names

    def test_registry_get_returns_backend(self):
        b = get("SBOL")
        assert b is not None
        assert b.name == "SBOL"

    def test_registry_get_unknown_returns_none(self):
        assert get("NonExistent") is None
