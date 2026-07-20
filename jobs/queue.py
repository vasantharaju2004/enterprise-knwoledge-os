import os
from redis import Redis
from rq import Queue
from dotenv import load_dotenv

load_dotenv()

_redis_url = os.getenv("REDIS_URL")
if _redis_url:
    _redis_conn = Redis.from_url(_redis_url, decode_responses=True)
else:
    _redis_conn = Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))

# A single named queue for ingestion jobs. RQ workers listen on
# this exact queue name _ the worker process and this file must
# agree on the name, or jobs get enqueued into a queue nobody's
# watching

task_queue = Queue("ingestion", connection=_redis_conn)


def enqueue_job(func, *args, **kwargs):
    """
    Submits a function to run in he background worker process,
    returning immediately with a job object rather than waiting
    for the function to actually execute.
    """
    return task_queue.enqueue(func, *args, **kwargs)
