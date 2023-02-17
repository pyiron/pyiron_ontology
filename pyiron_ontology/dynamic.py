# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A class for lazy construction of the ontologies
"""

from pyiron_ontology.atomistics.constructor import AtomisticsOntology
from pyiron_ontology.example.constructor import ExampleOntology


class DynamicOntologies:
    _atomistics = None
    _example = None

    @classmethod
    def atomistics(cls):
        if cls._atomistics is None:
            cls._atomistics = AtomisticsOntology().onto
        return cls._atomistics

    @classmethod
    def example(cls):
        if cls._example is None:
            cls._example = ExampleOntology().onto
        return cls._example
