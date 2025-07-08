"""
Fiction Mode Orchestration Pipeline

Coordinates the entire Fiction Mode workflow from data ingestion to delivery.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .data_ingestion import RideDataIngestionAgent, RaceDataIngestionAgent, RideData, StageRaceData
from .analysis import AnalysisMappingAgent, AnalysisResult
from .writer import WriterAgent
from .editor import EditorAgent, EditingReport
from .delivery import DeliveryAgent, DeliveryOptions, DeliveredNarrative


@dataclass
class FictionModeConfig:
    """Configuration for Fiction Mode pipeline"""
    narrative_style: str = 'krabbe'
    delivery_format: str = 'markdown'
    include_metadata: bool = True
    save_to_archive: bool = True
    auto_detect_stage: bool = True
    require_min_duration: int = 30  # minutes
    user_bio: Optional[str] = None


@dataclass
class PipelineResult:
    """Complete result of Fiction Mode pipeline"""
    success: bool
    narrative: Optional[str]
    delivered_narrative: Optional[DeliveredNarrative]
    analysis: Optional[AnalysisResult]
    editing_report: Optional[EditingReport]
    error_message: Optional[str]
    processing_time_seconds: float


class FictionModeOrchestrator:
    """Orchestrates the complete Fiction Mode pipeline"""

    def __init__(self, config: Optional[FictionModeConfig] = None):
        self.config = config or FictionModeConfig()

        # Initialize agents
        self.ride_agent = RideDataIngestionAgent()
        self.race_agent = RaceDataIngestionAgent()
        self.analysis_agent = AnalysisMappingAgent()
        self.writer_agent = WriterAgent()
        self.editor_agent = EditorAgent()
        self.delivery_agent = DeliveryAgent()

    def process_todays_ride(self, user_feedback: Optional[str] = None) -> PipelineResult:
        """Process today's ride through the complete Fiction Mode pipeline"""

        start_time = datetime.now()

        try:
            print("🎬 Starting Fiction Mode pipeline...")

            # Step 1: Find today's TDF ride
            print("📥 Looking for today's TDF simulation ride...")
            ride_data = self.ride_agent.find_todays_tdf_ride()

            if not ride_data:
                return PipelineResult(
                    success=False,
                    narrative=None,
                    delivered_narrative=None,
                    analysis=None,
                    editing_report=None,
                    error_message="No qualifying TDF ride found for today",
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )

            # Check minimum duration
            duration_minutes = ride_data.duration_seconds / 60
            if duration_minutes < self.config.require_min_duration:
                return PipelineResult(
                    success=False,
                    narrative=None,
                    delivered_narrative=None,
                    analysis=None,
                    editing_report=None,
                    error_message=f"Ride too short: {duration_minutes:.0f} minutes (minimum: {self.config.require_min_duration})",
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )

            print(f"✅ Found ride: {ride_data.activity_name} ({duration_minutes:.0f} minutes)")

            # Step 2: Detect stage number and get race data
            stage_number = self.ride_agent.detect_tdf_activity({
                'name': ride_data.activity_name,
                'description': ride_data.description
            })

            if not stage_number and self.config.auto_detect_stage:
                # Try to infer stage from date or other context
                stage_number = self._infer_stage_number(ride_data.start_time)

            if not stage_number:
                return PipelineResult(
                    success=False,
                    narrative=None,
                    delivered_narrative=None,
                    analysis=None,
                    editing_report=None,
                    error_message="Could not detect TDF stage number from ride",
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )

            print(f"🏁 Detected Stage {stage_number}")

            # Step 3: Get race data
            print("📊 Fetching official race data...")
            race_data = self.race_agent.fetch_stage_data(stage_number, ride_data.start_time)

            if not race_data:
                return PipelineResult(
                    success=False,
                    narrative=None,
                    delivered_narrative=None,
                    analysis=None,
                    editing_report=None,
                    error_message=f"Could not fetch race data for Stage {stage_number}",
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )

            print(f"✅ Race data: {race_data.stage_name}, won by {race_data.winner}")

            # Step 4: Analysis and mapping
            print("🔍 Analyzing ride and mapping to race events...")
            analysis = self.analysis_agent.analyze_and_map(ride_data, race_data)

            print(f"✅ Analysis complete: {analysis.rider_role.role_type} - {analysis.rider_role.tactical_description}")

            # Step 5: Generate narrative
            print(f"✍️ Generating narrative in {self.config.narrative_style} style...")
            narrative = self.writer_agent.generate_narrative(
                analysis,
                self.config.narrative_style,
                self.config.user_bio
            )

            print(f"✅ Narrative generated ({len(narrative.split())} words)")

            # Step 6: Editorial review
            print("📝 Running editorial review...")
            editing_report = self.editor_agent.edit_narrative(
                narrative,
                analysis,
                self.config.narrative_style,
                user_feedback
            )

            print(f"✅ Editing complete (style: {editing_report.style_consistency_score:.2f}, accuracy: {editing_report.factual_accuracy_score:.2f})")

            # Step 7: Delivery
            print(f"📦 Formatting for delivery ({self.config.delivery_format})...")
            delivery_options = DeliveryOptions(
                format=self.config.delivery_format,
                include_metadata=self.config.include_metadata,
                save_to_archive=self.config.save_to_archive
            )

            delivered_narrative = self.delivery_agent.deliver_narrative(
                editing_report.edited_narrative,
                analysis,
                editing_report,
                delivery_options
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            print(f"🎉 Fiction Mode complete! ({processing_time:.1f}s)")
            if delivered_narrative.file_path:
                print(f"📄 Saved to: {delivered_narrative.file_path}")

            return PipelineResult(
                success=True,
                narrative=editing_report.edited_narrative,
                delivered_narrative=delivered_narrative,
                analysis=analysis,
                editing_report=editing_report,
                error_message=None,
                processing_time_seconds=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Pipeline error: {str(e)}"
            print(f"❌ {error_msg}")

            return PipelineResult(
                success=False,
                narrative=None,
                delivered_narrative=None,
                analysis=None,
                editing_report=None,
                error_message=error_msg,
                processing_time_seconds=processing_time
            )

    def process_specific_activity(self, activity_id: int, stage_number: int,
                                user_feedback: Optional[str] = None) -> PipelineResult:
        """Process a specific Strava activity as a TDF stage"""

        start_time = datetime.now()

        try:
            print(f"🎬 Processing activity {activity_id} as Stage {stage_number}...")

            # Get specific ride data
            ride_data = self.ride_agent.fetch_ride_data(activity_id)
            if not ride_data:
                return PipelineResult(
                    success=False,
                    narrative=None,
                    delivered_narrative=None,
                    analysis=None,
                    editing_report=None,
                    error_message=f"Could not fetch activity {activity_id}",
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )

            # Get race data for specified stage
            race_data = self.race_agent.fetch_stage_data(stage_number, ride_data.start_time)
            if not race_data:
                return PipelineResult(
                    success=False,
                    narrative=None,
                    delivered_narrative=None,
                    analysis=None,
                    editing_report=None,
                    error_message=f"Could not fetch race data for Stage {stage_number}",
                    processing_time_seconds=(datetime.now() - start_time).total_seconds()
                )

            # Continue with rest of pipeline...
            # (Same as process_todays_ride from Step 4 onwards)
            analysis = self.analysis_agent.analyze_and_map(ride_data, race_data)

            narrative = self.writer_agent.generate_narrative(
                analysis,
                self.config.narrative_style,
                self.config.user_bio
            )

            editing_report = self.editor_agent.edit_narrative(
                narrative,
                analysis,
                self.config.narrative_style,
                user_feedback
            )

            delivery_options = DeliveryOptions(
                format=self.config.delivery_format,
                include_metadata=self.config.include_metadata,
                save_to_archive=self.config.save_to_archive
            )

            delivered_narrative = self.delivery_agent.deliver_narrative(
                editing_report.edited_narrative,
                analysis,
                editing_report,
                delivery_options
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            return PipelineResult(
                success=True,
                narrative=editing_report.edited_narrative,
                delivered_narrative=delivered_narrative,
                analysis=analysis,
                editing_report=editing_report,
                error_message=None,
                processing_time_seconds=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return PipelineResult(
                success=False,
                narrative=None,
                delivered_narrative=None,
                analysis=None,
                editing_report=None,
                error_message=f"Pipeline error: {str(e)}",
                processing_time_seconds=processing_time
            )

    def preview_analysis(self, activity_id: Optional[int] = None) -> Optional[AnalysisResult]:
        """Preview the analysis without generating narrative"""

        try:
            if activity_id:
                ride_data = self.ride_agent.fetch_ride_data(activity_id)
            else:
                ride_data = self.ride_agent.find_todays_tdf_ride()

            if not ride_data:
                return None

            stage_number = self.ride_agent.detect_tdf_activity({
                'name': ride_data.activity_name,
                'description': ride_data.description
            })

            if not stage_number:
                stage_number = self._infer_stage_number(ride_data.start_time)

            if not stage_number:
                return None

            race_data = self.race_agent.fetch_stage_data(stage_number, ride_data.start_time)
            if not race_data:
                return None

            return self.analysis_agent.analyze_and_map(ride_data, race_data)

        except Exception as e:
            print(f"Preview error: {e}")
            return None

    def _infer_stage_number(self, ride_date: datetime) -> Optional[int]:
        """Infer stage number from ride date during Tour de France"""

        # TDF 2025 starts July 5th - this is simplified logic
        # In production, this would use actual TDF calendar

        tdf_start_date = datetime(2025, 7, 5)

        if ride_date < tdf_start_date:
            return None

        days_since_start = (ride_date.date() - tdf_start_date.date()).days

        # Simple mapping - first 3 weeks = 21 stages
        if 0 <= days_since_start <= 20:
            return days_since_start + 1

        return None

    def get_available_styles(self) -> List[str]:
        """Get available narrative styles"""
        return self.writer_agent.get_available_styles()

    def update_config(self, **kwargs):
        """Update pipeline configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
