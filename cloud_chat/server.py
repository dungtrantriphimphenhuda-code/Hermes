"""
cloud_chat.server
==================

Một web chatbot cực nhẹ, đứng trước AIAgent thật của Hermes (đầy đủ tool-calling,
memory, v.v.) nhưng dùng model local (llama-server chạy Gemma 4 lượng tử hoá)
làm "não" thay vì gọi API trả phí.

Thiết kế cố tình đơn giản (1 file, không phụ thuộc web/ SPA đồ sộ của Hermes)
để chạy ổn định, không cần build npm, không đụng tới lớp auth/Host-header
hardening của `hermes dashboard` (lớp đó được thiết kế cho local-only + OAuth,
không hợp với việc expose qua Cloudflare Tunnel trong CI).

Bảo vệ bằng 1 mật khẩu đơn giản (biến môi trường CHAT_PASSWORD, CI sẽ tự sinh
ngẫu nhiên mỗi lần chạy và in ra trong job summary / docs/status.json).
"""

from __future__ import annotations

import os
import secrets
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Cho phép chạy trực tiếp `python cloud_chat/server.py` từ thư mục gốc repo.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from run_agent import AIAgent  # noqa: E402  (import sau khi chỉnh sys.path)

APP_PASSWORD = os.environ.get("CHAT_PASSWORD") or secrets.token_urlsafe(9)
LLAMA_BASE_URL = os.environ.get("LLAMA_BASE_URL", "http://127.0.0.1:8080/v1")
LLAMA_MODEL = os.environ.get("LLAMA_MODEL_NAME", "gemma-4")

app = FastAPI(title="Hermes Cloud Chatbot")

# Mỗi phiên trình duyệt (nhận diện qua cookie đơn giản) giữ lịch sử hội thoại
# riêng, trong bộ nhớ (mất khi job restart -- chấp nhận được cho một chatbot demo).
_sessions: dict[str, list[dict[str, Any]]] = {}


def _build_agent() -> AIAgent:
    return AIAgent(
        base_url=LLAMA_BASE_URL,
        api_key="not-needed",
        provider="custom",
        model=LLAMA_MODEL,
        max_iterations=40,
        skip_memory=True,        # mỗi job GH Actions là một máy mới toanh
        save_trajectories=False,
        quiet_mode=True,
    )


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    elapsed_seconds: float


def _check_password(x_chat_password: str | None) -> None:
    if not secrets.compare_digest(x_chat_password or "", APP_PASSWORD):
        raise HTTPException(status_code=401, detail="Sai mật khẩu")


@app.get("/api/health")
def health() -> JSONResponse:
    return JSONResponse({"ok": True})


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, x_chat_password: str | None = Header(default=None)):
    _check_password(x_chat_password)
    history = _sessions.setdefault(req.session_id, [])

    agent = _build_agent()
    start = time.time()
    result = agent.run_conversation(req.message, conversation_history=history)
    elapsed = time.time() - start

    reply = result.get("final_response") or "(không có phản hồi)"
    history.extend(
        [
            {"role": "user", "content": req.message},
            {"role": "assistant", "content": reply},
        ]
    )
    # Giữ lịch sử gọn để không phình ngữ cảnh vô hạn trong 1 job dài.
    _sessions[req.session_id] = history[-40:]

    return ChatResponse(reply=reply, elapsed_seconds=round(elapsed, 2))


_PAGE = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Hermes Cloud Chatbot</title>
<style>
  :root { color-scheme: dark; }
  body { margin:0; font-family: system-ui, sans-serif; background:#0b0d12; color:#e8e8ec; }
  #wrap { max-width: 760px; margin: 0 auto; padding: 16px; height:100dvh; box-sizing:border-box; display:flex; flex-direction:column; }
  h1 { font-size: 16px; opacity:.7; font-weight:600; margin: 4px 0 12px; }
  #log { flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:10px; padding-bottom: 8px;}
  .msg { padding:10px 14px; border-radius:12px; max-width: 85%; white-space:pre-wrap; line-height:1.45; }
  .user { align-self:flex-end; background:#2a5adf; }
  .bot { align-self:flex-start; background:#1b1e27; border:1px solid #2a2e3a; }
  .sys { align-self:center; font-size:12px; opacity:.6; }
  #bar { display:flex; gap:8px; padding-top:10px; border-top:1px solid #22252e; }
  #box { flex:1; padding:12px; border-radius:10px; border:1px solid #2a2e3a; background:#12141b; color:#eee; font-size:15px; }
  button { padding:12px 18px; border-radius:10px; border:none; background:#2a5adf; color:#fff; font-weight:600; cursor:pointer; }
  button:disabled { opacity:.5; }
  #pw { display:flex; gap:8px; margin-bottom:10px;}
  #pw input { flex:1; padding:10px; border-radius:8px; border:1px solid #2a2e3a; background:#12141b; color:#eee; }
</style>
</head>
<body>
<div id="wrap">
  <h1>🤖 Hermes Agent — chạy trên GitHub Actions, model local (Gemma 4)</h1>
  <div id="pw">
    <input id="pwInput" type="password" placeholder="Mật khẩu (xem docs/status.json hoặc job summary)" />
    <button onclick="savePw()">Vào</button>
  </div>
  <div id="log"></div>
  <div id="bar">
    <input id="box" placeholder="Nhập tin nhắn..." onkeydown="if(event.key==='Enter')send()" />
    <button id="sendBtn" onclick="send()">Gửi</button>
  </div>
</div>
<script>
let pw = localStorage.getItem('chat_pw') || '';
document.getElementById('pwInput').value = pw;
function savePw(){ pw = document.getElementById('pwInput').value; localStorage.setItem('chat_pw', pw); addSys('Đã lưu mật khẩu.'); }
function addMsg(role, text){
  const d = document.createElement('div');
  d.className = 'msg ' + role;
  d.textContent = text;
  document.getElementById('log').appendChild(d);
  d.scrollIntoView({behavior:'smooth'});
}
function addSys(text){ addMsg('sys', text); }
async function send(){
  const box = document.getElementById('box');
  const text = box.value.trim();
  if(!text) return;
  box.value = '';
  addMsg('user', text);
  document.getElementById('sendBtn').disabled = true;
  addSys('Đang suy nghĩ...');
  try {
    const res = await fetch('/api/chat', {
      method:'POST',
      headers: {'Content-Type':'application/json', 'X-Chat-Password': pw},
      body: JSON.stringify({message:text, session_id: 'web'})
    });
    document.getElementById('log').lastChild.remove();
    if(res.status === 401){ addSys('Sai mật khẩu — kiểm tra lại.'); }
    else {
      const data = await res.json();
      addMsg('bot', data.reply);
    }
  } catch(e){
    document.getElementById('log').lastChild.remove();
    addSys('Lỗi kết nối: ' + e);
  }
  document.getElementById('sendBtn').disabled = false;
}
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _PAGE


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("CHAT_PORT", "8000")))
