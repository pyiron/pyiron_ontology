import unittest
from dataclasses import dataclass

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyiron_workflow import Workflow
from rdflib import OWL, RDF, RDFS, Literal, Namespace, URIRef
from semantikon.ontology import (
    PNS,
    get_knowledge_graph,
    validate_values,
)
from semantikon.typing import u

from pyiron_ontology.parser import export_to_dict, parse_workflow

EX = Namespace("http://example.org/")


@Workflow.wrap.as_function_node("speed")
def calculate_speed(
    distance: u(float, units="meter") = 10.0,
    time: u(float, units="second") = 2.0,
) -> u(
    float,
    units="meter/second",
    triples=(
        (EX.somehowRelatedTo, "inputs.time"),
        (EX.subject, EX.predicate, EX.object),
        (EX.subject, EX.predicate, None),
        (None, EX.predicate, EX.object),
    ),
):
    return distance / time


@Workflow.wrap.as_function_node("result")
@u(uri=EX.Addition)
def add(a: float, b: float) -> u(float, triples=(EX.HasOperation, EX.Addition)):
    return a + b


@Workflow.wrap.as_function_node("result")
def multiply(a: float, b: float) -> u(
    float,
    triples=(
        (EX.HasOperation, EX.Multiplication),
        (PNS.inheritsPropertiesFrom, "inputs.a"),
    ),
):
    return a * b


@Workflow.wrap.as_macro_node("result")
def operation(macro=None, a: float = 1.0, b: float = 1.0) -> float:
    macro.addition = add(a=a, b=b)
    macro.multiply = multiply(a=macro.addition, b=b)
    return macro.multiply


@Workflow.wrap.as_function_node("result")
def correct_analysis(
    a: u(
        float,
        restrictions=(
            (OWL.onProperty, EX.HasOperation),
            (OWL.someValuesFrom, EX.Addition),
        ),
    ),
) -> float:
    return a


@Workflow.wrap.as_function_node("result")
def wrong_analysis(
    a: u(
        float,
        restrictions=(
            (OWL.onProperty, EX.HasOperation),
            (OWL.someValuesFrom, EX.Division),
        ),
    ),
) -> float:
    return a


@Workflow.wrap.as_function_node
def multiple_outputs(a: int = 1, b: int = 2) -> tuple[int, int]:
    return a, b


class TestParser(unittest.TestCase):
    def test_parser(self):
        wf = Workflow("speed")
        wf.c = calculate_speed()
        output_dict = export_to_dict(wf)
        for label in ["inputs", "outputs", "nodes", "data_edges", "label"]:
            self.assertIn(label, output_dict)

    def test_units_with_sparql(self):
        wf = Workflow("speed")
        wf.speed = calculate_speed()
        wf.run()
        graph = parse_workflow(wf)
        query_txt = [
            "PREFIX ex: <http://example.org/>",
            "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
            f"PREFIX pns: <{PNS.BASE}>",
            "SELECT DISTINCT ?speed ?units",
            "WHERE {",
            "    ?output pns:hasValue ?output_tag .",
            "    ?output_tag rdf:value ?speed .",
            "    ?output_tag pns:hasUnits ?units .",
            "}",
        ]
        query = "\n".join(query_txt)
        results = graph.query(query)
        self.assertEqual(len(results), 3)
        result_list = [row[0].value for row in graph.query(query)]
        self.assertEqual(sorted(result_list), [2.0, 5.0, 10.0])

    def test_triples(self):
        wf = Workflow("speed")
        wf.speed = calculate_speed()
        graph = parse_workflow(wf)
        subj = URIRef("http://example.org/subject")
        obj = URIRef("http://example.org/object")
        label = URIRef("speed.speed.outputs.speed")
        self.assertIn(
            (None, PNS.hasUnits, URIRef("meter/second")),
            graph,
            msg=graph.serialize(format="turtle"),
        )
        ex_triple = (
            None,
            EX.somehowRelatedTo,
            URIRef("speed.speed.inputs.time"),
        )
        self.assertIn(
            ex_triple,
            graph,
            msg=f"Triple {ex_triple} not found {graph.serialize(format='turtle')}",
        )
        self.assertIn((subj, EX.predicate, obj), graph)
        self.assertIn((subj, EX.predicate, label), graph)
        self.assertIn((label, EX.predicate, obj), graph)

    def test_correct_analysis(self):
        def get_graph(wf):
            data = export_to_dict(wf)
            graph = get_knowledge_graph(data)
            return graph

        wf = Workflow("correct_analysis")
        wf.addition = add(a=1.0, b=2.0)
        wf.multiply = multiply(a=wf.addition, b=3.0)
        wf.analysis = correct_analysis(a=wf.multiply)
        graph = get_graph(wf)
        # Not needed in semantikon 0.0.13
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertEqual(len(validate_values(graph)), 0)
        wf = Workflow("wrong_analysis")
        wf.addition = add(a=1.0, b=2.0)
        wf.multiply = multiply(a=wf.addition, b=3.0)
        wf.analysis = wrong_analysis(a=wf.multiply)
        graph = get_graph(wf)
        # Not needed in semantikon 0.0.13
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertEqual(len(validate_values(graph)), 1)

    def test_multiple_outputs(self):
        wf = Workflow("multiple_outputs")
        wf.node = multiple_outputs()
        wf.node.run()
        data = export_to_dict(wf)
        self.assertEqual(data["outputs"]["node__a"]["value"], 1)
        self.assertEqual(data["outputs"]["node__b"]["value"], 2)

    def test_parse_workflow(self):
        wf = Workflow("correct_analysis")
        wf.addition = add(a=1.0, b=2.0)
        data = export_to_dict(wf)
        graph = get_knowledge_graph(data)
        tag = "correct_analysis.addition.inputs.a"
        self.assertEqual(
            len(list(graph.triples((URIRef(tag), RDFS.label, Literal(tag))))),
            1,
        )
        self.assertTrue(
            EX.Addition
            in list(graph.objects(URIRef("correct_analysis.addition"), RDF.type))
        )

    def test_namespace(self):
        self.assertEqual(PNS.hasUnits, URIRef("http://pyiron.org/ontology/hasUnits"))
        with self.assertRaises(AttributeError):
            _ = PNS.ahoy

    def test_parsing_without_running(self):
        wf = Workflow("test")
        wf.addition = add(a=1.0, b=2.0)
        data = export_to_dict(wf)
        self.assertFalse("value" in data["outputs"]["addition__result"])
        graph = get_knowledge_graph(data)
        self.assertEqual(
            len(list(graph.triples((None, RDF.value, None)))),
            2,
            msg="There should be only values for a and b, but not for the output",
        )
        wf.run()
        data = export_to_dict(wf)
        graph = get_knowledge_graph(data)
        self.assertEqual(
            len(list(graph.triples((None, RDF.value, None)))),
            3,
            msg="There should be values for a, b and the output",
        )

    def test_macro(self):
        wf = Workflow("operation")
        wf.node = operation(a=1.0, b=2.0)
        wf.run()
        data = export_to_dict(wf)
        self.assertEqual(
            set(data.keys()), {"data_edges", "inputs", "label", "nodes", "outputs"}
        )
        self.assertEqual(
            data["inputs"]["node__b"],
            {"default": 1.0, "value": 2.0, "type_hint": float},
        )


@dataclass
class Input:
    T: u(float, units="kelvin")
    n: int

    @dataclass
    class parameters:
        a: int = 2

    class not_dataclass:
        b: int = 3


@dataclass
class Output:
    E: u(float, units="electron_volt")
    L: u(float, units="angstrom")


@Workflow.wrap.as_function_node
def run_md(inp: Input) -> Output:
    out = Output(E=1.0, L=2.0)
    return out


class TestDataclass(unittest.TestCase):
    def test_dataclass(self):
        wf = Workflow("my_wf")
        inp = Input(T=300.0, n=100)
        inp.parameters.a = 1
        wf.node = run_md(inp)
        wf.run()
        data = export_to_dict(wf)
        graph = get_knowledge_graph(data)
        i_txt = "my_wf.node.inputs.inp"
        o_txt = "my_wf.node.outputs.out"
        triples = (
            (URIRef(f"{i_txt}.n.value"), RDFS.subClassOf, URIRef(f"{i_txt}.value")),
            (URIRef(f"{i_txt}.n.value"), RDF.value, Literal(100)),
            (URIRef(f"{i_txt}.parameters.a.value"), RDF.value, Literal(1)),
            (URIRef(o_txt), PNS.hasValue, URIRef(f"{o_txt}.E.value")),
        )
        s = graph.serialize(format="turtle")
        for ii, triple in enumerate(triples):
            with self.subTest(i=ii):
                self.assertEqual(
                    len(list(graph.triples(triple))),
                    1,
                    msg=f"{triple} not found in {s}",
                )
        self.assertIsNone(graph.value(URIRef(f"{i_txt}.not_dataclass.b.value")))


if __name__ == "__main__":
    unittest.main()
