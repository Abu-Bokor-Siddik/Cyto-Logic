from .sbol_backend import SBOLBackend
from .simulation_backend import SimulationBackend
from .dna_backend import DNABackend
from .svg_backend import SVGBackend
from .genbank_backend import GenBankBackend


_BACKENDS = {}


def register(backend):
    _BACKENDS[backend.name] = backend


def get(name):
    return _BACKENDS.get(name)


def list_backends():
    return list(_BACKENDS.keys())


register(SBOLBackend())
register(SimulationBackend())
register(DNABackend())
register(SVGBackend())
register(GenBankBackend())
