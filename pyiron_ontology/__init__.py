from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions

from pyiron_ontology.atomistics.constructor import AtomisticsOntology
from pyiron_ontology.workflow import build_tree, build_path
from pyiron_ontology.dynamic import DynamicOntologies

from pyiron_ontology.atomistics.reasoning import AtomisticsReasoner


class Pyironto:
    build_tree = build_tree
    dynamic = DynamicOntologies
    static = None  # TODO: Allow loading constructed ontologies from a static/ dir

# from pyiron_ontology import Pyironto
# onto = Pyironto.dynamic.atomistics
# Pyironto.build_tree(onto.Bulk_modulus)
