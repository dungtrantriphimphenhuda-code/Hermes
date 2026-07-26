"""Ghi docs/status.json từ biến môi trường TUNNEL_URL, CHAT_PW, UPDATED_AT.

Tách riêng thành file .py (thay vì nhúng script Python nhiều dòng trong YAML)
vì đó chính là nguyên nhân gây lỗi "Invalid workflow file" trước đây.
"""

from __future__ import annotations

import json
import os

data = {
    "url": os.environ["TUNNEL_URL"],
    "password": os.environ["CHAT_PW"],
    "updated_at": os.environ["UPDATED_AT"],
    "note": "Link doi moi ~6h/lan. Luon xem trang nay de lay link + mat khau moi nhat.",
}

with open("docs/status.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
