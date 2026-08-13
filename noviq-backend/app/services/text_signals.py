"""Shared static primitives for heuristic AI-generated-text detection.
Split out of app.services.fraud.ai_text_detection so the whole-document
detector and the per-section detector (app.services.ai_section_detector)
can share the same buzzword list / tokenizer / sentence splitter without
duplicating them.
"""
import re

BUZZWORDS = [
    "results-driven", "detail-oriented", "team player", "proven track record", "dynamic",
    "leverage", "leveraged", "leveraging", "synergy", "spearheaded", "utilize", "utilized",
    "utilizing", "cutting-edge", "fast-paced environment", "self-starter", "go-getter",
    "highly motivated", "excellent communication skills", "passionate about", "strong ability to",
    "proficient in", "extensive experience", "wide range of", "in-depth knowledge",
    "seamlessly", "robust", "innovative solutions", "best-in-class", "value-added",
    "holistic approach", "paradigm", "streamline", "streamlined", "facilitate", "facilitated",
]

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
WORD_RE = re.compile(r"[a-zA-Z']+")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_SPLIT_RE.split(text) if len(s.strip()) > 15]
