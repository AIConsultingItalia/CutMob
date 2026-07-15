import json
with open("database.json", "r", encoding="utf-8") as f:
    db = json.load(f)

print("Keys:", db.keys())
print("Number of barre:", len(db.get("barre", [])))
print("Number of semilavorati:", len(db.get("semilavorati", [])))
print("Unique heights of barre:", set(b.get("height") for b in db.get("barre", [])))
print("Unique widths of barre:", set(b.get("width") for b in db.get("barre", [])))
print("Unique heights of semilavorati:", set(s.get("height") for s in db.get("semilavorati", [])))
print("Unique widths of semilavorati:", set(s.get("width") for s in db.get("semilavorati", [])))
