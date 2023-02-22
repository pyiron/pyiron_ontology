from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions

from pyiron_ontology.atomistics.constructor import AtomisticsOntology
from pyiron_ontology.constructor import Constructor
from pyiron_ontology.dynamic import DynamicOntologies as dynamic

from pyiron_ontology.atomistics.reasoning import AtomisticsReasoner
