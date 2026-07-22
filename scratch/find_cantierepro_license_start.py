with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cantierepro/index.php", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "function openLicenseModal" in line:
        print(f"openLicenseModal function starts at: {idx+1}")
        for j in range(idx - 4, idx + 4):
            print(f"{j+1}: {lines[j]}", end="")
        break
