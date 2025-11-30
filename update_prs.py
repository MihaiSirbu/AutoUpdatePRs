import os
import subprocess
from pathlib import Path
import json
import sys


def process_branches_batch(branch_names, old_value, new_value):
    if not (Path('.git').exists()):
        print("Error: Not in a git repository.")
        return

    for branch_name in branch_names:
        print(f"\n{'='*60}")
        print(f"Processing branch: {branch_name}")
        print(f"{'='*60}")

 
        update_branch_code(branch_name=branch_name, old_value=old_value, new_value=new_value)

        
        try:
            print(f"Rebasing '{branch_name}' onto 'main'...")
            subprocess.run(['git', 'rebase', 'main'], check=True)
            print(f"Successfully rebased '{branch_name}' onto 'main'.")
        except subprocess.CalledProcessError as e:
            print(f"Rebase failed. Resolve conflicts and retry manually. Error: {e}")
            continue 


        try:
            remote_branch = f"origin/{branch_name}"
            print(f"Pushing '{branch_name}' to remote '{remote_branch}'...")
            subprocess.run(['git', 'push', '--force-with-lease', 'origin', branch_name], check=True)
            print(f"Successfully pushed '{branch_name}' to remote.")
        except subprocess.CalledProcessError as e:
            print(f"Push failed: {e}")
            continue

        try:
            subprocess.run(['git', 'checkout', 'main'], check=True)
            print("Switched back to 'main'.")
        except subprocess.CalledProcessError:
            print("Warning: Could not switch back to 'main'.")


def update_branch_code(branch_name, old_value, new_value):
    """
    Updates code in files that were changed in the PR, using the original state of 'main'
    at the time the PR was created — automatically detected from git history.
    
    This avoids needing to manually provide the base commit hash.
    """

    if not (Path('.git').exists()):
        print("Error: Not in a git repository.")
        return
        


    result = subprocess.run(['git', 'show-ref', '--verify', f'refs/heads/{branch_name}'], 
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: Branch '{branch_name}' does not exist locally.")
        return

    
    try:
        subprocess.run(['git', 'fetch', 'origin', 'main'], check=True)
        print("Fetched latest 'main' from remote.")
    except subprocess.CalledProcessError as e:
        print("Error: Failed to fetch 'main' from remote. Please check your network or remote configuration.")
        return

    merge_base_result = subprocess.run(
        ['git', 'merge-base', 'main', branch_name],
        capture_output=True, text=True
    )

    if merge_base_result.returncode != 0:
        print("Error: Could not find merge base between 'main' and the branch.")
        print("Make sure 'main' exists and the branch is based on it.")
        return

    base_commit_hash = merge_base_result.stdout.strip()
    print(f" Detected base commit (main at PR creation): {base_commit_hash}")


    diff_result = subprocess.run(
        ['git', 'diff', '--name-only', f'{base_commit_hash}..{branch_name}'],
        capture_output=True, text=True
    )

    if diff_result.returncode != 0 or not diff_result.stdout.strip():
        print(f"No changes found between '{base_commit_hash}' and '{branch_name}'.")
        return

    changed_files = diff_result.stdout.strip().split('\n')

    print(f"Found {len(changed_files)} file(s) changed in the PR:")
    for file_path in changed_files:
        print(f"  - {file_path}")

    try:
        subprocess.run(['git', 'checkout', branch_name], check=True)
        print(f"Switched to branch '{branch_name}'.")
    except subprocess.CalledProcessError:
        print(f"Error: Could not switch to branch '{branch_name}'.")
        return
    updated_count = 0

    for file_path in changed_files:
        file_path = Path(file_path).resolve()
        if not file_path.is_file():
            print(f"Skipping non-file: {file_path}")
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_value in content:
                new_content = content.replace(old_value, new_value)
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f" Updated '{file_path}'")
                    updated_count += 1
                else:
                    print(f"  No changes needed in '{file_path}'")
            else:
                print(f" '{old_value}' not found in '{file_path}'")
                print(f"branch_name: {branch_name}")
                print("--------------------------------")

        except Exception as e:
            print(f" Error processing '{file_path}': {e}")



    print("\n All PR-targeted files updated.")


    if updated_count > 0:
        try:
            subprocess.run(['git', 'add'] + changed_files, check=True)
            commit_message = f"Update '{old_value}' → '{new_value}' in PR files"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            print(f"\n {updated_count} file(s) updated and committed in '{branch_name}'.")
        except subprocess.CalledProcessError as e:
            print(f"  Commit failed: {e}")
        else:
            print("\nNo changes were made. Nothing to commit.")


    try:
        subprocess.run(['git', 'checkout', 'main'], check=True)
        print("Switched back to 'main'.")
    except subprocess.CalledProcessError:
        print("Warning: Could not switch back to 'main'.")



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Branch file not found, use it with python update_prs.py <BRANCHFILE.json>")
        sys.exit(1)
    
    branches_file = sys.argv[1]
    with open(branches_file, 'r') as f:
        branches_names = json.load(f)
    process_branches_batch(branches_names, old_value='2.0', new_value='2.9')
