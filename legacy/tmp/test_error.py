try:
    None / 1024.0
except TypeError as e:
    print(f"Error with float: {e}")

try:
    None / 1024
except TypeError as e:
    print(f"Error with int: {e}")
