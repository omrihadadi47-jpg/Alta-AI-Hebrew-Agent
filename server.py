from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, Response
import os
from dotenv import load_dotenv
import threading
import queue
from deepdub import DeepdubClient
import uvicorn
import subprocess
import json
import logging
import asyncio
import time
import base64
import binascii
from typing import Optional
import websockets
from pathlib import Path


from tools import get_available_slots, book_meeting

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

deepdub_api_key = os.getenv("DEEPDUB_API_KEY")
DEEPDUB_WS_URL = "wss://wsapi.deepdub.ai/open"

PORT = 8000  

app = FastAPI()

print(f"🚀 Server Starting on Port {PORT}...")

def ffmpeg_wav_or_mp3_to_pcm16k(blob: bytes) -> bytes:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-i", "pipe:0",
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", "16000",
        "pipe:1",
    ]
    p = subprocess.run(cmd, input=blob, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if p.returncode != 0 or not p.stdout:
        err = p.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"ffmpeg failed: {err[:400]}")
    return p.stdout

def looks_like_wav(b: bytes) -> bool:
    return len(b) >= 12 and b[0:4] == b"RIFF" and b[8:12] == b"WAVE"

@app.post("/to-speech")
async def to_speech(request: Request):
    t0 = time.perf_counter()
    payload = await request.json()
    msg = payload.get("message") or {}

    text = payload.get("text") or msg.get("text") or msg.get("content")
    if not text:
        return Response(status_code=200)

    q: asyncio.Queue[Optional[bytes]] = asyncio.Queue(maxsize=400)

    async def producer():
        ws_chunks = 0
        total_decoded = 0
        total_pcm = 0
        first = True

        try:
            async with websockets.connect(
                DEEPDUB_WS_URL,
                additional_headers={"x-api-key": deepdub_api_key},
                ping_interval=20,
                ping_timeout=20,
                max_size=None,
            ) as ws:
                req = {
                    "action": "text-to-speech",
                    "locale": "he-IL",
                    "voicePromptId": "cd91dbf2-7265-420b-b8fd-9b90f2555d02_prompt-reading-neutral",
                    "model": "dd-etts-3.0-preview",
                    "targetText": text,
                    "cleanAudio": True,
                    "realTime": True
                }

                print(f"\n📨 /to-speech | text_len={len(text)}")
                await ws.send(json.dumps(req))

                while True:
                    raw_msg = await ws.recv()
                    msgj = json.loads(raw_msg)

                    ws_chunks += 1
                    idx = msgj.get("index")
                    gid = msgj.get("generationId")
                    is_finished = bool(msgj.get("isFinished"))
                    b64 = msgj.get("data")

                    print(f"📦 WS chunk | gid={gid} idx={idx} finished={is_finished} has_data={bool(b64)}")

                    if b64:
                        audio_bytes = base64.b64decode(b64)
                        total_decoded += len(audio_bytes)

                        if first:
                            ttfa = (time.perf_counter() - t0) * 1000
                            print(f"⚡ TTFA={ttfa:.1f}ms | first_size={len(audio_bytes)} bytes")
                            print("🔎 ascii4:", audio_bytes[:4])
                            print("🔎 first16(hex):", binascii.hexlify(audio_bytes[:16]).decode())
                            first = False

                        if looks_like_wav(audio_bytes):
                            pcm = await asyncio.to_thread(ffmpeg_wav_or_mp3_to_pcm16k, audio_bytes)
                            total_pcm += len(pcm)
                            await q.put(pcm)
                        else:
                            print("⚠️ chunk not WAV; skipping (or handle separately)")

                    if is_finished:
                        break

            t_total = (time.perf_counter() - t0) * 1000
            print(f"🏁 WS done | chunks={ws_chunks} decoded={total_decoded} pcm={total_pcm} total_time={t_total:.1f}ms")

        except Exception as e:
            print(f"❌ producer error: {e}")
        finally:
            await q.put(None)

    asyncio.create_task(producer())

    async def stream_pcm():
        sent = 0
        while True:
            chunk = await q.get()
            if chunk is None:
                print(f"🏁 stream done | total_sent_pcm={sent}")
                break
            sent += len(chunk)
            yield chunk

    return StreamingResponse(
        stream_pcm(),
        media_type="application/octet-stream",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/check-availability")
async def check_availability_tool(request: Request):
    data = await request.json()
    print(f"\n📅 Tool Call: Check Availability | Payload: {data}") 
    
    try:
        tool_call = data['message']['toolCalls'][0]
        args = tool_call['function']['arguments']
    except (KeyError, IndexError, TypeError):
        print("❌ Error parsing tool arguments")
        return {"results": [{"result": "Error parsing input"}]}

    requested_date = args.get('date')
    slots = get_available_slots(requested_date)
    
    result_text = f"השעות הפנויות ב-{requested_date} הן: {', '.join(slots)}"
    print(f"✅ Result: {result_text}")

    return {
        "results": [
            {
                "toolCallId": tool_call['id'],
                "result": result_text
            }
        ]
    }


@app.post("/book-meeting")
async def book_meeting_tool(request: Request):
    data = await request.json()
    print(f"\n📝 Tool Call: Book Meeting | Payload: {data}")
    
    try:
        tool_call = data['message']['toolCalls'][0]
        args = tool_call['function']['arguments']
    except (KeyError, IndexError, TypeError):
        print("❌ Error parsing tool arguments")
        return {"results": [{"result": "Error parsing input"}]}

    result = book_meeting(
        date_str=args.get('date'),
        time_str=args.get('time'),
        customer_email=args.get('email'), 
        customer_name=args.get('name', "Customer") 
    )
    
    print(f"✅ Booking Result: {result}")

    return {
        "results": [
            {
                "toolCallId": tool_call['id'],
                "result": "הפגישה נקבעה בהצלחה ביומן, ושלחתי לך מייל אישור עם הפרטים."
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)