import cocoindex
import inspect

print("Postgres Source Init:")
print(inspect.signature(cocoindex.sources.Postgres.__init__))

print("Postgres Target Init:")
print(inspect.signature(cocoindex.targets.Postgres.__init__))
