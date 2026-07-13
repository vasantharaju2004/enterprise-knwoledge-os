import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent
UPLOAD_DIR = PROJECT_ROOT / "uploads"


def save_file(file_bytes=bytes, filename="") -> str:
    """
    saves uploaded files bytes to the local uploads/ folder
    returns the full path where the file was saved
    """

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination = UPLOAD_DIR / filename

    with open(destination, "wb") as f:
        f.write(file_bytes)

    return str(destination)


def delete_file(filename: str) -> None:
    """
    Deletes a file from the uploads/ folder.
    used when a document is removed by the user.
    """
    target = UPLOAD_DIR / filename
    if target.exists():
        target.unlink()
