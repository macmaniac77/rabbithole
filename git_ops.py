import subprocess
import os
import json
from typing import List, Optional, Dict 
import shutil 
from pathlib import Path 
from datetime import datetime, timezone # Added timezone
import re # For regex parsing of frontmatter
import yaml # For robust YAML parsing/updating

# --- Git Configuration & Setup ---
GIT_REPO_PATH = Path(os.getcwd()) / "RABBITHOLE_GIT_REPO" # Define a dedicated directory for the git repo
GIT_STATE_PATH = GIT_REPO_PATH / "state" # For UserContext JSONs
GIT_MARKDOWN_PATH = GIT_REPO_PATH / "markdown_content" # For copies of markdown files

def ensure_git_repo():
    if not (GIT_REPO_PATH / ".git").exists():
        GIT_REPO_PATH.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(["git", "init"], cwd=str(GIT_REPO_PATH), check=True, capture_output=True, text=True)
            print(f"Initialized Git repository in {GIT_REPO_PATH}.")
            with open(GIT_REPO_PATH / ".gitignore", "w") as f:
                f.write("# Ignore nothing by default, or specify files like .DS_Store\n")
            subprocess.run(["git", "-C", str(GIT_REPO_PATH), "add", ".gitignore"], check=True)
            subprocess.run(["git", "-C", str(GIT_REPO_PATH), "commit", "-m", "Initial commit: Add .gitignore"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error during git init: {e.stderr}")
            raise
        except FileNotFoundError:
            print("Error: Git command not found. Ensure Git is installed and in PATH.")
            raise
    GIT_STATE_PATH.mkdir(parents=True, exist_ok=True)
    GIT_MARKDOWN_PATH.mkdir(parents=True, exist_ok=True)

def get_user_context_json_path(user_id: str) -> str:
    return str(GIT_STATE_PATH / f"{user_id}.json")

def prepare_commit_message(user_id: str, action: str, vp_id: Optional[str] = None, doc_path: Optional[str] = None) -> str:
    if vp_id:
        return f"ctx({user_id}): VP {vp_id} {action}"
    elif doc_path:
        doc_filename = Path(doc_path).name # Use Path object's name attribute
        return f"doc({user_id}): {doc_filename} {action}"
    else:
        return f"ctx({user_id}): User profile {action}"

def commit_and_push(user_id: str, user_context_data: Dict, commit_message: str, source_markdown_relative_paths_to_copy: Optional[List[str]] = None):
    ensure_git_repo()
    github_token = os.getenv("GITHUB_TOKEN")
    git_user_name = os.getenv("GIT_USER_NAME", "BoathouseBot")
    git_user_email = os.getenv("GIT_USER_EMAIL", "bot@boathouse.ai")
    git_remote_url_base = os.getenv("GIT_REMOTE_URL_BASE") 

    try:
        subprocess.run(["git", "-C", str(GIT_REPO_PATH), "config", "user.name", git_user_name], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(GIT_REPO_PATH), "config", "user.email", git_user_email], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error configuring Git user: {e.stderr}")
    
    files_to_add_to_git_repo_relative = [] # Store paths relative to GIT_REPO_PATH

    # 1. UserContext JSON
    user_context_json_abs_path = Path(get_user_context_json_path(user_id))
    with open(user_context_json_abs_path, 'w') as f:
        json.dump(user_context_data, f, indent=4)
    files_to_add_to_git_repo_relative.append(str(user_context_json_abs_path.relative_to(GIT_REPO_PATH)))

    # 2. Markdown files
    if source_markdown_relative_paths_to_copy:
        for relative_path_str in source_markdown_relative_paths_to_copy:
            if not relative_path_str: continue
            
            relative_path = Path(relative_path_str) 
            # source_markdown_full_path is from project root / "RABBITHOLE" / "markdown" / relative_path
            source_markdown_full_path = Path(os.getcwd()) / "RABBITHOLE" / "markdown" / relative_path
            
            if source_markdown_full_path.exists():
                target_markdown_path_in_git_repo = GIT_MARKDOWN_PATH / relative_path
                target_markdown_path_in_git_repo.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(str(source_markdown_full_path), str(target_markdown_path_in_git_repo))

                # --- Add/Update Metadata Frontmatter ---
                try:
                    current_content = target_markdown_path_in_git_repo.read_text(encoding='utf-8')
                    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', current_content, re.DOTALL | re.MULTILINE)
                    
                    existing_frontmatter_data = {}
                    main_content = current_content

                    if frontmatter_match:
                        frontmatter_str = frontmatter_match.group(1)
                        main_content = frontmatter_match.group(2) if frontmatter_match.group(2) else ''
                        try:
                            existing_frontmatter_data = yaml.safe_load(frontmatter_str)
                            if not isinstance(existing_frontmatter_data, dict): 
                                existing_frontmatter_data = {}
                        except yaml.YAMLError as e_yaml:
                            print(f"Warning: Could not parse YAML for {target_markdown_path_in_git_repo}. Error: {e_yaml}")
                            main_content = f"---\n{frontmatter_str}\n---\n{main_content}" # Prepend invalid YAML back
                    
                    file_path_in_repo_for_git_log = (GIT_MARKDOWN_PATH / relative_path).relative_to(GIT_REPO_PATH)
                    version_hash = "new" 
                    is_file_tracked_result = subprocess.run(
                        ["git", "-C", str(GIT_REPO_PATH), "ls-files", "--error-unmatch", str(file_path_in_repo_for_git_log)],
                        capture_output=True, text=True
                    )

                    if is_file_tracked_result.returncode == 0: 
                        git_log_hash_cmd = ["git", "-C", str(GIT_REPO_PATH), "log", "-1", "--pretty=format:%h", "--", str(file_path_in_repo_for_git_log)]
                        try:
                            result = subprocess.run(git_log_hash_cmd, capture_output=True, text=True, check=True)
                            if result.stdout.strip(): version_hash = result.stdout.strip()
                            else: version_hash = "updated_no_prior_hash" # File tracked, but no specific hash (e.g. after add but before commit)
                        except subprocess.CalledProcessError as e_git_log:
                            print(f"Warning: Could not get git log hash for {file_path_in_repo_for_git_log}: {e_git_log}. Using 'updated'.")
                            version_hash = "updated"
                        except FileNotFoundError:
                            version_hash = "unknown_git_not_found"
                    
                    updated_metadata = {
                        'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                        'version': version_hash,
                        'views': existing_frontmatter_data.get('views', 0) 
                    }
                    final_frontmatter_data = {**existing_frontmatter_data, **updated_metadata}
                    new_frontmatter_str = yaml.dump(final_frontmatter_data, sort_keys=False, allow_unicode=True, default_flow_style=False)
                    target_markdown_path_in_git_repo.write_text(f"---\n{new_frontmatter_str}---\n{main_content.lstrip()}", encoding='utf-8') # lstrip main_content to avoid leading newline if it had none
                    print(f"Updated frontmatter for {target_markdown_path_in_git_repo}")
                except Exception as e_fm:
                    print(f"Error processing frontmatter for {target_markdown_path_in_git_repo}: {e_fm}. File committed as is.")
                
                files_to_add_to_git_repo_relative.append(str(target_markdown_path_in_git_repo.relative_to(GIT_REPO_PATH)))
            else:
                print(f"Warning: Source markdown file {source_markdown_full_path} not found.")
    
    # 3. Git operations
    if not files_to_add_to_git_repo_relative:
        print("No files to commit.")
        return

    try:
        # Remove duplicates just in case (e.g., user context path and a specific file path could be the same if user_id is a filename)
        unique_relative_files_to_add = sorted(list(set(files_to_add_to_git_repo_relative)))
        
        subprocess.run(["git", "add"] + unique_relative_files_to_add, cwd=str(GIT_REPO_PATH), check=True, capture_output=True)
        
        status_result = subprocess.run(["git", "status", "--porcelain"], cwd=str(GIT_REPO_PATH), capture_output=True, text=True)
        if not status_result.stdout.strip():
            print("No changes staged for commit.")
            return

        subprocess.run(["git", "commit", "-m", commit_message], cwd=str(GIT_REPO_PATH), check=True, capture_output=True)
        print(f"Committed to {GIT_REPO_PATH}: {commit_message}")

        if github_token and git_remote_url_base:
            remote_check = subprocess.run(["git", "-C", str(GIT_REPO_PATH), "remote"], capture_output=True, text=True)
            current_remotes = remote_check.stdout.strip().split('\n')
            remote_url = f"https://{git_user_name}:{github_token}@{git_remote_url_base}"
            
            if "origin" in current_remotes:
                 subprocess.run(["git", "-C", str(GIT_REPO_PATH), "remote", "set-url", "origin", remote_url], check=True, capture_output=True)
            else:
                 subprocess.run(["git", "-C", str(GIT_REPO_PATH), "remote", "add", "origin", remote_url], check=True, capture_output=True)
            
            subprocess.run(["git", "-C", str(GIT_REPO_PATH), "fetch", "origin"], check=True, capture_output=True)
            current_branch_result = subprocess.run(["git", "-C", str(GIT_REPO_PATH), "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True)
            current_branch = current_branch_result.stdout.strip()
            subprocess.run(["git", "-C", str(GIT_REPO_PATH), "push", "-u", "origin", current_branch], check=True, capture_output=True)
            print(f"Push successful to origin/{current_branch}.")
        elif not github_token: print("GITHUB_TOKEN not set. Skipping push.")
        elif not git_remote_url_base: print("GIT_REMOTE_URL_BASE not set. Skipping push.")

    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e}")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Stdout: {e.stdout.strip() if e.stdout else 'N/A'}")
        print(f"Stderr: {e.stderr.strip() if e.stderr else 'N/A'}")
    except FileNotFoundError:
        print("Error: Git command not found. Ensure Git is installed and in PATH.")

# Example usage (for testing, not part of the file's normal execution):
# if __name__ == "__main__":
#     ensure_git_repo()
#     # Create a dummy markdown file in the main project for testing copy
#     dummy_original_md_dir = Path(os.getcwd()) / "RABBITHOLE" / "markdown" / "test_docs_for_gitops"
#     dummy_original_md_dir.mkdir(parents=True, exist_ok=True)
#     dummy_original_md_file = dummy_original_md_dir / "sample_for_frontmatter.md"
#     with open(dummy_original_md_file, "w") as f:
#         f.write("# Hello Git World\nThis is a test document.")
    
#     test_user_id = "test_fm_user"
#     test_context_data = {"credits_usd": 20.0, "last_input": "testing frontmatter"}
#     test_commit_msg = prepare_commit_message(test_user_id, "profile and doc with frontmatter updated")
    
#     # Commit it once to simulate an existing file
#     commit_and_push(test_user_id, test_context_data, "Initial commit of sample_for_frontmatter.md", source_markdown_relative_paths_to_copy=["test_docs_for_gitops/sample_for_frontmatter.md"])
    
#     # Now update it and see if version changes
#     with open(dummy_original_md_file, "a") as f:
#         f.write("\nSome new content added.")
#     test_context_data["credits_usd"] = 25.0 # Change context too
#     commit_and_push(test_user_id, test_context_data, "Updated sample_for_frontmatter.md with more content", source_markdown_relative_paths_to_copy=["test_docs_for_gitops/sample_for_frontmatter.md"])

#     print(f"Test commit done. Check {GIT_REPO_PATH}")
#     print(f"Check content of {GIT_MARKDOWN_PATH / 'test_docs_for_gitops' / 'sample_for_frontmatter.md'}")
#     print("If testing push, ensure GITHUB_TOKEN and GIT_REMOTE_URL_BASE are set.")
