import math
from .ode_system import ODESystem
from .solver import Solver


class SimulationResult:
    def __init__(self, times, values, species):
        self.times = list(times)
        self.values = [list(v) for v in values]
        self.species = list(species)

    @property
    def num_points(self):
        return len(self.times)

    @property
    def num_species(self):
        return len(self.species)

    def trajectory(self, species_name):
        if species_name not in self.species:
            raise ValueError(f"Unknown species: {species_name}")
        idx = self.species.index(species_name)
        return [row[idx] for row in self.values]

    def to_dict(self):
        return {
            "times": [round(t, 4) for t in self.times],
            "species": self.species,
            "trajectories": {
                sp: [
                    round(row[i], 4)
                    for row in self.values
                ]
                for i, sp in enumerate(self.species)
            },
            "num_points": self.num_points,
        }

    def final_concentration(self, species_name):
        if not self.times:
            return 0.0
        return self.trajectory(species_name)[-1]


def simulate_circuit(cir, inputs=None, params=None, y0=None,
                     t_span=(0, 100), dt=0.01):
    ode = ODESystem(cir, inputs=inputs, params=params)
    if y0 is not None:
        init = [y0.get(sp, 0.0) for sp in ode.species]
    else:
        init = [0.0] * ode.num_species
    solver = Solver(dt=dt)
    times, values = solver.run(ode, init, t_span)
    return SimulationResult(times, values, ode.species)
