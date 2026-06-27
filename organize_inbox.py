from pathlib import Path
import shutil
import re

# 이 스크립트가 있는 폴더를 Vault 루트로 사용
VAULT = Path(__file__).resolve().parent
INBOX = VAULT / "00_Inbox"

# type별 기본 이동 위치
DEST_BY_TYPE = {
    "research": VAULT / "20_Research",
    "concept": VAULT / "30_Concepts",
    "project": VAULT / "10_Projects",
    "decision": VAULT / "50_Decisions",
}

# 처음에는 True로 확인만 하고, 실제 이동하려면 False로 변경
DRY_RUN = False


def read_frontmatter(text: str) -> dict:
    """
    Markdown 파일 최상단 YAML frontmatter를 읽어서 dict로 변환한다.
    단순 key: value 구조를 기준으로 처리한다.
    """
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


def sanitize_folder_name(name: str) -> str:
    """
    project명을 안전한 폴더명으로 변환한다.
    Linux 기준으로 '/'는 경로 구분자라 제거하고,
    앞뒤 공백도 제거한다.
    """
    name = name.strip()

    # 경로 분리자로 오해될 수 있는 문자 제거/치환
    name = name.replace("/", "-")
    name = name.replace("\\", "-")

    # 너무 지저분한 공백 정리
    name = re.sub(r"\s+", " ", name)

    return name


def resolve_destination_dir(note_type: str, project: str | None) -> Path | None:
    """
    type과 project 값을 기준으로 최종 이동 폴더를 결정한다.

    예:
    type: concept
    project: auto-trading
    => 30_Concepts/auto-trading
    """
    base_dir = DEST_BY_TYPE.get(note_type)

    if base_dir is None:
        return None

    if project:
        safe_project = sanitize_folder_name(project)

        if safe_project:
            return base_dir / safe_project

    return base_dir


def safe_move(src: Path, dest_dir: Path):
    """
    파일을 목적지 폴더로 이동한다.
    목적지 폴더가 없으면 생성한다.
    동일 파일명이 이미 있으면 덮어쓰지 않고 건너뛴다.
    """
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
        project = meta.get("project")
        status = meta.get("status", "inbox")

        if status != "inbox":
            print(f"SKIP: status is not inbox -> {status}")
            continue

        if not note_type:
            print("REVIEW NEEDED: missing type")
            continue

        dest_dir = resolve_destination_dir(note_type, project)

        if dest_dir is None:
            print(f"REVIEW NEEDED: unknown type -> {note_type}")
            continue

        safe_move(md_file, dest_dir)


if __name__ == "__main__":
    main()