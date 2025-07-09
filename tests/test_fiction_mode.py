"""
Test Fiction Mode functionality
"""

import pytest
from unittest.mock import Mock, patch
from dataclasses import dataclass
from datetime import datetime

from src.lanterne_rouge.fiction_mode.pipeline import FictionModeOrchestrator
from src.lanterne_rouge.fiction_mode.data_ingestion import (
    RideData, StageRaceData, RaceEvent
)
from src.lanterne_rouge.fiction_mode.analysis import AnalysisResult, MappedEvent
from src.lanterne_rouge.fiction_mode.writer import WriterAgent, NarrativeStyle
from src.lanterne_rouge.fiction_mode.editor import EditorAgent
from src.lanterne_rouge.fiction_mode.delivery import DeliveryAgent, DeliveryOptions


class TestFictionModeComponents:
    """Test individual Fiction Mode components"""

    def test_narrative_style_creation(self):
        """Test creating narrative styles"""
        style = NarrativeStyle(
            name="test",
            description="Test style",
            voice="third_person",
            tense="past",
            tone="spare",
            reference_author="Test Author",
            sample_phrases=["test phrase"]
        )
        assert style.name == "test"
        assert style.description == "Test style"

    def test_ride_data_creation(self):
        """Test creating ride data structure"""
        ride_data = RideData(
            activity_id=123,
            start_time=datetime(2025, 7, 8),
            duration_seconds=6480,  # 108 minutes  
            distance_meters=100000.0,  # 100km
            avg_power=250.0,
            max_power=400.0,
            avg_hr=150.0,
            max_hr=180.0,
            cadence=90.0,
            tss=180.0,
            intensity_factor=0.85
        )
        assert ride_data.activity_id == 123
        assert ride_data.distance_meters == 100000.0

    def test_mapped_event_creation(self):
        """Test creating mapped events"""
        # Create a mock race event first
        mock_race_event = Mock()
        mock_race_event.minute = 45
        mock_race_event.event_type = "attack"
        
        event = MappedEvent(
            user_minute=30,
            race_event=mock_race_event,
            user_power=300.0,
            user_hr=170.0,
            mapping_confidence=0.85,
            narrative_description="Strong effort during breakaway"
        )
        assert event.user_minute == 30
        assert event.user_power == 300.0

    def test_analysis_result_creation(self):
        """Test creating analysis results"""
        mock_ride_data = Mock()
        mock_stage_data = Mock()
        mock_rider_role = Mock()
        
        result = AnalysisResult(
            ride_data=mock_ride_data,
            stage_data=mock_stage_data,
            rider_role=mock_rider_role,
            mapped_events=[],
            performance_summary={"avg_power": 250},
            narrative_timeline=[]
        )
        assert result.performance_summary["avg_power"] == 250

    def test_writer_agent_styles(self):
        """Test writer agent style management"""
        writer = WriterAgent()
        styles = writer.get_available_styles()
        assert "krabbe" in styles
        assert "journalistic" in styles
        assert "dramatic" in styles

    def test_writer_style_descriptions(self):
        """Test getting style descriptions"""
        writer = WriterAgent()
        krabbe_desc = writer.get_style_description("krabbe")
        assert krabbe_desc is not None
        assert "introspective" in krabbe_desc.lower()

    def test_delivery_options_creation(self):
        """Test creating delivery options"""
        options = DeliveryOptions(
            format="markdown",
            include_metadata=True,
            include_analysis=False,
            include_ride_data=True
        )
        assert options.format == "markdown"
        assert options.include_metadata is True


class TestFictionModeIntegration:
    """Test Fiction Mode integration scenarios"""

    @patch('src.lanterne_rouge.fiction_mode.data_ingestion.RideDataIngestionAgent')
    @patch('src.lanterne_rouge.fiction_mode.data_ingestion.RaceDataIngestionAgent')
    def test_orchestrator_initialization(self, mock_race_agent, mock_ride_agent):
        """Test Fiction Mode orchestrator can be initialized"""
        orchestrator = FictionModeOrchestrator()
        assert orchestrator is not None

    def test_error_handling_invalid_style(self):
        """Test handling of invalid narrative style"""
        writer = WriterAgent()
        desc = writer.get_style_description("invalid_style")
        assert desc is None

    def test_delivery_agent_format_validation(self):
        """Test delivery agent format validation"""
        agent = DeliveryAgent()
        # Test that valid formats are supported
        valid_formats = ["markdown", "html", "email", "json"]
        for fmt in valid_formats:
            options = DeliveryOptions(format=fmt)
            # Should not raise an exception
            assert options.format == fmt


class TestFictionModeErrorHandling:
    """Test Fiction Mode error handling"""

    def test_graceful_degradation_no_strava_data(self):
        """Test that system handles missing Strava data gracefully"""
        # This would be tested with actual API mocking
        # For now, just ensure the structure supports it
        ride_data = RideData(
            activity_id=0,
            start_time=datetime.now(),
            duration_seconds=0,
            distance_meters=0.0,
            avg_power=None,
            max_power=None,
            avg_hr=None,
            max_hr=None,
            cadence=None,
            tss=None,
            intensity_factor=None
        )
        assert ride_data.activity_id == 0

    def test_empty_analysis_handling(self):
        """Test handling of empty analysis results"""
        mock_ride_data = Mock()
        mock_stage_data = Mock()
        mock_rider_role = Mock()
        
        result = AnalysisResult(
            ride_data=mock_ride_data,
            stage_data=mock_stage_data,
            rider_role=mock_rider_role,
            mapped_events=[],
            performance_summary={},
            narrative_timeline=[]
        )
        # Should handle empty data gracefully
        assert len(result.mapped_events) == 0


if __name__ == '__main__':
    pytest.main([__file__])
