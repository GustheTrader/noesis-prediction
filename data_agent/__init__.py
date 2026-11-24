"""NOESIS data agent: Neo4j graph + test data -> ontology proposal."""

from .agent import DataAgent
from .graph_source import GraphSnapshot, Neo4jConfig
from .ontology import OntologyProposal

__all__ = ["DataAgent", "GraphSnapshot", "Neo4jConfig", "OntologyProposal"]
