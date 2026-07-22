import re

with open("c:/GitHub/Siti/CutMob/data_manager.py", "r", encoding="utf-8") as f:
    dm_content = f.read()

with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    app_content = f.read()

print("=== data_manager.py functions ===")
for m in re.finditer(r"def (\w+)\(.*\):", dm_content):
    print("DM:", m.group(1))

print("\n=== app.py functions ===")
for m in re.finditer(r"def (\w+)\(.*\):", app_content):
    if "import" in m.group(1).lower() or "csv" in m.group(1).lower() or "carica" in m.group(1).lower() or "file" in m.group(1).lower():
        print("APP:", m.group(1))

print("\n=== Occurrences of 'csv' in data_manager.py ===")
for line_no, line in enumerate(dm_content.splitlines(), 1):
    if "csv" in line.lower() or "import" in line.lower():
        if "def " in line or "class " in line or "import_csv" in line or "importa" in line:
            print(f"{line_no}: {line}")
