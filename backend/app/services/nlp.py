"""Lazily-loaded, process-wide NLP model singletons.

Loading spaCy / Sentence-Transformers is expensive (hundreds of ms to
seconds), so we load each model once on first use and reuse it for the
lifetime of the worker process.
"""
from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache
def get_spacy_model():
    import spacy

    try:
        return spacy.load(settings.SPACY_MODEL)
    except OSError:
        logger.warning(
            "spaCy model '%s' not found locally; downloading it now. "
            "For production, run `python -m spacy download %s` at build time instead.",
            settings.SPACY_MODEL,
            settings.SPACY_MODEL,
        )
        from spacy.cli import download

        download(settings.SPACY_MODEL)
        import spacy

        return spacy.load(settings.SPACY_MODEL)


@lru_cache
def get_sentence_transformer():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
