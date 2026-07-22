with open("c:/GitHub/Siti/CutMob/app.py", "r", encoding="utf-8") as f:
    content = f.read()

start_char = 47000
end_char = 49500
print(content[start_char:end_char])
