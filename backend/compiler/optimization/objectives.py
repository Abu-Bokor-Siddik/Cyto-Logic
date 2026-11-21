import math


class ObjectiveFunctions:
    def __init__(self, target_output=10.0, output_species="GFP"):
        self.target_output = target_output
        self.output_species = output_species

    def expression_accuracy(self, result):
        final = result.final_concentration(self.output_species)
        return abs(final - self.target_output)

    def metabolic_burden(self, result):
        burden = 0.0
        for sp in result.species:
            trajectory = result.trajectory(sp)
            avg = sum(trajectory) / len(trajectory) if trajectory else 0.0
            burden += avg
        return burden

    @staticmethod
    def noise_robustness(result, perturbation=0.05):
        sensitivity = 0.0
        for sp in result.species:
            trajectory = result.trajectory(sp)
            if len(trajectory) < 2:
                continue
            steady = trajectory[-1]
            if abs(steady) < 1e-12:
                continue
            for j in range(len(trajectory) - 1):
                diff = abs(trajectory[j + 1] - trajectory[j])
                if trajectory[j] > 1e-12:
                    sensitivity += diff / trajectory[j]
        return sensitivity

    def evaluate(self, result):
        return (
            self.expression_accuracy(result),
            self.metabolic_burden(result),
            self.noise_robustness(result),
        )
