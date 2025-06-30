#!/usr/bin/env python3

import os
import argparse
import sys
from typing import List, Dict, Tuple, Optional, Callable


class Perseus:
    def __init__(self, search_path: str, keywords: List[str], exclude_keywords: Optional[List[str]] = None):
        """Initialize with search path and keywords to find"""
        self.search_path = os.path.abspath(search_path)
        self.keywords = [k.lower() for k in keywords]
        self.exclude_keywords = [k.lower() for k in exclude_keywords] if exclude_keywords else []
        self.matches: Dict[str, List[Tuple[int, str]]] = {}

    def find_matches(self) -> Dict[str, List[Tuple[int, str]]]:
        """Find files containing ALL keywords and NONE of the excluded keywords (anywhere in file)"""
        print(f"Searching in: {self.search_path}")
        print(f"Looking for keywords: {self.keywords}")
        if self.exclude_keywords:
            print(f"Excluding keywords: {self.exclude_keywords}")

        self.matches.clear()
        for root, _, files in os.walk(self.search_path):
            for file in files:
                if file.endswith('.py') and ('test' in file.lower()):
                    filepath = os.path.join(root, file)
                    self._process_file(filepath)
        return self.matches

    def _process_file(self, filepath: str):
        """Check if file contains all keywords and none of the exclude keywords, and collect matches"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                if all(k in content for k in self.keywords) and not any(ek in content for ek in self.exclude_keywords):
                    f.seek(0)
                    for i, line in enumerate(f, 1):
                        if any(k in line.lower() for k in self.keywords):
                            self._add_match(filepath, i, line.strip())
        except Exception as e:
            print(f"Error reading {filepath}: {str(e)}")

    def _add_match(self, filepath: str, line_num: int, line: str):
        """Store matched lines"""
        if filepath not in self.matches:
            self.matches[filepath] = []
        self.matches[filepath].append((line_num, line))

    def print_results(self):
        """Display found matches"""
        if not self.matches:
            print("No matches found.")
            return
        print(f"\nFound {len(self.matches)} files with matches:")
        for file, matches in self.matches.items():
            print(f"\n{file}")
            for line_num, line in matches:
                print(f"Line {line_num}: {line}")

    def _confirm_action(self, action: str) -> bool:
        """Get user confirmation for destructive operations"""
        print(f"\nAbout to: {action}")
        resp = input("Continue? [y/N]: ").strip().lower()
        return resp == 'y'

    def _show_changes(self, old: List[str], new: List[str], context: int = 2):
        """Display diff of changes"""
        from difflib import unified_diff
        print("\nChanges to be made:")
        for line in unified_diff(old, new, n=context):
            if line.startswith('+'):
                print(f"\033[92m{line}\033[0m")
            elif line.startswith('-'):
                print(f"\033[91m{line}\033[0m")
            else:
                print(line, end='')

    def bulk_replace(self, old: str, new: str, dry_run: bool = False, bulk_confirm: bool = False) -> int:
        """Replace text with confirmation and diff preview"""
        modified = 0
        changes = []

        for filepath in self.matches:
            try:
                with open(filepath, 'r') as f:
                    original = f.readlines()

                updated = [line.replace(old, new) for line in original]

                if original != updated:
                    changes.append((filepath, original, updated))
            except Exception as e:
                print(f"Error processing {filepath}: {str(e)}")

        if not changes:
            print("No changes needed.")
            return 0

        print(f"\nFound {len(changes)} files that would be modified:")
        for filepath, original, updated in changes:
            print(f"\nFile: {filepath}")
            self._show_changes(original, updated)

        if not dry_run:
            if bulk_confirm:
                if not self._confirm_action(f"Replace '{old}' with '{new}' in {len(changes)} files"):
                    print("Skipped (user canceled bulk operation)")
                    return 0
            else:
                print("\nProcessing files individually...")

        for filepath, original, updated in changes:
            if not dry_run:
                if bulk_confirm or self._confirm_action(f"Replace '{old}' with '{new}' in {filepath}"):
                    try:
                        with open(filepath, 'w') as f:
                            f.writelines(updated)
                        modified += 1
                        print(f"Updated {filepath}")
                    except Exception as e:
                        print(f"Error updating {filepath}: {str(e)}")
                else:
                    print(f"Skipped {filepath}")
            else:
                print(f"[Dry-run] Would update {filepath}")

        return modified

    def bulk_remove_keyword(self, keyword: str, dry_run: bool = False, bulk_confirm: bool = False) -> int:
        """Remove keyword with confirmation"""
        return self.bulk_replace(keyword, "", dry_run, bulk_confirm)

    def bulk_add_keyword(self, keyword: str, condition: Optional[Callable[[str], bool]] = None,
                         dry_run: bool = False, bulk_confirm: bool = False) -> int:
        """Add keyword to matching lines with confirmation"""
        modified = 0
        changes = []

        for filepath in self.matches:
            try:
                with open(filepath, 'r') as f:
                    original = f.readlines()

                updated = []
                for line in original:
                    if not condition or condition(line):
                        updated.append(f"{keyword}\n{line}")
                    else:
                        updated.append(line)

                if original != updated:
                    changes.append((filepath, original, updated))
            except Exception as e:
                print(f"Error processing {filepath}: {str(e)}")

        if not changes:
            print("No changes needed.")
            return 0

        print(f"\nFound {len(changes)} files that would be modified:")
        for filepath, original, updated in changes:
            print(f"\nFile: {filepath}")
            self._show_changes(original, updated)

        if not dry_run:
            if bulk_confirm:
                if not self._confirm_action(f"Add '{keyword}' in {len(changes)} files"):
                    print("Skipped (user canceled bulk operation)")
                    return 0
            else:
                print("\nProcessing files individually...")

        for filepath, original, updated in changes:
            if not dry_run:
                if bulk_confirm or self._confirm_action(f"Add '{keyword}' in {filepath}"):
                    try:
                        with open(filepath, 'w') as f:
                            f.writelines(updated)
                        modified += 1
                        print(f"Updated {filepath}")
                    except Exception as e:
                        print(f"Error updating {filepath}: {str(e)}")
                else:
                    print(f"Skipped {filepath}")
            else:
                print(f"[Dry-run] Would update {filepath}")

        return modified

    def bulk_remove_lines(self, keyword: str, dry_run: bool = False, bulk_confirm: bool = False) -> int:
        """Remove entire lines containing the keyword with confirmation"""
        modified = 0
        changes = []

        for filepath in self.matches:
            try:
                with open(filepath, 'r') as f:
                    original = f.readlines()

                updated = [line for line in original if keyword.lower() not in line.lower()]

                if len(original) != len(updated):
                    changes.append((filepath, original, updated))
            except Exception as e:
                print(f"Error processing {filepath}: {str(e)}")

        if not changes:
            print("No changes needed.")
            return 0

        print(f"\nFound {len(changes)} files that would be modified:")
        for filepath, original, updated in changes:
            print(f"\nFile: {filepath}")
            self._show_changes(original, updated)

        if not dry_run:
            if bulk_confirm:
                if not self._confirm_action(f"Remove lines containing '{keyword}' in {len(changes)} files"):
                    print("Skipped (user canceled bulk operation)")
                    return 0
            else:
                print("\nProcessing files individually...")

        for filepath, original, updated in changes:
            if not dry_run:
                if bulk_confirm or self._confirm_action(f"Remove lines containing '{keyword}' in {filepath}"):
                    try:
                        with open(filepath, 'w') as f:
                            f.writelines(updated)
                        modified += 1
                        print(f"Updated {filepath}")
                    except Exception as e:
                        print(f"Error updating {filepath}: {str(e)}")
                else:
                    print(f"Skipped {filepath}")
            else:
                print(f"[Dry-run] Would update {filepath}")

        return modified

    def bulk_replace_lines(self, old_line: str, new_line: str, dry_run: bool = False,
                           bulk_confirm: bool = False) -> int:
        """Replace entire lines containing old_line with new_line"""
        modified = 0
        changes = []

        for filepath in self.matches:
            try:
                with open(filepath, 'r') as f:
                    original = f.readlines()

                updated = []
                for line in original:
                    if old_line.lower() in line.lower():
                        updated.append(new_line + '\n' if not new_line.endswith('\n') else new_line)
                    else:
                        updated.append(line)

                if original != updated:
                    changes.append((filepath, original, updated))
            except Exception as e:
                print(f"Error processing {filepath}: {str(e)}")

        if not changes:
            print("No changes needed.")
            return 0

        print(f"\nFound {len(changes)} files that would be modified:")
        for filepath, original, updated in changes:
            print(f"\nFile: {filepath}")
            self._show_changes(original, updated)

        if not dry_run:
            if bulk_confirm:
                if not self._confirm_action(f"Replace lines containing '{old_line}' in {len(changes)} files"):
                    print("Skipped (user canceled bulk operation)")
                    return 0
            else:
                print("\nProcessing files individually...")

        for filepath, original, updated in changes:
            if not dry_run:
                if bulk_confirm or self._confirm_action(f"Replace lines containing '{old_line}' in {filepath}"):
                    try:
                        with open(filepath, 'w') as f:
                            f.writelines(updated)
                        modified += 1
                        print(f"Updated {filepath}")
                    except Exception as e:
                        print(f"Error updating {filepath}: {str(e)}")
                else:
                    print(f"Skipped {filepath}")
            else:
                print(f"[Dry-run] Would update {filepath}")

        return modified

    def bulk_add_after(self, match_keyword: str, new_line: str, first_only: bool = False,
                       dry_run: bool = False, bulk_confirm: bool = False) -> int:
        """Add a new line after each line containing match_keyword"""
        modified = 0
        changes = []

        for filepath in self.matches:
            try:
                with open(filepath, 'r') as f:
                    lines = f.readlines()

                updated_lines = []
                inserted = False

                for i, line in enumerate(lines):
                    updated_lines.append(line)
                    if match_keyword in line:
                        if first_only and inserted:
                            continue
                        updated_lines.append(new_line + '\n')
                        inserted = True
                        if first_only:
                            updated_lines.extend(lines[i + 1:])
                            break

                if inserted and lines != updated_lines:
                    changes.append((filepath, lines, updated_lines))
            except Exception as e:
                print(f"Error processing {filepath}: {str(e)}")

        if not changes:
            print("No changes needed.")
            return 0

        print(f"\nFound {len(changes)} files that would be modified:")
        for filepath, original, updated in changes:
            print(f"\nFile: {filepath}")
            self._show_changes(original, updated)

        if not dry_run:
            if bulk_confirm:
                if not self._confirm_action(f"Add line after '{match_keyword}' in {len(changes)} files"):
                    print("Skipped (user canceled bulk operation)")
                    return 0
            else:
                print("\nProcessing files individually...")

        for filepath, original, updated in changes:
            if not dry_run:
                if bulk_confirm or self._confirm_action(f"Add line after '{match_keyword}' in {filepath}"):
                    try:
                        with open(filepath, 'w') as f:
                            f.writelines(updated)
                        modified += 1
                        print(f"Updated {filepath}")
                    except Exception as e:
                        print(f"Error updating {filepath}: {str(e)}")
                else:
                    print(f"Skipped {filepath}")
            else:
                print(f"[Dry-run] Would update {filepath}")

        return modified

    def bulk_add_before(self, match_keyword: str, new_line: str, first_only: bool = False,
                        dry_run: bool = False, bulk_confirm: bool = False) -> int:
        """Add a new line before each line containing match_keyword"""
        modified = 0
        changes = []

        for filepath in self.matches:
            try:
                with open(filepath, 'r') as f:
                    lines = f.readlines()

                updated_lines = []
                inserted = False

                for i, line in enumerate(lines):
                    if match_keyword in line:
                        if first_only and inserted:
                            updated_lines.append(line)
                            continue
                        updated_lines.append(new_line + '\n')
                        inserted = True
                        updated_lines.append(line)
                        if first_only:
                            updated_lines.extend(lines[i + 1:])
                            break
                    else:
                        updated_lines.append(line)

                if inserted and lines != updated_lines:
                    changes.append((filepath, lines, updated_lines))
            except Exception as e:
                print(f"Error processing {filepath}: {str(e)}")

        if not changes:
            print("No changes needed.")
            return 0

        print(f"\nFound {len(changes)} files that would be modified:")
        for filepath, original, updated in changes:
            print(f"\nFile: {filepath}")
            self._show_changes(original, updated)

        if not dry_run:
            if bulk_confirm:
                if not self._confirm_action(f"Add line before '{match_keyword}' in {len(changes)} files"):
                    print("Skipped (user canceled bulk operation)")
                    return 0
            else:
                print("\nProcessing files individually...")

        for filepath, original, updated in changes:
            if not dry_run:
                if bulk_confirm or self._confirm_action(f"Add line before '{match_keyword}' in {filepath}"):
                    try:
                        with open(filepath, 'w') as f:
                            f.writelines(updated)
                        modified += 1
                        print(f"Updated {filepath}")
                    except Exception as e:
                        print(f"Error updating {filepath}: {str(e)}")
                else:
                    print(f"Skipped {filepath}")
            else:
                print(f"[Dry-run] Would update {filepath}")

        return modified

    def output_filenames(self, output_file: str = None, trim_paths: bool = False, single_line: bool = False):
        """
        Output matched filenames with various formatting options

        Args:
            output_file: Save to file if specified
            trim_paths: Keep only the 'tests/' portion of paths
            single_line: Output as single line space-separated
        """
        if not self.matches:
            print("No matches found.")
            return

        paths = list(self.matches.keys())

        if trim_paths:
            trimmed_paths = []
            for path in paths:
                path = path.replace("\\", "/")
                if "tests/" in path:
                    trimmed = "tests/" + path.split("tests/", 1)[-1]
                    trimmed_paths.append(trimmed)
            paths = trimmed_paths

        if single_line:
            output = ' '.join(paths)
        else:
            output = '\n'.join(paths)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            print(f"Found {len(self.matches)} files with matches. Output saved to {output_file}")
        else:
            print(f"Found {len(self.matches)} files with matches:")
            print(output)

    @staticmethod
    def show_help():
        """Print usage examples with line operations"""
        print("""
    Test Label Finder - Complete Usage Examples:

    1. Search files containing ALL keywords:
       python test_label_finder.py --path tests --keywords "@mark1" "@mark2"

    2. Replace entire lines (with confirmation):
       python test_label_finder.py --path tests --keywords "@old" --replace-lines "@old" "@new"

    3. Remove lines containing keyword:
       python test_label_finder.py --path tests --keywords "@deprecated" --remove-lines "@deprecated"

    4. Standard replace/remove/add (substring):
       python test_label_finder.py --path tests --keywords "@test" --add "@pytest.mark.new"
       python test_label_finder.py --path tests --keywords "@old" --replace "@old" "@new"
       python test_label_finder.py --path tests --keywords "@temp" --remove "@temp"

    5. Output options:
       python test_label_finder.py --path tests --keywords "@test" --output results.txt
       python test_label_finder.py --path tests --keywords "@test" --trim-paths
       python test_label_finder.py --path tests --keywords "@test" --single-line

    6. Dry-run preview:
       Add --dry-run to any command to preview changes

    7. Bulk confirmation:
       Add --bulk-confirm to approve all changes at once
    """)


def main():
    parser = argparse.ArgumentParser(description="Find and modify test markers safely")
    parser.add_argument("--path", help="Directory to search")
    parser.add_argument("--keywords", nargs="+", help="Keywords to find")
    parser.add_argument("--not", dest="exclude_keywords", nargs="+", help="Exclude files containing these keywords")
    parser.add_argument("--replace", nargs=2, metavar=("OLD", "NEW"), help="Replace OLD with NEW")
    parser.add_argument("--remove", help="Keyword to remove")
    parser.add_argument("--add", help="Keyword to add")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    parser.add_argument("--help-examples", action="store_true", help="Show usage examples")
    parser.add_argument("--remove-lines", help="Remove entire lines containing this keyword")
    parser.add_argument("--replace-lines", nargs=2, metavar=("OLD", "NEW"),
                        help="Replace entire lines containing OLD with NEW")
    parser.add_argument("--add-after", nargs=2, metavar=("MATCH", "NEW_LINE"),
                        help="Add NEW_LINE after lines containing MATCH keyword")
    parser.add_argument("--add-before", nargs=2, metavar=("MATCH", "NEW_LINE"),
                        help="Add NEW_LINE before lines containing MATCH keyword")
    parser.add_argument('--first-only', action='store_true', help='Add only before/after the first match per file')
    parser.add_argument("--output", help="Output file for matched filenames")
    parser.add_argument("--trim-paths", action="store_true",
                        help="Trim paths to only include 'tests/' portion")
    parser.add_argument("--single-line", action="store_true",
                        help="Output filenames as single space-separated line")
    parser.add_argument("--bulk-confirm", action="store_true",
                        help="Confirm all changes at once rather than per file")

    args = parser.parse_args()

    if args.help_examples:
        TestLabelFinder.show_help()
        sys.exit(0)

    if not args.path or not args.keywords:
        parser.print_help()
        sys.exit(1)

    finder = TestLabelFinder(args.path, args.keywords, args.exclude_keywords)
    finder.find_matches()

    if args.output or args.trim_paths or args.single_line:
        finder.output_filenames(output_file=args.output,
                                trim_paths=args.trim_paths,
                                single_line=args.single_line)
    else:
        finder.print_results()

    if args.replace:
        finder.bulk_replace(args.replace[0], args.replace[1], args.dry_run, args.bulk_confirm)
    elif args.remove:
        finder.bulk_remove_keyword(args.remove, args.dry_run, args.bulk_confirm)
    elif args.add:
        finder.bulk_add_keyword(args.add, dry_run=args.dry_run, bulk_confirm=args.bulk_confirm)
    elif args.remove_lines:
        finder.bulk_remove_lines(args.remove_lines, args.dry_run, args.bulk_confirm)
    elif args.replace_lines:
        finder.bulk_replace_lines(args.replace_lines[0], args.replace_lines[1], args.dry_run, args.bulk_confirm)
    elif args.add_after:
        finder.bulk_add_after(args.add_after[0], args.add_after[1], first_only=args.first_only,
                              dry_run=args.dry_run, bulk_confirm=args.bulk_confirm)
    elif args.add_before:
        finder.bulk_add_before(args.add_before[0], args.add_before[1], first_only=args.first_only,
                               dry_run=args.dry_run, bulk_confirm=args.bulk_confirm)


if __name__ == "__main__":
    main()
