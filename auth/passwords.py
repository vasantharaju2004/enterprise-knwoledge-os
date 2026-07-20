import bcrypt


def hash_password(plain: str) -> str:
    """
    hashes a plaintext password using bcrypt. The salt is generated
    automatically and embedded in the resulting hash, so no seperate
    salt stoeage is nedded. Raw passwords are never stored anywhere
    in this codebase - only this hash.
    """

    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Checks a plaintext password against a stored bcrypt hash.
    Used at login - never at registration, where hash_password
    is used instead
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
