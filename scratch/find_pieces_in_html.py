with open("c:/GitHub/Siti/CutMob/data_manager.py", "r", encoding="utf-8") as f:
    content = f.read()

# Trova export_html_report (offset 27307) and print 4000 characters from character 30500 onwards
print(content[30500:34500])
