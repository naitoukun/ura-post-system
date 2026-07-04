"""
シークレット・ビューア: 開発用の簡易バックエンド。

- GET  /                現在の視聴ページ (index.html)
- GET  /admin           動画アップロード用の管理ページ (admin.html)
- GET  /api/videos      アップロード済み動画の一覧 (JSON)
- GET  /resolve-video   指定した(または最新の)動画のメタ情報 (JSON)
- GET  /video/<id>      指定した動画の配信（Range対応 = シーク可能）
- POST /api/upload      動画アップロード（multipart/form-data, パスフレーズ必須。動画ごとに新しいIDを発行）
- POST /api/videos/delete  動画の削除（JSON, パスフレーズ必須）
- GET  /site-config     プレミアムリンク等のサイト設定 (JSON)
- POST /api/set-premium-link  プレミアムリンクの更新（JSON, パスフレーズ必須）

環境変数:
  - PORT              待ち受けポート（Renderが自動設定。ローカルでは未設定なら5173）
  - UPLOAD_PASSPHRASE 管理操作（アップロード/削除/リンク変更）用のパスフレーズ
  - UPLOAD_DIR        動画・設定ファイルの保存先（Renderでは永続ディスクのマウント先を指定）

TODO: 本番運用前に以下を必ず対応すること
  - UPLOAD_PASSPHRASE を推測されにくい値に変更する（Renderの環境変数として設定し、コードには書かない）
  - HTTPS 経由での運用（Renderは自動でHTTPS化されるため、Render以外にデプロイする場合のみ要対応）
  - アップロードファイルのウイルススキャン等、必要な安全対策の追加
"""

import json
import mimetypes
import os
import re
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Render等では永続ディスクをこのフォルダにマウントする想定。
# config.json・videos.json・動画本体をすべてこの下に置くことで、
# 再デプロイ後も削除されずに残る（BASE_DIR直下はデプロイのたびに作り直される）。
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
VIDEOS_META_PATH = os.path.join(UPLOAD_DIR, "videos.json")
CONFIG_PATH = os.path.join(UPLOAD_DIR, "config.json")

# 本番ではRenderの環境変数 UPLOAD_PASSPHRASE で上書きすること。
# ここに書かれているのはローカル動作確認用の仮の値。
UPLOAD_PASSPHRASE = os.environ.get("UPLOAD_PASSPHRASE", "change-me-please")

MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}

DEFAULT_PREMIUM_LINK = "https://fantia.jp/"

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")

os.makedirs(UPLOAD_DIR, exist_ok=True)


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"premium_link": DEFAULT_PREMIUM_LINK}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    config.setdefault("premium_link", DEFAULT_PREMIUM_LINK)
    return config


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False)


def load_videos():
    if not os.path.exists(VIDEOS_META_PATH):
        return []
    with open(VIDEOS_META_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_videos(videos):
    with open(VIDEOS_META_PATH, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False)


def find_video(video_id):
    if not video_id or not VIDEO_ID_RE.match(video_id):
        return None
    for video in load_videos():
        if video["id"] == video_id:
            return video
    return None


def video_file_path(video):
    path = os.path.join(UPLOAD_DIR, video["stored_filename"])
    return path if os.path.exists(path) else None


def parse_multipart(body: bytes, boundary: bytes):
    """multipart/form-data を最小限だけ解釈するパーサ。"""
    delimiter = b"--" + boundary
    raw_parts = body.split(delimiter)
    fields = {}
    files = {}

    for raw_part in raw_parts[1:-1]:
        if raw_part.startswith(b"\r\n"):
            raw_part = raw_part[2:]
        if raw_part.endswith(b"\r\n"):
            raw_part = raw_part[:-2]

        header_end = raw_part.find(b"\r\n\r\n")
        if header_end == -1:
            continue

        header_block = raw_part[:header_end].decode("utf-8", errors="replace")
        content = raw_part[header_end + 4:]

        name_match = re.search(r'name="([^"]+)"', header_block)
        if not name_match:
            continue
        field_name = name_match.group(1)

        filename_match = re.search(r'filename="([^"]*)"', header_block)
        if filename_match:
            files[field_name] = {
                "filename": filename_match.group(1),
                "content": content,
            }
        else:
            fields[field_name] = content.decode("utf-8", errors="replace")

    return fields, files


class Handler(BaseHTTPRequestHandler):
    server_version = "SecretViewerDev/1.0"

    def log_message(self, format, *args):
        # デフォルトのアクセスログのみ標準出力へ
        print("[server]", self.address_string(), format % args)

    # ---------- GET ----------
    def do_GET(self):
        split = urlsplit(self.path)
        path = split.path
        if path == "/" or path == "/index.html":
            self.serve_file(os.path.join(BASE_DIR, "index.html"), "text/html; charset=utf-8")
        elif path == "/admin" or path == "/admin.html":
            self.serve_file(os.path.join(BASE_DIR, "admin.html"), "text/html; charset=utf-8")
        elif path == "/api/videos":
            self.handle_list_videos()
        elif path == "/resolve-video":
            self.handle_resolve_video(parse_qs(split.query))
        elif path.startswith("/video/"):
            self.handle_serve_video(path[len("/video/"):])
        elif path == "/site-config":
            self.handle_site_config()
        else:
            self.send_error(404, "Not Found")

    def handle_site_config(self):
        config = load_config()
        payload = json.dumps({"premiumLink": config["premium_link"]}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def handle_list_videos(self):
        videos = sorted(load_videos(), key=lambda v: v["uploaded_at"], reverse=True)
        body = [
            {
                "id": v["id"],
                "originalFilename": v["original_filename"],
                "uploadedAt": v["uploaded_at"],
            }
            for v in videos
        ]
        self.respond_json(200, body)

    def handle_resolve_video(self, query):
        requested_id = (query.get("v") or [None])[0]

        if requested_id:
            video = find_video(requested_id)
            if not video or not video_file_path(video):
                self.respond_json(200, {"exists": False})
                return
        else:
            videos = sorted(load_videos(), key=lambda v: v["uploaded_at"], reverse=True)
            video = videos[0] if videos else None
            if not video or not video_file_path(video):
                self.respond_json(200, {"exists": False})
                return

        self.respond_json(200, {
            "exists": True,
            "id": video["id"],
            "originalFilename": video["original_filename"],
            "uploadedAt": video["uploaded_at"],
        })

    def handle_serve_video(self, video_id):
        video = find_video(video_id)
        path = video_file_path(video) if video else None
        if not path:
            self.send_error(404, "Video not found")
            return

        file_size = os.path.getsize(path)
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        range_header = self.headers.get("Range")

        if range_header:
            match = re.match(r"bytes=(\d*)-(\d*)", range_header)
            if not match:
                self.send_error(416, "Invalid Range")
                return
            start_str, end_str = match.groups()
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            end = min(end, file_size - 1)

            if start > end or start >= file_size:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{file_size}")
                self.end_headers()
                return

            chunk_size = end - start + 1
            self.send_response(206)
            self.send_header("Content-Type", content_type)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(chunk_size))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

            with open(path, "rb") as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    chunk = f.read(min(65536, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        else:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(file_size))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

    def serve_file(self, path, content_type):
        if not os.path.exists(path):
            self.send_error(404, "Not Found")
            return
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---------- POST ----------
    def do_POST(self):
        path = urlsplit(self.path).path
        if path == "/api/upload":
            self.handle_upload()
        elif path == "/api/videos/delete":
            self.handle_delete_video()
        elif path == "/api/set-premium-link":
            self.handle_set_premium_link()
        else:
            self.send_error(404, "Not Found")

    def handle_set_premium_link(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 10_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        if data.get("passphrase") != UPLOAD_PASSPHRASE:
            self.respond_json(401, {"ok": False, "error": "invalid_passphrase"})
            return

        url = (data.get("url") or "").strip()
        if not re.match(r"^https?://", url):
            self.respond_json(400, {"ok": False, "error": "invalid_url"})
            return

        config = load_config()
        config["premium_link"] = url
        save_config(config)

        self.respond_json(200, {"ok": True, "premiumLink": url})

    def handle_upload(self):
        content_type_header = self.headers.get("Content-Type", "")
        boundary_match = re.search(r"boundary=(.+)", content_type_header)
        content_length = int(self.headers.get("Content-Length", 0))

        if not content_type_header.startswith("multipart/form-data") or not boundary_match:
            self.respond_json(400, {"ok": False, "error": "invalid_content_type"})
            return

        if content_length <= 0 or content_length > MAX_UPLOAD_BYTES:
            self.respond_json(413, {"ok": False, "error": "file_too_large"})
            return

        boundary = boundary_match.group(1).strip('"').encode("utf-8")
        body = self.rfile.read(content_length)
        fields, files = parse_multipart(body, boundary)

        if fields.get("passphrase") != UPLOAD_PASSPHRASE:
            self.respond_json(401, {"ok": False, "error": "invalid_passphrase"})
            return

        video_file = files.get("video")
        if not video_file:
            self.respond_json(400, {"ok": False, "error": "missing_video_field"})
            return

        original_filename = video_file["filename"] or "upload"
        ext = os.path.splitext(original_filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            self.respond_json(400, {"ok": False, "error": "unsupported_file_type"})
            return

        video_id = secrets.token_urlsafe(9)
        stored_filename = video_id + ext

        with open(os.path.join(UPLOAD_DIR, stored_filename), "wb") as f:
            f.write(video_file["content"])

        videos = load_videos()
        videos.append({
            "id": video_id,
            "stored_filename": stored_filename,
            "original_filename": original_filename,
            "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        save_videos(videos)

        self.respond_json(200, {
            "ok": True,
            "id": video_id,
            "originalFilename": original_filename,
        })

    def handle_delete_video(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 10_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        if data.get("passphrase") != UPLOAD_PASSPHRASE:
            self.respond_json(401, {"ok": False, "error": "invalid_passphrase"})
            return

        video_id = data.get("id")
        video = find_video(video_id)
        if not video:
            self.respond_json(404, {"ok": False, "error": "not_found"})
            return

        path = os.path.join(UPLOAD_DIR, video["stored_filename"])
        if os.path.exists(path):
            os.remove(path)

        videos = [v for v in load_videos() if v["id"] != video_id]
        save_videos(videos)

        self.respond_json(200, {"ok": True})

    def respond_json(self, status, body):
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    # Renderは起動するポート番号を環境変数PORTで渡してくるため、
    # ローカル動作確認時のみ5173番にフォールバックする。
    port = int(os.environ.get("PORT", 5173))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Secret Viewer server running on http://0.0.0.0:{port}")
    print(f"Admin upload page: /admin")
    server.serve_forever()
