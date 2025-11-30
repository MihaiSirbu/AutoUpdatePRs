# PR Variable Updater

A Python script to systematically update variable values across specified PR branches while preserving only the original changes made in each PR.

## Problem Statement

You have a production main branch with many open PRs, each modifying a single variable (e.g., version) in one folder. The requirements are:

- Cannot merge all changes at once — updates must be incremental
- All PRs need variable value updated (e.g., 1.2 → 2.0)
- Main branch has evolved significantly (thousands of changes)
- Cannot rebase or modify entire PR — only files originally changed should be updated
- PRs are outdated and need to be updated to reflect current main state
- Only preserve original changes from each PR

## Solution

This script processes each branch in the following sequence:

1. **Checkout to target branch**: Switches to the branch to be updated
2. **Find original changes**: Finds the common ancestor with main and identifies which files were originally changed
3. **Selective updates**: Updates the variable value (1.2 → 2.0) **only** in files that were originally changed in that PR
4. **Commit changes**: Creates a new commit with the variable update
5. **Rebase on main**: Rebases the branch on the latest main branch to bring it up to date

## Requirements

- Python 3.6+
- Git installed and accessible from command line
- Repository must be a git repository
- You should be in a clean working state (commit or stash any uncommitted changes)

## Usage

### Basic Usage - Command Line Branches

```bash
# Update specific branches (provide as arguments)
python update_prs.py --branches feature/branch1 feature/branch2 feature/branch3 --old-value 1.2 --new-value 2.0

# Dry run first to see what would happen
python update_prs.py --branches feature/branch1 --old-value 1.2 --new-value 2.0 --dry-run
```

### Using a JSON File

```bash
# Create a branches.json file with your branch names
# Then run:
python update_prs.py --branches-file branches.json --old-value 1.2 --new-value 2.0
```

Example `branches.json`:
```json
[
  "feature/update-config-1",
  "feature/update-config-2",
  "feature/update-config-3"
]
```

### Advanced Usage

```bash
# Specify a different main branch
python update_prs.py --branches feature/branch1 --main-branch master --old-value 1.2 --new-value 2.0

# Dry run with multiple branches
python update_prs.py --branches feature/branch1 feature/branch2 --old-value 1.2 --new-value 2.0 --dry-run
```

## How It Works

For each branch/PR, the script follows this exact sequence:

1. **Checkout to target branch**: Switches to the branch to be processed
2. **Find common ancestor**: Uses `git merge-base` to find the common ancestor between the PR branch and main
3. **Identify changed files**: Uses `git diff` between the common ancestor and the PR commit to find originally changed files
4. **Selective variable update**: Updates the variable value (1.2 → 2.0) only in the files that were originally changed
5. **Commit changes**: Creates a commit with the variable update
6. **Rebase on main**: Rebases the branch on the latest main branch to bring it up to date
7. **Loop to next branch**: Moves to the next branch in the list

## Safety Features

- **Dry run mode**: Test without making changes
- **Selective updates**: Only modifies files originally changed in each PR
- **Error handling**: Continues processing other branches if one fails
- **Confirmation prompt**: Asks for confirmation before processing (unless in dry-run mode)

## Example Output

```
Branches to process: 3
  1. feature/update-config-1
  2. feature/update-config-2
  3. feature/update-config-3

Proceed with updating 3 branch(es)? (yes/no): yes

============================================================
Processing branch: feature/update-config-1
============================================================
  Checking out branch: feature/update-config-1
  Files changed in original PR: config/version.txt
  Updated config/version.txt
  Committing changes...
  ✓ Committed variable updates
  Rebasing on main...
  ✓ Successfully rebased on main
  ✓ Completed processing branch feature/update-config-1

============================================================
Processing branch: feature/update-config-2
============================================================
  Checking out branch: feature/update-config-2
  Files changed in original PR: app/config.json
  Updated app/config.json
  Committing changes...
  ✓ Committed variable updates
  Rebasing on main...
  ✓ Successfully rebased on main
  ✓ Completed processing branch feature/update-config-2

...

============================================================
Summary: 3/3 branches processed successfully
============================================================
```

## Important Notes

1. **Backup first**: Make sure you have a backup or are working in a safe environment
2. **Clean working directory**: The script will checkout branches, so ensure you have a clean working directory
3. **Merge conflicts**: If a branch has significant conflicts with main, the script will attempt to handle it but may require manual intervention
4. **Variable matching**: The script uses pattern matching to find and replace the variable value. It handles:
   - Exact matches: `1.2`
   - Quoted values: `"1.2"` or `'1.2'`
   - Values with spaces: `= 1.2` or `: 1.2`

## Troubleshooting

### "Not in a git repository"
Make sure you're running the script from within a git repository.

### "Cannot find branch"
The branch might not exist locally or remotely. Make sure to fetch remote branches first:
```bash
git fetch --all
```

### Rebase conflicts
If a branch has conflicts during rebase, the script will warn you. You'll need to:
1. Manually resolve the conflicts
2. Run `git rebase --continue` to complete the rebase
3. The script will continue with the next branch

### Variable not found
If the variable value isn't being updated, check:
- The old value matches exactly (including quotes, spacing, etc.)
- The file format is text-based (not binary)
- The file exists in the branch

## License

This script is provided as-is for your use case.

