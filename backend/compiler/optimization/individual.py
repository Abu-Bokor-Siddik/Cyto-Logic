import random


PARAM_BOUNDS = {
    "vmax": (0.1, 50.0),
    "kd": (0.01, 10.0),
    "hill_n": (0.5, 6.0),
    "delta": (0.01, 2.0),
}

PARAM_NAMES = ["vmax", "kd", "hill_n", "delta"]

DEFAULT_PARAMS = {
    "vmax": 10.0,
    "kd": 1.0,
    "hill_n": 2.0,
    "delta": 0.5,
}


class Individual:
    def __init__(self, num_species):
        self.num_species = num_species
        self._params = [
            {name: DEFAULT_PARAMS[name] for name in PARAM_NAMES}
            for _ in range(num_species)
        ]
        self.objectives = []
        self.rank = -1
        self.crowding_distance = 0.0

    def encode(self):
        flat = []
        for p in self._params:
            for name in PARAM_NAMES:
                flat.append(p[name])
        return flat

    def decode(self, flat):
        idx = 0
        for i in range(self.num_species):
            for name in PARAM_NAMES:
                self._params[i][name] = flat[idx]
                idx += 1

    @classmethod
    def random(cls, num_species):
        ind = cls(num_species)
        ind._params = []
        for _ in range(num_species):
            params = {}
            for name in PARAM_NAMES:
                lo, hi = PARAM_BOUNDS[name]
                params[name] = random.uniform(lo, hi)
            ind._params.append(params)
        return ind

    def params_for_species(self, species_idx):
        return dict(self._params[species_idx])

    def all_params(self):
        return [dict(p) for p in self._params]

    def clone(self):
        ind = Individual(self.num_species)
        ind._params = [dict(p) for p in self._params]
        ind.objectives = list(self.objectives)
        ind.rank = self.rank
        ind.crowding_distance = self.crowding_distance
        return ind

    def dominates(self, other):
        not_worse = True
        strictly_better = False
        for a, b in zip(self.objectives, other.objectives):
            if a > b:
                not_worse = False
            if a < b:
                strictly_better = True
        return not_worse and strictly_better

    def __repr__(self):
        return (
            f"Individual(objectives={self.objectives}, "
            f"rank={self.rank})"
        )
