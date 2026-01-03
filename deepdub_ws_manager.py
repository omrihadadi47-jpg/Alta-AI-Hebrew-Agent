import asyncio
import json
import time
from typing import Optional, Awaitable, Callable

import websockets


class DeepdubWebsocketManager:
    def __init__(self, url: str, api_key: Optional[str], idle_timeout: float = 60.0, recv_timeout: float = 15.0):
        self.url = url
        self.api_key = api_key
        self.idle_timeout = idle_timeout
        self.recv_timeout = recv_timeout
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._conn_lock = asyncio.Lock()
        self._request_lock = asyncio.Lock()
        self.last_used = 0.0

    def _is_closed(self) -> bool:
        ws = self._ws
        if ws is None:
            return True
        state = getattr(ws, "state", None)
        state_name = getattr(state, "name", None)
        if state_name:
            return state_name.upper() != "OPEN"
        close_code = getattr(ws, "close_code", None)
        if close_code is not None:
            return True
        closed_attr = getattr(ws, "closed", None)
        if isinstance(closed_attr, bool):
            return closed_attr
        return False

    def _needs_reconnect(self) -> bool:
        if self._is_closed():
            return True
        if not self.idle_timeout:
            return False
        return (time.monotonic() - self.last_used) > self.idle_timeout

    async def _close_unlocked(self) -> None:
        if self._ws and not self._is_closed():
            try:
                await self._ws.close()
            except Exception as exc:
                print(f"⚠️ Error while closing Deepdub WS: {exc}")
        self._ws = None

    async def close(self) -> None:
        async with self._conn_lock:
            await self._close_unlocked()

    async def _ensure_connection(self) -> websockets.WebSocketClientProtocol:
        async with self._conn_lock:
            if self._needs_reconnect():
                await self._close_unlocked()
                self._ws = await websockets.connect(
                    self.url,
                    additional_headers={"x-api-key": self.api_key},
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=None,
                )
                print("🔌 Deepdub WS connected (reused)")
            return self._ws  # type: ignore[return-value]

    async def _mark_broken(self) -> None:
        await self.close()

    async def run_tts(self, payload: dict, on_message: Callable[[dict], Awaitable[None]]) -> None:
        async def _execute_once() -> None:
            ws = await self._ensure_connection()
            await ws.send(json.dumps(payload))
            while True:
                raw_msg = await asyncio.wait_for(ws.recv(), timeout=self.recv_timeout)
                msgj = json.loads(raw_msg)
                await on_message(msgj)
                if msgj.get("isFinished"):
                    break

        async with self._request_lock:
            success = False
            try:
                await _execute_once()
                success = True
            except Exception as exc:
                print(f"❌ Deepdub WS error: {exc}")
                await self._mark_broken()
                try:
                    await _execute_once()
                    success = True
                except Exception as retry_exc:
                    print(f"❌ Deepdub WS retry failed: {retry_exc}")
                    await self._mark_broken()
                    raise
            finally:
                if success:
                    self.last_used = time.monotonic()
