from src.utils.health import check_for_updates, print_update_banner

import subprocess


print("🔍 Debugging Update Check...")

try:
    # 1. מנסים לעשות Fetch ידנית כדי לראות אם יש שגיאה
    print("running: git fetch...")
    subprocess.run(["git", "fetch"], check=True)
    print("✅ git fetch passed")

    # 2. בודקים פער
    print("running: git rev-list...")
    output = subprocess.check_output(
        ["git", "rev-list", "--count", "HEAD..origin/main"], 
        text=True
    )
    count = int(output.strip())
    print(f"📊 Commits behind: {count}")

    if count > 0:
        print("✅ Logic says: Update Available!")
        print_update_banner()
    else:
        print("❌ Logic says: System is up to date.")

except Exception as e:
    print(f"\n❌ ERROR DETECTED: {e}")

