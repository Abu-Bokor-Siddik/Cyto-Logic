from .models import (
    hill_activator,
    hill_repressor,
    or_combine,
    and_combine,
    degradation,
    DEFAULT_VMAX,
    DEFAULT_KD,
    DEFAULT_HILL_N,
    DEFAULT_DELTA,
)


def _is_flat(d):
    return bool(d) and not any(isinstance(v, dict) for v in d.values())


class ODESystem:
    def __init__(self, cir, inputs=None, params=None):
        self._cir = cir
        self._inputs = inputs or {}
        raw = params or {}
        self._global_params = raw if _is_flat(raw) else {}
        self._per_species_params = raw if not _is_flat(raw) else {}
        self._species, self._rates = self._build()

    def _build(self):
        species = []
        rates = {}
        nodes = dict(self._cir.nodes)
        edges = list(self._cir.edges)

        for nid, data in nodes.items():
            label = data["label"]
            ntype = data.get("type", "input")
            sp_params = {**self._global_params, **self._per_species_params.get(label, {})}

            if ntype == "input":
                species.append(label)
                target = self._inputs.get(label, 1.0)
                rates[label] = _InputRate(label, target=target)
            else:
                input_labels = [
                    nodes[src]["label"]
                    for src, tgt in edges
                    if tgt == nid and src in nodes
                ]
                species.append(label)
                kinetics = data.get("kinetics", data["label"])
                rates[label] = _GateRate(
                    label, kinetics, input_labels, sp_params
                )

        return species, rates

    @property
    def species(self):
        return list(self._species)

    @property
    def num_species(self):
        return len(self._species)

    def _idx(self, name):
        return self._species.index(name)

    def __call__(self, t, y):
        return self.eval(t, y)

    def eval(self, t, y):
        concentrations = dict(zip(self._species, y))
        dydt = [0.0] * self.num_species
        for name, rate in self._rates.items():
            idx = self._idx(name)
            dydt[idx] = rate(t, concentrations)
        for i, name in enumerate(self._species):
            if y[i] <= 0.0 and dydt[i] < 0.0:
                dydt[i] = 0.0
        return dydt


class _InputRate:
    def __init__(self, name, target=1.0):
        self._name = name
        self._target = target

    def __call__(self, t, conc):
        current = conc.get(self._name, 0.0)
        target = self._target
        delta = DEFAULT_DELTA
        return degradation(target, delta)


class _GateRate:
    def __init__(self, name, gate_type, input_labels, params=None):
        self._name = name
        self._gate_type = gate_type
        self._input_labels = input_labels
        self._params = params or {}

    def _v(self, name, default):
        return self._params.get(name, default)

    def __call__(self, t, conc):
        conc = {k: max(0.0, v) for k, v in conc.items()}
        vmax = self._v("vmax", DEFAULT_VMAX)
        kd = self._v("kd", DEFAULT_KD)
        hn = self._v("hill_n", DEFAULT_HILL_N)
        delta = self._v("delta", DEFAULT_DELTA)

        if self._gate_type in ("NOT", "not"):
            input_conc = (
                conc.get(self._input_labels[0], 0.0)
                if self._input_labels
                else 0.0
            )
            prod = hill_repressor(input_conc, vmax, kd, hn)
        elif self._gate_type in ("AND", "and"):
            c1 = conc.get(self._input_labels[0], 0.0) if len(self._input_labels) > 0 else 0.0
            c2 = conc.get(self._input_labels[1], 0.0) if len(self._input_labels) > 1 else 0.0
            a1 = hill_activator(c1, vmax, kd, hn)
            a2 = hill_activator(c2, vmax, kd, hn)
            prod = and_combine(a1, a2)
        elif self._gate_type in ("OR", "or"):
            c1 = conc.get(self._input_labels[0], 0.0) if len(self._input_labels) > 0 else 0.0
            c2 = conc.get(self._input_labels[1], 0.0) if len(self._input_labels) > 1 else 0.0
            a1 = hill_activator(c1, vmax, kd, hn)
            a2 = hill_activator(c2, vmax, kd, hn)
            prod = or_combine(a1, a2, vmax=vmax)
        elif self._gate_type == "output":
            input_conc = (
                conc.get(self._input_labels[0], 0.0)
                if self._input_labels
                else 0.0
            )
            prod = hill_activator(input_conc, vmax, kd, hn)
        elif self._gate_type in ("NAND", "nand"):
            input_conc = (
                conc.get(self._input_labels[0], 0.0)
                if self._input_labels
                else 0.0
            )
            prod = hill_repressor(input_conc, vmax, kd, hn)
        elif self._gate_type in ("NOR", "nor"):
            input_conc = (
                conc.get(self._input_labels[0], 0.0)
                if self._input_labels
                else 0.0
            )
            prod = hill_repressor(input_conc, vmax, kd, hn)
        else:
            input_conc = (
                conc.get(self._input_labels[0], 0.0)
                if self._input_labels
                else 0.0
            )
            prod = hill_activator(input_conc, vmax, kd, hn)

        current_conc = conc.get(self._name, 0.0)
        deg = degradation(current_conc, delta)
        return prod - deg
