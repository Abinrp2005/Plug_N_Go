import subprocess
import sys
import os

print("=" * 50)
print("  ⚡ PLUG AND GO — Auto Fix & Start")
print("=" * 50)
print()

# Step 1: Check Python version
print(f"✅ Python: {sys.version.split()[0]}")

# Step 2: Install missing packages
print("\n📦 Installing/checking packages...")
packages = [
    "flask",
    "flask-login", 
    "flask-sqlalchemy",
    "flask-wtf",
    "pymysql",
    "cryptography",
    "werkzeug"
]
for pkg in packages:
    result = subprocess.run(
        [sys.executable, "-m", "pip", 
         "install", pkg, "-q"],
        capture_output=True
    )
    print(f"  ✅ {pkg}")

# Step 3: Check MySQL connection
print("\n🗄️  Checking MySQL...")
try:
    import pymysql
    
    # Try connecting to MySQL server
    conn = pymysql.connect(
        host     = "localhost",
        user     = "root",
        password = "lbscek",
        port     = 3306
    )
    print("  ✅ MySQL server is running!")
    
    # Create database if not exists
    cursor = conn.cursor()
    cursor.execute(
        "CREATE DATABASE IF NOT EXISTS "
        "plugandgo CHARACTER SET utf8mb4 "
        "COLLATE utf8mb4_unicode_ci;"
    )
    conn.commit()
    print("  ✅ Database 'plugandgo' ready!")
    
    # Check tables
    cursor.execute("USE plugandgo")
    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    if tables:
        print(f"  ✅ Tables found: {', '.join(tables)}")
    else:
        print("  ⚠️  No tables yet — will be created by Flask")
    
    conn.close()

except pymysql.err.OperationalError as e:
    error_code = e.args[0]
    if error_code == 1045:
        print("  ❌ Wrong MySQL password!")
        print("     Current password: lbscek")
        print("     Fix: Update password in app.py")
    elif error_code == 2003:
        print("  ❌ MySQL server is NOT running!")
        print("     Fix: Open Windows Services")
        print("          Find MySQL80")
        print("          Right click → Start")
    else:
        print(f"  ❌ MySQL error: {e}")
    
    print("\n  Cannot start Flask without MySQL.")
    input("\n  Press Enter to exit...")
    sys.exit(1)

except Exception as e:
    print(f"  ❌ Unexpected error: {e}")
    input("\n  Press Enter to exit...")
    sys.exit(1)

# Step 4: Check app.py exists
print("\n📁 Checking project files...")
if os.path.exists("app.py"):
    print("  ✅ app.py found!")
else:
    print("  ❌ app.py NOT found!")
    print("     Make sure you are in the")
    print("     correct project folder")
    input("\n  Press Enter to exit...")
    sys.exit(1)

# Step 5: Check for syntax errors
print("\n🔍 Checking app.py for errors...")
result = subprocess.run(
    [sys.executable, "-m", "py_compile", "app.py"],
    capture_output=True,
    text=True
)
if result.returncode == 0:
    print("  ✅ No syntax errors found!")
else:
    print("  ❌ Syntax error in app.py!")
    print(f"     {result.stderr}")
    input("\n  Press Enter to exit...")
    sys.exit(1)

# Step 6: Check port 5000
print("\n🔌 Checking port 5000...")
import socket
sock = socket.socket(
    socket.AF_INET, socket.SOCK_STREAM
)
result = sock.connect_ex(('127.0.0.1', 5000))
sock.close()

if result == 0:
    print("  ⚠️  Port 5000 is already in use!")
    print("     Another Flask may be running")
    print("     Opening on port 5001 instead...")
    port = 5001
else:
    print("  ✅ Port 5000 is free!")
    port = 5000

# Step 7: Start Flask
print()
print("=" * 50)
print(f"  🚀 Starting Flask on port {port}...")
print(f"  🌐 Open: http://127.0.0.1:{port}/login")
print()
print("  Admin  : arjun.menon@plugandgo.in")
print("  Pass   : Admin@1234")
print()
print("  User   : aravind.krishnamurthy")
print("           @gmail.com")
print("  Pass   : Aravind@123")
print()
print("  ⚠️  Keep this window OPEN!")
print("  ⚠️  Press Ctrl+C to stop")
print("=" * 50)
print()

# Modify port if needed
if port == 5001:
    with open("app.py", "r") as f:
        content = f.read()
    if "port=5000" in content:
        content = content.replace(
            "port=5000", "port=5001"
        )
        with open("app.py", "w") as f:
            f.write(content)

# Start the app
os.system("python app.py")

input("\nPress Enter to exit...")
