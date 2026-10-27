"""Download the public documents for RAG (data/docs_rag/sources.yaml) into DATA_ROOT/docs_rag/.

Never blocks: a document without a verified URL, or a failed download, prints manual steps.
Afterwards run `python -m voltguard index-docs`. Until a legal text is loaded, the field
assistant answers "not found in approved documents" for it and reports cite the provision by
name only.
"""

from __future__ import annotations

import os
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", ROOT / ".data"))


def main() -> int:
    import yaml

    sources = yaml.safe_load((ROOT / "data" / "docs_rag" / "sources.yaml").read_text(encoding="utf-8")) or {}
    target = DATA_ROOT / "docs_rag"
    target.mkdir(parents=True, exist_ok=True)
    for doc in sources.get("documents", []):
        have = [p for p in target.glob(f"{doc['id']}.*") if p.suffix in (".pdf", ".txt", ".md")]
        if have:
            print(f"  {doc['id']}: already present ({have[0].name})")
            continue
        url = (doc.get("url") or "").strip()
        if url:
            out = target / f"{doc['id']}.pdf"
            try:
                with urllib.request.urlopen(url, timeout=60) as response, open(out.with_suffix(".part"), "wb") as fh:
                    shutil.copyfileobj(response, fh)
                out.with_suffix(".part").rename(out)
                print(f"  {doc['id']}: downloaded {out}")
                continue
            except Exception as exc:
                out.with_suffix(".part").unlink(missing_ok=True)
                print(f"  {doc['id']}: download failed ({str(exc)[:100]})")
        print(f"  {doc['id']}: {doc['title']}. Manual step: {doc['manual']} Save it as {target / (doc['id'] + '.pdf')}")
    print("Then run: python -m voltguard index-docs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
