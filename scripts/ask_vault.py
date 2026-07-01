#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from inno_obsidian_ai.config import load_config
from inno_obsidian_ai.nvidia_client import (
    NVIDIAAPIKeyMissingError,
    NVIDIAClient,
    NVIDIAClientError,
)
from inno_obsidian_ai.rag import answer_question
from inno_obsidian_ai.vector_store import ChromaVectorStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", help="Question to ask against indexed vault")
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "obsidian_ai.example.yaml"),
        help="Path to config YAML",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        client = NVIDIAClient.from_config(config)
        stores = [
            ChromaVectorStore(
                persist_dir=str(config.chroma_dir),
                collection_name=collection_name,
            )
            for collection_name in config.rag_collection_names
        ]
        result = answer_question(config, client, stores, args.question)
    except (NVIDIAAPIKeyMissingError, NVIDIAClientError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(result.to_markdown())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
