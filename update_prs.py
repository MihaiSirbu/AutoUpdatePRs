#!/usr/bin/env python3
"""
Script to update all open PRs by:
1. Checkout to target branch
2. Find common ancestor with main and identify files changed in this branch
3. Update variables ONLY in changed files (1.2 → 1.3)
4. Commit changes
5. Rebase on main
6. Loop to next target branch

Usage:
    python update_prs.py --branches branch1 branch2 branch3 --old-value 1.2 --new-value 1.3
    python update_prs.py --branches-file branches.json --old-value 1.2 --new-value 1.3
"""

import subprocess
import sys
import argparse
import re
from pathlib import Path
import json


def run_git(*args, check=True, dry_run=False):
    """Run a git command."""
    cmd = ['git'] + list(args)
    if dry_run:
        print(f"[DRY RUN] Would run: {' '.join(cmd)}")
        return subprocess.CompletedProcess(cmd, 0, '', '')
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def get_repo_root():
    """Get the git repository root directory."""
    result = run_git('rev-parse', '--show-toplevel', check=True)
    return Path(result.stdout.strip())


def checkout_branch(branch, dry_run=False):
    """Checkout a branch, creating it if it doesn't exist locally."""
    print(f"  Checking out branch: {branch}")
    run_git('fetch', '--all', check=False, dry_run=dry_run)
    
    result = run_git('checkout', branch, check=False, dry_run=dry_run)
    if result.returncode != 0:
        result = run_git('checkout', '-b', branch, f'origin/{branch}', check=False, dry_run=dry_run)
        if result.returncode != 0:
            raise RuntimeError(f"Cannot checkout branch {branch}")


def get_merge_base(branch1, branch2, dry_run=False):
    """Get the merge base (common ancestor) between two branches."""
    result = run_git('merge-base', branch1, branch2, check=True, dry_run=dry_run)
    return result.stdout.strip()


def get_changed_files(base_commit, branch_commit, dry_run=False):
    """Get list of files changed between base_commit and branch_commit."""
    result = run_git('diff', '--name-only', '--diff-filter=AM', base_commit, branch_commit, check=True, dry_run=dry_run)
    files = {f.strip() for f in result.stdout.strip().split('\n') if f.strip()}
    return files


def get_branch_commit(branch, dry_run=False):
    """Get the latest commit SHA for a branch."""
    result = run_git('rev-parse', branch, check=True, dry_run=dry_run)
    return result.stdout.strip()


def update_file_variable(file_path, old_value, new_value, dry_run=False):
    """Update variable value in a file. Returns True if modified."""
    if not file_path.exists():
        print(f"  Warning: File {file_path} does not exist, skipping")
        return False

    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        print("--------------------------------")
        print("content", content)
        print("old_value", old_value)
        print("new_value", new_value)
        print("file_path", file_path)
        print("--------------------------------")

        # Simple replacement - handles most cases
        if old_value in content:
            new_content = content.replace(old_value, new_value)
            if new_content != original_content:
                if not dry_run:
                    file_path.write_text(new_content, encoding='utf-8')
                print(f"  Updated {file_path}")
                return True
        return False
    except Exception as e:
        print(f"  Error updating {file_path}: {e}")
        return False


def rebase_on_main(main_branch, dry_run=False):
    """Rebase current branch on main."""
    print(f"  Rebasing on {main_branch}...")
    run_git('fetch', 'origin', main_branch, check=True, dry_run=dry_run)
    
    result = run_git('rebase', f'origin/{main_branch}', check=False, dry_run=dry_run)
    if result.returncode != 0:
        print(f"  Warning: Rebase encountered conflicts. Manual intervention may be needed.")
        return False
    return True


def process_branch(branch, main_branch, old_value, new_value, repo_root, dry_run=False):
    """
    Process a single branch:
    1. Checkout to target branch
    2. Find common ancestor with main and see what files were changed
    3. Update variables ONLY in changed files
    4. Commit changes
    5. Rebase on main
    """
    print(f"\n{'='*60}")
    print(f"Processing branch: {branch}")
    print(f"{'='*60}")

    try:
        # Step 1: Checkout to target branch
        checkout_branch(branch, dry_run)

        # Step 2: Find common ancestor and changed files
        branch_commit = get_branch_commit('HEAD', dry_run)
        merge_base = get_merge_base(f'origin/{main_branch}', 'HEAD', dry_run)
        changed_files = get_changed_files(merge_base, branch_commit, dry_run)
        
        if not changed_files:
            print(f"  ⚠ No files changed in this PR, skipping")
            return True

        print(f"  Files changed in original PR: {', '.join(sorted(changed_files))}")

        # Step 3: Update variables ONLY in changed files
        updated_count = 0
        for file_path_str in changed_files:
            file_path = repo_root / file_path_str
            if update_file_variable(file_path, old_value, new_value, dry_run):
                updated_count += 1

        # Step 4: Commit changes
        if updated_count > 0:
            result = run_git('status', '--porcelain', check=True, dry_run=dry_run)
            if result.stdout.strip():
                commit_message = f"Update {old_value} → {new_value} in PR files"
                print(f"  Committing changes...")
                run_git('add', *changed_files, check=True, dry_run=dry_run)
                run_git('commit', '-m', commit_message, check=True, dry_run=dry_run)
                print(f" Committed variable updates")
        else:
            print(f"  No files were updated (variable {old_value} not found or already updated)")

        # Step 5: Rebase on main
        rebase_success = rebase_on_main(main_branch, dry_run)
        if rebase_success:
            print(f"  ✓ Successfully rebased on {main_branch}")
        else:
            print(f"  ⚠ Rebase had conflicts - manual intervention needed")

        print(f"  ✓ Completed processing branch {branch}")
        return True

    except Exception as e:
        print(f"  ✗ Error processing branch {branch}: {e}")
        return False


def load_branches_from_file(file_path):
    """Load branch names from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'branches' in data:
            return data['branches']
        else:
            raise ValueError("JSON file must contain a list of branches or a dict with 'branches' key")


def main():
    parser = argparse.ArgumentParser(
        description='Update variable values in specified PR branches',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_prs.py --branches feature/branch1 feature/branch2 --old-value 1.2 --new-value 1.3
  python update_prs.py --branches-file branches.json --old-value 1.2 --new-value 1.3
  python update_prs.py --branches feature/branch1 --old-value 1.2 --new-value 1.3 --dry-run
        """
    )
    parser.add_argument('--main-branch', default='main', help='Name of the main branch (default: main)')
    parser.add_argument('--old-value', required=True, help='Old variable value to replace (e.g., 1.2)')
    parser.add_argument('--new-value', required=True, help='New variable value (e.g., 1.3)')
    parser.add_argument('--branches', nargs='+', help='List of branch names to process')
    parser.add_argument('--branches-file', help='JSON file containing array of branch names')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    args = parser.parse_args()

    if not args.branches and not args.branches_file:
        parser.error("Either --branches or --branches-file must be provided")
    if args.branches and args.branches_file:
        parser.error("Cannot specify both --branches and --branches-file")

    # Load branch list
    if args.branches_file:
        branches = load_branches_from_file(args.branches_file)
    else:
        branches = args.branches

    # Get repo root
    try:
        repo_root = get_repo_root()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Show branches to process
    print(f"Branches to process: {len(branches)}")
    for i, branch in enumerate(branches, 1):
        print(f"  {i}. {branch}")

    # Confirm before proceeding
    if not args.dry_run:
        response = input(f"\nProceed with updating {len(branches)} branch(es)? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Aborted")
            return

    # Process each branch
    success_count = 0
    for branch in branches:
        if process_branch(branch, args.main_branch, args.old_value, args.new_value, repo_root, args.dry_run):
            success_count += 1

    print(f"\n{'='*60}")
    print(f"Summary: {success_count}/{len(branches)} branches processed successfully")
    print(f"{'='*60}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
