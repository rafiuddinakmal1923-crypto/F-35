"""Notes scrubber (SDD 8.4, NFR-15): inspector notes -> notes_redacted before any agent, search or model.

Presidio's name detection is built for English and misses Malaysian names, so custom
recognisers always run:
* IC numbers with or without dashes, Malaysian phone numbers, e-mail addresses
* names after honorifics (Encik, En., Puan, Pn., Cik, Tuan, Haji, Hajah, Datuk, Dato', Datin,
  Tan Sri, Puan Sri, Dr.) and names around bin, binti, bte, a/l, a/p
* addresses: No., Lot, Jalan/Jln, Lorong/Lrg, Taman/Tmn, Kampung/Kg, Persiaran, Bandar and
  5-digit postcodes
* the case's own holder name and address from the restricted table (`known`), word by word
When Presidio and its spaCy model are installed, its PERSON/LOCATION/EMAIL/PHONE results are
added on top. The output never contains the removed values, only typed placeholders.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

HONORIFICS = r"(?:Encik|En\.|Puan Sri|Puan|Pn\.|Cik|Tuan|Haji|Hajah|Hj\.|Hjh\.|Datuk Seri|Datuk|Dato'|Dato|Datin|Tan Sri|Dr\.|Mr\.|Mrs\.|Ms\.|Mdm\.?|Madam)"
NAME_WORD = r"[A-Z][a-zA-Z'\-]+"
CONNECTOR = r"(?:bin|binti|bte|bt\.|a/l|a/p|s/o|d/o)"
ADDRESS_WORDS = r"(?:Jalan|Jln\.?|Lorong|Lrg\.?|Taman|Tmn\.?|Kampung|Kampong|Kg\.?|Persiaran|Bandar|Lebuh|Lebuhraya|Pangsapuri|Apartment|Blok|Block)"

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("IC", re.compile(r"\b\d{6}[-\s]?\d{2}[-\s]?\d{4}\b")),
    ("PHONE", re.compile(r"(?:\+?6?0)1\d[-\s]?\d{3,4}[-\s]?\d{4}\b|\+60\s?\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}\b|\b0\d[-\s]?\d{3,4}[-\s]?\d{4}\b")),
    # "Encik Ahmad bin Ali", "Pn. Siti Aishah", "Dato' Seri Lim"
    ("NAME", re.compile(rf"\b{HONORIFICS}\s+{NAME_WORD}(?:\s+(?:{CONNECTOR}\s+)?{NAME_WORD}){{0,4}}")),
    # "Kumar a/l Muthu", "Siti binti Rahman", "Ahmad bin Haji Ali"
    ("NAME", re.compile(rf"\b{NAME_WORD}(?:\s+{NAME_WORD}){{0,2}}\s+{CONNECTOR}\s+(?:Haji\s+|Hj\.\s+)?{NAME_WORD}(?:\s+{NAME_WORD}){{0,2}}")),
    # "No. 12, Jalan Mawar 3, Taman Seri Indah, 47000 Sungai Buloh"
    ("ADDRESS", re.compile(rf"\b(?:No\.?|Lot|Unit)\s*[A-Z]?-?\d+[A-Za-z]?(?:-\d+)?(?:,?\s*(?:{ADDRESS_WORDS}\s+[\w'.]+(?:\s+[A-Z0-9][\w'.]*){{0,3}}))*"
                           r"(?:,\s*\d{5}(?:\s+[A-Z][a-z]+){0,3})?")),
    ("ADDRESS", re.compile(rf"\b{ADDRESS_WORDS}\s+[A-Z0-9][\w'.]*(?:\s+[A-Z0-9][\w'.]*){{0,3}}")),
    ("ADDRESS", re.compile(r"\b\d{5}(?=\s+[A-Z][a-z])|(?<=,\s)\d{5}\b")),
]
PLACEHOLDER = {"NAME": "[NAME]", "IC": "[IC]", "PHONE": "[PHONE]", "ADDRESS": "[ADDRESS]", "EMAIL": "[EMAIL]",
               "PERSON": "[NAME]", "LOCATION": "[ADDRESS]", "EMAIL_ADDRESS": "[EMAIL]", "PHONE_NUMBER": "[PHONE]"}
STOP_WORDS = {"no", "lot", "jalan", "jln", "taman", "tmn", "the", "and", "fake", "bin", "binti", "a/l", "a/p", "kampung", "kg",
              "lorong", "persiaran", "bandar", "selangor", "pulau", "pinang"}


@dataclass
class ScrubResult:
    text: str
    found: dict[str, int] = field(default_factory=dict)   # type -> count; never the values themselves

    @property
    def changed(self) -> bool:
        return bool(self.found)


_presidio = None
_presidio_tried = False


def _presidio_analyzer():
    """Presidio with its spaCy model, if installed (optional; regexes always run)."""
    global _presidio, _presidio_tried
    if _presidio_tried:
        return _presidio
    _presidio_tried = True
    if os.environ.get("PRESIDIO", "auto") == "off":
        return None
    try:
        from presidio_analyzer import AnalyzerEngine

        _presidio = AnalyzerEngine()
    except Exception:
        _presidio = None
    return _presidio


def _known_patterns(known: list[str]) -> list[re.Pattern]:
    words = set()
    for value in known:
        for word in re.findall(r"[A-Za-z][A-Za-z'\-]{2,}", value or ""):
            if word.lower() not in STOP_WORDS:
                words.add(word)
    return [re.compile(rf"\b{re.escape(w)}\b", re.IGNORECASE) for w in sorted(words, key=len, reverse=True)]


def scrub(text: str | None, known: list[str] | None = None) -> ScrubResult:
    if not text:
        return ScrubResult(text or "")
    spans: list[tuple[int, int, str]] = []
    for kind, pattern in PATTERNS:
        spans += [(m.start(), m.end(), kind) for m in pattern.finditer(text)]
    for pattern in _known_patterns(known or []):
        spans += [(m.start(), m.end(), "NAME") for m in pattern.finditer(text)]
    analyzer = _presidio_analyzer()
    if analyzer is not None:
        for r in analyzer.analyze(text=text, language="en", entities=["PERSON", "LOCATION", "EMAIL_ADDRESS", "PHONE_NUMBER"]):
            if r.score >= 0.6:
                spans.append((r.start, r.end, r.entity_type))
    if not spans:
        return ScrubResult(text)
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    merged: list[list] = []
    for start, end, kind in spans:
        if merged and start <= merged[-1][1]:
            if end > merged[-1][1]:
                merged[-1][1] = end
            continue
        merged.append([start, end, kind])
    out, last, found = [], 0, {}
    for start, end, kind in merged:
        out.append(text[last:start])
        out.append(PLACEHOLDER.get(kind, "[REDACTED]"))
        label = PLACEHOLDER.get(kind, "[REDACTED]").strip("[]")
        found[label] = found.get(label, 0) + 1
        last = end
    out.append(text[last:])
    return ScrubResult(re.sub(r"(\[(?:NAME|ADDRESS)\])(\s*,?\s*\1)+", r"\1", "".join(out)), found)
