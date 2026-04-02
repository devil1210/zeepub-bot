import cocoindex

print("Available targets in cocoindex.targets:")
for attr in dir(cocoindex.targets):
    if not attr.startswith("_"):
        print(f" - {attr}")
