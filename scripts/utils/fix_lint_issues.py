#!/usr/bin/env python3
"""
Fix common lint issues in Python files for lanterne_rouge.

This script fixes:
1. Line length issues (breaks long lines)
2. Import organization
3. Blank line issues
4. Common style violations
"""

import os
import re
import ast
import sys


def fix_line_length(content, max_length=88):
    """Break long lines at appropriate points."""
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        if len(line) <= max_length:
            fixed_lines.append(line)
            continue

        # Don't break strings or comments arbitrarily
        if line.strip().startswith('#') or '"""' in line or "'''" in line:
            fixed_lines.append(line)
            continue

        # Try to break at common points
        if ' and ' in line and len(line) > max_length:
            # Break long conditional statements
            indent = len(line) - len(line.lstrip())
            parts = line.split(' and ')
            if len(parts) > 1:
                fixed_lines.append(parts[0] + ' and')
                for part in parts[1:-1]:
                    fixed_lines.append(' ' * (indent + 4) + part + ' and')
                fixed_lines.append(' ' * (indent + 4) + parts[-1])
                continue

        # Break long function calls
        if '(' in line and ')' in line and len(line) > max_length:
            # Simple heuristic for function calls
            if line.count('(') == line.count(')') and '=' in line[:line.index('(')]:
                paren_pos = line.index('(')
                if ', ' in line[paren_pos:]:
                    indent = len(line) - len(line.lstrip())
                    func_part = line[:paren_pos + 1]
                    args_part = line[paren_pos + 1:line.rindex(')')]
                    args = [arg.strip() for arg in args_part.split(', ')]

                    fixed_lines.append(func_part)
                    for i, arg in enumerate(args):
                        if i == len(args) - 1:
                            fixed_lines.append(' ' * (indent + 4) + arg)
                        else:
                            fixed_lines.append(' ' * (indent + 4) + arg + ',')
                    fixed_lines.append(' ' * indent + ')')
                    continue

        # If we can't break it intelligently, just add it as-is
        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def fix_imports(content):
    """Organize imports according to PEP 8."""
    lines = content.split('\n')

    # Find import blocks
    import_start = None
    import_end = None

    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            if import_start is None:
                import_start = i
            import_end = i
        elif import_start is not None and line.strip() == '':
            continue
        elif import_start is not None:
            break

    if import_start is None:
        return content

    # Extract imports
    import_lines = lines[import_start:import_end + 1]

    # Separate different types of imports
    stdlib_imports = []
    third_party_imports = []
    local_imports = []

    for line in import_lines:
        if not line.strip() or line.startswith('#'):
            continue

        if line.startswith('from .') or line.startswith('from ..'):
            local_imports.append(line)
        elif any(lib in line for lib in ['os', 'sys', 're', 'json', 'datetime', 'typing', 'dataclasses', 'pathlib']):
            stdlib_imports.append(line)
        else:
            third_party_imports.append(line)

    # Sort each group
    stdlib_imports.sort()
    third_party_imports.sort()
    local_imports.sort()

    # Rebuild import section
    new_imports = []
    if stdlib_imports:
        new_imports.extend(stdlib_imports)
        new_imports.append('')
    if third_party_imports:
        new_imports.extend(third_party_imports)
        new_imports.append('')
    if local_imports:
        new_imports.extend(local_imports)
        new_imports.append('')

    # Remove extra blank line at the end
    if new_imports and new_imports[-1] == '':
        new_imports.pop()

    # Reconstruct content
    new_lines = lines[:import_start] + new_imports + lines[import_end + 1:]
    return '\n'.join(new_lines)


def fix_blank_lines(content):
    """Fix blank line issues."""
    lines = content.split('\n')
    fixed_lines = []

    prev_line_type = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Determine line type
        if not stripped:
            line_type = 'blank'
        elif stripped.startswith('class '):
            line_type = 'class'
        elif stripped.startswith('def '):
            line_type = 'function'
        elif stripped.startswith('"""') or stripped.startswith("'''"):
            line_type = 'docstring'
        elif stripped.startswith('#'):
            line_type = 'comment'
        elif stripped.startswith('import ') or stripped.startswith('from '):
            line_type = 'import'
        else:
            line_type = 'code'

        # Add appropriate blank lines
        if line_type == 'class' and prev_line_type not in ['blank', None]:
            fixed_lines.append('')
            fixed_lines.append('')
        elif line_type == 'function' and prev_line_type not in ['blank', None, 'class']:
            fixed_lines.append('')

        # Don't add multiple consecutive blank lines
        if line_type == 'blank' and prev_line_type == 'blank':
            continue

        fixed_lines.append(line)
        prev_line_type = line_type

    return '\n'.join(fixed_lines)


def fix_common_issues(content):
    """Fix other common style issues."""
    # Remove trailing commas in single-element tuples that are not needed
    content = re.sub(r'\(\s*([^,\(\)]+)\s*,\s*\)', r'(\1)', content)

    # Fix spacing around operators
    content = re.sub(r'([^=!<>])=([^=])', r'\1 = \2', content)
    content = re.sub(r'([^=!<>])  =  ([^=])', r'\1 = \2', content)

    # Fix spacing after commas
    content = re.sub(r',([^\s])', r', \1', content)

    return content


def fix_file(file_path):
    """Fix lint issues in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        content = original_content

        # Apply fixes
        content = fix_imports(content)
        content = fix_blank_lines(content)
        content = fix_line_length(content)
        content = fix_common_issues(content)

        # Check if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Fix lint issues in Fiction Mode files."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    fiction_mode_dir = os.path.join(base_dir, 'src', 'lanterne_rouge', 'fiction_mode')

    if not os.path.exists(fiction_mode_dir):
        print(f"Fiction Mode directory not found: {fiction_mode_dir}")
        return

    py_files = []
    for file in os.listdir(fiction_mode_dir):
        if file.endswith('.py'):
            py_files.append(os.path.join(fiction_mode_dir, file))

    fixed_count = 0
    for py_file in py_files:
        if fix_file(py_file):
            fixed_count += 1
            print(f"Fixed lint issues in {os.path.basename(py_file)}")

    print(f"\nFixed {fixed_count} out of {len(py_files)} files.")


if __name__ == "__main__":
    main()