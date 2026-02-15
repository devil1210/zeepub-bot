import json

with open("audit_report.json") as f:
    data = json.load(f)

e402_files = sorted({i["filename"] for i in data if i["code"] == "E402"})
print("Files with E402:")
for f in e402_files:
    print(f"- {f}")

b904_files = sorted({i["filename"] for i in data if i["code"] == "B904"})
print("\nFiles with B904:")
for f in b904_files:
    print(f"- {f}")
