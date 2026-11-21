import random
import math
from .individual import Individual, PARAM_BOUNDS, PARAM_NAMES


class NSGAII:
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
    def _fast_non_dominated_sort(population):
        fronts = [[]]
        for p in population:
            p.domination_count = 0
            p.dominated_set = []
            for q in population:
                if p.dominates(q):
                    p.dominated_set.append(q)
                elif q.dominates(p):
                    p.domination_count += 1
            if p.domination_count == 0:
                p.rank = 0
                fronts[0].append(p)
        i = 0
        while fronts[i]:
            next_front = []
            for p in fronts[i]:
                for q in p.dominated_set:
                    q.domination_count -= 1
                    if q.domination_count == 0:
                        q.rank = i + 1
                        next_front.append(q)
            i += 1
            fronts.append(next_front)
        return [f for f in fronts if f]

    @staticmethod
    def _crowding_distance(front):
        if not front:
            return
        num_obj = len(front[0].objectives)
        for ind in front:
            ind.crowding_distance = 0.0
        for m in range(num_obj):
            front.sort(key=lambda x: x.objectives[m])
            front[0].crowding_distance = float("inf")
            front[-1].crowding_distance = float("inf")
            obj_min = front[0].objectives[m]
            obj_max = front[-1].objectives[m]
            if obj_max - obj_min < 1e-12:
                continue
            for i in range(1, len(front) - 1):
                front[i].crowding_distance += (
                    front[i + 1].objectives[m] - front[i - 1].objectives[m]
                ) / (obj_max - obj_min)

    @staticmethod
    def _crowded_tournament_select(population, k=3):
        best = random.choice(population)
        for _ in range(k - 1):
            candidate = random.choice(population)
            if (candidate.rank < best.rank or
                (candidate.rank == best.rank and
                 candidate.crowding_distance > best.crowding_distance)):
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

    def run(self, num_species, objective_func):
        pop = self._init_population(num_species)
        for ind in pop:
            ind.objectives = list(objective_func(ind))
        fronts = self._fast_non_dominated_sort(pop)
        for f in fronts:
            self._crowding_distance(f)
        self._history = [list(pop)]
        for gen in range(self.generations):
            offspring = []
            while len(offspring) < self.pop_size:
                p1 = self._crowded_tournament_select(pop)
                p2 = self._crowded_tournament_select(pop)
                if random.random() < self.crossover_prob:
                    c1, c2 = self._crossover(p1, p2)
                else:
                    c1, c2 = p1.clone(), p2.clone()
                self._mutate(c1)
                self._mutate(c2)
                c1.objectives = list(objective_func(c1))
                c2.objectives = list(objective_func(c2))
                offspring.append(c1)
                if len(offspring) < self.pop_size:
                    offspring.append(c2)
            combined = pop + offspring[:self.pop_size]
            for ind in combined:
                ind.objectives = list(objective_func(ind))
            fronts = self._fast_non_dominated_sort(combined)
            new_pop = []
            for f in fronts:
                self._crowding_distance(f)
                if len(new_pop) + len(f) <= self.pop_size:
                    new_pop.extend(f)
                else:
                    f.sort(key=lambda x: x.crowding_distance,
                           reverse=True)
                    remaining = self.pop_size - len(new_pop)
                    new_pop.extend(f[:remaining])
                    break
            pop = new_pop
            self._history.append(list(pop))
        fronts = self._fast_non_dominated_sort(pop)
        return (
            fronts[0] if fronts else [],
            pop,
            self._history,
        )
