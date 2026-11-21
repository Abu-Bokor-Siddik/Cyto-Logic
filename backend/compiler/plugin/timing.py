import time
from .base import PluginBase


class TimingPlugin(PluginBase):
    @property
    def name(self):
        return "Timing"

    def __init__(self):
        self._timings = {}

    def before_compile(self, source_code):
        self._timings["compile_start"] = time.time()
        return None

    def after_compile(self, cir, messages):
        start = self._timings.pop("compile_start", time.time())
        elapsed = time.time() - start
        self._timings["compile"] = elapsed
        return None

    def before_simulate(self, cir, inputs, params, t_span, dt):
        self._timings["simulate_start"] = time.time()
        return None

    def after_simulate(self, result):
        start = self._timings.pop("simulate_start", time.time())
        elapsed = time.time() - start
        self._timings["simulate"] = elapsed
        return None

    def before_optimize(self, cir, config):
        self._timings["optimize_start"] = time.time()
        return None

    def after_optimize(self, result):
        start = self._timings.pop("optimize_start", time.time())
        elapsed = time.time() - start
        self._timings["optimize"] = elapsed
        return None

    def summary(self):
        return dict(self._timings)
