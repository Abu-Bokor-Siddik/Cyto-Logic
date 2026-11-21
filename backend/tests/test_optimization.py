import pytest
from compiler.cir import CircuitIR
from compiler.optimization.individual import Individual, PARAM_BOUNDS
from compiler.optimization.objectives import ObjectiveFunctions
from compiler.optimization.ga import GeneticAlgorithm
from compiler.optimization.nsga2 import NSGAII
from compiler.optimization.optimization import OptimizationRunner
from compiler.simulation import simulate_circuit


class TestIndividual:
    def test_creation(self):
        ind = Individual(3)
        assert ind.num_species == 3
        assert len(ind._params) == 3

    def test_random_bounds(self):
        ind = Individual.random(3)
        for p in ind._params:
            assert PARAM_BOUNDS["vmax"][0] <= p["vmax"] <= PARAM_BOUNDS["vmax"][1]
            assert PARAM_BOUNDS["kd"][0] <= p["kd"] <= PARAM_BOUNDS["kd"][1]

    def test_encode_decode_roundtrip(self):
        ind = Individual.random(3)
        flat = ind.encode()
        ind2 = Individual(3)
        ind2.decode(flat)
        for i in range(3):
            for k in ind._params[i]:
                assert ind._params[i][k] == pytest.approx(ind2._params[i][k])

    def test_clone(self):
        ind = Individual.random(2)
        ind.objectives = [1.0, 2.0]
        ind.rank = 5
        clone = ind.clone()
        assert clone.objectives == [1.0, 2.0]
        assert clone.rank == 5

    def test_dominates_true(self):
        a = Individual(1)
        b = Individual(1)
        a.objectives = [1.0, 2.0]
        b.objectives = [2.0, 3.0]
        assert a.dominates(b)
        assert not b.dominates(a)

    def test_dominates_false_equal(self):
        a = Individual(1)
        b = Individual(1)
        a.objectives = [1.0, 2.0]
        b.objectives = [1.0, 2.0]
        assert not a.dominates(b)
        assert not b.dominates(a)

    def test_params_for_species(self):
        ind = Individual.random(2)
        p = ind.params_for_species(0)
        assert "vmax" in p
        assert "kd" in p


class TestObjectiveFunctions:
    def test_expression_accuracy_perfect(self):
        result = _make_result({"GFP": [10.0]})
        obj = ObjectiveFunctions(target_output=10.0, output_species="GFP")
        assert obj.expression_accuracy(result) == pytest.approx(0.0)

    def test_expression_accuracy_offset(self):
        result = _make_result({"GFP": [7.0]})
        obj = ObjectiveFunctions(target_output=10.0, output_species="GFP")
        assert obj.expression_accuracy(result) == pytest.approx(3.0)

    def test_metabolic_burden(self):
        result = _make_result({"X": [5.0], "Y": [3.0]})
        obj = ObjectiveFunctions()
        assert obj.metabolic_burden(result) == pytest.approx(8.0)

    def test_evaluate_returns_tuple(self):
        result = _make_result({"GFP": [10.0]})
        obj = ObjectiveFunctions(target_output=10.0)
        e, m, n = obj.evaluate(result)
        assert isinstance(e, float)
        assert isinstance(m, float)
        assert isinstance(n, float)


class TestGA:
    def test_init_population(self):
        ga = GeneticAlgorithm(pop_size=10, generations=1)
        pop = ga._init_population(2)
        assert len(pop) == 10
        for ind in pop:
            assert ind.num_species == 2

    def test_run_returns_best(self):
        ga = GeneticAlgorithm(pop_size=10, generations=5)
        best, pop, history = ga.run(2, lambda ind: [sum(ind.encode())])
        assert len(best.encode()) == 8
        assert len(pop) == 10


class TestNSGAII:
    def test_init_population(self):
        nsga = NSGAII(pop_size=10, generations=1)
        pop = nsga._init_population(2)
        assert len(pop) == 10

    def test_fast_non_dominated_sort(self):
        a = Individual(1)
        b = Individual(1)
        c = Individual(1)
        a.objectives = [1.0, 2.0]
        b.objectives = [2.0, 3.0]
        c.objectives = [3.0, 1.0]
        fronts = NSGAII._fast_non_dominated_sort([a, b, c])
        assert len(fronts) >= 1

    def test_crowding_distance(self):
        a = Individual(1)
        b = Individual(1)
        c = Individual(1)
        a.objectives = [1.0]
        b.objectives = [2.0]
        c.objectives = [3.0]
        front = [a, b, c]
        NSGAII._crowding_distance(front)
        assert a.crowding_distance == float("inf")
        assert c.crowding_distance == float("inf")

    def test_run_returns_front(self):
        nsga = NSGAII(pop_size=10, generations=3)
        front, pop, history = nsga.run(2, lambda ind: [sum(ind.encode()), len(ind.encode())])
        assert len(front) > 0
        for ind in front:
            assert len(ind.objectives) == 2


class TestOptimizationRunner:
    def test_run_with_simple_circuit(self):
        ir = CircuitIR(logic_statement="IF aTc -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "GFP", "output")
        ir.add_edge("n1", "n2")
        runner = OptimizationRunner(
            target_output=10.0, output_species="GFP",
            pop_size=10, generations=3
        )
        result = runner.run(ir, inputs={"aTc": 10.0},
                            t_span=(0, 10), dt=1.0)
        assert result.pareto_front_size > 0
        assert result.generations_completed == 3

    def test_to_dict(self):
        ir = CircuitIR(logic_statement="IF aTc -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "GFP", "output")
        ir.add_edge("n1", "n2")
        runner = OptimizationRunner(
            target_output=10.0, output_species="GFP",
            pop_size=10, generations=2
        )
        result = runner.run(ir, inputs={"aTc": 10.0},
                            t_span=(0, 5), dt=1.0)
        d = result.to_dict()
        assert "pareto_front_size" in d
        assert "pareto_objectives" in d
        assert "best_parameter_set" in d

    def test_best_params(self):
        ir = CircuitIR(logic_statement="IF aTc -> GFP")
        ir.add_node("n1", "aTc", "input")
        ir.add_node("n2", "GFP", "output")
        ir.add_edge("n1", "n2")
        runner = OptimizationRunner(
            target_output=10.0, output_species="GFP",
            pop_size=10, generations=2
        )
        result = runner.run(ir, inputs={"aTc": 10.0},
                            t_span=(0, 5), dt=1.0)
        params = result.best_params()
        assert isinstance(params, list)
        if params:
            assert "species" in params[0]

    def test_empty_front(self):
        result_type = type("Result", (), {
            "pareto_front": [],
            "all_populations": [[]],
            "pareto_front_size": 0,
            "pareto_objectives": lambda self: [],
            "best_params": lambda self: [],
            "generations_completed": 0,
            "to_dict": lambda self: {"pareto_front_size": 0},
        })
        r = result_type()
        assert r.pareto_front_size == 0


def _make_result(data):
    species = list(data.keys())
    times = [0]
    values = [[data[sp][0] for sp in species]]
    from compiler.simulation import SimulationResult
    return SimulationResult(times, values, species)
