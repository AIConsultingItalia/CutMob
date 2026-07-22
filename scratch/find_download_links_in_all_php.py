import os

panel_path = "c:/GitHub/Siti/aiconsultingitalia/panel"
for root, dirs, files in os.walk(panel_path):
    for file in files:
        if file.endswith(".php"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            for idx, line in enumerate(lines):
                if "$download_link" in line:
                    print(f"{path} (line {idx+1}): {line.strip()}")
