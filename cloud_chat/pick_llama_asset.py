"""Chọn asset ubuntu-x64 (CPU) phù hợp từ GitHub Release mới nhất của llama.cpp.

Tách riêng thành file .py để tránh lỗi thụt lề khi nhúng script Python
nhiều dòng trực tiếp trong YAML (đây chính là nguyên nhân lỗi
"Invalid workflow file" ở dòng có `python3 -c "..."` nhiều dòng).
"""

from __future__ import annotations

import json
import re
import sys


def main() -> None:
    data = json.load(sys.stdin)
    assets = [a["browser_download_url"] for a in data["assets"]]
    pick = [
        u
        for u in assets
        if re.search(r"ubuntu-x64\.(zip|tar\.gz)$", u)
        and "sycl" not in u
        and "vulkan" not in u
    ]
    print(pick[0] if pick else "")


if __name__ == "__main__":
    main()
