"""
Open Drama Engine — Backup & Restore Point Creator Script
Compresses project source files into OPEN-DRAMA-ENGINE_RestorePoint_Milestone2_Passed.zip
and creates Git commit & tag if git is initialized.
"""

import os
import sys
import zipfile
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE_DIR = Path(__file__).parent.resolve()
ZIP_FILENAME = "OPEN-DRAMA-ENGINE_RestorePoint_Milestone2_Passed.zip"
ZIP_PATH = WORKSPACE_DIR / ZIP_FILENAME

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "dist", ".idea", ".vscode"}
EXCLUDE_FILES = {ZIP_FILENAME, "test_sequence_render.mp4", "test_end_to_end_cartoon_sequence.mp4", "test_milestone2_assembled_script_sequence.mp4"}

def create_zip_archive():
    print(f"📦 Creating Zip Restore Point: {ZIP_FILENAME}...")
    file_count = 0
    total_bytes = 0

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(WORKSPACE_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if file in EXCLUDE_FILES or file.endswith(".zip"):
                    continue
                
                full_path = Path(root) / file
                rel_path = full_path.relative_to(WORKSPACE_DIR)
                
                zipf.write(full_path, rel_path)
                file_count += 1
                total_bytes += full_path.stat().st_size
                print(f"  + Added: {rel_path} ({full_path.stat().st_size} bytes)")

    zip_size = ZIP_PATH.stat().st_size
    print(f"✅ Archive Saved: {ZIP_FILENAME} ({file_count} files, {zip_size} bytes / {(zip_size/1024/1024):.2f} MB)")
    return ZIP_PATH

def create_git_commit_and_tag():
    git_dir = WORKSPACE_DIR / ".git"
    if not git_dir.exists():
        print("ℹ️ Git repository not initialized. Initializing git repository for tracking...")
        try:
            subprocess.run(["git", "init"], cwd=WORKSPACE_DIR, check=True)
        except Exception as err:
            print(f"Notice: Git init skipped ({err})")
            return

    try:
        print("🐙 Staging files and creating Git commit & tag...")
        subprocess.run(["git", "add", "."], cwd=WORKSPACE_DIR, check=True)
        subprocess.run(["git", "commit", "-m", "restore-point-milestone2-verified"], cwd=WORKSPACE_DIR, check=True)
        subprocess.run(["git", "tag", "-f", "-a", "restore-point-milestone2-verified", "-m", "Milestone 2 Verified Restore Point"], cwd=WORKSPACE_DIR, check=True)
        print("✅ Git Commit & Tag 'restore-point-milestone2-verified' created successfully!")
    except Exception as err:
        print(f"Notice on Git commit/tag: {err}")

if __name__ == "__main__":
    archive_path = create_zip_archive()
    create_git_commit_and_tag()
    print("\n🎉 COMPLETE RESTORE POINT CREATED SUCCESSFULLY!")
