"""
Router for chat completions using Suno and OpenAI tools with SSE streaming support.
"""
import json
import time
import asyncio
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

# Support both v0 and v1 OpenAI SDK
try:
    from openai import OpenAI
    USE_V1_SDK = True
except (ImportError, AttributeError):
    import openai
    USE_V1_SDK = False
from app.schemas.chat import GeneralOpenAIRequest
from app.config import settings
from app.utils.templates import templates
from app.services.suno_service import suno_service

router = APIRouter()

# Define OpenAI function spec for Suno tool
FUNCTIONS = [
    {
        "name": "generate_song_custom",
        "description": "You are Suno AI, a songwriting assistant.",
        "parameters": {
            "type": "object",
            "properties": {
                "make_instrumental": {
                    "type": "boolean",
                    "description": (
                        "Specifies whether to generate instrumental music tracks. "
                        "Default false, set to true only if explicitly requested."
                    ),
                },
                "prompt": {"type": "string", "description": "Text prompt describing the song."},
                "title": {"type": "string", "description": "Name of the song."},
                "tags": {"type": "string", "description": "Comma-separated style tags."},
                "continue_at": {"type": "number", "description": "Time in seconds to continue writing."},
                "continue_clip_id": {"type": "string", "description": "ID of clip to continue."},
            },
            "required": ["tags", "prompt"],
        },
    }
]

@router.post("/completions")
async def chat_completions(request: Request):
    body = await request.json()
    try:
        req = GeneralOpenAIRequest.parse_obj(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Determine streaming
    is_stream = req.stream or False
    model = req.model or settings.chat_openai_model

    # Configure OpenAI client
    if USE_V1_SDK:
        client = OpenAI(api_key=settings.chat_openai_key, base_url=settings.chat_openai_base.rstrip('/'))
    else:
        openai.api_key = settings.chat_openai_key
        openai.api_base = settings.chat_openai_base.rstrip('/')

    # Unique chat ID
    chat_id = f"chatcmpl-{request.state.request_id}"

    async def event_generator():
        # Initial tool call via OpenAI
        try:
            if USE_V1_SDK:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[msg.dict() for msg in req.messages],
                    functions=FUNCTIONS,
                    function_call="auto",
                    stream=False,
                )
            else:
                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=[msg.dict() for msg in req.messages],
                    functions=FUNCTIONS,
                    function_call="required",
                    stream=False,
                )
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        choice = resp.choices[0]
        if not hasattr(choice.message, 'function_call'):
            yield f"data: {json.dumps({'error': 'No function call from OpenAI'})}\n\n"
            return

        func_call = choice.message.function_call
        try:
            params = json.loads(func_call.arguments)
        except Exception as e:
            yield f"data: {json.dumps({'error': 'Invalid function arguments'})}\n\n"
            return

        # Add model param for Suno
        params['mv'] = model

        # Submit Suno task
        try:
            task_id = suno_service.submit_song(params)
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        # Initial notification
        submit_tmpl = templates.get('chat_stream_submit')
        if submit_tmpl:
            msg = submit_tmpl.render()
            yield f"data: {msg}\n\n"

        # Polling loop
        first_tick = False
        start_time = time.time()
        while True:
            # Timeout
            if time.time() - start_time > settings.chat_timeout:
                yield f"data: timeout\n\n"
                break

            # Tick
            if not first_tick:
                tick_tmpl = templates.get('chat_stream_tick')
                if tick_tmpl:
                    yield f"data: {tick_tmpl.render()}\n\n"
            first_tick = True

            # Fetch task status
            try:
                task = suno_service.fetch_by_id(task_id)
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break

            status = task.get('status')
            data = task.get('data') or []
            # Continue until done
            if status not in ('SUCCESS', 'FAILURE', 'UNKNOWN'):
                await asyncio.sleep(5)
                continue

            # Final render
            resp_tmpl = templates.get('chat_resp')
            if resp_tmpl:
                msg = resp_tmpl.render(Data=data)
                yield f"data: {msg}\n\n"
            # Done
            yield "data: [DONE]\n\n"
            break

    if is_stream:
        return EventSourceResponse(event_generator(), ping=5)
    else:
        # Collect all data chunks and return as JSON
        full_msg = []
        async for event in event_generator():
            # each event is string like 'data: ...'
            if event.startswith('data: '):
                content = event[len('data: '):].strip()
                if content == '[DONE]':
                    break
                full_msg.append(content)
        # Return as final chat completion response
        # For simplicity, return aggregated string
        return JSONResponse({
            'id': chat_id,
            'object': 'chat.completion',
            'created': int(time.time()),
            'model': model,
            'choices': [
                {'index': 0, 'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': ''.join(full_msg)}}
            ]
        })