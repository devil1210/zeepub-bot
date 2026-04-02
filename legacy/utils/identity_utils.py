import hashlib
import secrets
import string


def generate_short_link(book_hash: str) -> str:
    """
    Genera un link corto determinista de 10 caracteres basado en el hash del libro.
    Garantiza que el mismo libro siempre tenga el mismo link.
    """
    if not book_hash:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(10))

    # Derivamos un valor numérico estable del hash usando MD5
    alphabet = string.ascii_letters + string.digits
    hash_int = int(hashlib.md5(book_hash.encode()).hexdigest(), 16)

    res = []
    temp_hash = hash_int
    for _ in range(10):
        res.append(alphabet[temp_hash % len(alphabet)])
        temp_hash //= len(alphabet)

    return "".join(res)
