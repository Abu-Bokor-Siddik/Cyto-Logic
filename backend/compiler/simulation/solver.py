class Solver:
    def __init__(self, dt=0.01):
        if dt <= 0:
            raise ValueError("dt must be positive")
        self.dt = dt

    def run(self, ode_system, y0, t_span):
        t0, t1 = t_span
        if t1 <= t0:
            raise ValueError("t_span[1] must be greater than t_span[0]")
        times = []
        values = []
        t = t0
        y = list(y0)
        times.append(t)
        values.append(list(y))
        while t < t1 - 1e-12:
            y = self._step(ode_system, t, y)
            t += self.dt
            times.append(t)
            values.append(list(y))
        return times, values

    def _step(self, ode_system, t, y):
        return self._rk4(ode_system, t, y, self.dt)

    @staticmethod
    def _rk4(f, t, y, dt):
        k1 = f(t, y)
        k2 = f(t + 0.5 * dt, [yi + 0.5 * dt * k1i for yi, k1i in zip(y, k1)])
        k3 = f(t + 0.5 * dt, [yi + 0.5 * dt * k2i for yi, k2i in zip(y, k2)])
        k4 = f(t + dt, [yi + dt * k3i for yi, k3i in zip(y, k3)])
        return [
            yi + (dt / 6.0) * (k1i + 2.0 * k2i + 2.0 * k3i + k4i)
            for yi, k1i, k2i, k3i, k4i in zip(y, k1, k2, k3, k4)
        ]
