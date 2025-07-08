"""
Fiction Mode - Automated Cycling Narrative Generator

Generates immersive, stage-by-stage cycling narratives by blending user's
real ride data from Strava with official Tour de France race events.
"""

from .pipeline import FictionModeOrchestrator
from .data_ingestion import RideDataIngestionAgent, RaceDataIngestionAgent
from .analysis import AnalysisMappingAgent
from .writer import WriterAgent
from .editor import EditorAgent
from .delivery import DeliveryAgent

__all__ = [
    'FictionModeOrchestrator',
    'RideDataIngestionAgent',
    'RaceDataIngestionAgent',
    'AnalysisMappingAgent',
    'WriterAgent',
    'EditorAgent',
    'DeliveryAgent'
]
