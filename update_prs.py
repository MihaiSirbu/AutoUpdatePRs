import os
import subprocess
from pathlib import Path


def update_branch_code(branch_name, old_value, new_value):
    """
    Updates code in files that were changed in the PR, using the original state of 'main'
    at the time the PR was created — automatically detected from git history.
    
    This avoids needing to manually provide the base commit hash.
    """
    # Ensure we're in a git repo
    if not (Path('.git').exists()):
        print("Error: Not in a git repository.")
        return

    # Check if branch exists locally
    result = subprocess.run(['git', 'show-ref', '--verify', f'refs/heads/{branch_name}'], 
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: Branch '{branch_name}' does not exist locally.")
        return

    # Step 1: Find the merge base between main and the branch
    # This gives the common ancestor — the commit where the branch was created from main
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

    # Step 2: Get list of files changed between that base and the branch
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

    # Step 3: Update the files
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
                else:
                    print(f"ℹ  No changes needed in '{file_path}'")
            else:
                print(f"ℹ  '{old_value}' not found in '{file_path}'")

        except Exception as e:
            print(f" Error processing '{file_path}': {e}")

    print("\n All PR-targeted files updated.")


# Example usage:
if __name__ == "__main__":
    # Update branch 'feature1', change '5' to '10'
    update_branch_code(branch_name='feature1', old_value='1.6', new_value='1.6')
