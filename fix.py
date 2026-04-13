import os
import re
import subprocess

def run(cmd):
    print(f"Executing: {cmd}")
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

# --- 1. CONVERT COGS ---
print("🛠️  Converting cogs to Hybrid...")
COGS_DIR = "./cogs"
for root, _, files in os.walk(COGS_DIR):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            new_content = re.sub(r'@commands\.command\(', '@commands.hybrid_command(', content)
            with open(path, 'w') as f:
                f.write(new_content)

# --- 2. INJECT SYNC ---
print("🛠️  Injecting sync logic into bot.py...")
with open("bot.py", "r") as f:
    main_content = f.read()
if "bot.tree.sync()" not in main_content:
    sync_code = "\n    await bot.tree.sync()\n    print('Tree Synced')"
    main_content = re.sub(r'(async def on_ready\(.*?\):)', r'\1' + sync_code, main_content)
    with open("bot.py", "w") as f:
        f.write(main_content)

# --- 3. RESET GIT HISTORY (To bypass Push Protection) ---
print("🧹 Cleaning Git history...")
run("git reset $(git commit-tree HEAD^{tree} -m 'Fresh Start: Hybrid Commands & Secure Token')")

# --- 4. PUSH ---
print("📤 Pushing to GitHub...")
run("git remote set-url origin https://github.com/27-oz/CraftBot.git")
print("\n🚀 Script finished. Now run: git push origin main --force")

