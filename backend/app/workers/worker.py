"""
Background worker daemon.
Polls the jobs table and runs tasks asynchronously.
"""
import asyncio
import traceback
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.workers.queue import claim_job, complete_job, fail_job
from app.workers.tasks import run_task

_stop_event = asyncio.Event()


async def worker_loop():
    """Main worker loop."""
    print("Background worker started.")
    while not _stop_event.is_set():
        db: Session = SessionLocal()
        try:
            job = claim_job(db)
            if job:
                print(f"Starting job {job.id} ({job.type})...")
                try:
                    run_task(db, job)
                    complete_job(db, job)
                    print(f"Completed job {job.id}.")
                except Exception as e:
                    print(f"Job {job.id} failed: {e}")
                    traceback.print_exc()
                    fail_job(db, job, str(e))
            else:
                # No jobs, sleep
                await asyncio.sleep(2)
        except Exception as e:
            print(f"Worker loop error: {e}")
            await asyncio.sleep(5)
        finally:
            db.close()


def start_worker():
    """Start the worker loop in an asyncio task."""
    _stop_event.clear()
    asyncio.create_task(worker_loop())


def stop_worker():
    """Stop the worker loop."""
    _stop_event.set()
