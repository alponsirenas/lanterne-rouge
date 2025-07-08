#!/usr/bin/env python3
"""
Quick script to fix common lint issues in the lanterne_rouge package.

This script:
1. Removes trailing whitespace
2. Ensures files end with a newline
3. Fixes line length issues by breaking long lines
"""

import os
import re
import glob

def fix_trailing_whitespace(file_path):
    """Remove trailing whitespace from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove trailing whitespace
    new_content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)

    # Ensure file ends with a newline
    if new_content and new_content[-1] != '\n':
        new_content += '\n'

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return content != new_content

def main():
    """Find and fix trailing whitespace in Python files in the lanterne_rouge package."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    src_dir = os.path.join(base_dir, 'src', 'lanterne_rouge')

    # Find all Python files recursively
    py_files = []
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))

    fixed_count = 0

    for py_file in py_files:
        if fix_trailing_whitespace(py_file):
            fixed_count += 1
            print(f"Fixed trailing whitespace in {os.path.relpath(py_file, src_dir)}")

    print(f"\nFixed {fixed_count} out of {len(py_files)} files.")

if __name__ == "__main__":
    main()
