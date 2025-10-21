from __future__ import annotations

import io
from typing import Dict, List, Optional

import requests

from .config import settings


class TelegramClient:
    """Thin wrapper around Telegram Bot API used by this app."""

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or settings.bot_token
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.file_base = f"https://api.telegram.org/file/bot{self.token}"
        self._file_path_cache: Dict[str, str] = {}

    def get_updates(self, offset: Optional[int] = None, limit: int = 100) -> dict:
        params = {"limit": limit}
        if offset is not None:
            params["offset"] = offset
        resp = requests.get(f"{self.base_url}/getUpdates", params=params, timeout=20)
        if resp.status_code == 409:
            # Webhook set; return empty to avoid confusing the UI
            return {"ok": True, "result": []}
        resp.raise_for_status()
        return resp.json()

    def extract_gif_animations(self, updates: dict) -> List[dict]:
        animations: List[dict] = []
        for upd in updates.get("result", []):
            msg = upd.get("message") or upd.get("edited_message")
            if not msg:
                continue
            anim = msg.get("animation")
            if anim:
                # Keep only essentials used by frontend
                animations.append(
                    {
                        "file_id": anim.get("file_id"),
                        "file_unique_id": anim.get("file_unique_id"),
                        "width": anim.get("width"),
                        "height": anim.get("height"),
                        "duration": anim.get("duration"),
                        "file_size": anim.get("file_size"),
                    }
                )
        # Dedupe by file_unique_id while preserving order
        seen = set()
        deduped: List[dict] = []
        for a in animations:
            uid = a.get("file_unique_id")
            if uid in seen:
                continue
            seen.add(uid)
            deduped.append(a)
        return deduped

    def get_file_path(self, file_id: str) -> str:
        if file_id in self._file_path_cache:
            return self._file_path_cache[file_id]
        resp = requests.get(f"{self.base_url}/getFile", params={"file_id": file_id}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError("Telegram getFile failed")
        file_path = data["result"]["file_path"]
        self._file_path_cache[file_id] = file_path
        return file_path

    def download_file_stream(self, file_id: str):
        file_path = self.get_file_path(file_id)
        url = f"{self.file_base}/{file_path}"
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        return resp

    def send_animation(
        self,
        chat_id: str,
        animation: str,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
    ) -> dict:
        payload = {"chat_id": chat_id, "animation": animation}
        if caption:
            payload["caption"] = caption
        if parse_mode:
            payload["parse_mode"] = parse_mode
        resp = requests.post(f"{self.base_url}/sendAnimation", data=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()


telegram_client = TelegramClient()
