#!/usr/bin/env python3
"""
Fix linting issues in Fiction Mode modules incrementally
"""

import os
import re
import sys
import subprocess
from pathlib import Path


def fix_unused_imports(file_path):
    """Remove unused imports from a Python file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove common unused imports we can safely identify
    unused_patterns = [
        r'from typing import.*?Tuple.*?\n',
        r'from typing import.*?Any.*?\n', 
        r'from typing import.*?Dict.*?\n',
        r'import datetime.*?\n',
        r'import timedelta.*?\n',
        r'import json\n',
        r'import os\n',
        r'import requests\n',
        r'from dataclasses import asdict\n',
    ]
    
    original_content = content
    
    # Only remove if we can be confident they're unused
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        skip = False
        # Check specific unused imports we found in lint output
        if file_path.endswith('analysis.py'):
            if ('Tuple' in line and 'from typing import' in line) or \
               ('datetime' in line and 'import datetime' in line) or \
               ('timedelta' in line and 'import timedelta' in line) or \
               ('import json' in line and line.strip() == 'import json'):
                skip = True
        elif file_path.endswith('data_ingestion.py'):
            if ('import os' in line and line.strip() == 'import os') or \
               ('import requests' in line and line.strip() == 'import requests') or \
               ('timedelta' in line and 'import timedelta' in line) or \
               ('import json' in line and line.strip() == 'import json') or \
               ('get_athlete_id' in line and 'imported but unused' in line):
                skip = True
        elif file_path.endswith('delivery.py'):
            if ('import os' in line and line.strip() == 'import os') or \
               ('asdict' in line and 'from dataclasses import' in line):
                skip = True
        elif file_path.endswith('editor.py'):
            if ('Any' in line and 'from typing import' in line):
                skip = True
        elif file_path.endswith('pipeline.py'):
            if ('import os' in line and line.strip() == 'import os') or \
               ('Dict' in line and 'from typing import' in line) or \
               ('Any' in line and 'from typing import' in line) or \
               ('RideData' in line and 'imported but unused' in line) or \
               ('StageRaceData' in line and 'imported but unused' in line):
                skip = True
        elif file_path.endswith('writer.py'):
            if ('Any' in line and 'from typing import' in line) or \
               ('import json' in line and line.strip() == 'import json') or \
               ('MappedEvent' in line and 'imported but unused' in line):
                skip = True
        
        if not skip:
            new_lines.append(line)
    
    new_content = '\n'.join(new_lines)
    
    if new_content != original_content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Removed unused imports from {file_path}")
        return True
    return False


def fix_line_length_issues(file_path):
    """Fix some basic line length issues"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    new_lines = []
    changes_made = False
    
    for line in lines:
        if len(line) > 88:
            # Try some simple fixes for long lines
            if 'logger.info(' in line or 'logger.error(' in line or 'logger.warning(' in line:
                # Break long logger statements
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                
                if 'logger.info(' in line:
                    parts = line.split('logger.info(')
                    if len(parts) == 2:
                        new_line = f"{parts[0]}logger.info(\n{indent_str}    {parts[1]}"
                        new_lines.append(new_line)
                        changes_made = True
                        continue
            
            # For very long string literals, we'll leave them for manual fixing
        
        new_lines.append(line)
    
    if changes_made:
        new_content = '\n'.join(new_lines)
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Fixed some line length issues in {file_path}")
    
    return changes_made


def fix_bare_except(file_path):
    """Fix bare except clauses"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace bare except with except Exception
    new_content = re.sub(r'\bexcept:\s*\n', 'except Exception:\n', content)
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Fixed bare except clauses in {file_path}")
        return True
    return False


def fix_unused_variables(file_path):
    """Fix some obvious unused variable issues"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix f-string without placeholders
    content = re.sub(r'f"([^{}"]*)"', r'"\1"', content)
    content = re.sub(r"f'([^{}']*)'", r"'\1'", content)
    
    # Remove obvious unused variables (be conservative)
    if file_path.endswith('writer.py'):
        # Fix the specific unused variable we found
        content = re.sub(r'character_desc = f".*?"', '# Character description logic here', content)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed unused variables in {file_path}")
        return True
    return False


def main():
    """Main function to fix lint issues"""
    fiction_mode_dir = Path(__file__).parent.parent.parent / 'src' / 'lanterne_rouge' / 'fiction_mode'
    
    if not fiction_mode_dir.exists():
        print(f"Fiction mode directory not found: {fiction_mode_dir}")
        return 1
    
    python_files = list(fiction_mode_dir.glob('*.py'))
    
    print(f"Fixing lint issues in {len(python_files)} Fiction Mode files...")
    
    total_changes = 0
    
    for file_path in python_files:
        print(f"\nProcessing {file_path.name}...")
        
        changes = 0
        changes += fix_unused_imports(str(file_path))
        changes += fix_bare_except(str(file_path))
        changes += fix_unused_variables(str(file_path))
        changes += fix_line_length_issues(str(file_path))
        
        if changes:
            print(f"  Made {changes} fixes to {file_path.name}")
            total_changes += changes
        else:
            print(f"  No changes needed for {file_path.name}")
    
    print(f"\nTotal fixes applied: {total_changes}")
    
    # Run flake8 to see remaining issues
    print("\nChecking remaining issues...")
    try:
        result = subprocess.run([
            'python', '-m', 'flake8', str(fiction_mode_dir),
            '--count', '--select=E9,F63,F7,F82'
        ], capture_output=True, text=True, cwd=fiction_mode_dir.parent.parent.parent)
        
        if result.returncode == 0:
            print("✅ No critical syntax errors remaining!")
        else:
            print(f"⚠️  Some issues remain: {result.stdout}")
    except Exception as e:
        print(f"Could not run flake8 check: {e}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
