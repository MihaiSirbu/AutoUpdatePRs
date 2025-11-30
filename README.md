# Git Branch Code Updater with Rebase and Push

This script updates code in files changed in a given branch, rebase the branch off `main`, and push the updated branch to remote. It supports processing multiple branches from an array.

---

## 

Steps

- Accepts an array of branch names as input
- Loops through each branch, checks out the branch

For each branch : 
- merge-base to find common ancestor between the branch and main (where the branch diverged from main)
- diff between the merge-base commit hash and current head of the branch, to find what files have been changed (i.e between main at the time it diverged and current `HEAD` of branch)
- Updates specified strings in files changed in the branch ( eg. change from version 1.2 to 1.4 )
- commits locally to the target branch
- Rebases the branch on top of latest `main`
- Push the updated branch to remote using `--force-with-lease`

This in theory will update all open Pull Requests with the latest commit from the code.

## Usage

1. Create a local json file that contains an array of target branches(strings). See `branches.json` as an example.
2. run `python update_prs.py --branches_file "branches.json" --old_value "<string>oldvalue" --new_value "<string>newvalue"`



---

##  Prerequisites

- Python 3.6+
- Git installed and configured
- Access to remote repository


## Example Output : 
```
Processing 3 branches...

==================================================
Processing branch: feature1
==================================================

Detected base commit (main at PR creation): abc1234
Found 2 file(s) changed in the PR:
  - src/utils.py
  - docs/README.md
 Updated 'src/utils.py'
  No changes needed in 'docs/README.md'
 All PR-targeted files updated.
 1 file(s) updated and committed in 'feature1'.
Fetched latest changes from origin.
Successfully rebased 'feature1' onto 'origin/main'.
Successfully pushed rebased 'feature1' to remote.
Switched back to 'main'.

Completed: feature1
---
```
