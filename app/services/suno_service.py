"""
Core Suno API operations: submit tasks, fetch results, and loop polling.
"""
import time
from loguru import logger
from typing import List

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.task import Task as TaskModel
from app.services.account import account_service
from app.utils.http_client import do_request


class SunoService:
    """
    Service for submitting and polling Suno tasks.
    """
    @staticmethod
    def submit_song(params: dict) -> str:
        # Build request
        url = f"{settings.base_url}/api/generate/v2/"
        # Ensure mv parameter
        if not params.get("mv"):
            params["mv"] = "chirp-v3-0"
        # Send request
        resp = do_request("POST", url, json=params)
        data = resp.json()
        # Check status
        if data.get("status") != "complete":
            raise RuntimeError(f"generateSong failed: {data}")
        # Prepare task entry
        task_id = data.get("id") or data.get("batch_id") or str(int(time.time() * 1000))
        songs = data.get("clips", [])

        # Persist task
        db: Session = SessionLocal()
        try:
            task = TaskModel(
                task_id=task_id,
                action="MUSIC",
                status="NOT_START",
                submit_time=int(time.time()),
                data=songs,
            )
            db.add(task)
            db.commit()
        finally:
            db.close()
        # Enqueue for background polling
        # Import here to avoid circular import at module load
        from app.services.tasks import add_task
        add_task(task_id, "MUSIC")
        return task_id

    @staticmethod
    def submit_lyrics(params: dict) -> str:
        # Submit lyrics generation
        url = f"{settings.base_url}/api/generate/lyrics/"
        resp = do_request("POST", url, json=params)
        data = resp.json()
        lyric_id = data.get("id")
        if not lyric_id:
            raise RuntimeError(f"generateLyrics failed: {data}")

        # Poll until complete or timeout
        start = time.time()
        status = None
        text = None
        while True:
            if time.time() - start > settings.chat_timeout:
                raise RuntimeError("lyrics generation timeout")
            poll_url = f"{settings.base_url}/api/generate/lyrics/{lyric_id}"
            poll_resp = do_request("GET", poll_url)
            info = poll_resp.json()
            status = info.get("status")
            text = info.get("text")
            if status == "complete" or text:
                break
            time.sleep(5)

        # Persist task
        db: Session = SessionLocal()
        try:
            task = TaskModel(
                task_id=lyric_id,
                action="LYRICS",
                status="SUCCESS",
                submit_time=int(start),
                start_time=int(start),
                finish_time=int(time.time()),
                data={"id": lyric_id, "status": status, "text": text},
            )
            db.add(task)
            db.commit()
        finally:
            db.close()
        return lyric_id

    @staticmethod
    def fetch_by_id(task_id: str) -> dict:
        db: Session = SessionLocal()
        try:
            task = db.query(TaskModel).filter_by(task_id=task_id).first()
            if not task:
                raise KeyError(f"Task {task_id} not found")
            # Return a clean dictionary instead of __dict__
            return {
                "id": task.id,
                "task_id": task.task_id,
                "action": task.action,
                "status": task.status,
                "fail_reason": task.fail_reason,
                "submit_time": task.submit_time,
                "start_time": task.start_time,
                "finish_time": task.finish_time,
                "search_item": task.search_item,
                "data": task.data,
            }
        finally:
            db.close()

    @staticmethod
    def fetch_tasks(ids: List[str], action: str) -> List[dict]:
        db: Session = SessionLocal()
        try:
            q = db.query(TaskModel).filter(TaskModel.task_id.in_(ids))
            if action:
                q = q.filter_by(action=action)
            tasks = q.all()
            # Return clean dictionaries
            return [
                {
                    "id": t.id,
                    "task_id": t.task_id,
                    "action": t.action,
                    "status": t.status,
                    "fail_reason": t.fail_reason,
                    "submit_time": t.submit_time,
                    "start_time": t.start_time,
                    "finish_time": t.finish_time,
                    "search_item": t.search_item,
                    "data": t.data,
                }
                for t in tasks
            ]
        finally:
            db.close()

    @staticmethod
    def get_account_info() -> dict:
        return account_service.get_account_info()
    
    def loop_fetch_song(self, task_id: str) -> None:
        """
        Poll the task record by querying Suno API until it reaches a terminal state.
        """
        db = SessionLocal()
        # start time for polling timeout
        start_poll = time.time()
        while True:
            try:
                # timeout to avoid infinite polling
                if time.time() - start_poll > settings.poll_timeout:
                    logger.error(f"Polling timeout for song task {task_id}")
                    # mark task as failure due to timeout
                    task = db.query(TaskModel).filter_by(task_id=task_id).first()
                    if task:
                        task.status = "FAILURE"
                        task.fail_reason = "Polling timeout"
                        task.finish_time = int(time.time())
                        db.commit()
                    break
                # Get task from database
                task = db.query(TaskModel).filter_by(task_id=task_id).first()
                if not task:
                    logger.warning(f"Task {task_id} not found in database")
                    break

                # Poll Suno API for updates
                url = f"{settings.base_url}/api/clips/{task_id}"
                try:
                    resp = do_request("GET", url)
                    data = resp.json()
                    clips = data.get("clips", [])

                    # Update task status based on API response
                    if clips and all(clip.get("status") == "complete" for clip in clips):
                        task.status = "SUCCESS"
                        task.data = clips
                        task.finish_time = int(time.time())
                        db.commit()
                        break
                    elif any(clip.get("status") == "error" for clip in clips):
                        task.status = "FAILURE"
                        task.fail_reason = "Suno API reported error"
                        task.data = clips
                        db.commit()
                        break
                    elif not task.start_time and any(clip.get("status") != "waiting" for clip in clips):
                        # First time seeing activity
                        task.status = "PROCESSING"
                        task.start_time = int(time.time())
                        db.commit()

                    # Update data even while in progress
                    task.data = clips
                    db.commit()
                except Exception as e:
                    logger.error(f"Error polling task {task_id}: {e}")
                    # Continue polling

                # Check terminal status
                if task.status in ("SUCCESS", "FAILURE", "UNKNOWN"):
                    break

                # Wait before next poll
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in loop_fetch_song for {task_id}: {e}")
                time.sleep(5)
        db.close()

    def loop_fetch_lyrics(self, task_id: str) -> None:
        """
        Poll the lyrics task record by querying Suno API until it reaches a terminal state.
        """
        db = SessionLocal()
        # start time for polling timeout
        start_poll = time.time()
        while True:
            try:
                # timeout to avoid infinite polling
                if time.time() - start_poll > settings.poll_timeout:
                    logger.error(f"Polling timeout for lyrics task {task_id}")
                    # mark task as failure due to timeout
                    task = db.query(TaskModel).filter_by(task_id=task_id).first()
                    if task:
                        task.status = "FAILURE"
                        task.fail_reason = "Polling timeout"
                        task.finish_time = int(time.time())
                        db.commit()
                    break
                # Get task from database
                task = db.query(TaskModel).filter_by(task_id=task_id).first()
                if not task:
                    logger.warning(f"Lyrics task {task_id} not found in database")
                    break

                # Poll Suno API for updates
                url = f"{settings.base_url}/api/generate/lyrics/{task_id}"
                try:
                    resp = do_request("GET", url)
                    data = resp.json()
                    status = data.get("status")
                    text = data.get("text")

                    # Update task status based on API response
                    if status == "complete" or text:
                        task.status = "SUCCESS"
                        task.data = data
                        task.finish_time = int(time.time())
                        db.commit()
                        break
                    elif status == "error":
                        task.status = "FAILURE"
                        task.fail_reason = data.get("fail_reason") or "Suno API reported error"
                        task.data = data
                        db.commit()
                        break
                    elif not task.start_time and status != "waiting":
                        # First time seeing activity
                        task.status = "PROCESSING"
                        task.start_time = int(time.time())
                        db.commit()

                    # Update data even while in progress
                    task.data = data
                    db.commit()
                except Exception as e:
                    logger.error(f"Error polling lyrics task {task_id}: {e}")
                    # Continue polling

                # Check terminal status
                if task.status in ("SUCCESS", "FAILURE", "UNKNOWN"):
                    break

                # Wait before next poll
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in loop_fetch_lyrics for {task_id}: {e}")
                time.sleep(5)
        db.close()


# Singleton instance
suno_service = SunoService()