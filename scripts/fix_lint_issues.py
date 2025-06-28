#!/usr/bin/env python3
"""
Fix common linting issues in Python files.
This script automatically fixes some common linting issues:
- Trailing whitespace
- Import order
- Line length
- Unused imports
- f-strings without interpolation
- Missing encoding in file operations
"""

import os
import re
import subprocess
from pathlib import Path

import autopep8
import isort

def fix_f_strings_without_interpolation(content):
    """Fix f-strings that don't contain any formatted expressions."""
    # Find f-strings that don't contain any {expression}
    pattern = r'f["\'](?![^{]*\{[^}]*\})[^"\']*["\']'
    # Replace f-strings with regular strings
    return re.sub(pattern, lambda m: m.group(0)[1:], content)


def fix_missing_encoding(content):
    """Fix file operations missing encoding parameter."""
    # Replace open() calls without encoding
    open_pattern = r'open\s*\(\s*([^,)]+)\s*,\s*[\'"]([rwab+]+)[\'"]\s*\)'
    open_replacement = r'open(\1, "\2", encoding="utf-8")'
    return re.sub(open_pattern, open_replacement, content)


def fix_file(file_path):
    """Fix linting issues in a single file."""
    print(f"Processing {file_path}...")

    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix trailing whitespace
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
    # Fix f-strings without interpolation
    content = fix_f_strings_without_interpolation(content)
    # Fix missing encoding in file operations
    content = fix_missing_encoding(content)
    # Write back corrected content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Fix import order using isort
    isort.file(file_path, profile="black", quiet=True)

    # Fix line length and other PEP 8 issues
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    fixed_content = autopep8.fix_code(
        content,
        options={
            'max_line_length': 100,
            'aggressive': 1,
            'experimental': True
        }
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    # Run autoflake to remove unused imports
    try:
        subprocess.run(
            ['autoflake', '--remove-all-unused-imports', '--in-place', file_path],
            check=True,
            capture_output=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: Could not run autoflake. Unused imports not removed.")
        print("To fix, install autoflake: pip install autoflake")


def find_python_files(directory):
    """Find all Python files in the given directory recursively."""
    python_files = []
    for root, _, files in os.walk(directory):
        # Skip __pycache__ and .venv directories
        if "__pycache__" in root or ".venv" in root:
            continue

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    return python_files


def check_installed_packages():
    """Check if required packages are installed."""
    required_packages = ['autopep8', 'isort', 'autoflake']
    missing_packages = []
    for package in required_packages:
        try:
            subprocess.run(['pip', 'show', package],
                          check=True,
                          capture_output=True)
        except subprocess.CalledProcessError:
            missing_packages.append(package)
    if missing_packages:
        print("The following required packages are missing:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall them with: pip install " + " ".join(missing_packages))
        user_input = input("Would you like to install them now? (y/n): ")
        if user_input.lower() == 'y':
            try:
                subprocess.run(['pip', 'install'] + missing_packages, check=True)
                print("Packages installed successfully!")
            except subprocess.CalledProcessError:
                print("Failed to install packages. Please install them manually.")
                return False
        else:
            print("Please install the required packages manually and run this script again.")
            return False
    return True


def main():
    """Main function to process all Python files."""
    if not check_installed_packages():
        return
    project_dir = Path(__file__).parents[1]
    python_files = find_python_files(project_dir)

    print(f"Found {len(python_files)} Python files to process.")

    for file_path in python_files:
        fix_file(file_path)

    print("\nDone! Fixed the following issues across all files:")
    print("- Trailing whitespace")
    print("- Import order")
    print("- Line length (where possible)")
    print("- Unused imports (if autoflake is installed)")
    print("- f-strings without interpolation")
    print("- Missing encoding in file operations")
    print("\nRun pylint again to check the remaining issues.")


if __name__ == "__main__":
    main()
