import csv
from pathlib import Path

from .cleaner import clean_ticket


def read_csv(path: str) -> list[dict]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset no encontrado: {path}")

    seen: dict[int, dict] = {}

    with open(file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = clean_ticket(row)
            tid = cleaned["ticket_id"]
            if tid <= 0:
                continue
            # En caso de ticket_id duplicado, conservar el último
            seen[tid] = cleaned

    return list(seen.values())
