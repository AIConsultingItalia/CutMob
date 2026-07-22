with open("c:/GitHub/Siti/aiconsultingitalia/panel/panel_cantierepro/index.php", "r", encoding="utf-8") as f:
    lines_cantierepro = f.readlines()

for idx, line in enumerate(lines_cantierepro):
    if "actionButtons =" in line and "isDemo" in lines_cantierepro[idx-1]:
        print(f"CantierePro isDemo block at: {idx+1}")
        for j in range(idx - 1, idx + 18):
            print(f"{j+1}: {lines_cantierepro[j]}", end="")
        break
