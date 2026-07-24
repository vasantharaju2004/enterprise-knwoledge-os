from knowledge.extraction.pdf_extractor import extract_pdf
from knowledge.extraction.docx_extractor import extract_docx
from knowledge.extraction.img_extractor import extract_image
from knowledge.extraction.audio_extractor import extract_audio


from knowledge.chunking.recursive_chunker import chunk_recursive

from knowledge.embeddings.embedder_factory import get_embedder

from storage.vector_store.qdrant_store import upsert_chunks
import os

EXTRACTORS = {
    "pdf": extract_pdf,
    "docx": extract_docx,
    "image": extract_image,
    "audio": extract_audio,
}


def ingest_document(
    file_path: str,
    source_type: str,
    document_id: str,
    user_id: str,
    org_id: str,
) -> dict:
    """
    Runs the full journey from a saved file to searchable,
    embedded knwoledge: extract text, chunk it, embed each
    chunk, store the vectors into Qdrant.

    This function deliberately contains no extraction, chunking,
    or embedding logic itself - it only calls the functions that
    already live in their own tested modules, in order. that's
    what makes it a conductor rather than a doer, mathing the
    architecture doc's design for this  exact file.
    """
    # extracting text
    if source_type not in EXTRACTORS:
        raise ValueError(f"Unsupported source: {source_type}")

    extractor = EXTRACTORS[source_type]
    pages = extractor(file_path)

    full_text = "\n\n".join(p["text"] for p in pages)

    chunks = chunk_recursive(full_text, chunk_size=512, overlap=64)
    embed_texts = get_embedder()
    vectors = embed_texts(chunks, input_type="search_document")

    upsert_chunks(
        document_id=document_id,
        chunks=chunks,
        vectors=vectors,
        user_id=user_id,
        org_id=org_id,
    )
    return {
        "document_id": document_id,
        "chunk_count": len(chunks),
        "pages_processed": len(pages),
    }
