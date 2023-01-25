from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions


from pyiron_ontology.atomistics.constructor import AtomisticsOntology
from pyiron_ontology.atomistics.tree import build_tree as build_atomistics_tree

atomistics_onto = AtomisticsOntology().onto
from pyiron_ontology.atomistics.reasoning import AtomisticsReasoner
