import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
import psycopg2
import redis
from qdrant_client import QdrantClient


from storage.relational_store.document_repository import (
    create_documents_table,
    create_document_record,
    update_document_status,
    get_all_documents,
)
from storage.object_store.local_store import (
    save_file,
    # delete_file
)
# from knowledge.extraction.pdf_extractor import extract_pdf
# from knowledge.extraction.docx_extractor import extract_docx
# from knowledge.extraction.img_extractor import extract_image
# from knowledge.extraction.audio_extractor import extract_audio

# pipeline
from knowledge.ingestion.pipeline import ingest_document

# query request
from reasoning.chains.rag_chain import answer_question
from pydantic import BaseModel

# CORS (cross-origin resource sharing)
from fastapi.middleware.cors import CORSMiddleware

# recent chat history
from memory.conversation_memory import get_all_history

# Authentication
from auth.passwords import hash_password, verify_password
from auth.jwt_handler import create_token, verify_token
from storage.relational_store.user_repository import (
    create_user,
    get_user_by_email,
    create_auth_tables,
)
import jwt as pyjt

# Document Authoriztion
from fastapi import Depends
from auth.dependencies import get_current_user

# feteching all databases tables
from storage.relational_store.document_repository import get_all_db_tables

# queuing the uploaded files
from jobs.queue import enqueue_job
from jobs.ingestion_task import run_ingestion_job

load_dotenv()

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    results = {}

    # Postgres
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            dbname=os.getenv("POSTGRES_DB"),
        )
        conn.close()
        results["postgres"] = "connected"
    except Exception as e:
        results["postgres"] = f"failed :{e}"

    # Redis
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=os.getenv("REDIS_PORT"),
        )
        r.ping()
        results["redis"] = "connected"
    except Exception as e:
        results["redis"] = f"failed :{e}"

    # Qdrant
    try:
        q = QdrantClient(
            host=os.getenv("QDRANT_HOST"), port=int(os.getenv("QDRANT_PORT"))
        )
        q.get_collections()
        results["qdrant"] = "connected"
    except Exception as e:
        results["qdrant"] = f"failed :{e}"

    return results


@app.on_event("startup")
def startup():
    create_documents_table()
    print("documents table created :)")


@app.post("/upload")
async def upload_documents(
    file: UploadFile = File(...), user: dict = Depends(get_current_user)
):
    """
    Accepts a file upload, saves it to disk, records it in
    Postgres and runs full ingestion pipeline(extract,
     chunks, embed, store Qdrant)
     via knowledge/ingestion/pipeline.py

    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename missing.")

    if file.filename.lower().endswith(".pdf"):
        source_type = "pdf"
    elif file.filename.lower().endswith(".docx"):
        source_type = "docx"
    elif file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        source_type = "image"
    elif file.filename.lower().endswith((".mp3", ".wav", ".mpeg")):
        source_type = "audio"
    else:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, PNG, JPG, JPEG, audio files are accepted at this stage.",
        )

    file_bytes = await file.read()
    file_path = save_file(file_bytes, file.filename)

    doc_id = create_document_record(
        file.filename,
        source_type=source_type,
        file_path=file_path,
        source_url=None,
        user_id=user["user_id"],
        org_id=user["org_id"],
    )

    # results = ingest_document(
    #     file_path=file_path,
    #     source_type=source_type,
    #     document_id=doc_id,
    #     user_id=user["user_id"],
    #     org_id=user["org_id"],
    # )

    # update_document_status(
    #     doc_id=doc_id,
    #     status="embedded",
    #     page_count=results["pages_processed"],
    #     duration_seconds=None,
    # )

    enqueue_job(
        run_ingestion_job,
        file_path,
        source_type,
        doc_id,
        user["user_id"],
        org_id=user["org_id"],
    )

    return {
        "document_id": doc_id,
        "filename": file.filename,
        "status": "processing",
    }


class QueryRequest(BaseModel):
    question: str
    document_id: str | None = None


@app.post("/query")
def query_documents(request: QueryRequest, user: dict = Depends(get_current_user)):
    """
    Accepts a question , retireves relevant chunks scoped
    to the current user/org , and returns a generated answer with sources.
    """
    return answer_question(
        question=request.question,
        user_id=user["user_id"],
        org_id=user["org_id"],
        document_id=request.document_id,
        top_k=5,
    )


@app.get("/documents")
def list_documents(user: dict = Depends(get_current_user)):
    """
    Returns all uploaded documents and their current
    pipeline status. This is what the frontend's upload
    page will call to show the document list.
    """
    return get_all_documents(user_id=user["user_id"], org_id=user["org_id"])


@app.get("/history")
def get_history(user: dict = Depends(get_current_user)):
    return get_all_history(user["user_id"], user["org_id"])


# authentication


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/register")
def register(request: RegisterRequest):
    existing = get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    hashed = hash_password(request.password)
    user = create_user(request.email, hashed)
    token = create_token(user_id=user["id"], org_id=user["org_id"])

    return {"token": token, "user_id": user["id"], "org_id": user["org_id"]}


@app.post("/login")
def login(request: LoginRequest):
    user = get_user_by_email(request.email)
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="invalid emial or password.")

    token = create_token(user_id=user["id"], org_id=user["org_id"])
    return {"token": token, "user_id": user["id"], "org_id": user["org_id"]}


@app.get("/db-schema")
def db_schema():
    return get_all_db_tables()
