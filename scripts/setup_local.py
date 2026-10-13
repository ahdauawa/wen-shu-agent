"""Create local configuration once without printing or committing secrets."""
import secrets
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / ".env"
    if target.exists():
        print(".env already exists; kept unchanged.")
        return
    template = (root / ".env.example").read_text(encoding="utf-8")
    content = template.replace("replace-with-a-random-local-key", secrets.token_urlsafe(24))
    with target.open("x", encoding="utf-8") as handle:
        handle.write(content)
    print("Created .env with a random API key. Open it locally to copy WENSHU_API_KEYS.")


if __name__ == "__main__":
    main()
