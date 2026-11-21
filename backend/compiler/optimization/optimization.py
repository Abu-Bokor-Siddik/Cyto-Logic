from .individual import Individual
from .objectives import ObjectiveFunctions
from .nsga2 import NSGAII


class OptimizationResult:
    def __init__(self, pareto_front, all_populations, species_names):
        self.pareto_front = pareto_front
        self.all_populations = all_populations
        self.species_names = list(species_names)
        self.pareto_front_size = len(pareto_front)
        self.generations_completed = len(all_populations) - 1

    def pareto_objectives(self):
        return [ind.objectives for ind in self.pareto_front]

    def best_params(self):
        if not self.pareto_front:
            return []
        best = min(self.pareto_front,
                   key=lambda x: x.objectives[0])
        return self._params_to_dict(best)

    def _params_to_dict(self, ind):
        return [
            {"species": sp, **ind.params_for_species(i)}
            for i, sp in enumerate(self.species_names)
        ]

    def to_dict(self):
        return {
            "pareto_front_size": len(self.pareto_front),
            "pareto_objectives": [
                {
                    "expression_accuracy": obj[0],
                    "metabolic_burden": obj[1],
                    "noise_robustness": obj[2],
                }
                for obj in self.pareto_objectives()
            ],
            "best_parameter_set": self.best_params(),
            "generations_completed": len(self.all_populations) - 1,
        }


class OptimizationRunner:
    def __init__(self, target_output=10.0, output_species="GFP",
                 pop_size=30, generations=10):
        self.target_output = target_output
        self.output_species = output_species
        self.pop_size = pop_size
        self.generations = generations

    def run(self, cir, inputs=None, t_span=(0, 100), dt=0.5):
        from ..simulation import simulate_circuit

        species = self._get_species(cir)
        objectives = ObjectiveFunctions(
            target_output=self.target_output,
            output_species=self.output_species,
        )

        def objective_func(individual):
            params = {
                sp: individual.params_for_species(i)
                for i, sp in enumerate(species)
            }
            result = simulate_circuit(
                cir, inputs=inputs, params=params,
                t_span=t_span, dt=dt,
            )
            return objectives.evaluate(result)

        optimizer = NSGAII(
            pop_size=self.pop_size,
            generations=self.generations,
        )
        pareto_front, final_pop, history = optimizer.run(
            len(species), objective_func
        )
        return OptimizationResult(
            pareto_front, history, species
        )

    @staticmethod
    def _get_species(cir):
        seen = set()
        result = []
        for nid, data in cir.nodes:
            label = data["label"]
            if label not in seen:
                seen.add(label)
                result.append(label)
        return result
