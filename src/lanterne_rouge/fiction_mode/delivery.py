"""
Delivery Agent for Fiction Mode

Formats and delivers completed narratives in various formats.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

from .analysis import AnalysisResult
from .editor import EditingReport


@dataclass
class DeliveryOptions:
    """Configuration for narrative delivery"""
    format: str  # 'markdown', 'html', 'email', 'json'
    include_metadata: bool = True
    include_analysis: bool = False
    include_ride_data: bool = False
    title_format: str = "Stage {stage_num} — {stage_name}"
    add_timestamp: bool = True
    save_to_archive: bool = True


@dataclass
class DeliveredNarrative:
    """Complete delivered narrative package"""
    title: str
    formatted_content: str
    metadata: Dict[str, Any]
    file_path: Optional[str]
    delivery_timestamp: datetime
    format: str


class DeliveryAgent:
    """Formats and delivers completed cycling narratives"""

    def __init__(self, archive_dir: str = "output/fiction_mode"):
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def deliver_narrative(self,
                         narrative: str,
                         analysis: AnalysisResult,
                         editing_report: EditingReport,
                         options: DeliveryOptions) -> DeliveredNarrative:
        """Deliver narrative in specified format"""

        # Generate title
        title = self._generate_title(analysis, options.title_format)

        # Build metadata
        metadata = self._build_metadata(analysis, editing_report, options)

        # Format content based on delivery format
        if options.format == 'markdown':
            formatted_content = self._format_markdown(narrative, title, metadata, options)
        elif options.format == 'html':
            formatted_content = self._format_html(narrative, title, metadata, options)
        elif options.format == 'email':
            formatted_content = self._format_email(narrative, title, metadata, options)
        elif options.format == 'json':
            formatted_content = self._format_json(narrative, title, metadata, analysis, editing_report)
        else:
            formatted_content = narrative  # Plain text fallback

        # Save to archive if requested
        file_path = None
        if options.save_to_archive:
            file_path = self._save_to_archive(formatted_content, title, analysis, options.format)

        return DeliveredNarrative(
            title=title,
            formatted_content=formatted_content,
            metadata=metadata,
            file_path=str(file_path) if file_path else None,
            delivery_timestamp=datetime.now(),
            format=options.format
        )

    def _generate_title(self, analysis: AnalysisResult, title_format: str) -> str:
        """Generate narrative title"""

        stage_data = analysis.stage_data

        return title_format.format(
            stage_num=stage_data.stage_number,
            stage_name=stage_data.stage_name,
            date=stage_data.date.strftime('%B %d, %Y'),
            winner=stage_data.winner,
            distance=stage_data.distance_km
        )

    def _build_metadata(self,
                       analysis: AnalysisResult,
                       editing_report: EditingReport,
                       options: DeliveryOptions) -> Dict[str, Any]:
        """Build metadata for the narrative"""

        metadata = {
            'generation_timestamp': datetime.now().isoformat(),
            'stage_number': analysis.stage_data.stage_number,
            'stage_name': analysis.stage_data.stage_name,
            'stage_date': analysis.stage_data.date.isoformat(),
            'stage_winner': analysis.stage_data.winner,
            'rider_role': analysis.rider_role.role_type,
            'narrative_style': 'krabbe',  # Could be parameterized
            'word_count': len(editing_report.edited_narrative.split()),
        }

        if options.include_analysis:
            metadata.update({
                'performance_summary': analysis.performance_summary,
                'mapped_events_count': len(analysis.mapped_events),
                'editing_scores': {
                    'style_consistency': editing_report.style_consistency_score,
                    'factual_accuracy': editing_report.factual_accuracy_score,
                    'readability': editing_report.readability_score
                }
            })

        if options.include_ride_data:
            metadata.update({
                'ride_data': {
                    'activity_id': analysis.ride_data.activity_id,
                    'duration_minutes': analysis.ride_data.duration_seconds / 60,
                    'distance_km': analysis.ride_data.distance_meters / 1000,
                    'avg_power': analysis.ride_data.avg_power,
                    'avg_hr': analysis.ride_data.avg_hr
                }
            })

        return metadata

    def _format_markdown(self, narrative: str, title: str, metadata: Dict[str, Any], options: DeliveryOptions) -> str:
        """Format narrative as Markdown"""

        content = f"# {title}\n\n"

        # Add stage info
        stage_date = datetime.fromisoformat(metadata['stage_date']).strftime('%B %d, %Y')
        content += f"*{stage_date}*\n\n"

        # Add quote or subtitle if present in narrative
        lines = narrative.split('\n')
        if lines and lines[0].startswith('"') and lines[0].endswith('"'):
            content += f"*{lines[0]}*\n\n"
            narrative = '\n'.join(lines[1:]).strip()

        # Add separator
        content += "⸻\n\n"

        # Add main narrative
        content += narrative + "\n\n"

        # Add metadata section if requested
        if options.include_metadata:
            content += "---\n\n"
            content += f"**Stage:** {metadata['stage_name']}  \n"
            content += f"**Winner:** {metadata['stage_winner']}  \n"
            content += f"**Role:** {metadata['rider_role']}  \n"
            content += f"**Words:** {metadata['word_count']}  \n"

            if options.add_timestamp:
                timestamp = datetime.fromisoformat(metadata['generation_timestamp']).strftime('%B %d, %Y at %I:%M %p')
                content += f"**Generated:** {timestamp}  \n"

        return content

    def _format_html(self, narrative: str, title: str, metadata: Dict[str, Any], options: DeliveryOptions) -> str:
        """Format narrative as HTML"""

        # First convert to markdown, then to HTML
        markdown_content = self._format_markdown(narrative, title, metadata, options)

        # Convert markdown to HTML
        if MARKDOWN_AVAILABLE:
            html_content = markdown.markdown(markdown_content, extensions=['nl2br'])
        else:
            # Fallback: simple HTML conversion
            html_content = markdown_content.replace('\n', '<br>\n')

        # Wrap in complete HTML document
        html_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Georgia, serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        em {{
            color: #7f8c8d;
        }}
        .metadata {{
            background-color: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #3498db;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""

        return html_document

    def _format_email(self, narrative: str, title: str, metadata: Dict[str, Any], options: DeliveryOptions) -> str:
        """Format narrative for email delivery"""

        subject = f"Tour de France Fiction Mode: {title}"

        # Email body with plain text formatting
        body = f"""Subject: {subject}

{title}
{datetime.fromisoformat(metadata['stage_date']).strftime('%B %d, %Y')}

⸻

{narrative}

---

Stage: {metadata['stage_name']}
Winner: {metadata['stage_winner']}
Your Role: {metadata['rider_role']}

Generated by Lanterne Rouge Fiction Mode
{datetime.fromisoformat(metadata['generation_timestamp']).strftime('%B %d, %Y at %I:%M %p')}
"""

        return body

    def _format_json(self, narrative: str, title: str, metadata: Dict[str, Any],
                    analysis: AnalysisResult, editing_report: EditingReport) -> str:
        """Format as structured JSON"""

        json_data = {
            'title': title,
            'narrative': narrative,
            'metadata': metadata,
            'analysis': {
                'stage_data': {
                    'stage_number': analysis.stage_data.stage_number,
                    'stage_name': analysis.stage_data.stage_name,
                    'date': analysis.stage_data.date.isoformat(),
                    'distance_km': analysis.stage_data.distance_km,
                    'stage_type': analysis.stage_data.stage_type,
                    'winner': analysis.stage_data.winner,
                    'weather': analysis.stage_data.weather
                },
                'rider_role': {
                    'role_type': analysis.rider_role.role_type,
                    'position_in_race': analysis.rider_role.position_in_race,
                    'tactical_description': analysis.rider_role.tactical_description,
                    'effort_level': analysis.rider_role.effort_level
                },
                'performance_summary': analysis.performance_summary,
                'mapped_events_count': len(analysis.mapped_events)
            },
            'editing': {
                'style_consistency_score': editing_report.style_consistency_score,
                'factual_accuracy_score': editing_report.factual_accuracy_score,
                'readability_score': editing_report.readability_score,
                'errors_found': editing_report.errors_found,
                'improvements_made': editing_report.improvements_made
            }
        }

        return json.dumps(json_data, indent=2, ensure_ascii=False)

    def _save_to_archive(self, content: str, title: str, analysis: AnalysisResult, format: str) -> Path:
        """Save narrative to archive"""

        # Create filename
        stage_num = analysis.stage_data.stage_number
        date_str = analysis.stage_data.date.strftime('%Y-%m-%d')

        # Sanitize title for filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]  # Limit length

        filename = f"stage_{stage_num:02d}_{date_str}_{safe_title}.{format}"
        file_path = self.archive_dir / filename

        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"📄 Narrative saved to: {file_path}")
        return file_path

    def get_archive_files(self) -> List[Dict[str, Any]]:
        """Get list of archived narratives"""

        files = []
        for file_path in self.archive_dir.glob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    'filename': file_path.name,
                    'path': str(file_path),
                    'size_bytes': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })

        return sorted(files, key=lambda x: x['created'], reverse=True)

    def deliver_to_email(self, delivered_narrative: DeliveredNarrative,
                        recipient_email: str) -> bool:
        """Send narrative via email (requires email configuration)"""

        try:
            # This would integrate with the existing email notification system
            # For now, just print what would be sent
            print(f"📧 Would send narrative to {recipient_email}")
            print(f"Subject: Tour de France Fiction Mode: {delivered_narrative.title}")
            print("Content preview:")
            print(delivered_narrative.formatted_content[:200] + "...")
            return True

        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

    def create_season_archive(self, year: int = 2025) -> str:
        """Create a combined archive of all narratives for the season"""

        # Find all narratives for the year
        pattern = f"*{year}*"
        narrative_files = list(self.archive_dir.glob(pattern))

        if not narrative_files:
            return f"No narratives found for {year}"

        # Sort by stage number
        narrative_files.sort()

        # Combine into season archive
        season_content = f"# Tour de France {year} - Fiction Mode Season Archive\n\n"
        season_content += f"Generated on {datetime.now().strftime('%B %d, %Y')}\n\n"
        season_content += "⸻\n\n"

        for file_path in narrative_files:
            if file_path.suffix == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    season_content += content + "\n\n⸻\n\n"

        # Save season archive
        season_filename = f"tdf_{year}_complete_season.md"
        season_path = self.archive_dir / season_filename

        with open(season_path, 'w', encoding='utf-8') as f:
            f.write(season_content)

        print(f"📚 Season archive created: {season_path}")
        return str(season_path)
