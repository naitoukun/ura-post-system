"""
シークレット・ビューア: 開発用の簡易バックエンド。

- GET  /                動画アンロックページ(index.html)。共有リンク専用にするため
                        一覧等は置かず、常にindex.htmlを返す。og:image等は?vに応じて動的に差し込む
- GET  /index.html      動画アンロックページに直接アクセス(?v=無しでも常にアプリを表示)
- GET  /admin           管理ページ。未ログインならログイン画面、ログイン済みならadmin.html
- GET  /admin/totp-setup  TOTPシークレットをQRコード化するツール（サーバーの実際の値は扱わない）
- GET  /video-merge-tool  クリエイター向け動画結合ツール（ブラウザ内完結、ログイン不要）
- GET  /terms           利用規約
- GET  /disclaimer      免責事項
- GET  /copyright-policy 著作権ポリシー・2257条コンプライアンス表明（ExoClick審査要件）
- GET  /og-image        SNSシェア時のOGP/Twitterカード用サイト共通画像（管理画面で差し替え可能。未設定時は同梱の既定画像）
- GET  /thumb/<id>      動画ごとに設定した個別サムネイル（未設定ならそもそも参照されない）
- GET  /stats/<token>   クリエイター向けの視聴データページ（ログイン不要。共有リンクとは別トークン）
- POST /api/login       パスフレーズ+TOTPコードでログインし、セッションCookieを発行
- POST /api/logout      ログアウト（セッションを破棄）
- GET  /api/videos      アップロード済み動画の一覧 (JSON) ※要ログイン
- GET  /resolve-video   指定した(または最新の)コンテンツのメタ情報 (JSON。動画/画像共通)
- GET  /video/<id>      指定した動画の配信（Range対応 = シーク可能。画像ギャラリーには404）
- GET  /image/<id>/<index>  画像ギャラリーのうち指定した1枚の配信
- POST /api/upload      動画または画像ギャラリーのアップロード（multipart/form-data。
                        contentType=video/image。新規IDを発行）※要ログイン
- POST /api/videos/delete  動画の削除（JSON）※要ログイン
- POST /api/videos/set-ads  動画ごとの広告A/B個別設定の更新・解除（JSON）※要ログイン
- POST /api/videos/set-time-limit  動画ごとの24時間限定設定の有効/無効切り替え（JSON）※要ログイン
- POST /api/videos/set-cta  動画ごとの出演者名+Fantia URLの更新・解除（JSON）※要ログイン
- POST /api/videos/set-thumbnail  動画ごとの個別サムネイル画像の設定（multipart/form-data）※要ログイン
- POST /api/videos/reset-thumbnail  動画ごとの個別サムネイルを解除しサイト既定画像に戻す（JSON）※要ログイン
- GET  /site-config     プレミアムリンク・誘導ボタンの文字・既定の広告設定等のサイト設定 (JSON)
- POST /api/set-premium-link  プレミアムリンク・誘導ボタンの文字の更新（JSON）※要ログイン
- POST /api/set-ads     既定（動画に個別設定が無い場合用）の広告A/Bと表示比率の更新（JSON）※要ログイン
- POST /api/set-points  クリエイターへのポイント付与ルール（アップロード1件の付与量・24時間以内の最低閲覧数）の更新（JSON）※要ログイン
- POST /api/set-og-image  OGP画像の差し替え（multipart/form-data）※要ログイン
- POST /api/reset-og-image  OGP画像を同梱の既定画像に戻す（JSON）※要ログイン

クリエイター(女の子)アカウント。管理者(上記の/api/login)とは完全に別のセッション/Cookieで扱う:
- GET  /join/<invite_token>  招待受諾ページ。パスワードを設定してアカウントを有効化する
- GET  /creator          クリエイター向けダッシュボード。未ログインならログイン画面
- POST /api/creator/register  招待トークン+パスワードで登録し、セッションCookieを発行
- POST /api/creator/login  ログインコード+パスワードでログイン
- POST /api/creator/logout
- GET  /api/creator/content  自分がアップロードしたコンテンツの一覧(JSON、ポイント状況込み)※要クリエイターログイン
- GET  /api/creators/me  自分のポイント残高・交換申請履歴(JSON)※要クリエイターログイン
- POST /api/creator/upload  動画/画像ギャラリーのセルフアップロード ※要クリエイターログイン
- POST /api/creator/content/delete  自分のコンテンツの削除（所有者チェック有り）※要クリエイターログイン
- POST /api/creator/request-redemption  貯まったポイントのギフト券交換を申請（JSON）※要クリエイターログイン
- GET  /api/creators     クリエイター一覧＋ポイント残高＋交換申請一覧（JSON）※要ログイン(管理者)
- POST /api/creators/invite  招待URL+ログインコードを新規発行（JSON）※要ログイン(管理者)
- POST /api/creators/approve-points  投稿1件を承認しポイント付与（サーバー側で状態を再検証）※要ログイン(管理者)
- POST /api/creators/adjust-points  ポイント残高の手動調整（返金・是正用）※要ログイン(管理者)
- POST /api/creators/fulfill-redemption  ギフト券交換申請を対応済みにする（JSON）※要ログイン(管理者)

※「要ログイン」の操作は、/api/login で発行されたセッションCookieが無いと401になる。
※「要クリエイターログイン」の操作は、/api/creator/login等で発行された別のセッションCookieが無いと401になる。

環境変数:
  - PORT              待ち受けポート（Renderが自動設定。ローカルでは未設定なら5173）
  - UPLOAD_PASSPHRASE 管理者ログイン用のパスフレーズ（1つ目の要素）
  - TOTP_SECRET       管理者ログイン用の2段階認証シークレット（Base32。2つ目の要素）
  - UPLOAD_DIR        動画・設定ファイルの保存先（Renderでは永続ディスクのマウント先を指定）
  - PUBLIC_SITE_URL   OGP画像等の絶対URL組み立てに使う公開ドメイン（未設定時は https://ura-post.com）

TODO: 本番運用前に以下を必ず対応すること
  - UPLOAD_PASSPHRASE / TOTP_SECRET を推測されにくい値に変更する
    （Renderの環境変数として設定し、コードには書かない）
  - HTTPS 経由での運用（Renderは自動でHTTPS化されるため、Render以外にデプロイする場合のみ要対応）
  - アップロードファイルのウイルススキャン等、必要な安全対策の追加
"""

import base64
import hmac
import hashlib
import html
import json
import mimetypes
import os
import re
import secrets
import struct
import threading
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

# 画像モード(複数枚のギャラリー)用。1枚あたりのサイズ・枚数上限は動画よりだいぶ小さいので別枠にする。
IMAGE_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_BYTES = 20 * 1024 * 1024  # 1枚あたり20MB
MAX_IMAGES_PER_GALLERY = 30

# SNSシェア時のOGP/Twitterカード画像。管理画面から差し替えが無い場合は
# BASE_DIR直下の同梱デフォルト画像を使う。差し替え分は永続ディスク(UPLOAD_DIR)に保存する。
# 動画ごとに個別のサムネイルを設定した場合は、その動画の共有リンクを開いた時だけ
# サイト既定の代わりにそちらをOGP画像として使う(index.htmlを動的に組み立てて差し込む)。
DEFAULT_OG_IMAGE_PATH = os.path.join(BASE_DIR, "og-image.png")
OG_IMAGE_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_OG_IMAGE_BYTES = 5 * 1024 * 1024  # 5MB
# og:image等はSNS側のクローラーが絶対URLで取得するため、公開ドメインを固定で持っておく。
# 別ドメインで動作確認する場合は環境変数で上書きできるようにしておく。
PUBLIC_SITE_URL = os.environ.get("PUBLIC_SITE_URL", "https://ura-post.com")

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

# サイト全体共通のA/B広告設定。ad_code はGoogle IMA SDKに渡すVASTタグURL。
DEFAULT_ADS = [
    {"id": "ad1", "label": "広告A", "ad_code": "https://s.magsrv.com/v1/vast.php?idz=5967416", "weight": 15},
    {"id": "ad2", "label": "広告B", "ad_code": "", "weight": 85},
]
MAX_AD_LABEL_LENGTH = 40
MAX_AD_CODE_LENGTH = 2000

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- クリエイター（女の子）アカウント / ポイント・ギフト券システム ----------
# 招待制のセルフアップロードアカウント。管理者アカウントとは完全に別のセッション・
# Cookieで扱う（管理者用のSESSIONS/認証コードには一切手を入れない）。
CREATORS_META_PATH = os.path.join(UPLOAD_DIR, "creators.json")

CREATOR_SESSION_COOKIE_NAME = "sv_creator_session"
CREATOR_SESSION_DURATION_SECONDS = 12 * 60 * 60  # 12時間（アップロード作業が長引くことを考慮し管理者より長め）
CREATOR_SESSIONS = {}

MIN_CREATOR_PASSWORD_LENGTH = 8
LOGIN_CODE_RE = re.compile(r"^[A-F0-9]{8}$")

# アップロードから24時間以内に、この閲覧数を超えないとポイント付与対象にならない。
# 固定ポイント自体も含め、サイト全体の既定値。管理画面(ポイント設定)で変更可能。
POINTS_WINDOW_SECONDS = 24 * 60 * 60
DEFAULT_POINTS_PER_UPLOAD = 100
DEFAULT_POINTS_VIEW_THRESHOLD = 10

# creators.json への書き込みは、ポイント残高・交換申請という「実害に直結する値」を
# 扱うため、他のJSONファイル(videos.json等)と違い read-modify-write をロックで保護する。
CREATORS_LOCK = threading.Lock()


def load_creators():
    if not os.path.exists(CREATORS_META_PATH):
        return []
    with open(CREATORS_META_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_creators(creators):
    with open(CREATORS_META_PATH, "w", encoding="utf-8") as f:
        json.dump(creators, f, ensure_ascii=False)


def find_creator(creators, creator_id):
    return next((c for c in creators if c["id"] == creator_id), None)


def find_creator_by_login_code(creators, login_code):
    return next((c for c in creators if c.get("login_code") == login_code and c.get("status") == "active"), None)


def find_creator_by_invite_token(creators, invite_token):
    return next((c for c in creators if c.get("invite_token") == invite_token and c.get("status") == "invited"), None)


def hash_password(password, salt_hex=None):
    """stdlibのみでのパスワードハッシュ化(PBKDF2-HMAC-SHA256, 20万イテレーション)。"""
    salt_hex = salt_hex or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 200_000)
    return salt_hex, digest.hex()


def verify_password(password, salt_hex, expected_hash_hex):
    if not salt_hex or not expected_hash_hex:
        return False
    _, computed_hash_hex = hash_password(password, salt_hex)
    return hmac.compare_digest(computed_hash_hex, expected_hash_hex)


def get_points_status(video, config):
    """クリエイター投稿1件の、ポイント付与に関する現在の状態を返す。

    管理者自身のアップロード(owner_creator_id無し)には適用されないのでNoneを返す。
    get_time_limit_status と同様、DBには「承認済みかどうか」しか保存せず、
    それ以外の状態(集計中/対象外等)は呼ばれるたびに計算するだけにする。
    """
    if not video.get("owner_creator_id"):
        return None
    if video.get("points_awarded"):
        return {"state": "awarded", "amount": video.get("points_awarded_amount"), "viewCount": video.get("view_count", 0)}

    window_end = video.get("uploaded_at_epoch", 0) + POINTS_WINDOW_SECONDS
    view_count = video.get("view_count", 0)
    threshold = config.get("points_view_threshold", DEFAULT_POINTS_VIEW_THRESHOLD)

    if time.time() < window_end:
        return {"state": "collecting", "viewCount": view_count, "threshold": threshold, "windowEndsAt": window_end}
    if view_count >= threshold:
        return {"state": "eligible_pending_approval", "viewCount": view_count, "threshold": threshold}
    return {"state": "not_eligible", "viewCount": view_count, "threshold": threshold}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "premium_link": DEFAULT_PREMIUM_LINK,
            "premium_button_text": DEFAULT_PREMIUM_BUTTON_TEXT,
            "ads": json.loads(json.dumps(DEFAULT_ADS)),
            "og_image_filename": None,
            "points_per_upload": DEFAULT_POINTS_PER_UPLOAD,
            "points_view_threshold": DEFAULT_POINTS_VIEW_THRESHOLD,
        }
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    config.setdefault("premium_link", DEFAULT_PREMIUM_LINK)
    config.setdefault("premium_button_text", DEFAULT_PREMIUM_BUTTON_TEXT)
    config.setdefault("ads", json.loads(json.dumps(DEFAULT_ADS)))
    config.setdefault("og_image_filename", None)
    config.setdefault("points_per_upload", DEFAULT_POINTS_PER_UPLOAD)
    config.setdefault("points_view_threshold", DEFAULT_POINTS_VIEW_THRESHOLD)
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
    """コンテンツの実体ファイルの存在確認用。画像ギャラリーの場合は1枚目で代表させる。"""
    if video.get("content_type") == "image":
        filenames = video.get("image_filenames") or []
        if not filenames:
            return None
        path = os.path.join(UPLOAD_DIR, filenames[0])
        return path if os.path.exists(path) else None
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


def get_stats_token(video, videos_list):
    """クリエイター向け視聴データページ(/stats/<token>)用のトークンを返す。

    共有リンク(動画ID)とは別物にすることで、視聴用リンクを知っている一般の
    視聴者に統計を見せない・逆に統計リンクから動画本編を見られないようにする。
    既存動画(このトークン導入前にアップロードされたもの)には無いので、
    無ければここで発行して保存する。
    """
    if not video.get("stats_token"):
        video["stats_token"] = secrets.token_urlsafe(9)
        save_videos(videos_list)
    return video["stats_token"]


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


def serialize_redemption_request(r):
    return {
        "id": r["id"],
        "points": r["points"],
        "status": r["status"],
        "requestedAt": r.get("requested_at"),
        "fulfilledAt": r.get("fulfilled_at"),
    }


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
    """multipart/form-data を最小限だけ解釈するパーサ。

    同じフィールド名で複数ファイルが送られてくる場合(画像ギャラリーの複数選択等)に
    対応するため、files[field_name] は常にリスト(1件でも[dict])で返す。
    """
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
            files.setdefault(field_name, []).append({
                "filename": filename_match.group(1),
                "content": content,
            })
        else:
            fields[field_name] = content.decode("utf-8", errors="replace")

    return fields, files


def first_file(files, field_name):
    """files[field_name](リスト)の先頭1件だけ取り出す。無ければNone。"""
    entries = files.get(field_name)
    return entries[0] if entries else None


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

    # ---------- 認証(クリエイター用セッションCookie。管理者用とは完全に別物) ----------
    def get_creator_id(self):
        """クリエイターとしてログイン中ならそのidを、そうでなければNoneを返す。"""
        cookies = parse_cookies(self.headers.get("Cookie"))
        token = cookies.get(CREATOR_SESSION_COOKIE_NAME)
        if not token or token not in CREATOR_SESSIONS:
            return None
        session = CREATOR_SESSIONS[token]
        if session["expires"] < time.time():
            del CREATOR_SESSIONS[token]
            return None
        return session["creator_id"]

    def require_creator_auth(self):
        """要クリエイターログインの操作の先頭で呼ぶ。未ログインなら401を返してTrueを返す。"""
        if self.get_creator_id() is not None:
            return False
        self.respond_json(401, {"ok": False, "error": "not_authenticated"})
        return True

    def create_creator_session(self, creator_id):
        now = time.time()
        for existing_token in [t for t, s in CREATOR_SESSIONS.items() if s["expires"] < now]:
            del CREATOR_SESSIONS[existing_token]

        token = secrets.token_urlsafe(32)
        CREATOR_SESSIONS[token] = {"creator_id": creator_id, "expires": now + CREATOR_SESSION_DURATION_SECONDS}
        return token

    def destroy_creator_session(self):
        cookies = parse_cookies(self.headers.get("Cookie"))
        token = cookies.get(CREATOR_SESSION_COOKIE_NAME)
        if token:
            CREATOR_SESSIONS.pop(token, None)

    def set_creator_session_cookie(self, token):
        cookie = (
            f"{CREATOR_SESSION_COOKIE_NAME}={token}; Path=/; HttpOnly; Secure; "
            f"SameSite=Strict; Max-Age={CREATOR_SESSION_DURATION_SECONDS}"
        )
        self.send_header("Set-Cookie", cookie)

    def clear_creator_session_cookie(self):
        self.send_header(
            "Set-Cookie",
            f"{CREATOR_SESSION_COOKIE_NAME}=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0",
        )

    # ---------- GET ----------
    def do_GET(self):
        split = urlsplit(self.path)
        path = split.path
        # 末尾のスラッシュ有無で別ルート扱いになり404になるのを防ぐ(例: /admin/ → /admin)
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")
        if path == "/":
            # TOP(素のURL)は共有リンク専用。個別の?v=<動画ID>を知っている相手だけが
            # 動画にたどり着ける状態にし、他の動画への回遊(一覧からの流出)は作らない。
            self.handle_serve_unlock_page(parse_qs(split.query))
        elif path == "/index.html":
            # 動画アンロックページへの直接アクセス用（?v=無しでも常にアプリを表示）
            self.handle_serve_unlock_page(parse_qs(split.query))
        elif path == "/admin" or path == "/admin.html":
            if self.is_authenticated():
                self.serve_file(os.path.join(BASE_DIR, "admin.html"), "text/html; charset=utf-8")
            else:
                self.serve_file(os.path.join(BASE_DIR, "admin-login.html"), "text/html; charset=utf-8")
        elif path == "/admin/totp-setup":
            # サーバーの実際のTOTP_SECRETはここでは一切扱わない。
            # 入力された値をブラウザ内だけでQRコード化する単なるツール。
            self.serve_file(os.path.join(BASE_DIR, "admin-totp-setup.html"), "text/html; charset=utf-8")
        elif path == "/video-merge-tool":
            # クリエイターに渡す用の動画結合ツール。処理はブラウザ内(ffmpeg.wasm)で完結し、
            # 動画はサーバーに一切送信されないため、ログイン不要で誰でも使える。
            # ffmpeg.wasmがSharedArrayBufferを使うため、このページだけcrossOriginIsolated
            # (COOP/COEP)を有効にする。
            self.serve_file(
                os.path.join(BASE_DIR, "video-merge-tool.html"),
                "text/html; charset=utf-8",
                extra_headers={
                    "Cross-Origin-Opener-Policy": "same-origin",
                    "Cross-Origin-Embedder-Policy": "require-corp",
                },
            )
        elif path == "/terms":
            self.serve_file(os.path.join(BASE_DIR, "terms.html"), "text/html; charset=utf-8")
        elif path == "/disclaimer":
            self.serve_file(os.path.join(BASE_DIR, "disclaimer.html"), "text/html; charset=utf-8")
        elif path == "/copyright-policy":
            self.serve_file(os.path.join(BASE_DIR, "copyright-policy.html"), "text/html; charset=utf-8")
        elif path == "/og-image":
            self.handle_serve_og_image()
        elif path.startswith("/thumb/"):
            self.handle_serve_thumbnail(path[len("/thumb/"):])
        elif path.startswith("/stats/"):
            self.handle_serve_creator_stats(path[len("/stats/"):])
        elif path == "/api/videos":
            if self.require_auth():
                return
            self.handle_list_videos()
        elif path == "/resolve-video":
            self.handle_resolve_video(parse_qs(split.query))
        elif path.startswith("/video/"):
            self.handle_serve_video(path[len("/video/"):])
        elif path.startswith("/image/"):
            self.handle_serve_image(path[len("/image/"):])
        elif path == "/site-config":
            self.handle_site_config()
        elif path.startswith("/join/"):
            self.handle_serve_join_page(path[len("/join/"):])
        elif path == "/creator":
            if self.get_creator_id() is not None:
                self.serve_file(os.path.join(BASE_DIR, "creator-dashboard.html"), "text/html; charset=utf-8")
            else:
                self.serve_file(os.path.join(BASE_DIR, "creator-login.html"), "text/html; charset=utf-8")
        elif path == "/api/creator/content":
            if self.require_creator_auth():
                return
            self.handle_list_creator_content()
        elif path == "/api/creators":
            if self.require_auth():
                return
            self.handle_list_creators()
        elif path == "/api/creators/me":
            if self.require_creator_auth():
                return
            self.handle_get_own_creator_info()
        else:
            self.send_error(404, "Not Found")

    def handle_site_config(self):
        config = load_config()
        payload = json.dumps({
            "premiumLink": config["premium_link"],
            "premiumButtonText": config["premium_button_text"],
            "ads": [serialize_ad(ad) for ad in config["ads"]],
            "hasCustomOgImage": bool(config.get("og_image_filename")),
            "pointsPerUpload": config.get("points_per_upload", DEFAULT_POINTS_PER_UPLOAD),
            "pointsViewThreshold": config.get("points_view_threshold", DEFAULT_POINTS_VIEW_THRESHOLD),
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def handle_list_videos(self):
        videos = sorted(load_videos(), key=lambda v: v["uploaded_at"], reverse=True)
        config = load_config()
        creators = load_creators()
        body = [
            {
                "id": v["id"],
                "originalFilename": v["original_filename"],
                "uploadedAt": v["uploaded_at"],
                "ads": [serialize_ad(ad) for ad in v["ads"]] if v.get("ads") else None,
                "timeLimit": get_time_limit_status(v),
                "creatorName": v.get("creator_name"),
                "creatorUrl": v.get("creator_url"),
                "viewCount": v.get("view_count", 0),
                "hasCustomThumbnail": bool(v.get("og_image_filename")),
                "statsToken": get_stats_token(v, videos),
                "contentType": v.get("content_type", "video"),
                "imageCount": len(v.get("image_filenames") or []) if v.get("content_type") == "image" else None,
                "ownerDisplayName": (
                    (find_creator(creators, v["owner_creator_id"]) or {}).get("display_name")
                    if v.get("owner_creator_id") else None
                ),
                "pointsStatus": get_points_status(v, config),
            }
            for v in videos
        ]
        self.respond_json(200, body)

    def handle_resolve_video(self, query):
        requested_id = (query.get("v") or [None])[0]

        if not requested_id:
            # 共有リンク(?v=<id>)が無いアクセスは、他の動画への回遊を防ぐため
            # 動画を一切表示しない(「リンクが必要です」の案内のみ)。
            self.respond_json(200, {"linkRequired": True})
            return

        videos_list = load_videos()
        video = next((v for v in videos_list if v["id"] == requested_id), None)
        if not video or not video_file_path(video):
            # 削除済み・存在しないIDへのアクセスは「期限切れ」と同じ画面に統一する。
            # (手動削除なのか自然に24時間経過したのかを外部から区別させないため)
            self.respond_json(200, {"expired": True})
            return

        # 「URLが初めて開かれた瞬間」をこの時点で記録する
        mark_first_access(video, videos_list)

        if get_time_limit_status(video)["expired"]:
            self.respond_json(200, {"expired": True})
            return

        # モザイク越しのロック画面が表示された回数を視聴回数としてカウントする
        # (期限切れの場合はロック画面自体を表示しないため、ここではカウントしない)
        video["view_count"] = video.get("view_count", 0) + 1
        save_videos(videos_list)

        config = load_config()
        effective_ads = video.get("ads") or config["ads"]
        cta = get_effective_cta(video, config)

        content_type = video.get("content_type", "video")
        self.respond_json(200, {
            "expired": False,
            "id": video["id"],
            "contentType": content_type,
            "imageCount": len(video.get("image_filenames") or []) if content_type == "image" else None,
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
        if video and video.get("content_type") == "image":
            # 画像ギャラリーは /image/<id>/<index> の方を使う
            self.send_error(404, "Video not found")
            return
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

    def handle_serve_image(self, path_suffix):
        parts = path_suffix.split("/", 1)
        if len(parts) != 2:
            self.send_error(404, "Not Found")
            return
        video_id, index_str = parts
        try:
            index = int(index_str)
        except ValueError:
            self.send_error(404, "Not Found")
            return

        videos_list = load_videos()
        video = next((v for v in videos_list if v["id"] == video_id), None)
        if not video or video.get("content_type") != "image":
            self.send_error(404, "Not Found")
            return

        image_filenames = video.get("image_filenames") or []
        if index < 0 or index >= len(image_filenames):
            self.send_error(404, "Not Found")
            return

        path = os.path.join(UPLOAD_DIR, image_filenames[index])
        if not os.path.exists(path):
            self.send_error(404, "Not Found")
            return

        mark_first_access(video, videos_list)
        if get_time_limit_status(video)["expired"]:
            self.send_error(410, "This link has expired")
            return

        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        self.serve_file(path, content_type, extra_headers={"Cache-Control": "no-store"})

    def serve_file(self, path, content_type, extra_headers=None):
        if not os.path.exists(path):
            self.send_error(404, "Not Found")
            return
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def handle_serve_og_image(self):
        config = load_config()
        filename = config.get("og_image_filename")
        if filename:
            custom_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(custom_path):
                content_type = mimetypes.guess_type(custom_path)[0] or "application/octet-stream"
                self.serve_file(custom_path, content_type)
                return
        self.serve_file(DEFAULT_OG_IMAGE_PATH, "image/png")

    def handle_serve_thumbnail(self, video_id):
        video = find_video(video_id)
        filename = video.get("og_image_filename") if video else None
        if not filename:
            self.send_error(404, "Not Found")
            return
        path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(path):
            self.send_error(404, "Not Found")
            return
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        self.serve_file(path, content_type)

    def handle_serve_creator_stats(self, token):
        videos_list = load_videos()
        video = next((v for v in videos_list if v.get("stats_token") == token), None)
        if not video:
            self.send_error(404, "Not Found")
            return

        with open(os.path.join(BASE_DIR, "creator-stats.html"), "r", encoding="utf-8") as f:
            page_html = f.read()

        time_limit = get_time_limit_status(video)
        if not time_limit["enabled"]:
            status_text = "無期限で公開中"
        elif time_limit["expired"]:
            status_text = "期限切れ（非公開）"
        else:
            status_text = "24時間限定リンクで公開中"

        creator_name = video.get("creator_name")
        heading = (html.escape(creator_name) + "さんの視聴データ") if creator_name else "視聴データ"

        page_html = page_html.replace("{{HEADING}}", heading)
        page_html = page_html.replace("{{VIEW_COUNT}}", str(video.get("view_count", 0)))
        page_html = page_html.replace("{{UPLOADED_AT}}", html.escape(video["uploaded_at"]))
        page_html = page_html.replace("{{STATUS_TEXT}}", status_text)

        body = page_html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def handle_serve_unlock_page(self, query):
        """動画アンロックページ(index.html)を返す。

        OGP画像は、共有リンク(?v=<id>)が指している動画に個別サムネイルが
        設定されていればそれを、無ければサイト共通の既定画像を差し込む。
        SNSのクローラーはJSを実行しないため、この差し込みはHTMLを返す
        このタイミングでサーバー側にやっておく必要がある。
        """
        with open(os.path.join(BASE_DIR, "index.html"), "r", encoding="utf-8") as f:
            html = f.read()

        requested_id = (query.get("v") or [None])[0]
        image_url = PUBLIC_SITE_URL + "/og-image"
        if requested_id:
            video = find_video(requested_id)
            if video and video.get("og_image_filename"):
                thumb_path = os.path.join(UPLOAD_DIR, video["og_image_filename"])
                if os.path.exists(thumb_path):
                    image_url = PUBLIC_SITE_URL + "/thumb/" + requested_id

        html = html.replace("{{OG_IMAGE_URL}}", image_url)
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
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
        elif path == "/api/videos/set-thumbnail":
            if self.require_auth():
                return
            self.handle_set_video_thumbnail()
        elif path == "/api/videos/reset-thumbnail":
            if self.require_auth():
                return
            self.handle_reset_video_thumbnail()
        elif path == "/api/set-premium-link":
            if self.require_auth():
                return
            self.handle_set_premium_link()
        elif path == "/api/set-ads":
            if self.require_auth():
                return
            self.handle_set_ads()
        elif path == "/api/set-og-image":
            if self.require_auth():
                return
            self.handle_set_og_image()
        elif path == "/api/reset-og-image":
            if self.require_auth():
                return
            self.handle_reset_og_image()
        elif path == "/api/creator/register":
            self.handle_creator_register()
        elif path == "/api/creator/login":
            self.handle_creator_login()
        elif path == "/api/creator/logout":
            self.handle_creator_logout()
        elif path == "/api/creator/upload":
            if self.require_creator_auth():
                return
            self.handle_creator_upload()
        elif path == "/api/creator/content/delete":
            if self.require_creator_auth():
                return
            self.handle_creator_delete_content()
        elif path == "/api/creator/request-redemption":
            if self.require_creator_auth():
                return
            self.handle_creator_request_redemption()
        elif path == "/api/set-points":
            if self.require_auth():
                return
            self.handle_set_points()
        elif path == "/api/creators/invite":
            if self.require_auth():
                return
            self.handle_creators_invite()
        elif path == "/api/creators/approve-points":
            if self.require_auth():
                return
            self.handle_creators_approve_points()
        elif path == "/api/creators/adjust-points":
            if self.require_auth():
                return
            self.handle_creators_adjust_points()
        elif path == "/api/creators/fulfill-redemption":
            if self.require_auth():
                return
            self.handle_creators_fulfill_redemption()
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

    def handle_set_points(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        points_per_upload = data.get("pointsPerUpload")
        points_view_threshold = data.get("pointsViewThreshold")

        def is_positive_int(value):
            return isinstance(value, int) and not isinstance(value, bool) and value > 0

        if not is_positive_int(points_per_upload) or not is_positive_int(points_view_threshold):
            self.respond_json(400, {"ok": False, "error": "invalid_points_config"})
            return

        config = load_config()
        config["points_per_upload"] = points_per_upload
        config["points_view_threshold"] = points_view_threshold
        save_config(config)

        self.respond_json(200, {
            "ok": True,
            "pointsPerUpload": points_per_upload,
            "pointsViewThreshold": points_view_threshold,
        })

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

    def handle_set_video_thumbnail(self):
        content_type_header = self.headers.get("Content-Type", "")
        boundary_match = re.search(r"boundary=(.+)", content_type_header)
        content_length = int(self.headers.get("Content-Length", 0))

        if not content_type_header.startswith("multipart/form-data") or not boundary_match:
            self.respond_json(400, {"ok": False, "error": "invalid_content_type"})
            return

        if content_length <= 0 or content_length > MAX_OG_IMAGE_BYTES:
            self.respond_json(413, {"ok": False, "error": "file_too_large"})
            return

        boundary = boundary_match.group(1).strip('"').encode("utf-8")
        body = self.rfile.read(content_length)
        fields, files = parse_multipart(body, boundary)

        videos = load_videos()
        video = next((v for v in videos if v["id"] == fields.get("id")), None)
        if not video:
            self.respond_json(404, {"ok": False, "error": "not_found"})
            return

        image_file = first_file(files, "thumbnail")
        if not image_file:
            self.respond_json(400, {"ok": False, "error": "missing_image_field"})
            return

        ext = os.path.splitext(image_file["filename"] or "")[1].lower()
        if ext not in OG_IMAGE_ALLOWED_EXTENSIONS:
            self.respond_json(400, {"ok": False, "error": "unsupported_file_type"})
            return

        # 拡張子が変わった場合に前のサムネイルが残らないよう、既存分は一旦削除する
        old_filename = video.get("og_image_filename")
        if old_filename:
            old_path = os.path.join(UPLOAD_DIR, old_filename)
            if os.path.exists(old_path):
                os.remove(old_path)

        new_filename = "thumb_" + video["id"] + ext
        with open(os.path.join(UPLOAD_DIR, new_filename), "wb") as f:
            f.write(image_file["content"])

        video["og_image_filename"] = new_filename
        save_videos(videos)

        self.respond_json(200, {"ok": True})

    def handle_reset_video_thumbnail(self):
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

        old_filename = video.get("og_image_filename")
        if old_filename:
            old_path = os.path.join(UPLOAD_DIR, old_filename)
            if os.path.exists(old_path):
                os.remove(old_path)
        video.pop("og_image_filename", None)
        save_videos(videos)

        self.respond_json(200, {"ok": True})

    def handle_upload(self):
        self._process_upload_request(owner_creator_id=None)

    def handle_creator_upload(self):
        creator_id = self.get_creator_id()
        self._process_upload_request(owner_creator_id=creator_id)

    def _process_upload_request(self, owner_creator_id):
        """multipart/form-dataを読んでバリデーションし、動画または画像ギャラリーを保存する。

        管理者本人のアップロード(/api/upload, owner_creator_id=None)と
        クリエイターのセルフアップロード(/api/creator/upload)の両方から使う共通処理。
        owner_creator_id はサーバー側(セッション)から決まる値のみを渡すこと
        (クライアントが送ってきた値をそのまま信用してはいけない)。
        """
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

        time_limit_enabled = fields.get("timeLimitEnabled") in ("1", "true", "on")
        content_type = fields.get("contentType") if fields.get("contentType") == "image" else "video"

        owner_fields = {}
        if owner_creator_id:
            owner_fields = {"owner_creator_id": owner_creator_id, "uploaded_at_epoch": time.time()}

        if content_type == "image":
            image_files = files.get("images") or []
            if not image_files:
                self.respond_json(400, {"ok": False, "error": "missing_image_field"})
                return
            if len(image_files) > MAX_IMAGES_PER_GALLERY:
                self.respond_json(400, {"ok": False, "error": "too_many_images"})
                return
            for image_file in image_files:
                ext = os.path.splitext(image_file["filename"] or "")[1].lower()
                if ext not in IMAGE_ALLOWED_EXTENSIONS:
                    self.respond_json(400, {"ok": False, "error": "unsupported_file_type"})
                    return
                if len(image_file["content"]) > MAX_IMAGE_BYTES:
                    self.respond_json(413, {"ok": False, "error": "file_too_large"})
                    return

            content_id = secrets.token_urlsafe(9)
            image_filenames = []
            for index, image_file in enumerate(image_files):
                ext = os.path.splitext(image_file["filename"] or "")[1].lower()
                stored_name = f"{content_id}_{index}{ext}"
                with open(os.path.join(UPLOAD_DIR, stored_name), "wb") as f:
                    f.write(image_file["content"])
                image_filenames.append(stored_name)

            original_filename = image_files[0]["filename"] or "upload"

            videos = load_videos()
            videos.append({
                "id": content_id,
                "content_type": "image",
                "image_filenames": image_filenames,
                "original_filename": original_filename,
                "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "time_limit_enabled": time_limit_enabled,
                "stats_token": secrets.token_urlsafe(9),
                **creator_fields,
                **owner_fields,
            })
            save_videos(videos)

            self.respond_json(200, {
                "ok": True,
                "id": content_id,
                "originalFilename": original_filename,
            })
            return

        video_file = first_file(files, "video")
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
            "content_type": "video",
            "stored_filename": stored_filename,
            "original_filename": original_filename,
            "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "time_limit_enabled": time_limit_enabled,
            "stats_token": secrets.token_urlsafe(9),
            **creator_fields,
            **owner_fields,
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

        self._delete_video_entry(video_id, video)
        self.respond_json(200, {"ok": True})

    def handle_creator_delete_content(self):
        creator_id = self.get_creator_id()
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
        # 他のクリエイターや管理者本人のコンテンツを消せないよう、所有者一致を必ず確認する
        if not video or video.get("owner_creator_id") != creator_id:
            self.respond_json(404, {"ok": False, "error": "not_found"})
            return

        self._delete_video_entry(video_id, video)
        self.respond_json(200, {"ok": True})

    def _delete_video_entry(self, video_id, video):
        """動画/画像ギャラリー本体・サムネイル・videos.json中のエントリを削除する共通処理。"""
        if video.get("content_type") == "image":
            for image_filename in video.get("image_filenames") or []:
                image_path = os.path.join(UPLOAD_DIR, image_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
        else:
            path = os.path.join(UPLOAD_DIR, video["stored_filename"])
            if os.path.exists(path):
                os.remove(path)

        thumbnail_filename = video.get("og_image_filename")
        if thumbnail_filename:
            thumbnail_path = os.path.join(UPLOAD_DIR, thumbnail_filename)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)

        videos = [v for v in load_videos() if v["id"] != video_id]
        save_videos(videos)

    def handle_set_og_image(self):
        content_type_header = self.headers.get("Content-Type", "")
        boundary_match = re.search(r"boundary=(.+)", content_type_header)
        content_length = int(self.headers.get("Content-Length", 0))

        if not content_type_header.startswith("multipart/form-data") or not boundary_match:
            self.respond_json(400, {"ok": False, "error": "invalid_content_type"})
            return

        if content_length <= 0 or content_length > MAX_OG_IMAGE_BYTES:
            self.respond_json(413, {"ok": False, "error": "file_too_large"})
            return

        boundary = boundary_match.group(1).strip('"').encode("utf-8")
        body = self.rfile.read(content_length)
        _, files = parse_multipart(body, boundary)

        image_file = first_file(files, "ogImage")
        if not image_file:
            self.respond_json(400, {"ok": False, "error": "missing_image_field"})
            return

        ext = os.path.splitext(image_file["filename"] or "")[1].lower()
        if ext not in OG_IMAGE_ALLOWED_EXTENSIONS:
            self.respond_json(400, {"ok": False, "error": "unsupported_file_type"})
            return

        # 拡張子が変わった場合に前の差し替え画像が残らないよう、既存分は一旦削除する
        config = load_config()
        old_filename = config.get("og_image_filename")
        if old_filename:
            old_path = os.path.join(UPLOAD_DIR, old_filename)
            if os.path.exists(old_path):
                os.remove(old_path)

        new_filename = "og-image" + ext
        with open(os.path.join(UPLOAD_DIR, new_filename), "wb") as f:
            f.write(image_file["content"])

        config["og_image_filename"] = new_filename
        save_config(config)

        self.respond_json(200, {"ok": True})

    def handle_reset_og_image(self):
        config = load_config()
        old_filename = config.get("og_image_filename")
        if old_filename:
            old_path = os.path.join(UPLOAD_DIR, old_filename)
            if os.path.exists(old_path):
                os.remove(old_path)
        config["og_image_filename"] = None
        save_config(config)

        self.respond_json(200, {"ok": True})

    # ---------- クリエイター(女の子)アカウント: 招待・登録・ログイン ----------
    def handle_serve_join_page(self, invite_token):
        creators = load_creators()
        creator = find_creator_by_invite_token(creators, invite_token)

        with open(os.path.join(BASE_DIR, "creator-join.html"), "r", encoding="utf-8") as f:
            page_html = f.read()

        state = {"valid": bool(creator), "token": invite_token}
        page_html = page_html.replace("{{INVITE_STATE_JSON}}", json.dumps(state))

        body = page_html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def handle_creator_register(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        invite_token = data.get("inviteToken") or ""
        password = data.get("password") or ""
        if len(password) < MIN_CREATOR_PASSWORD_LENGTH:
            self.respond_json(400, {"ok": False, "error": "password_too_short"})
            return

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator_by_invite_token(creators, invite_token)
            if not creator:
                self.respond_json(400, {"ok": False, "error": "invalid_invite"})
                return

            salt_hex, hash_hex = hash_password(password)
            creator["password_salt"] = salt_hex
            creator["password_hash"] = hash_hex
            creator["status"] = "active"
            creator["activated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_creators(creators)
            login_code = creator["login_code"]
            creator_id = creator["id"]

        token = self.create_creator_session(creator_id)
        self.send_response(200)
        self.set_creator_session_cookie(token)
        payload = json.dumps({"ok": True, "loginCode": login_code}).encode("utf-8")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_creator_login(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        login_code = (data.get("loginCode") or "").strip().upper()
        password = data.get("password") or ""

        creators = load_creators()
        creator = find_creator_by_login_code(creators, login_code)
        # ログインコード・パスワードのどちらが間違っていたかは区別せず返す
        if not creator or not verify_password(password, creator.get("password_salt"), creator.get("password_hash")):
            self.respond_json(401, {"ok": False, "error": "invalid_credentials"})
            return

        token = self.create_creator_session(creator["id"])
        self.send_response(200)
        self.set_creator_session_cookie(token)
        payload = json.dumps({"ok": True}).encode("utf-8")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_creator_logout(self):
        self.destroy_creator_session()
        self.send_response(200)
        self.clear_creator_session_cookie()
        payload = json.dumps({"ok": True}).encode("utf-8")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_list_creator_content(self):
        creator_id = self.get_creator_id()
        config = load_config()
        videos = sorted(load_videos(), key=lambda v: v["uploaded_at"], reverse=True)
        own_videos = [v for v in videos if v.get("owner_creator_id") == creator_id]
        body = [
            {
                "id": v["id"],
                "originalFilename": v["original_filename"],
                "uploadedAt": v["uploaded_at"],
                "contentType": v.get("content_type", "video"),
                "imageCount": len(v.get("image_filenames") or []) if v.get("content_type") == "image" else None,
                "timeLimit": get_time_limit_status(v),
                "viewCount": v.get("view_count", 0),
                "pointsStatus": get_points_status(v, config),
            }
            for v in own_videos
        ]
        self.respond_json(200, body)

    def handle_get_own_creator_info(self):
        creator_id = self.get_creator_id()
        creators = load_creators()
        creator = find_creator(creators, creator_id)
        if not creator:
            self.respond_json(404, {"ok": False, "error": "not_found"})
            return

        self.respond_json(200, {
            "ok": True,
            "pointsBalance": creator.get("points_balance", 0),
            "redemptionRequests": [
                serialize_redemption_request(r) for r in creator.get("redemption_requests", [])
            ],
        })

    def handle_creator_request_redemption(self):
        creator_id = self.get_creator_id()
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        points = data.get("points")
        if not isinstance(points, int) or isinstance(points, bool) or points <= 0:
            self.respond_json(400, {"ok": False, "error": "invalid_points"})
            return

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return
            if points > creator.get("points_balance", 0):
                self.respond_json(400, {"ok": False, "error": "insufficient_balance"})
                return

            creator["points_balance"] -= points
            creator.setdefault("redemption_requests", []).append({
                "id": secrets.token_urlsafe(9),
                "points": points,
                "status": "pending",
                "requested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "fulfilled_at": None,
            })
            save_creators(creators)
            new_balance = creator["points_balance"]

        self.respond_json(200, {"ok": True, "pointsBalance": new_balance})

    # ---------- クリエイター(女の子)アカウント: 管理者側の操作 ----------
    def handle_list_creators(self):
        creators = load_creators()
        body = [
            {
                "id": c["id"],
                "displayName": c.get("display_name"),
                "status": c["status"],
                "loginCode": c.get("login_code"),
                "pointsBalance": c.get("points_balance", 0),
                "redemptionRequests": [serialize_redemption_request(r) for r in c.get("redemption_requests", [])],
                "invitedAt": c.get("invited_at"),
                "activatedAt": c.get("activated_at"),
            }
            for c in sorted(creators, key=lambda c: c.get("invited_at", ""), reverse=True)
        ]
        self.respond_json(200, body)

    def handle_creators_invite(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length < 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            raw = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            data = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        display_name = (data.get("displayName") or "").strip()[:40]

        with CREATORS_LOCK:
            creators = load_creators()
            creator = {
                "id": secrets.token_urlsafe(9),
                "display_name": display_name or None,
                "invite_token": secrets.token_urlsafe(16),
                "login_code": secrets.token_hex(4).upper(),
                "status": "invited",
                "password_salt": None,
                "password_hash": None,
                "points_balance": 0,
                "points_history": [],
                "redemption_requests": [],
                "invited_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "activated_at": None,
            }
            creators.append(creator)
            save_creators(creators)

        self.respond_json(200, {
            "ok": True,
            "id": creator["id"],
            "inviteUrl": PUBLIC_SITE_URL + "/join/" + creator["invite_token"],
            "loginCode": creator["login_code"],
        })

    def handle_creators_approve_points(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        content_id = data.get("contentId")

        with CREATORS_LOCK:
            config = load_config()
            videos = load_videos()
            video = next((v for v in videos if v["id"] == content_id), None)
            if not video:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            # クライアント側の表示だけを信用せず、サーバー側で承認可能な状態か再検証する
            status = get_points_status(video, config)
            if not status or status["state"] != "eligible_pending_approval":
                self.respond_json(400, {"ok": False, "error": "not_eligible"})
                return

            amount = config.get("points_per_upload", DEFAULT_POINTS_PER_UPLOAD)

            creators = load_creators()
            creator = find_creator(creators, video.get("owner_creator_id"))
            if not creator:
                self.respond_json(404, {"ok": False, "error": "creator_not_found"})
                return

            creator["points_balance"] = creator.get("points_balance", 0) + amount
            creator.setdefault("points_history", []).append({
                "delta": amount,
                "reason": "upload_approved",
                "content_id": content_id,
                "at": time.strftime("%Y-%m-%d %H:%M:%S"),
            })
            save_creators(creators)

            video["points_awarded"] = True
            video["points_awarded_amount"] = amount
            video["points_awarded_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_videos(videos)

        self.respond_json(200, {"ok": True, "amount": amount})

    def handle_creators_adjust_points(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        creator_id = data.get("creatorId")
        delta = data.get("delta")
        note = (data.get("note") or "").strip()[:200]
        if not isinstance(delta, (int, float)) or isinstance(delta, bool) or delta == 0:
            self.respond_json(400, {"ok": False, "error": "invalid_delta"})
            return

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            creator["points_balance"] = creator.get("points_balance", 0) + delta
            creator.setdefault("points_history", []).append({
                "delta": delta,
                "reason": "manual_adjustment: " + note if note else "manual_adjustment",
                "content_id": None,
                "at": time.strftime("%Y-%m-%d %H:%M:%S"),
            })
            save_creators(creators)
            new_balance = creator["points_balance"]

        self.respond_json(200, {"ok": True, "pointsBalance": new_balance})

    def handle_creators_fulfill_redemption(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        creator_id = data.get("creatorId")
        request_id = data.get("requestId")

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            request = next((r for r in creator.get("redemption_requests", []) if r["id"] == request_id), None)
            if not request or request["status"] != "pending":
                self.respond_json(400, {"ok": False, "error": "invalid_request_state"})
                return

            request["status"] = "fulfilled"
            request["fulfilled_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_creators(creators)

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
