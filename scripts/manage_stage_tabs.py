#!/usr/bin/env python3
"""
Dynamic Stage Documentation Manager

Manages stage tab visibility based on completion status:
- Future stages: Only "Planned" tab
- Current stage (with briefing): "Recommended" + "Planned" tabs  
- Completed stages: "Completed" + "Recommended" + "Planned" tabs
"""

import json
from pathlib import Path
from datetime import datetime, date


class StageManager:
    
    def __init__(self):
        self.tdf_data = self.load_tdf_data()
        self.current_stage = self.determine_current_stage()
        
    def load_tdf_data(self):
        """Load TDF points data to determine completion status."""
        points_file = Path("output/tdf_points.json")
        if points_file.exists():
            with open(points_file, 'r') as f:
                return json.load(f)
        return {"stages": {}, "stages_completed": 0}
    
    def determine_current_stage(self):
        """Determine current stage based on completion status and briefing availability."""
        completed_stages = self.tdf_data.get("stages_completed", 0)
        
        # Check if there's a morning briefing for the next stage
        briefing_file = Path("output/morning_tdf_briefing.txt")
        if briefing_file.exists():
            # Parse briefing to get stage number
            with open(briefing_file, 'r') as f:
                content = f.read()
                if "Stage" in content:
                    # Extract stage number from briefing
                    import re
                    match = re.search(r'Stage (\d+)', content)
                    if match:
                        return int(match.group(1))
        
        # Default to next stage after completed ones
        return completed_stages + 1
    
    def get_stage_status(self, stage_num):
        """Determine status of a stage: 'completed', 'current', or 'future'."""
        completed_stages = self.tdf_data.get("stages_completed", 0)
        
        if stage_num <= completed_stages:
            return 'completed'
        elif stage_num == self.current_stage:
            return 'current'
        else:
            return 'future'
    
    def get_required_tabs(self, stage_num):
        """Return which tabs should be visible for a stage."""
        status = self.get_stage_status(stage_num)
        
        if status == 'completed':
            return ['Completed', 'Recommended', 'Planned']
        elif status == 'current':
            # Check if briefing exists
            briefing_exists = self.has_morning_briefing(stage_num)
            if briefing_exists:
                return ['Recommended', 'Planned']
            else:
                return ['Planned']
        else:  # future
            return ['Planned']
    
    def has_morning_briefing(self, stage_num):
        """Check if morning briefing exists for this stage."""
        briefing_file = Path("output/morning_tdf_briefing.txt")
        if briefing_file.exists():
            with open(briefing_file, 'r') as f:
                content = f.read()
                return f"Stage {stage_num}" in content
        return False
    
    def update_stage_tabs(self, stage_num):
        """Update a stage file to show only appropriate tabs."""
        stage_file = Path(f"docs_src/tdf-simulation/stages/stage{stage_num}.md")
        
        if not stage_file.exists():
            print(f"⚠️  Stage {stage_num} file not found")
            return
        
        with open(stage_file, 'r') as f:
            content = f.read()
        
        required_tabs = self.get_required_tabs(stage_num)
        status = self.get_stage_status(stage_num)
        
        print(f"Stage {stage_num}: {status} - showing tabs: {', '.join(required_tabs)}")
        
        # Split content into sections
        lines = content.split('\n')
        
        # Find where Stage Report starts
        report_start = None
        for i, line in enumerate(lines):
            if '## Stage Report' in line:
                report_start = i
                break
        
        if report_start is None:
            print(f"⚠️  Could not find Stage Report section in Stage {stage_num}")
            return
        
        # Keep everything before Stage Report
        new_content = lines[:report_start + 1] + ['']
        
        # Add only required tabs
        tab_content = self.get_tab_content(stage_num, required_tabs)
        new_content.extend(tab_content)
        
        # Write updated content
        with open(stage_file, 'w') as f:
            f.write('\n'.join(new_content))
        
        print(f"✅ Updated Stage {stage_num} tabs")
    
    def get_tab_content(self, stage_num, required_tabs):
        """Generate tab content based on requirements."""
        tab_content = []
        
        for i, tab in enumerate(required_tabs):
            if i == 0:
                tab_content.append(f'=== "{tab}"')
            else:
                tab_content.append(f'=== "{tab}"')
            
            tab_content.append('')
            
            if tab == 'Completed':
                tab_content.extend(self.get_completed_tab_content(stage_num))
            elif tab == 'Recommended':
                tab_content.extend(self.get_recommended_tab_content(stage_num))
            elif tab == 'Planned':
                tab_content.extend(self.get_planned_tab_content(stage_num))
            
            tab_content.append('')
        
        return tab_content
    
    def get_completed_tab_content(self, stage_num):
        """Get completed tab content (from existing data or placeholders)."""
        # Try to read existing completed content
        stage_file = Path(f"docs_src/tdf-simulation/stages/stage{stage_num}.md")
        if stage_file.exists():
            with open(stage_file, 'r') as f:
                content = f.read()
                
            # Extract existing completed content if it exists
            if '=== "Completed"' in content:
                lines = content.split('\n')
                completed_content = []
                in_completed = False
                
                for line in lines:
                    if '=== "Completed"' in line:
                        in_completed = True
                        continue
                    elif in_completed and line.startswith('=== '):
                        break
                    elif in_completed:
                        completed_content.append(line)
                
                if completed_content:
                    return completed_content
        
        # Default completed template
        return [
            f'\t### 🎉 TDF Stage {stage_num} Complete!',
            '',
            '\t🏁 **Stage Type:** [To be updated]',
            '\t🚴 **Mode Completed:** [To be updated]',
            '\t⭐ **Points Earned:** [To be updated]',
            '\t📊 **Total Points:** [To be updated]',
            '',
            '\t#### 📈 Performance Metrics:',
            '\t* **Duration:** [To be updated]',
            '\t* **Distance:** [To be updated]',
            '\t* **Average Power:** [To be updated]',
            '\t* **Weighted Power:** [To be updated]',
            '\t* **Average HR:** [To be updated]',
            '\t* **TSS:** [To be updated]',
            '\t* **Effort Level:** [To be updated]',
            '',
            '\t#### 🏆 Stage Analysis:',
            '\t[Stage completion analysis to be added after ride]',
            '',
            '\t---',
            '\t**Stage completed on:** [Date]',
            '\t**Activity ID:** [ID]'
        ]
    
    def get_recommended_tab_content(self, stage_num):
        """Get recommended tab content (from briefing or existing)."""
        # Try to get from existing file first
        stage_file = Path(f"docs_src/tdf-simulation/stages/stage{stage_num}.md")
        if stage_file.exists():
            with open(stage_file, 'r') as f:
                content = f.read()
                
            if '=== "Recommended"' in content:
                lines = content.split('\n')
                recommended_content = []
                in_recommended = False
                
                for line in lines:
                    if '=== "Recommended"' in line:
                        in_recommended = True
                        continue
                    elif in_recommended and line.startswith('=== '):
                        break
                    elif in_recommended:
                        recommended_content.append(line)
                
                if recommended_content and '[To be updated]' not in '\n'.join(recommended_content):
                    return recommended_content
        
        # Default template
        return [
            f'\t### 🏆 Stage {stage_num} TDF Morning Briefing',
            '',
            '\t**🏁 Stage Type**: [Stage Type]',
            '',
            '\t#### 📊 Readiness Check:',
            '\t- Readiness Score: [To be updated]',
            '\t- TSB (Form): [To be updated]',
            '\t- CTL (Fitness): [To be updated]',
            '',
            '\t#### 🎯 Today\'s Recommendation:',
            '\t- **Ride Mode**: [To be updated]',
            '\t- **Expected Points**: [To be updated]',
            '\t- **Rationale**: [AI recommendation to be added]',
            '',
            '\t#### 📈 Points Status:',
            '\t- Current Total: [To be updated]',
            '\t- Stages Completed: [To be updated]/21',
            '',
            '\t#### 📝 Strategic Notes:',
            '\t[Morning briefing to be generated]'
        ]
    
    def get_planned_tab_content(self, stage_num):
        """Get planned tab content (always show existing workout plans)."""
        stage_file = Path(f"docs_src/tdf-simulation/stages/stage{stage_num}.md")
        if stage_file.exists():
            with open(stage_file, 'r') as f:
                content = f.read()
                
            if '=== "Planned"' in content:
                lines = content.split('\n')
                planned_content = []
                in_planned = False
                
                for line in lines:
                    if '=== "Planned"' in line:
                        in_planned = True
                        continue
                    elif in_planned and line.startswith('=== '):
                        break
                    elif in_planned:
                        planned_content.append(line)
                
                if planned_content:
                    return planned_content
        
        # Default planned template
        return [
            f'\t### 🚴 Stage {stage_num} Ride Options',
            '',
            '\t#### 🏆 Breakaway Mode',
            '\t',
            '\t"[Breakaway strategy description]"',
            '',
            '\t- [Workout plan to be added]',
            '',
            '\t#### 🦺 GC Mode',
            '',
            '\t"[GC strategy description]"',
            '',
            '\t- [Workout plan to be added]'
        ]
    
    def update_all_stages(self):
        """Update all stage files based on current status."""
        print("🔄 Updating all stage documentation based on current status...")
        print(f"Current stage: {self.current_stage}")
        print(f"Completed stages: {self.tdf_data.get('stages_completed', 0)}")
        print()
        
        for stage_num in range(1, 22):  # TDF has 21 stages
            self.update_stage_tabs(stage_num)
        
        print("\n✅ All stages updated!")


def main():
    """Main function to update stage documentation."""
    manager = StageManager()
    manager.update_all_stages()


if __name__ == "__main__":
    main()
