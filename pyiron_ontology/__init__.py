from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions

from pyiron_ontology.atomistics.constructor import AtomisticsOntology
from pyiron_ontology.workflow import build_tree, build_path
from pyiron_ontology.dynamic import DynamicOntologies as dynamic

from pyiron_ontology.atomistics.reasoning import AtomisticsReasoner
