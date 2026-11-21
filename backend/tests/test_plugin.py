import pytest
from compiler.plugin.base import PluginBase
from compiler.plugin.manager import PluginManager, get_manager, reset_manager
from compiler.plugin.timing import TimingPlugin
from compiler.pipeline import CompilerPipeline


class TestPluginBase:
    def test_base_properties(self):
        p = PluginBase()
        assert p.name is not None

    def test_hooks_return_none_by_default(self):
        p = PluginBase()
        assert p.before_compile("source") is None
        assert p.after_compile(None, []) is None
        assert p.before_simulate(None, None, None, None, None) is None
        assert p.after_simulate(None) is None


class CapturePlugin(PluginBase):
    def __init__(self):
        self.events = []

    @property
    def name(self):
        return "Capture"

    def before_compile(self, source_code):
        self.events.append(("before_compile", source_code))
        return None

    def after_compile(self, cir, messages):
        self.events.append(("after_compile", cir, messages))
        return None

    def before_simulate(self, cir, inputs, params, t_span, dt):
        self.events.append(("before_simulate", cir, inputs))
        return None

    def after_simulate(self, result):
        self.events.append(("after_simulate", result))
        return None


class TestPluginManager:
    def setup_method(self):
        reset_manager()

    def test_manager_is_singleton(self):
        m1 = get_manager()
        m2 = get_manager()
        assert m1 is m2

    def test_reset_creates_new_manager(self):
        m1 = get_manager()
        reset_manager()
        m2 = get_manager()
        assert m1 is not m2

    def test_register_plugin_instance(self):
        mgr = PluginManager()
        plugin = CapturePlugin()
        mgr.register(plugin)
        assert len(mgr.plugins) == 1

    def test_register_plugin_class(self):
        mgr = PluginManager()
        mgr.register(CapturePlugin)
        assert len(mgr.plugins) == 1

    def test_no_duplicate_registration(self):
        mgr = PluginManager()
        mgr.register(CapturePlugin())
        mgr.register(CapturePlugin())
        assert len(mgr.plugins) == 1

    def test_invoke_captures_events(self):
        mgr = PluginManager()
        plugin = CapturePlugin()
        mgr.register(plugin)
        mgr.invoke("before_compile", "IF aTc -> GFP")
        assert len(plugin.events) == 1
        assert plugin.events[0][0] == "before_compile"

    def test_invoke_all_plugins(self):
        mgr = PluginManager()
        p1 = CapturePlugin()
        mgr.register(p1)
        mgr.register(TimingPlugin())
        mgr.invoke("before_compile", "test")
        assert len(p1.events) == 1

    def test_unknown_hook_does_not_crash(self):
        mgr = PluginManager()
        mgr.register(CapturePlugin())
        mgr.invoke("nonexistent_hook")
        assert True

    def test_plugin_error_does_not_crash(self):
        class BrokenPlugin(PluginBase):
            @property
            def name(self):
                return "Broken"
            def before_compile(self, source_code):
                raise RuntimeError("oops")
        mgr = PluginManager()
        mgr.register(BrokenPlugin())
        mgr.register(CapturePlugin())
        mgr.invoke("before_compile", "test")
        mgr.invoke("after_compile", None, [])
        assert True


class TestTimingPlugin:
    def test_timing_after_compile(self):
        p = TimingPlugin()
        assert p._timings.get("compile") is None
        p.before_compile("test")
        p.after_compile(None, [])
        assert "compile" in p._timings
        assert p._timings["compile"] >= 0

    def test_summary_returns_dict(self):
        p = TimingPlugin()
        p.before_compile("test")
        p.after_compile(None, [])
        s = p.summary()
        assert "compile" in s


class TestPipelineIntegration:
    def test_pipeline_with_capture_plugin(self):
        reset_manager()
        mgr = get_manager()
        plugin = CapturePlugin()
        mgr.register(plugin)
        pipeline = CompilerPipeline()
        cir, _ = pipeline.run("IF aTc -> GFP")
        events = [e[0] for e in plugin.events]
        assert "before_compile" in events
        assert "after_compile" in events

    def test_pipeline_without_plugins_still_works(self):
        reset_manager()
        pipeline = CompilerPipeline()
        cir, _ = pipeline.run("IF aTc -> GFP")
        assert cir is not None
