import random
import math
from .individual import Individual, PARAM_BOUNDS, PARAM_NAMES


class GeneticAlgorithm:
    def __init__(self, pop_size=50, generations=20,
                 crossover_prob=0.8, mutation_prob=0.1,
                 mutation_sigma=0.1):
        self.pop_size = pop_size
        self.generations = generations
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.mutation_sigma = mutation_sigma
        self._history = []

    def _init_population(self, num_species):
        return [Individual.random(num_species)
                for _ in range(self.pop_size)]

    @staticmethod
    def _tournament_select(population, k=3):
        best = random.choice(population)
        for _ in range(k - 1):
            candidate = random.choice(population)
            if candidate.objectives[0] < best.objectives[0]:
                best = candidate
        return best

    def _crossover(self, p1, p2):
        c1 = p1.clone()
        c2 = p2.clone()
        f1 = c1.encode()
        f2 = c2.encode()
        for i in range(len(f1)):
            if random.random() < 0.5:
                f1[i], f2[i] = f2[i], f1[i]
        c1.decode(f1)
        c2.decode(f2)
        return c1, c2

    def _mutate(self, ind):
        flat = ind.encode()
        for i in range(len(flat)):
            if random.random() < self.mutation_prob:
                flat[i] += random.gauss(0, self.mutation_sigma)
        gene_idx = 0
        for si in range(ind.num_species):
            for pname in PARAM_NAMES:
                lo, hi = PARAM_BOUNDS[pname]
                flat[gene_idx] = max(lo, min(hi, flat[gene_idx]))
                gene_idx += 1
        ind.decode(flat)

    def run(self, num_species, fitness_func):
        pop = self._init_population(num_species)
        for ind in pop:
            ind.objectives = [fitness_func(ind)]
        self._history = [list(pop)]
        for gen in range(self.generations):
            new_pop = []
            elite = min(pop, key=lambda x: x.objectives[0])
            new_pop.append(elite.clone())
            while len(new_pop) < self.pop_size:
                p1 = self._tournament_select(pop)
                p2 = self._tournament_select(pop)
                if random.random() < self.crossover_prob:
                    c1, c2 = self._crossover(p1, p2)
                else:
                    c1, c2 = p1.clone(), p2.clone()
                self._mutate(c1)
                self._mutate(c2)
                c1.objectives = [fitness_func(c1)]
                c2.objectives = [fitness_func(c2)]
                new_pop.append(c1)
                if len(new_pop) < self.pop_size:
                    new_pop.append(c2)
            pop = new_pop[:self.pop_size]
            self._history.append(list(pop))
        best = min(pop, key=lambda x: x.objectives[0])
        return best, pop, self._history
