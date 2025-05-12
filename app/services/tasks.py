"""
Task queue and background worker for processing Suno tasks.
"""
import threading
import time
from loguru import logger
from queue import Queue

from app.database import SessionLocal
from app.models.task import Task as TaskModel
from app.services.suno_service import suno_service
from app.config import settings

# Queue for task processing
task_queue = Queue(maxsize=100)

def add_task(task_id: str, action: str):
    """
    Add a task to the processing queue.
    """
    task_queue.put((task_id, action))

def task_worker():
    """
    Background worker that processes tasks from the queue.
    """
    while True:
        task_id, action = task_queue.get()
        try:
            if action == "MUSIC":
                suno_service.loop_fetch_song(task_id)
            elif action == "LYRICS":
                # Lyrics tasks fetch logic can be similar to song polling
                suno_service.loop_fetch_lyrics(task_id)
            else:
                logger.warning(f"Unknown task action: {action}")
        except Exception as e:
            logger.error(f"Error processing task {task_id} ({action}): {e}")
        finally:
            task_queue.task_done()

def start_task_worker():
    """
    Start the background task worker thread.
    """
    thread = threading.Thread(target=task_worker, daemon=True)
    thread.start()