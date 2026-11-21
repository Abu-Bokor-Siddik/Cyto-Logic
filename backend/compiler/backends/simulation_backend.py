from .base import Backend
from ..simulation import simulate_circuit
from ..plugin.manager import get_manager


class SimulationBackend(Backend):
    def __init__(self, t_span=(0, 100), dt=0.01):
        self._t_span = t_span
        self._dt = dt
        self._plugin_manager = get_manager()

    @property
    def name(self):
        return "Simulation"

    def generate(self, cir, inputs=None, params=None):
        self._plugin_manager.invoke(
            "before_simulate", cir, inputs, params,
            self._t_span, self._dt,
        )
        result = simulate_circuit(cir, inputs=inputs, params=params,
                                  t_span=self._t_span, dt=self._dt)
        self._plugin_manager.invoke("after_simulate", result)
        return result.to_dict()
