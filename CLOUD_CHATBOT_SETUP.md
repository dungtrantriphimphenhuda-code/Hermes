# Hermes Cloud Chatbot — chạy trên GitHub Actions, model local (Gemma 4)

## Đã thêm vào repo
- `cloud_chat/server.py` — web chatbot nhẹ (FastAPI), gọi thẳng `AIAgent` thật
  của Hermes (tool-calling đầy đủ), trỏ vào một `llama-server` local.
- `.github/workflows/cloud-chatbot.yml` — workflow tự:
  1. Tải **llama-server** bản dựng sẵn (CPU, không cần compile).
  2. Tải **Gemma 4 E4B (QAT, GGUF, quant `UD-Q4_K_XL`)** từ
     `unsloth/gemma-4-E4B-it-qat-GGUF` — repo **public, không cần HF token**,
     bản QAT giữ chất lượng gần bf16 dù đã lượng tử hoá sâu, đủ mạnh và vẫn
     nhẹ (~7GB RAM của runner free là đủ chạy).
  3. Chạy Hermes agent trỏ vào model đó (không cần bất kỳ API key trả phí nào).
  4. Mở **Cloudflare Quick Tunnel** (miễn phí, không cần tài khoản) để có link
     `https://xxxx.trycloudflare.com` truy cập từ bất kỳ đâu.
  5. Ghi link + mật khẩu vào `docs/status.json`, hiển thị qua GitHub Pages.
  6. Tự lặp lại mỗi 6 giờ (giới hạn cứng của GitHub-hosted runner).
- `docs/index.html` — trang trạng thái (GitHub Pages) luôn hiện link + mật khẩu
  mới nhất, vì link tunnel đổi mỗi lần restart.

## Việc bạn cần làm (1 lần)
1. Push nhánh này lên GitHub (repo có thể public hoặc private; public thì
   Actions chạy **miễn phí không giới hạn thời gian**, private thì tính vào
   2.000 phút/tháng miễn phí — với lịch 6h/lần gần như chắc chắn vượt quota
   private, nên khuyến nghị dùng **repo public**).
2. Vào **Settings → Pages** → Source: chọn "Deploy from a branch" → Branch:
   `main`, folder: `/docs`. Sau ~1 phút bạn sẽ có địa chỉ dạng
   `https://<user>.github.io/<repo>/`.
3. Vào tab **Actions** → chọn workflow **"Hermes Cloud Chatbot"** → **Run workflow**
   (chạy lần đầu bằng tay; sau đó tự động lặp lại mỗi 6 giờ).
4. Đợi ~3–5 phút (tải model lần đầu), rồi mở trang GitHub Pages ở bước 2 —
   trang đó sẽ hiện link chat + mật khẩu.

## Không cần token nào cả
- Model Gemma 4 (unsloth repack): repo public trên Hugging Face, không cần
  `HF_TOKEN`.
- llama-server: tải trực tiếp từ GitHub Releases công khai.
- Cloudflare Tunnel: dùng "quick tunnel" ẩn danh, không cần tài khoản/token.
- Duy nhất thứ được dùng là `GITHUB_TOKEN` — cái này GitHub tự cấp cho mỗi
  job, bạn không phải tạo hay nhập gì cả.

## Giới hạn thành thật cần biết
- GitHub-hosted runner có **trần cứng 6 giờ/job**. Đây không phải giới hạn
  Hermes hay llama.cpp mà là giới hạn nền tảng của GitHub — không thể có một
  tiến trình "chạy mãi mãi" trên GH Actions miễn phí. Workflow tự khởi động
  lại sau mỗi chu kỳ, có vài giây gián đoạn khi chuyển giao, và **link tunnel
  đổi mỗi lần restart** (đó là lý do có trang trạng thái `docs/index.html`).
- Nếu bạn cần **link cố định vĩnh viễn** (không muốn người dùng phải vào lại
  trang trạng thái), cần thêm 1 domain riêng + Cloudflare *named tunnel* — đã
  ghi chú chi tiết ở cuối file workflow.
- Đây vẫn là CPU inference (runner free không có GPU) — Gemma 4 E4B lượng tử
  hoá chạy được nhưng tốc độ sinh chữ sẽ chậm hơn so với có GPU thật.
