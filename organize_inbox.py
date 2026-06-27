from pathlib import Path
import shutil
import re

VAULT = Path.home() / "Documents" / "Obsidian" / "INNO-KB"
INBOX = VAULT / "00_Inbox"

DEST_BY_TYPE = {
    "research": VAULT / "20_Research",
    "concept": VAULT / "30_Concepts",
    "project": VAULT / "10_Projects",
    "decision": VAULT / "50_Decisions",
}

def read_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}

    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    frontmatter = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip().strip('"').strip("'")

    return frontmatter

def safe_move(src: Path, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name

    if dest.exists():
        print(f"SKIP: already exists -> {dest}")
        return

    shutil.move(str(src), str(dest))
    print(f"MOVED: {src.name} -> {dest_dir.relative_to(VAULT)}")

def main():
    for md_file in INBOX.glob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        meta = read_frontmatter(text)

        note_type = meta.get("type")
        status = meta.get("status", "inbox")

        if status != "inbox":
            continue

        if note_type in DEST_BY_TYPE:
            safe_move(md_file, DEST_BY_TYPE[note_type])
        else:
            print(f"REVIEW NEEDED: {md_file.name}")

if __name__ == "__main__":
    main()