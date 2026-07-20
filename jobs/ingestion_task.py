from knowledge.ingestion.pipeline import ingest_document
from storage.relational_store.document_repository import update_document_status


def run_ingestion_job(
    file_path: str, source_type: str, document_id: str, user_id: str, org_id: str
) -> dict:
    """
    The background version of ingestion - runs in the RQ worker
    process , not inside the API request. Updates the SAME status
    colummn the frontend already polls via GET /documents, so no
    new tracking mechanism is needed: ' processing ' while running,
    'embedded' sucess, 'failed' if something breaks.
    """
    try:
        update_document_status(document_id, status="processing")
        result = ingest_document(
            file_path=file_path,
            source_type=source_type,
            document_id=document_id,
            user_id=user_id,
            org_id=org_id,
        )
        update_document_status(
            document_id, status="embedded", page_count=result["pages_processed"]
        )

        return result
    except Exception as e:
        # A failed job should be visible not silently vanish -
        # the document's status becomes a permanent, honest record
        # that something went wrong, rather than staying stuck at
        # 'uploaded forever with no explaination.
        update_document_status(document_id, status="failed")
        raise
