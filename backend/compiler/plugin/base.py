class PluginBase:
    @property
    def name(self):
        return self.__class__.__name__

    def before_compile(self, source_code):
        return None

    def after_compile(self, cir, messages):
        return None

    def before_simulate(self, cir, inputs, params, t_span, dt):
        return None

    def after_simulate(self, result):
        return None

    def before_optimize(self, cir, config):
        return None

    def after_optimize(self, result):
        return None

    def before_export(self, backend_name, cir, config):
        return None

    def after_export(self, output):
        return None
