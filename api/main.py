import os
from dotenv import load_dotenv
from fastapi import FastAPI
import psycopg2
import redis
from qdrant_client import QdrantClient

load_dotenv()

app = FastAPI()


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
