import csv
import sys
from pathlib import Path
from db.session import get_session, init_db
from db.repository import add_news

# CSV: text,is_fake,explanation,source_url,category
# is_fake: true/false
def main(csv_path: str) -> None:
    init_db()
    session = get_session()
    added = 0
    try:
        with open(csv_path, encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            required = {"text", "is_fake", "explanation"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("CSV должен содержать колонки text,is_fake,explanation.")
            for row in reader:
                label = row["is_fake"].strip().lower()
                if label not in ("true", "false", "1", "0"):
                    raise ValueError(f"Некорректная метка: {label}")
                add_news(session, row["text"].strip(), label in ("true", "1"),
                         row["explanation"].strip(), row.get("source_url", "").strip(),
                         row.get("category", "").strip())
                added += 1
    finally:
        session.close()
    print(f"Загружено новостей: {added}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python -m scripts.load_dataset data/news.csv")
        raise SystemExit(1)
    main(sys.argv[1])
