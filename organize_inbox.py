from pathlib import Path
import shutil
import re

# 이 스크립트가 있는 폴더를 Vault 루트로 사용
VAULT = Path(__file__).resolve().parent
INBOX = VAULT / "00_Inbox"

DEST_BY_TYPE = {
    "research": VAULT / "20_Research",
    "concept": VAULT / "30_Concepts",
    "project": VAULT / "10_Projects",
    "decision": VAULT / "50_Decisions",
}

DRY_RUN = False  # 처음에는 True. 실제 이동하려면 False로 변경.

def read_frontmatter(text: str) -> dict:
    text = text.lstrip("\ufeff")
    text = text.lstrip()

    if not text.startswith("---"):
        return {}

    match = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not match:
        return {}

    frontmatter = {}

    for line in match.group(1).splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip().strip('"').strip("'")

    return frontmatter

def safe_move(src: Path, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name

    if dest.exists():
        print(f"SKIP: already exists -> {dest.relative_to(VAULT)}")
        return

    if DRY_RUN:
        print(f"DRY-RUN: {src.relative_to(VAULT)} -> {dest.relative_to(VAULT)}")
    else:
        shutil.move(str(src), str(dest))
        print(f"MOVED: {src.relative_to(VAULT)} -> {dest.relative_to(VAULT)}")

def main():
    print(f"VAULT: {VAULT}")
    print(f"INBOX: {INBOX}")
    print(f"INBOX exists: {INBOX.exists()}")

    if not INBOX.exists():
        print("ERROR: 00_Inbox folder does not exist.")
        return

    md_files = list(INBOX.rglob("*.md"))
    print(f"Found markdown files: {len(md_files)}")

    for md_file in md_files:
        print(f"\nCHECK: {md_file.relative_to(VAULT)}")

        text = md_file.read_text(encoding="utf-8")
        meta = read_frontmatter(text)

        print(f"META: {meta}")

        note_type = meta.get("type")
        status = meta.get("status", "inbox")

        if status != "inbox":
            print(f"SKIP: status is not inbox -> {status}")
            continue

        if note_type in DEST_BY_TYPE:
            safe_move(md_file, DEST_BY_TYPE[note_type])
        else:
            print(f"REVIEW NEEDED: unknown or missing type -> {note_type}")

if __name__ == "__main__":
    main()
