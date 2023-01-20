# pyiron_ontology

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/pyiron/pyiron_ontology/HEAD?labpath=example.ipynb)

## Overview

`pyiron_ontology` is a new pyiron project built on top of `owlready2` for ontologically-guided workflow design.
This project is currently in alpha-stage and subject to rapid change.
Right now, there is only an ontology for pyiron-atomistics, and it is quite limited in scope.
However, at present you are already able to automatically generate a tree of workflows for any of the properties defined, e.g.:

```python
from pyiron_ontology import AtomisticsReasoner, atomistics_onto as onto
reasoner = AtomisticsReasoner(onto) 
bulk_modulus_worflows = reasoner.build_tree(onto.Bulk_modulus)
bulk_modulus_worflows.render()  # Still very ugly! Graphviz rendering forthcoming...
```

Or leverage the ontology to search over your existing pyiron data for instances of a particular property, e.g.:

```python
from pyiron_atomistics import Project
pr = Project('my_project')

reasoner.search_database_for_property(onto.B_prime, pr, select_alloy="Cu")
```
