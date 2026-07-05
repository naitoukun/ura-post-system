"""
シークレット・ビューア: 開発用の簡易バックエンド。

- GET  /                TOPページ。通常はブログ(gadget-lifehack-blog.html)、
                        ?v=<動画ID> 付きの場合は動画アンロックページ(index.html)
- GET  /index.html      動画アンロックページに直接アクセス(?v=無しでも常にアプリを表示)
- GET  /admin           管理ページ。未ログインならログイン画面、ログイン済みならadmin.html
- GET  /admin/totp-setup  TOTPシークレットをQRコード化するツール（サーバーの実際の値は扱わない）
- GET  /terms           利用規約
- GET  /disclaimer      免責事項
- POST /api/login       パスフレーズ+TOTPコードでログインし、セッションCookieを発行
- POST /api/logout      ログアウト（セッションを破棄）
- GET  /api/videos      アップロード済み動画の一覧 (JSON) ※要ログイン
- GET  /resolve-video   指定した(または最新の)動画のメタ情報 (JSON)
- GET  /video/<id>      指定した動画の配信（Range対応 = シーク可能）
- POST /api/upload      動画アップロード（multipart/form-data。動画ごとに新しいIDを発行）※要ログイン
- POST /api/videos/delete  動画の削除（JSON）※要ログイン
- POST /api/videos/set-ads  動画ごとの広告A/B個別設定の更新・解除（JSON）※要ログイン
- POST /api/videos/set-time-limit  動画ごとの24時間限定設定の有効/無効切り替え（JSON）※要ログイン
- POST /api/videos/set-cta  動画ごとの出演者名+Fantia URLの更新・解除（JSON）※要ログイン
- GET  /site-config     プレミアムリンク・誘導ボタンの文字・既定の広告設定等のサイト設定 (JSON)
- POST /api/set-premium-link  プレミアムリンク・誘導ボタンの文字の更新（JSON）※要ログイン
- POST /api/set-ads     既定（動画に個別設定が無い場合用）の広告A/Bと表示比率の更新（JSON）※要ログイン

※「要ログイン」の操作は、/api/login で発行されたセッションCookieが無いと401になる。

環境変数:
  - PORT              待ち受けポート（Renderが自動設定。ローカルでは未設定なら5173）
  - UPLOAD_PASSPHRASE 管理者ログイン用のパスフレーズ（1つ目の要素）
  - TOTP_SECRET       管理者ログイン用の2段階認証シークレット（Base32。2つ目の要素）
  - UPLOAD_DIR        動画・設定ファイルの保存先（Renderでは永続ディスクのマウント先を指定）

TODO: 本番運用前に以下を必ず対応すること
  - UPLOAD_PASSPHRASE / TOTP_SECRET を推測されにくい値に変更する
    （Renderの環境変数として設定し、コードには書かない）
  - HTTPS 経由での運用（Renderは自動でHTTPS化されるため、Render以外にデプロイする場合のみ要対応）
  - アップロードファイルのウイルススキャン等、必要な安全対策の追加
"""

import base64
import hmac
import hashlib
import json
import mimetypes
import os
import re
import secrets
import struct
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

# 本番ではRenderの環境変数 UPLOAD_PASSPHRASE / TOTP_SECRET で上書きすること。
# ここに書かれているのはローカル動作確認用の仮の値。
UPLOAD_PASSPHRASE = os.environ.get("UPLOAD_PASSPHRASE", "change-me-please")
# ローカル確認用のダミー秘密鍵。Google Authenticator等に手入力で登録して試せる。
TOTP_SECRET = os.environ.get("TOTP_SECRET", "TUGSIULMQWTNMATI")

SESSION_COOKIE_NAME = "sv_session"
SESSION_DURATION_SECONDS = 4 * 60 * 60  # 4時間
# 単一プロセス前提のシンプルな実装のため、セッションはメモリ上にのみ保持する
# （サーバー再起動でログイン状態はリセットされる）。
SESSIONS = {}

MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}

# 「URL発行時」ではなく「誰かが初めてそのURLにアクセスした時刻」を起点にするため、
# 動画ごとに first_accessed_at (初回アクセス時刻) を記録し、そこから24時間で期限切れにする。
TIME_LIMIT_SECONDS = 24 * 60 * 60

DEFAULT_PREMIUM_LINK = "https://fantia.jp/"
DEFAULT_PREMIUM_BUTTON_TEXT = "【ファン限定】Fantia特設ページへ"
MAX_BUTTON_TEXT_LENGTH = 60

# 動画ごとに「出演者名」+「本人のFantia URL」を設定すると、誘導ボタンの文字を
# 「{name}を応援する」に、リンク先をそのURLに個別上書きできる。
# 両方セットされていない場合は、既定(DEFAULT_PREMIUM_LINK等)にフォールバックする。
CREATOR_BUTTON_TEXT_TEMPLATE = "{name}を応援する"
MAX_CREATOR_NAME_LENGTH = 20

# サイト全体共通のA/B広告設定。実際のi-mobile等のSDKはまだ繋いでいないため、
# ad_code は今のところ「将来SDKに渡すための識別子」を自由記述で保存するだけの欄。
DEFAULT_ADS = [
    {"id": "ad1", "label": "広告A", "ad_code": "", "weight": 70},
    {"id": "ad2", "label": "広告B", "ad_code": "", "weight": 30},
]
MAX_AD_LABEL_LENGTH = 40
MAX_AD_CODE_LENGTH = 2000

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")

os.makedirs(UPLOAD_DIR, exist_ok=True)


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "premium_link": DEFAULT_PREMIUM_LINK,
            "premium_button_text": DEFAULT_PREMIUM_BUTTON_TEXT,
            "ads": json.loads(json.dumps(DEFAULT_ADS)),
        }
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    config.setdefault("premium_link", DEFAULT_PREMIUM_LINK)
    config.setdefault("premium_button_text", DEFAULT_PREMIUM_BUTTON_TEXT)
    config.setdefault("ads", json.loads(json.dumps(DEFAULT_ADS)))
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


def format_epoch(epoch):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch))


def get_time_limit_status(video):
    """24時間限定設定の現在の状態を返す。

    - enabled=False: 無期限（通常の動画）
    - enabled=True かつ firstAccessedAt=None: 有効だがまだ誰もアクセスしていない（未開始）
    - enabled=True かつ firstAccessedAt有り: 初回アクセス時刻から24時間後がexpiresAt
    """
    enabled = bool(video.get("time_limit_enabled"))
    first_accessed = video.get("first_accessed_at")

    if not enabled:
        return {"enabled": False, "firstAccessedAt": None, "expiresAt": None, "expiresAtEpoch": None, "expired": False}
    if not first_accessed:
        return {"enabled": True, "firstAccessedAt": None, "expiresAt": None, "expiresAtEpoch": None, "expired": False}

    expires_at = first_accessed + TIME_LIMIT_SECONDS
    return {
        "enabled": True,
        "firstAccessedAt": format_epoch(first_accessed),
        "expiresAt": format_epoch(expires_at),
        # JS側でクライアントの時計を基準にライブカウントダウンするための生の秒数(UNIX epoch)
        "expiresAtEpoch": expires_at,
        "expired": time.time() > expires_at,
    }


def mark_first_access(video, videos_list):
    """24時間限定が有効で、まだ初回アクセスが記録されていなければ今の時刻を記録する。"""
    if video.get("time_limit_enabled") and not video.get("first_accessed_at"):
        video["first_accessed_at"] = time.time()
        save_videos(videos_list)


def get_effective_cta(video, config):
    """誘導ボタンのリンク先・文字を返す。

    動画に出演者名+URLの個別設定があればそれを、無ければサイト全体の既定値を使う。
    """
    name = video.get("creator_name")
    url = video.get("creator_url")
    if name and url:
        return {
            "premiumLink": url,
            "premiumButtonText": CREATOR_BUTTON_TEXT_TEMPLATE.format(name=name),
        }
    return {
        "premiumLink": config["premium_link"],
        "premiumButtonText": config["premium_button_text"],
    }


def _totp_code_at(secret_b32, counter, digits=6):
    """RFC 6238 (TOTP) の計算。secret_b32はGoogle Authenticator等と同じBase32形式。"""
    padded = secret_b32.upper() + "=" * ((8 - len(secret_b32) % 8) % 8)
    key = base64.b32decode(padded)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code_int).zfill(digits)


def verify_totp_code(secret_b32, code, period=30, window=1):
    """現在時刻の前後 window ステップ分は許容し、多少の時刻ずれを吸収する。"""
    if not code or not re.match(r"^\d{6}$", code):
        return False
    now_counter = int(time.time() // period)
    for delta in range(-window, window + 1):
        try:
            if hmac.compare_digest(_totp_code_at(secret_b32, now_counter + delta), code):
                return True
        except (ValueError, TypeError):
            return False
    return False


def parse_cookies(cookie_header):
    cookies = {}
    if not cookie_header:
        return cookies
    for part in cookie_header.split(";"):
        if "=" not in part:
            continue
        key, value = part.strip().split("=", 1)
        cookies[key] = value
    return cookies


def serialize_ad(ad):
    return {"id": ad["id"], "label": ad["label"], "adCode": ad["ad_code"], "weight": ad["weight"]}


def validate_ads_payload(ads_input):
    """広告A/B設定(2件固定)の共通バリデーション。

    成功時は (ads_list, None) を、失敗時は (None, error_code) を返す。
    サイト全体の既定設定・動画ごとの個別設定の両方から使い回す。
    """
    if not isinstance(ads_input, list) or len(ads_input) != 2:
        return None, "invalid_ads_count"

    new_ads = []
    for index, ad in enumerate(ads_input):
        label = (ad.get("label") or "").strip() if isinstance(ad, dict) else ""
        ad_code = (ad.get("adCode") or "").strip() if isinstance(ad, dict) else ""
        weight = ad.get("weight") if isinstance(ad, dict) else None

        if not label or len(label) > MAX_AD_LABEL_LENGTH:
            return None, "invalid_ad_label"
        if len(ad_code) > MAX_AD_CODE_LENGTH:
            return None, "invalid_ad_code"
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight < 0:
            return None, "invalid_ad_weight"

        new_ads.append({
            "id": "ad" + str(index + 1),
            "label": label,
            "ad_code": ad_code,
            "weight": weight,
        })

    if sum(ad["weight"] for ad in new_ads) <= 0:
        return None, "invalid_ad_weight"

    return new_ads, None


def validate_creator_cta(name, url):
    """動画ごとの出演者名+Fantia URLのバリデーション。

    成功時は (name, url, None) を、失敗時は (None, None, error_code) を返す。
    """
    name = (name or "").strip()
    url = (url or "").strip()

    if not name or len(name) > MAX_CREATOR_NAME_LENGTH:
        return None, None, "invalid_creator_name"
    if not re.match(r"^https?://", url):
        return None, None, "invalid_creator_url"

    return name, url, None


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

    # ---------- 認証(セッションCookie) ----------
    def is_authenticated(self):
        cookies = parse_cookies(self.headers.get("Cookie"))
        token = cookies.get(SESSION_COOKIE_NAME)
        if not token or token not in SESSIONS:
            return False
        if SESSIONS[token] < time.time():
            del SESSIONS[token]
            return False
        return True

    def require_auth(self):
        """要ログインの操作の先頭で呼ぶ。未ログインなら401を返してTrueを返す（呼び出し側はreturnする）。"""
        if self.is_authenticated():
            return False
        self.respond_json(401, {"ok": False, "error": "not_authenticated"})
        return True

    def create_session(self):
        # 既存の期限切れセッションを掃除してからメモリの肥大化を防ぐ
        now = time.time()
        for existing_token in [t for t, exp in SESSIONS.items() if exp < now]:
            del SESSIONS[existing_token]

        token = secrets.token_urlsafe(32)
        SESSIONS[token] = now + SESSION_DURATION_SECONDS
        return token

    def destroy_session(self):
        cookies = parse_cookies(self.headers.get("Cookie"))
        token = cookies.get(SESSION_COOKIE_NAME)
        if token:
            SESSIONS.pop(token, None)

    def set_session_cookie(self, token):
        # SameSite=Strict: 管理画面は外部サイトから叩かれる想定が無いためCSRF対策を最大限厳しくする
        # Secure: Renderは常にHTTPSなので有効。ローカルのhttp://localhostでもブラウザ側で許容される
        cookie = (
            f"{SESSION_COOKIE_NAME}={token}; Path=/; HttpOnly; Secure; "
            f"SameSite=Strict; Max-Age={SESSION_DURATION_SECONDS}"
        )
        self.send_header("Set-Cookie", cookie)

    def clear_session_cookie(self):
        self.send_header("Set-Cookie", f"{SESSION_COOKIE_NAME}=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0")

    # ---------- GET ----------
    def do_GET(self):
        split = urlsplit(self.path)
        path = split.path
        if path == "/":
            # TOP(素のURL)はブログをトップページとして表示する。
            # ただし ?v=<動画ID> の共有リンクでアクセスされた場合は、
            # 従来通り動画アンロックページ(index.html)を表示する。
            if "v" in parse_qs(split.query):
                self.serve_file(os.path.join(BASE_DIR, "index.html"), "text/html; charset=utf-8")
            else:
                self.serve_file(os.path.join(BASE_DIR, "gadget-lifehack-blog.html"), "text/html; charset=utf-8")
        elif path == "/index.html":
            # 動画アンロックページへの直接アクセス用（?v=無しでも常にアプリを表示）
            self.serve_file(os.path.join(BASE_DIR, "index.html"), "text/html; charset=utf-8")
        elif path == "/admin" or path == "/admin.html":
            if self.is_authenticated():
                self.serve_file(os.path.join(BASE_DIR, "admin.html"), "text/html; charset=utf-8")
            else:
                self.serve_file(os.path.join(BASE_DIR, "admin-login.html"), "text/html; charset=utf-8")
        elif path == "/admin/totp-setup":
            # サーバーの実際のTOTP_SECRETはここでは一切扱わない。
            # 入力された値をブラウザ内だけでQRコード化する単なるツール。
            self.serve_file(os.path.join(BASE_DIR, "admin-totp-setup.html"), "text/html; charset=utf-8")
        elif path == "/terms":
            self.serve_file(os.path.join(BASE_DIR, "terms.html"), "text/html; charset=utf-8")
        elif path == "/disclaimer":
            self.serve_file(os.path.join(BASE_DIR, "disclaimer.html"), "text/html; charset=utf-8")
        elif path == "/api/videos":
            if self.require_auth():
                return
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
        payload = json.dumps({
            "premiumLink": config["premium_link"],
            "premiumButtonText": config["premium_button_text"],
            "ads": [serialize_ad(ad) for ad in config["ads"]],
        }).encode("utf-8")
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
                "ads": [serialize_ad(ad) for ad in v["ads"]] if v.get("ads") else None,
                "timeLimit": get_time_limit_status(v),
                "creatorName": v.get("creator_name"),
                "creatorUrl": v.get("creator_url"),
            }
            for v in videos
        ]
        self.respond_json(200, body)

    def handle_resolve_video(self, query):
        requested_id = (query.get("v") or [None])[0]
        videos_list = load_videos()

        if requested_id:
            video = next((v for v in videos_list if v["id"] == requested_id), None)
            if not video or not video_file_path(video):
                self.respond_json(200, {"exists": False})
                return
        else:
            videos_sorted = sorted(videos_list, key=lambda v: v["uploaded_at"], reverse=True)
            video = videos_sorted[0] if videos_sorted else None
            if not video or not video_file_path(video):
                self.respond_json(200, {"exists": False})
                return

        # 「URLが初めて開かれた瞬間」をこの時点で記録する
        mark_first_access(video, videos_list)

        if get_time_limit_status(video)["expired"]:
            self.respond_json(200, {"exists": True, "expired": True})
            return

        config = load_config()
        effective_ads = video.get("ads") or config["ads"]
        cta = get_effective_cta(video, config)

        self.respond_json(200, {
            "exists": True,
            "expired": False,
            "id": video["id"],
            "originalFilename": video["original_filename"],
            "uploadedAt": video["uploaded_at"],
            "ads": [serialize_ad(ad) for ad in effective_ads],
            "timeLimit": get_time_limit_status(video),
            "premiumLink": cta["premiumLink"],
            "premiumButtonText": cta["premiumButtonText"],
        })

    def handle_serve_video(self, video_id):
        videos_list = load_videos()
        video = next((v for v in videos_list if v["id"] == video_id), None)
        path = video_file_path(video) if video else None
        if not path:
            self.send_error(404, "Video not found")
            return

        mark_first_access(video, videos_list)
        if get_time_limit_status(video)["expired"]:
            self.send_error(410, "This video link has expired")
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
        if path == "/api/login":
            self.handle_login()
        elif path == "/api/logout":
            self.handle_logout()
        elif path == "/api/upload":
            if self.require_auth():
                return
            self.handle_upload()
        elif path == "/api/videos/delete":
            if self.require_auth():
                return
            self.handle_delete_video()
        elif path == "/api/videos/set-ads":
            if self.require_auth():
                return
            self.handle_set_video_ads()
        elif path == "/api/videos/set-time-limit":
            if self.require_auth():
                return
            self.handle_set_time_limit()
        elif path == "/api/videos/set-cta":
            if self.require_auth():
                return
            self.handle_set_video_cta()
        elif path == "/api/set-premium-link":
            if self.require_auth():
                return
            self.handle_set_premium_link()
        elif path == "/api/set-ads":
            if self.require_auth():
                return
            self.handle_set_ads()
        else:
            self.send_error(404, "Not Found")

    def handle_login(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        passphrase_ok = hmac.compare_digest(data.get("passphrase") or "", UPLOAD_PASSPHRASE)
        code_ok = verify_totp_code(TOTP_SECRET, (data.get("code") or "").strip())

        # パスフレーズ・コードのどちらが間違っていたかは区別せず返す
        # （攻撃者にどちらが正しいか手がかりを与えないため）
        if not (passphrase_ok and code_ok):
            self.respond_json(401, {"ok": False, "error": "invalid_credentials"})
            return

        token = self.create_session()
        self.send_response(200)
        self.set_session_cookie(token)
        payload = json.dumps({"ok": True}).encode("utf-8")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_logout(self):
        self.destroy_session()
        self.send_response(200)
        self.clear_session_cookie()
        payload = json.dumps({"ok": True}).encode("utf-8")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

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

        url = (data.get("url") or "").strip()
        if not re.match(r"^https?://", url):
            self.respond_json(400, {"ok": False, "error": "invalid_url"})
            return

        button_text = (data.get("buttonText") or "").strip()
        if not button_text or len(button_text) > MAX_BUTTON_TEXT_LENGTH:
            self.respond_json(400, {"ok": False, "error": "invalid_button_text"})
            return

        config = load_config()
        config["premium_link"] = url
        config["premium_button_text"] = button_text
        save_config(config)

        self.respond_json(200, {
            "ok": True,
            "premiumLink": url,
            "premiumButtonText": button_text,
        })

    def handle_set_ads(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 20_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        new_ads, error = validate_ads_payload(data.get("ads"))
        if error:
            self.respond_json(400, {"ok": False, "error": error})
            return

        config = load_config()
        config["ads"] = new_ads
        save_config(config)

        self.respond_json(200, {"ok": True, "ads": [serialize_ad(ad) for ad in new_ads]})

    def handle_set_video_ads(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 20_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        videos = load_videos()
        video = next((v for v in videos if v["id"] == data.get("id")), None)
        if not video:
            self.respond_json(404, {"ok": False, "error": "not_found"})
            return

        ads_input = data.get("ads")
        if ads_input is None:
            # ads未指定(null)は「個別設定を解除して既定に戻す」の意味
            video.pop("ads", None)
            save_videos(videos)
            self.respond_json(200, {"ok": True, "ads": None})
            return

        new_ads, error = validate_ads_payload(ads_input)
        if error:
            self.respond_json(400, {"ok": False, "error": error})
            return

        video["ads"] = new_ads
        save_videos(videos)

        self.respond_json(200, {"ok": True, "ads": [serialize_ad(ad) for ad in new_ads]})

    def handle_set_time_limit(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        enabled = data.get("enabled")
        if not isinstance(enabled, bool):
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        videos = load_videos()
        video = next((v for v in videos if v["id"] == data.get("id")), None)
        if not video:
            self.respond_json(404, {"ok": False, "error": "not_found"})
            return

        video["time_limit_enabled"] = enabled
        if not enabled:
            # 無効化したら計測もリセットする（再度有効化した時は次回アクセスから計測し直す）
            video.pop("first_accessed_at", None)
        save_videos(videos)

        self.respond_json(200, {"ok": True, "timeLimit": get_time_limit_status(video)})

    def handle_set_video_cta(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        videos = load_videos()
        video = next((v for v in videos if v["id"] == data.get("id")), None)
        if not video:
            self.respond_json(404, {"ok": False, "error": "not_found"})
            return

        name_input = data.get("creatorName")
        url_input = data.get("creatorUrl")

        if name_input is None and url_input is None:
            # 両方null(未指定)は「個別設定を解除して既定に戻す」の意味
            video.pop("creator_name", None)
            video.pop("creator_url", None)
            save_videos(videos)
            self.respond_json(200, {"ok": True, "creatorName": None, "creatorUrl": None})
            return

        name, url, error = validate_creator_cta(name_input, url_input)
        if error:
            self.respond_json(400, {"ok": False, "error": error})
            return

        video["creator_name"] = name
        video["creator_url"] = url
        save_videos(videos)

        self.respond_json(200, {"ok": True, "creatorName": name, "creatorUrl": url})

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

        video_file = files.get("video")
        if not video_file:
            self.respond_json(400, {"ok": False, "error": "missing_video_field"})
            return

        original_filename = video_file["filename"] or "upload"
        ext = os.path.splitext(original_filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            self.respond_json(400, {"ok": False, "error": "unsupported_file_type"})
            return

        # 出演者名+Fantia URLは任意入力。どちらか一方でも入力されていれば両方揃っているか検証する
        creator_name_input = fields.get("creatorName", "").strip()
        creator_url_input = fields.get("creatorUrl", "").strip()
        creator_fields = {}
        if creator_name_input or creator_url_input:
            name, url, error = validate_creator_cta(creator_name_input, creator_url_input)
            if error:
                self.respond_json(400, {"ok": False, "error": error})
                return
            creator_fields = {"creator_name": name, "creator_url": url}

        video_id = secrets.token_urlsafe(9)
        stored_filename = video_id + ext
        time_limit_enabled = fields.get("timeLimitEnabled") in ("1", "true", "on")

        with open(os.path.join(UPLOAD_DIR, stored_filename), "wb") as f:
            f.write(video_file["content"])

        videos = load_videos()
        videos.append({
            "id": video_id,
            "stored_filename": stored_filename,
            "original_filename": original_filename,
            "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "time_limit_enabled": time_limit_enabled,
            **creator_fields,
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
