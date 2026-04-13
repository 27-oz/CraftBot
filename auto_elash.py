import os
import re
import subprocess

# --- CONFIGURATION ---
COGS_DIR = "./cogs"  # Change this if your cogs are in a different folder
MAIN_FILE = "main.py"  # Change this to your bot's entry point
COMMIT_MSG = "Automated conversion to Hybrid Commands and Slash Sync"

def run_git(commands):
    for cmd in commands:
        print(f"Executing: {cmd}")
        subprocess.run(cmd, shell=True)

def transform_code():
    print("🛠️  Refactoring cogs to Hybrid Commands...")
    # Update Cogs
    for root, _, files in os.walk(COGS_DIR):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()
                
                # Swap standard command for hybrid
                new_content = re.sub(r'@commands\.command\(', '@commands.hybrid_command(', content)
                
                if new_content != content:
                    with open(path, 'w') as f:
                        f.write(new_content)
                    print(f"✅ Updated {file}")

    # Update Main File for Tree Sync
    print(f"🛠️  Injecting sync logic into {MAIN_FILE}...")
    with open(MAIN_FILE, 'r') as f:
        main_content = f.read()

    if "await bot.tree.sync()" not in main_content:
        # Simple injection: find on_ready and add the sync line
        sync_code = "\n    await bot.tree.sync()\n    print('Tree Synced')"
        main_content = re.sub(r'(async def on_ready\(.*?\):)', r'\1' + sync_code, main_content)
        with open(MAIN_FILE, 'w') as f:
            f.write(main_content)
        print("✅ Sync logic added to on_ready.")

def push_to_repo():
    print("📤 Pushing changes to Git...")
    run_git([
        "git add .",
        f'git commit -m "{COMMIT_MSG}"',
        "git push"
    ])

if __name__ == "__main__":
    transform_code()
    push_to_repo()
    print("\n✨ Automation complete! Your bot now supports /commands and !prefix.")

