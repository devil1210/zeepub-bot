import cocoindex

print("Available functions in cocoindex.functions:")
for attr in dir(cocoindex.functions):
    if not attr.startswith("_"):
        print(f" - {attr}")
