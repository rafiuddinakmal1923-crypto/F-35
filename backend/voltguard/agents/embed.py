"""Embeddings for RAG and similar-case search (SDD 8.2-8.3).

multilingual-e5-small (MIT; English and Bahasa Melayu) runs locally through ONNX Runtime when
`python -m voltguard fetch-models` has put it under HF_HOME. e5 expects prefixes: documents as
"passage: <text>" and questions as "query: <text>". Without the model files (offline laptop,
tests) a deterministic hashing embedder of the same size is used and the index records which.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

DIM = 384
BATCH = 16                      # passages per model run: bounded memory however long the document
MODEL_ID = os.environ.get("EMBED_MODEL", "intfloat/multilingual-e5-small")
TOKEN = re.compile(r"[a-z0-9]+")
STOP = set("the a an and or of to in on at for is are was were be by with this that it its as from into than then there their "
           "yang dan di ke dari untuk pada ini itu dengan atau adalah oleh "
           # question words: "What should I ..." shares them with every passage that says "what" or "should"
           "what which who whom whose when where why how do does did can could should would will my me we our you your about "
           "apa apakah adakah bagaimana bila bilakah mana siapa mengapa kenapa saya kami kita anda tentang mengenai".split())


def _model_dir() -> Path | None:
    home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
    for candidate in [home / "voltguard" / MODEL_ID.replace("/", "--"), *home.glob(f"hub/models--{MODEL_ID.replace('/', '--')}/snapshots/*")]:
        if (candidate / "onnx" / "model.onnx").exists() and (candidate / "tokenizer.json").exists():
            return candidate
    return None


@lru_cache(maxsize=1)
def _onnx():
    folder = _model_dir()
    if folder is None:
        return None
    try:
        import onnxruntime as ort
        from tokenizers import Tokenizer
    except ImportError:
        return None
    tok = Tokenizer.from_file(str(folder / "tokenizer.json"))
    tok.enable_truncation(512)
    tok.enable_padding()
    return tok, ort.InferenceSession(str(folder / "onnx" / "model.onnx"), providers=["CPUExecutionProvider"])


def model_name() -> str:
    return MODEL_ID if _onnx() is not None else "hash-384"


def words(text: str) -> list[str]:
    return [w for w in TOKEN.findall(text.lower()) if w not in STOP and len(w) > 1]


def _hash_embed(text: str) -> np.ndarray:
    v = np.zeros(DIM)
    tokens = words(text)
    grams = tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
    for g in grams:
        h = int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8).digest(), "little")
        v[h % DIM] += 1.0 if (h >> 32) & 1 else -1.0
    n = np.linalg.norm(v)
    return v / n if n else v


def embed(texts: list[str], kind: str = "passage") -> np.ndarray:
    """(n, 384) unit vectors. kind = passage | query (the e5 prefixes)."""
    model = _onnx()
    if model is None:
        return np.array([_hash_embed(t) for t in texts]) if texts else np.zeros((0, DIM))
    tok, session = model
    if not texts:
        return np.zeros((0, DIM))
    out = []
    # Small batches: one batch of every passage (the Penal Code alone has ~1,100), padded to 512 tokens,
    # needs several GB and was killed by the out-of-memory check.
    for start in range(0, len(texts), BATCH):
        enc = tok.encode_batch([f"{kind}: {t}" for t in texts[start:start + BATCH]])
        ids = np.array([e.ids for e in enc], dtype=np.int64)
        mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
        feeds = {"input_ids": ids, "attention_mask": mask}
        if "token_type_ids" in [i.name for i in session.get_inputs()]:
            feeds["token_type_ids"] = np.zeros_like(ids)
        hidden = session.run(None, feeds)[0]
        pooled = (hidden * mask[..., None]).sum(axis=1) / np.maximum(mask.sum(axis=1, keepdims=True), 1)
        out.append(pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-9))
    return np.vstack(out)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na and nb else 0.0


# Words that mean the same in English and Bahasa Melayu, for the keyword check: the Electricity Supply
# Act on file is the Malay reprint, and an English question about it ("penalty for tampering") shares
# almost no words with "didenda ... mengganggu". Domain terms only, so unrelated questions stay unmatched.
TERMS = [
    # the Act words electricity theft as dishonestly taking or using it ("dengan curang mengambil elektrik")
    {"theft", "steal", "stealing", "stolen", "curi", "mencuri", "kecurian", "dishonestly", "abstracts", "abstraction", "curang"},
    {"penalty", "penalties", "punishment", "punished", "fine", "fined", "hukuman", "dihukum", "denda", "didenda", "penalti"},
    {"imprisonment", "imprisoned", "jail", "prison", "penjara", "dipenjarakan", "pemenjaraan"},
    {"tamper", "tampering", "tampered", "interfere", "interferes", "interference", "usik", "mengusik", "ganggu", "mengganggu"},
    {"convicted", "conviction", "disabitkan", "sabitan"},
    {"offence", "offences", "offense", "kesalahan"},
    {"electricity", "electric", "electrical", "elektrik"},
    {"supply", "bekalan", "pembekalan"},
    {"act", "akta"},
    {"section", "seksyen"},
    {"licence", "license", "licensee", "lesen"},
    {"installation", "installations", "pepasangan"},
    {"equipment", "kelengkapan"},
    {"consumer", "consumers", "customer", "customers", "pengguna"},
    {"disconnect", "disconnection", "memotong", "pemotongan"},
    {"inspect", "inspection", "inspections", "pemeriksaan", "memeriksa"},
    {"evidence", "bukti", "keterangan"},
    {"owner", "occupier", "pemunya", "penghuni"},
    {"premises", "premis"},
    {"damage", "damaged", "rosak", "kerosakan", "merosakkan"},
    {"meter", "meters", "penyukatan"},
    {"cable", "cables", "kabel"},
    {"wiring", "wire", "wires", "pendawaian", "wayar"},
    {"connection", "connect", "connected", "sambungan", "menyambung"},
    {"compensation", "pampasan"},
    {"court", "mahkamah"},
    {"seize", "seizure", "sita", "menyita"},
    {"enter", "entry", "memasuki"},
    {"solar", "suria"},
]
_SAME = {w: group for group in TERMS for w in group}


def keyword_overlap(query: str, text: str) -> float:
    """Share of the question's words found in the text (√-scaled); a word also counts when its English or
    Malay counterpart (TERMS) is there."""
    q = set(words(query))
    if not q:
        return 0.0
    t = set(words(text))
    return sum(1 for w in q if w in t or not _SAME.get(w, set()).isdisjoint(t)) / math.sqrt(len(q))


def download(target: Path | None = None) -> Path:
    """Fetch the ONNX model and tokenizer into HF_HOME/voltguard (used by `fetch-models`)."""
    from huggingface_hub import hf_hub_download

    home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
    target = target or home / "voltguard" / MODEL_ID.replace("/", "--")
    for name in ("onnx/model.onnx", "tokenizer.json", "config.json"):
        hf_hub_download(MODEL_ID, name, local_dir=target)
    _onnx.cache_clear()
    return target
