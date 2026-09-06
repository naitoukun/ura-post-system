"""
シークレット・ビューア: 開発用の簡易バックエンド。

- GET  /                通常は動画アンロックページ(index.html)。共有リンク専用にするため
                        一覧等は置かず、常にindex.htmlを返す。og:image等は?vに応じて動的に差し込む。
                        例外: 管理者ログイン中に?v=無しでアクセスした場合だけ、一般公開に向けた
                        プレビューとして新着投稿一覧(top.html)を返す
- GET  /index.html      動画アンロックページに直接アクセス(?v=無しでも常にアプリを表示。top.htmlへの切り替えは無し)
- GET  /api/top-posts   TOPページ(top.html)用の新着投稿一覧・ピックアップ枠(JSON、offset/limitでページング)※要ログイン
- GET  /robots.txt      クローラー向け設定(静的ファイル)
- GET  /sitemap.xml     検索エンジン向けの投稿URL一覧(公開・認証不要。TOPページが一般公開されるまでは実質未使用)
- GET  /admin           管理ページ。未ログインならログイン画面、ログイン済みならadmin.html
- GET  /admin/totp-setup  TOTPシークレットをQRコード化するツール（サーバーの実際の値は扱わない）
- GET  /video-merge-tool  クリエイター向け動画結合ツール（ブラウザ内完結、ログイン不要）
- GET  /terms           利用規約
- GET  /disclaimer      免責事項
- GET  /copyright-policy 著作権ポリシー・2257条コンプライアンス表明（ExoClick審査要件）
- GET  /creator-terms    クリエイター向け利用規約（登録時に同意が必須）
- GET  /recruit          クリエイター募集用のPRページ（ログイン不要、サイト内の他ページへのリンク無し）
- GET  /og-image        SNSシェア時のOGP/Twitterカード用サイト共通画像（管理画面で差し替え可能。未設定時は同梱の既定画像）
- GET  /favicon.ico /favicon-32x32.png /apple-touch-icon.png  ファビコン一式（静的ファイル）
- GET  /thumb/<id>      動画ごとに設定した個別サムネイル（未設定ならそもそも参照されない）
- GET  /stats/<token>   クリエイター向けの視聴データページ（ログイン不要。共有リンクとは別トークン）
- GET  /all-posts       現在公開中の全投稿URL一覧ページ（サイト内のどこからもリンクしていない。ログイン不要）
- GET  /api/all-posts   上記ページ用のJSON（削除済み・24時間限定で期限切れの投稿は除外）
- POST /api/login       パスフレーズ+TOTPコードでログインし、セッションCookieを発行
- POST /api/logout      ログアウト（セッションを破棄）
- GET  /api/videos      アップロード済み動画の一覧 (JSON) ※要ログイン
- GET  /resolve-video   指定した(または最新の)コンテンツのメタ情報 (JSON。動画/画像共通)
- GET  /video/<id>      指定した動画の配信（Range対応 = シーク可能。画像ギャラリーには404）
- GET  /image/<id>/<index>  画像ギャラリーのうち指定した1枚の配信
- POST /api/upload      動画または画像ギャラリーのアップロード（multipart/form-data。
                        contentType=video/image。新規IDを発行）※要ログイン
- POST /api/videos/delete  動画の削除（JSON）※要ログイン
- POST /api/videos/set-ads  動画/画像ごとの広告個別設定の更新・解除（JSON）※要ログイン
- POST /api/videos/set-time-limit  動画ごとの24時間限定設定の有効/無効切り替え（JSON）※要ログイン
- POST /api/videos/set-cta  動画ごとの出演者名+Fantia URLの更新・解除（JSON）※要ログイン
- POST /api/videos/set-cta-text  投稿ごとの誘導ボタン文言・リンク先の直接個別指定・解除（JSON）※要ログイン
- POST /api/videos/set-thumbnail  動画ごとの個別サムネイル画像の設定（multipart/form-data）※要ログイン
- POST /api/videos/reset-thumbnail  動画ごとの個別サムネイルを解除しサイト既定画像に戻す（JSON）※要ログイン
- GET  /site-config     プレミアムリンク・誘導ボタンの文字・既定の広告設定等のサイト設定 (JSON)
- POST /api/set-premium-link  プレミアムリンク・誘導ボタンの文字の更新（JSON）※要ログイン
- POST /api/set-content-page-ad  視聴ページ(動画・画像共通)のバナー広告ゾーンID(PC用/スマホ用)の更新・解除（JSON）※要ログイン
- POST /api/set-ads     既定（個別設定が無い場合用）の動画側/画像側の広告の更新（JSON）※要ログイン
- POST /api/set-points  クリエイターへのポイント付与ルール（動画/画像それぞれのアップロード1件の付与量・24時間以内の最低閲覧数・ボーナス閲覧数閾値とボーナス付与量）の既定値更新（JSON）※要ログイン
- POST /api/set-og-image  OGP画像の差し替え（multipart/form-data）※要ログイン
- POST /api/reset-og-image  OGP画像を同梱の既定画像に戻す（JSON）※要ログイン
- POST /api/dmca-report  著作権侵害の申し立てフォームからの送信（/copyright-policy用。公開・ログイン不要。JSON）
- GET  /api/dmca-reports  著作権侵害の申し立て一覧（JSON）※要ログイン
- POST /api/dmca-reports/resolve  著作権侵害の申し立てを対応済みにする（JSON）※要ログイン

クリエイター(女の子)アカウント。管理者(上記の/api/login)とは完全に別のセッション/Cookieで扱う:
- GET  /join/<invite_token>  招待受諾ページ。パスワードを設定してアカウントを有効化する
- GET  /creator          クリエイター向けダッシュボード。未ログインならログイン画面
- POST /api/creator/register  招待トークン+パスワードで登録し、セッションCookieを発行
- POST /api/creator/magic-link-enter  ライト版(パスワード無し)。招待トークンだけで毎回セッションを発行(初回のみ規約同意が必要)
- POST /api/creator/login  ログインコード+パスワードでログイン
- POST /api/creator/logout
- GET  /api/creator/content  自分がアップロードしたコンテンツの一覧(JSON、ポイント状況込み)※要クリエイターログイン
- GET  /api/creators/me  自分のポイント残高・交換申請履歴(JSON)※要クリエイターログイン
- POST /api/creator/upload  動画/画像ギャラリーのセルフアップロード（動画は20秒以上・画像は5枚以上が必須）※要クリエイターログイン
- POST /api/creator/content/delete  自分のコンテンツの削除（所有者チェック有り）※要クリエイターログイン
- POST /api/creator/content/set-cta-text  自分の投稿の誘導ボタン文言・リンク先の個別指定・解除（所有者チェック有り、JSON）※要クリエイターログイン
- POST /api/creator/set-default-cta  自分の全投稿に使う既定の誘導ボタン文言・リンク先の設定・解除（投稿ごとの個別指定があればそちらが優先、JSON）※要クリエイターログイン
- POST /api/creator/request-redemption  貯まったポイントのギフト券交換を申請（最低申請ポイント数あり、JSON）※要クリエイターログイン
- POST /api/creator/submit-id  年齢確認用の身分証提出・再提出（multipart/form-data）※要クリエイターログイン
- GET  /api/creators     クリエイター一覧＋ポイント残高＋交換申請一覧（JSON）※要ログイン(管理者)
- POST /api/creators/invite  招待URL+ログインコードを新規発行（JSON）※要ログイン(管理者)
- POST /api/creators/approve-points  投稿1件を承認しポイント付与（サーバー側で状態を再検証）※要ログイン(管理者)
- POST /api/creators/approve-all-points  承認待ちの投稿を全件まとめて承認しポイント付与（JSON、パラメータ無し）※要ログイン(管理者)
- POST /api/creators/adjust-points  ポイント残高の手動調整（返金・是正用）※要ログイン(管理者)
- POST /api/creators/fulfill-redemption  ギフト券交換申請を対応済みにする（JSON）※要ログイン(管理者)
- POST /api/creators/set-points-override  クリエイターごとの動画/画像付与ポイントの個別上書き（null=サイト既定値を使用）（JSON）※要ログイン(管理者)
- POST /api/creators/set-contact  クリエイターの連絡先リンク(SNS等)の設定・更新・解除（JSON）※要ログイン(管理者)
- POST /api/creators/reset-password  クリエイターのパスワードを強制再発行(新パスワードを一度だけ返す)（JSON）※要ログイン(管理者)
- POST /api/creators/impersonate  管理者がパスワードを知らずにそのクリエイターとしてログインする(なりすまし。監査ログに記録)（JSON）※要ログイン(管理者)
- GET  /api/creators/id-document  提出された身分証の画像/PDFの配信（機微情報のため管理者のみ）※要ログイン(管理者)
- POST /api/creators/approve-id  提出された身分証を承認し、セルフアップロードを解禁する（JSON）※要ログイン(管理者)
- POST /api/creators/reject-id  提出された身分証を却下する（理由は任意入力、JSON）※要ログイン(管理者)
- POST /api/creators/delete  クリエイターアカウントの削除（投稿済みの全コンテンツも連鎖削除）（JSON）※要ログイン(管理者)

※「要ログイン」の操作は、/api/login で発行されたセッションCookieが無いと401になる。
※「要クリエイターログイン」の操作は、/api/creator/login等で発行された別のセッションCookieが無いと401になる。

環境変数:
  - PORT              待ち受けポート（Renderが自動設定。ローカルでは未設定なら5173）
  - UPLOAD_PASSPHRASE 管理者ログイン用のパスフレーズ（1つ目の要素）
  - TOTP_SECRET       管理者ログイン用の2段階認証シークレット（Base32。2つ目の要素）
  - UPLOAD_DIR        動画・設定ファイルの保存先（Renderでは永続ディスクのマウント先を指定）
  - PUBLIC_SITE_URL   OGP画像等の絶対URL組み立てに使う公開ドメイン（未設定時は https://ura-post.com）
  - SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD/NOTIFY_EMAIL_TO
                      管理者への通知メール(新規投稿・ポイント交換申請・新規登録・身分証提出・
                      DMCA申し立て)用のSMTP設定。SMTP_USER/SMTP_PASSWORD未設定なら通知は送られない

TODO: 本番運用前に以下を必ず対応すること
  - UPLOAD_PASSPHRASE / TOTP_SECRET を推測されにくい値に変更する
    （Renderの環境変数として設定し、コードには書かない）
  - HTTPS 経由での運用（Renderは自動でHTTPS化されるため、Render以外にデプロイする場合のみ要対応）
  - アップロードファイルのウイルススキャン等、必要な安全対策の追加
"""

import base64
import datetime
import hmac
import hashlib
import html
import io
import json
import mimetypes
import os
import random
import re
import secrets
import smtplib
import struct
import threading
import time
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs

from PIL import Image, ImageOps

# 生年月日のような「承認後も保持し続ける個人情報」の暗号化と、アップロード画像の
# Exif除去(下記strip_image_metadata参照)にのみ外部ライブラリを使う。他は引き続き
# 標準ライブラリのみで完結させている。
from cryptography.fernet import Fernet, InvalidToken

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

# クリエイターの生年月日(年齢確認の承認後も保持する個人情報)を暗号化して保存するための鍵。
# 本番ではVPSの環境変数 PII_ENCRYPTION_KEY で上書きすること(systemdのEnvironment=で設定済み)。
# 未設定時はプロセス起動のたびにランダムな鍵を生成する(固定のフォールバック値をコードに
# 埋め込むと、その値がgit履歴に残り続け、環境変数の設定を忘れた場合に暗号化が無意味になる
# ため)。ローカル動作確認では、再起動するとそれまで保存したPIIが復号できなくなる点に注意。
PII_ENCRYPTION_KEY = os.environ.get("PII_ENCRYPTION_KEY") or Fernet.generate_key().decode("ascii")
_pii_fernet = Fernet(PII_ENCRYPTION_KEY.encode("ascii"))


def encrypt_pii(plaintext):
    """個人情報の文字列をFernet(AES-CBC+HMAC)で暗号化し、保存用の文字列として返す。"""
    return _pii_fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_pii(token):
    """encrypt_piiで暗号化した文字列を復号する。改ざん・鍵不一致等で失敗した場合はNoneを返す。"""
    if not token:
        return None
    try:
        return _pii_fernet.decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        return None

SESSION_COOKIE_NAME = "sv_session"
SESSION_DURATION_SECONDS = 4 * 60 * 60  # 4時間
# 単一プロセス前提のシンプルな実装のため、セッションはメモリ上にのみ保持する
# （サーバー再起動でログイン状態はリセットされる）。
SESSIONS = {}

# ログイン試行のブルートフォース対策。管理者ログイン(/api/login)とクリエイターログイン
# (/api/creator/login)の両方に共通で使う、IPアドレス単位のシンプルな回数制限。
# scope("admin"/"creator")ごとに別カウントにする(管理者への攻撃でクリエイターまで
# ロックされる、といった巻き添えを防ぐため)。
LOGIN_ATTEMPTS_LOCK = threading.Lock()
LOGIN_ATTEMPTS = {}  # (scope, ip) -> {"count": int, "window_started_at": float, "locked_until": float|None}
MAX_LOGIN_ATTEMPTS = 5
LOGIN_FAILURE_WINDOW_SECONDS = 15 * 60
LOGIN_LOCKOUT_SECONDS = 15 * 60


def get_client_ip(handler):
    """Nginxリバースプロキシ経由の実クライアントIPを取得する。

    アプリはファイアウォールでポート8000への直接外部アクセスを塞いでいるため、
    ここに届くリクエストは必ずNginx経由であり、X-Real-IP/X-Forwarded-Forは
    Nginx自身が上書き設定した信頼できる値になる。
    """
    real_ip = handler.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    forwarded = handler.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return handler.client_address[0]


def is_same_site_referer(handler):
    """/resolve-videoのview_count等、副作用のある処理を実行してよいリクエストかを判定する。

    正規の流れでは、ブラウザがindex.htmlを読み込んだ後にそのページ自身のJSが
    fetch('/resolve-video?...')を呼ぶため、Refererは常にura-post.com自身になる。
    他サイトに埋め込まれた<iframe>やJS(fetch(..., {mode:'no-cors'})等)からの
    呼び出しはReferer(有れば)が別ドメインになるため、そこだけ弾いて水増しを防ぐ。
    Refererを送らないブラウザ・プライバシー拡張機能もあるため、Referer自体が
    無い場合は(誤検知で正規ユーザーの分まで弾かないよう)許可する側に倒す。
    """
    referer = handler.headers.get("Referer")
    if not referer:
        return True
    return referer.startswith(PUBLIC_SITE_URL)


def _prune_expired_login_attempts(now):
    expired_keys = [
        key for key, entry in LOGIN_ATTEMPTS.items()
        if not entry.get("locked_until") and now - entry["window_started_at"] > LOGIN_FAILURE_WINDOW_SECONDS
    ]
    for key in expired_keys:
        del LOGIN_ATTEMPTS[key]


def is_login_locked_out(scope, ip):
    """ロック中なら (True, 残り秒数) を、そうでなければ (False, 0) を返す。"""
    key = (scope, ip)
    now = time.time()
    with LOGIN_ATTEMPTS_LOCK:
        entry = LOGIN_ATTEMPTS.get(key)
        if not entry or not entry.get("locked_until"):
            return False, 0
        if entry["locked_until"] <= now:
            del LOGIN_ATTEMPTS[key]
            return False, 0
        return True, int(entry["locked_until"] - now)


def record_login_failure(scope, ip):
    key = (scope, ip)
    now = time.time()
    with LOGIN_ATTEMPTS_LOCK:
        entry = LOGIN_ATTEMPTS.get(key)
        if not entry or now - entry["window_started_at"] > LOGIN_FAILURE_WINDOW_SECONDS:
            entry = {"count": 0, "window_started_at": now, "locked_until": None}
        entry["count"] += 1
        if entry["count"] >= MAX_LOGIN_ATTEMPTS:
            entry["locked_until"] = now + LOGIN_LOCKOUT_SECONDS
        LOGIN_ATTEMPTS[key] = entry
        _prune_expired_login_attempts(now)


def record_login_success(scope, ip):
    key = (scope, ip)
    with LOGIN_ATTEMPTS_LOCK:
        LOGIN_ATTEMPTS.pop(key, None)


# 視聴回数の水増し対策。同一IP+同一コンテンツからのアクセスは、直近24時間以内なら
# 1回しかカウントしない(ページを何度再読み込みしても閲覧数が伸び続けないようにする)。
# ログイン試行制限と同じくメモリ上のみで管理する簡易な仕組みで、サーバー再起動で
# リセットされるが、閲覧数自体が既に「概算」である前提の機能なのでこれで十分とする。
VIEW_DEDUP_LOCK = threading.Lock()
VIEW_DEDUP = {}  # (video_id, ip) -> last_counted_epoch
VIEW_DEDUP_WINDOW_SECONDS = 24 * 60 * 60


def should_count_view(video_id, ip):
    """このIPからのこのコンテンツへのアクセスを、閲覧数として数えるべきかを返す。

    数えるべき(=直近のウィンドウ内に記録が無かった)場合はTrueを返し、同時に記録を更新する。
    """
    key = (video_id, ip)
    now = time.time()
    with VIEW_DEDUP_LOCK:
        last_counted_at = VIEW_DEDUP.get(key)
        if last_counted_at is not None and now - last_counted_at < VIEW_DEDUP_WINDOW_SECONDS:
            return False
        VIEW_DEDUP[key] = now
        expired_keys = [k for k, t in VIEW_DEDUP.items() if now - t > VIEW_DEDUP_WINDOW_SECONDS]
        for k in expired_keys:
            del VIEW_DEDUP[k]
        return True


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


def strip_image_metadata(content, ext):
    """スマホ撮影時に埋め込まれるExif情報(GPS位置情報・撮影日時・機種名等)を除去する。

    向き(Orientationタグ)だけは画素に焼き込んでから捨てる(単純に除去すると
    横向き撮影の画像が縦のまま表示されてしまうため)。GIFはアニメーションの
    コマが壊れる恐れがあり、かつそもそもExifを持つ形式ではないため対象外とする。

    戻り値はNoneまたは処理後のバイト列。画像として読めなかった場合はNoneを返す
    (拡張子だけ画像で中身が画像でないファイルをそのまま保存しないよう、
    呼び出し側でアップロード自体を拒否すること。元のバイト列で「失敗を握りつぶして
    そのまま保存」はしない)。
    """
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        return content
    try:
        img = Image.open(io.BytesIO(content))
        img.load()
        if getattr(img, "is_animated", False):
            return content
        img = ImageOps.exif_transpose(img)
        output = io.BytesIO()
        if ext in (".jpg", ".jpeg"):
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output, format="JPEG", quality=92)
        elif ext == ".png":
            img.save(output, format="PNG")
        else:
            img.save(output, format="WEBP", quality=92)
        return output.getvalue()
    except Exception:
        print("WARNING: strip_image_metadata failed to parse upload as image:", ext)
        return None

# クリエイターの年齢確認用の身分証提出。18歳未満のコンテンツを扱わないための本人確認であり、
# 承認(id_verification_status == "approved")されるまでセルフアップロードはできない。
# 提出物は本人確認書類という機微情報のため、管理者のみが閲覧できる専用ルートでのみ配信する
# (静的ファイルとして誰でも見れる場所には絶対に置かない)。
ID_DOCUMENT_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
MAX_ID_DOCUMENT_BYTES = 10 * 1024 * 1024  # 10MB
MAX_ID_REJECTION_REASON_LENGTH = 300
# 書類の種類は管理者が承認時に写真と付け合わせて確認するための表示用ラベル。
# サーバー側の値の妥当性チェック以外の意味は持たせない(自己申告のまま保持する)。
ID_DOCUMENT_TYPES = {
    "drivers_license": "運転免許証",
    "passport": "パスポート",
    "mynumber_card": "マイナンバーカード",
    "residence_card": "在留カード",
    "other": "その他の公的書類",
}
MIN_CREATOR_AGE_YEARS = 18


def validate_id_document_type(value):
    return value if value in ID_DOCUMENT_TYPES else None


def validate_date_of_birth(value):
    """"YYYY-MM-DD"形式かつ18歳以上に相当する日付であることを検証する。不正ならNoneを返す。"""
    if not value or not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return None
    try:
        dob = datetime.date.fromisoformat(value)
    except ValueError:
        return None
    today = datetime.date.today()
    if dob > today:
        return None
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < MIN_CREATOR_AGE_YEARS or age > 120:
        return None
    return value


def calculate_age(date_of_birth_str):
    try:
        dob = datetime.date.fromisoformat(date_of_birth_str)
    except (ValueError, TypeError):
        return None
    today = datetime.date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
# og:image等はSNS側のクローラーが絶対URLで取得するため、公開ドメインを固定で持っておく。
# 別ドメインで動作確認する場合は環境変数で上書きできるようにしておく。
PUBLIC_SITE_URL = os.environ.get("PUBLIC_SITE_URL", "https://ura-post.com")

# 管理者への通知メール(新規投稿・ポイント交換申請・新規登録・身分証提出・DMCA申し立て)用のSMTP設定。
# SMTP_USER/SMTP_PASSWORDが未設定(空)の場合は通知メール機能そのものが無効になる
# (開発環境やまだ設定していない本番環境で、送信エラーが表示・ログに出続けないようにするため)。
# GmailのSMTPを使う場合、SMTP_PASSWORDにはGoogleアカウントの「アプリパスワード」を使う
# (通常のログインパスワードではない。2段階認証を有効にした上でGoogleアカウント設定から発行する)。
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
NOTIFY_EMAIL_TO = os.environ.get("NOTIFY_EMAIL_TO", "naitoukun.n@gmail.com")


def send_notification_email(subject, body):
    """管理者への通知メールを(設定済みなら)非同期で送信する。

    SMTP未設定なら何もしない。メール送信の失敗・遅延が本来の処理(投稿・申請等の
    レスポンス)を止めないよう、必ず例外を握りつぶしたうえで別スレッドから送る。
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        return

    def _send():
        try:
            msg = EmailMessage()
            msg["Subject"] = "[ura-post] " + subject
            msg["From"] = SMTP_USER
            msg["To"] = NOTIFY_EMAIL_TO
            msg.set_content(body)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
                smtp.starttls()
                smtp.login(SMTP_USER, SMTP_PASSWORD)
                smtp.send_message(msg)
        except Exception:
            pass

    threading.Thread(target=_send, daemon=True).start()


# 「URL発行時」ではなく「誰かが初めてそのURLにアクセスした時刻」を起点にするため、
# 動画ごとに first_accessed_at (初回アクセス時刻) を記録し、そこから24時間で期限切れにする。
TIME_LIMIT_SECONDS = 24 * 60 * 60

DEFAULT_PREMIUM_LINK = "https://fantia.jp/"
DEFAULT_PREMIUM_BUTTON_TEXT = "【ファン限定】Fantia特設ページへ"
MAX_BUTTON_TEXT_LENGTH = 60
MAX_CTA_LINK_URL_LENGTH = 500

# 動画ごとに「出演者名」+「本人のFantia URL」を設定すると、誘導ボタンの文字を
# 「{name}を応援する」に、リンク先をそのURLに個別上書きできる。
# 両方セットされていない場合は、既定(DEFAULT_PREMIUM_LINK等)にフォールバックする。
CREATOR_BUTTON_TEXT_TEMPLATE = "{name}を応援する"
MAX_CREATOR_NAME_LENGTH = 20

# クリエイター(女の子)ごとの連絡先リンク(SNS等)。管理者がポイント交換等の連絡を
# 素早く取れるようにするための、管理画面上でのみ使うメモ用途のリンク。
MAX_CONTACT_URL_LENGTH = 500

# サイト全体共通の広告設定。ad1は動画アンロック用(Google IMA SDKに渡すVASTタグURL)、
# ad2は画像ギャラリーアンロック用(ExoClick AdProviderのゾーンID。空欄なら既定のゾーンIDを使う)。
# 以前はA/Bランダム表示だったが、動画/画像で完全に振り分ける仕様に変更したため重みは廃止した。
DEFAULT_ADS = [
    {"id": "ad1", "label": "動画側の広告", "ad_code": "https://s.magsrv.com/v1/vast.php?idz=5967416"},
    {"id": "ad2", "label": "画像側の広告", "ad_code": ""},
]
MAX_AD_LABEL_LENGTH = 40
MAX_AD_CODE_LENGTH = 2000

# アンロック後の視聴ページ(動画再生ページ・画像ページ両方)に常に表示するバナー広告。
# 上記ad1/ad2(アンロック待ちの間だけ表示するゲート広告)とは別枠で、コンテンツ種別を問わず
# 同じゾーンIDを使う。PC/スマホでゾーンIDを出し分けられるよう別々に持つ。空欄にすると非表示になる。
DEFAULT_CONTENT_PAGE_AD_ZONE_ID_MOBILE = "5968878"
DEFAULT_CONTENT_PAGE_AD_ZONE_ID_DESKTOP = "5968882"
MAX_CONTENT_PAGE_AD_ZONE_ID_LENGTH = 100

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")

os.makedirs(UPLOAD_DIR, exist_ok=True)


def json_for_script(value):
    """<script>タグの中にそのまま埋め込んでも安全なJSON文字列を返す。

    json.dumpsは"<"をエスケープしないため、値の中に"</script>"のような文字列が
    含まれていると、そこでscriptタグが閉じられHTMLとして解釈されてしまう
    (JSON-in-scriptの定番の穴)。"<"だけ\\u003cに変換して防ぐ。
    """
    return json.dumps(value).replace("<", "\\u003c")

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
# 付与ポイントは動画/画像で別々に設定でき、さらにクリエイターごとに個別上書きもできる
# (creators.json側にpoints_per_video_upload/points_per_image_uploadがあればそちらを優先)。
# ここにあるのはそのどちらも無い場合の、サイト全体の既定値。管理画面(ポイント設定)で変更可能。
POINTS_WINDOW_SECONDS = 24 * 60 * 60
DEFAULT_POINTS_PER_VIDEO_UPLOAD = 100
DEFAULT_POINTS_PER_IMAGE_UPLOAD = 100
DEFAULT_POINTS_VIEW_THRESHOLD = 10

# 24時間以内の閲覧数がボーナス閾値(既定1000)を超えた投稿には、通常の付与ポイントに加えて
# ボーナスポイントを上乗せする。判定は通常の閾値判定と同じく「24時間経過後の時点での
# 累計閲覧数」で行う(厳密に24時間"以内"の閲覧だけを数えているわけではない点も既存の
# 閾値判定と同じ)。ボーナス額は既定0(未設定)なので、管理画面で金額を設定するまでは
# 何も変わらない(意図しない支払いが発生しないようにするための安全な既定値)。
DEFAULT_BONUS_VIEW_THRESHOLD = 1000
DEFAULT_BONUS_POINTS_VIDEO = 0
DEFAULT_BONUS_POINTS_IMAGE = 0

# ギフト券交換は最低このポイント数から申請可能(既定150000pt = 1500円分。100pt=1円で換算)。
# サイト全体共通、管理画面(ポイント設定)で変更可能。
DEFAULT_MIN_REDEMPTION_POINTS = 150000

# ポイント→円換算レート(100pt=1円)。DBには常に整数ポイントのみを保存し、
# 円換算は表示のたびにこのレートで都度計算する(換算値自体は保存しない)。
POINTS_PER_YEN = 100


def points_to_yen(points):
    return points // POINTS_PER_YEN

# 低品質・水増し目的の投稿を防ぐための最低ライン。クリエイターのセルフアップロードにのみ適用し
# (管理者自身の/api/uploadには適用しない)、満たさない場合はアップロード自体を拒否する。
MIN_CREATOR_VIDEO_DURATION_SECONDS = 20
MIN_CREATOR_IMAGE_COUNT = 5

# TOPページ(top.html)の「ピックアップ」枠(新着順とは別に無作為抽出する投稿数)。
# 埋もれ対策(投稿頻度が低い子の投稿が新着一覧から実質見えなくなるのを防ぐ)の一環。
MAX_TOP_PICKUP_COUNT = 6

# TOPページの新着一覧(/api/top-posts)のページングの1ページあたり件数。
# 投稿数が増えても1回のレスポンス/初回表示が肥大化しないようにする。
TOP_POSTS_PAGE_SIZE = 20
MAX_TOP_POSTS_PAGE_SIZE = 50

# creators.json への書き込みは、ポイント残高・交換申請という「実害に直結する値」を
# 扱うため、他のJSONファイル(videos.json等)と違い read-modify-write をロックで保護する。
CREATORS_LOCK = threading.Lock()

# ---------- DMCA/著作権侵害の申し立て(/copyright-policy のフォーム) ----------
# 広告ネットワーク(ExoClick)の審査要件で、2257準拠声明に加えて「専用のメールアドレスまたは
# 問い合わせフォーム」が必須とされたため、SNS(X)のDMだけだった連絡手段をこのフォームに変更した。
DMCA_REPORTS_PATH = os.path.join(UPLOAD_DIR, "dmca_reports.json")
DMCA_REPORTS_LOCK = threading.Lock()
MAX_DMCA_NAME_LENGTH = 100
MAX_DMCA_EMAIL_LENGTH = 200
MAX_DMCA_URL_LENGTH = 500
MAX_DMCA_MESSAGE_LENGTH = 4000

# 公開・ログイン不要のフォームのため、荒らし/スパム対策として同一IPからの連投を軽く制限する。
DMCA_SUBMISSIONS = {}  # ip -> [timestamp, ...]（直近の送信時刻。ウィンドウ外の古いものは随時間引く）
DMCA_SUBMISSIONS_LOCK = threading.Lock()
DMCA_SUBMISSION_WINDOW_SECONDS = 60 * 60
MAX_DMCA_SUBMISSIONS_PER_IP_PER_WINDOW = 3


def is_dmca_submission_rate_limited(ip):
    """直近DMCA_SUBMISSION_WINDOW_SECONDS以内の同一IPからの送信回数が上限を超えていればTrue。"""
    now = time.time()
    with DMCA_SUBMISSIONS_LOCK:
        recent = [t for t in DMCA_SUBMISSIONS.get(ip, []) if now - t < DMCA_SUBMISSION_WINDOW_SECONDS]
        if len(recent) >= MAX_DMCA_SUBMISSIONS_PER_IP_PER_WINDOW:
            DMCA_SUBMISSIONS[ip] = recent
            return True
        recent.append(now)
        DMCA_SUBMISSIONS[ip] = recent
        return False


def load_dmca_reports():
    if not os.path.exists(DMCA_REPORTS_PATH):
        return []
    with open(DMCA_REPORTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_dmca_reports(reports):
    with open(DMCA_REPORTS_PATH, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False)


def validate_dmca_report(data):
    """/copyright-policy のフォーム入力値をチェックする。

    成功時は (フィールドの辞書, None) を、失敗時は (None, エラーコード) を返す。
    """
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    url = (data.get("url") or "").strip()
    message = (data.get("message") or "").strip()

    if len(name) > MAX_DMCA_NAME_LENGTH:
        return None, "invalid_name"
    if not email or len(email) > MAX_DMCA_EMAIL_LENGTH or "@" not in email:
        return None, "invalid_email"
    if not url or len(url) > MAX_DMCA_URL_LENGTH:
        return None, "invalid_url"
    if not message or len(message) > MAX_DMCA_MESSAGE_LENGTH:
        return None, "invalid_message"

    return {"name": name, "email": email, "url": url, "message": message}, None


def serialize_dmca_report(r):
    return {
        "id": r["id"],
        "name": r.get("name") or "",
        "email": r["email"],
        "url": r["url"],
        "message": r["message"],
        "submittedAt": r["submitted_at"],
        "resolved": r.get("resolved", False),
    }


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
    return next(
        (
            c for c in creators
            if c.get("invite_token") == invite_token
            and c.get("status") == "invited"
            and c.get("auth_mode", "password") == "password"
        ),
        None,
    )


def find_creator_by_magic_link_token(creators, invite_token):
    """マジックリンク方式(ライト版)のクリエイターを探す。

    パスワード方式と違い、招待トークンは登録後も無効化されず、本人の恒久的な
    アクセス手段として使い続ける想定のため、statusによる絞り込みは行わない。
    """
    return next(
        (c for c in creators if c.get("invite_token") == invite_token and c.get("auth_mode") == "magic_link"),
        None,
    )


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


def get_effective_points_amount(video, creator, config):
    """このコンテンツ(動画/画像)を承認した場合に付与される通常ポイント数を返す(ボーナス抜き)。

    クリエイター側に動画/画像それぞれの個別上書き設定があればそれを、
    無ければサイト全体の既定値(config)を使う。
    """
    if video.get("content_type") == "image":
        override = creator.get("points_per_image_upload") if creator else None
        return override if override is not None else config.get("points_per_image_upload", DEFAULT_POINTS_PER_IMAGE_UPLOAD)
    override = creator.get("points_per_video_upload") if creator else None
    return override if override is not None else config.get("points_per_video_upload", DEFAULT_POINTS_PER_VIDEO_UPLOAD)


def get_effective_bonus_points_amount(video, config):
    """ボーナス閾値を超えた場合に追加で付与されるボーナスポイント数を返す。

    個別上書きは無く、サイト全体の既定値のみ(0なら実質ボーナス無効)。
    """
    if video.get("content_type") == "image":
        return config.get("bonus_points_image", DEFAULT_BONUS_POINTS_IMAGE)
    return config.get("bonus_points_video", DEFAULT_BONUS_POINTS_VIDEO)


def get_points_status(video, creator, config):
    """クリエイター投稿1件の、ポイント付与に関する現在の状態を返す。

    管理者自身のアップロード(owner_creator_id無し)には適用されないのでNoneを返す。
    get_time_limit_status と同様、DBには「承認済みかどうか」しか保存せず、
    それ以外の状態(集計中/対象外等)は呼ばれるたびに計算するだけにする。
    ボーナス判定(24時間以内の閲覧数がbonus_view_thresholdを超えたか)も通常の
    閾値判定と同じタイミング(24時間経過後の累計閲覧数)で行い、amount/amountYenには
    ボーナス込みの合計を入れる。
    """
    if not video.get("owner_creator_id"):
        return None
    if video.get("points_awarded"):
        amount = video.get("points_awarded_amount")
        return {
            "state": "awarded",
            "amount": amount,
            "amountYen": points_to_yen(amount),
            "viewCount": video.get("view_count", 0),
            "bonusApplied": bool(video.get("bonus_points_applied")),
        }

    window_end = video.get("uploaded_at_epoch", 0) + POINTS_WINDOW_SECONDS
    view_count = video.get("view_count", 0)
    threshold = config.get("points_view_threshold", DEFAULT_POINTS_VIEW_THRESHOLD)
    bonus_threshold = config.get("bonus_view_threshold", DEFAULT_BONUS_VIEW_THRESHOLD)
    bonus_eligible = view_count >= bonus_threshold
    bonus_amount = get_effective_bonus_points_amount(video, config) if bonus_eligible else 0
    amount = get_effective_points_amount(video, creator, config) + bonus_amount
    amount_yen = points_to_yen(amount)

    if time.time() < window_end:
        return {
            "state": "collecting", "viewCount": view_count, "threshold": threshold,
            "windowEndsAt": window_end, "amount": amount, "amountYen": amount_yen,
            "bonusThreshold": bonus_threshold, "bonusEligible": bonus_eligible, "bonusAmount": bonus_amount,
        }
    if view_count >= threshold:
        return {
            "state": "eligible_pending_approval", "viewCount": view_count, "threshold": threshold,
            "amount": amount, "amountYen": amount_yen,
            "bonusThreshold": bonus_threshold, "bonusEligible": bonus_eligible, "bonusAmount": bonus_amount,
        }
    return {"state": "not_eligible", "viewCount": view_count, "threshold": threshold}


def approve_points_for_video(video, creator, config):
    """指定した投稿のポイントを承認し、creator/video辞書を直接書き換える(単体承認・一括承認で共用)。

    承認可能な状態(eligible_pending_approval)でなければ何もせずNoneを返す。
    呼び出し側でCREATORS_LOCK+VIDEOS_LOCKの取得、save_creators/save_videosを行うこと。
    """
    # クライアント側の表示だけを信用せず、サーバー側で承認可能な状態か再検証する
    status = get_points_status(video, creator, config)
    if not status or status["state"] != "eligible_pending_approval":
        return None

    # amountはボーナス込みの合計(get_points_status内で計算済み)。ここで再計算せず
    # 同じ値をそのまま使うことで、承認可否の判定に使った金額と実際に付与する金額が
    # 食い違わないようにする。
    amount = status["amount"]
    bonus_applied = status.get("bonusEligible", False)

    creator["points_balance"] = creator.get("points_balance", 0) + amount
    creator.setdefault("points_history", []).append({
        "delta": amount,
        "reason": "upload_approved",
        "content_id": video["id"],
        "bonusApplied": bonus_applied,
        "at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })

    video["points_awarded"] = True
    video["points_awarded_amount"] = amount
    video["points_awarded_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    video["bonus_points_applied"] = bonus_applied

    return amount


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "premium_link": DEFAULT_PREMIUM_LINK,
            "premium_button_text": DEFAULT_PREMIUM_BUTTON_TEXT,
            "ads": json.loads(json.dumps(DEFAULT_ADS)),
            "og_image_filename": None,
            "points_per_video_upload": DEFAULT_POINTS_PER_VIDEO_UPLOAD,
            "points_per_image_upload": DEFAULT_POINTS_PER_IMAGE_UPLOAD,
            "points_view_threshold": DEFAULT_POINTS_VIEW_THRESHOLD,
            "min_redemption_points": DEFAULT_MIN_REDEMPTION_POINTS,
            "bonus_view_threshold": DEFAULT_BONUS_VIEW_THRESHOLD,
            "bonus_points_video": DEFAULT_BONUS_POINTS_VIDEO,
            "bonus_points_image": DEFAULT_BONUS_POINTS_IMAGE,
            "content_page_ad_zone_id_mobile": DEFAULT_CONTENT_PAGE_AD_ZONE_ID_MOBILE,
            "content_page_ad_zone_id_desktop": DEFAULT_CONTENT_PAGE_AD_ZONE_ID_DESKTOP,
        }
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    config.setdefault("premium_link", DEFAULT_PREMIUM_LINK)
    config.setdefault("premium_button_text", DEFAULT_PREMIUM_BUTTON_TEXT)
    config.setdefault("ads", json.loads(json.dumps(DEFAULT_ADS)))
    config.setdefault("og_image_filename", None)
    config.setdefault("points_per_video_upload", DEFAULT_POINTS_PER_VIDEO_UPLOAD)
    config.setdefault("points_per_image_upload", DEFAULT_POINTS_PER_IMAGE_UPLOAD)
    config.setdefault("points_view_threshold", DEFAULT_POINTS_VIEW_THRESHOLD)
    config.setdefault("min_redemption_points", DEFAULT_MIN_REDEMPTION_POINTS)
    config.setdefault("bonus_view_threshold", DEFAULT_BONUS_VIEW_THRESHOLD)
    config.setdefault("bonus_points_video", DEFAULT_BONUS_POINTS_VIDEO)
    config.setdefault("bonus_points_image", DEFAULT_BONUS_POINTS_IMAGE)
    # 旧: PC/スマホ分離前の単一ゾーンID設定からの移行(既存の値はモバイル用として引き継ぐ)
    legacy_zone_id = config.pop("content_page_ad_zone_id", None)
    config.setdefault("content_page_ad_zone_id_mobile", legacy_zone_id or DEFAULT_CONTENT_PAGE_AD_ZONE_ID_MOBILE)
    config.setdefault("content_page_ad_zone_id_desktop", DEFAULT_CONTENT_PAGE_AD_ZONE_ID_DESKTOP)
    # 旧: 全画面広告(フォールバック広告)機能は在庫(フィル)が無く廃止したため、
    # 過去に保存された設定値が残っていれば掃除する
    config.pop("fallback_ad_zone_id", None)
    config.pop("fallback_ad_zone_id_mobile", None)
    config.pop("fallback_ad_zone_id_desktop", None)
    return config


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False)


# videos.json への書き込みも、複数のクリエイターが同時にアップロード/削除/設定変更した際に
# 片方の変更が丸ごと消える(read-modify-writeのロスト・アップデート)のを防ぐため、
# creators.json と同様にロックで保護する。両方のロックが必要な処理(ポイント承認等)では
# 必ず CREATORS_LOCK を先に、VIDEOS_LOCK を後に取得すること(デッドロック防止のため順序を統一)。
VIDEOS_LOCK = threading.Lock()


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


def validate_cta_button_text(text):
    """投稿ごとの誘導ボタン文言の個別上書き。空文字/Noneは「未設定(自動)」として許可する。

    成功時は (text_or_None, None) を、失敗時は (None, error_code) を返す。
    """
    text = (text or "").strip()
    if not text:
        return None, None
    if len(text) > MAX_BUTTON_TEXT_LENGTH:
        return None, "invalid_cta_button_text"
    return text, None


def validate_cta_link_url(url):
    """投稿ごとの誘導ボタンのリンク先個別上書き。空文字/Noneは「未設定(自動)」として許可する。

    成功時は (url_or_None, None) を、失敗時は (None, error_code) を返す。
    """
    url = (url or "").strip()
    if not url:
        return None, None
    if len(url) > MAX_CTA_LINK_URL_LENGTH or not re.match(r"^https?://", url):
        return None, "invalid_cta_link_url"
    return url, None


def get_effective_cta(video, config, creator=None):
    """誘導ボタンのリンク先・文字を返す。ボタンの文言は次の優先順位で決まる。

    1. 投稿ごとの文言個別指定(cta_button_text)
    2. 出演者名+URL個別設定(creator_name+creator_url)がともにある場合、そのテンプレート文言
    3. クリエイター自身が自分のダッシュボードで設定した既定文言(default_cta_button_text)
    4. クリエイター自身の投稿(owner_creator_id有り)で、上記が無ければアカウントの表示名から自動生成
    5. どれも無ければサイト既定の文言

    リンク先は次の優先順位で決まる。
    1. 投稿ごとのリンク先個別指定(cta_link_url)
    2. 出演者名+URL個別設定(creator_name+creator_url)がともにある場合、そのURL
    3. クリエイター自身が自分のダッシュボードで設定した既定リンク(default_cta_link_url)
    4. どれも無ければサイト既定のリンク
    """
    cta_text_override = video.get("cta_button_text")
    cta_link_override = video.get("cta_link_url")
    name = video.get("creator_name")
    url = video.get("creator_url")

    if cta_text_override:
        button_text = cta_text_override
    elif name and url:
        button_text = CREATOR_BUTTON_TEXT_TEMPLATE.format(name=name)
    elif creator and creator.get("default_cta_button_text"):
        button_text = creator["default_cta_button_text"]
    elif creator and creator.get("display_name"):
        button_text = CREATOR_BUTTON_TEXT_TEMPLATE.format(name=creator["display_name"])
    else:
        button_text = config["premium_button_text"]

    if cta_link_override:
        premium_link = cta_link_override
    elif name and url:
        premium_link = url
    elif creator and creator.get("default_cta_link_url"):
        premium_link = creator["default_cta_link_url"]
    else:
        premium_link = config["premium_link"]

    return {
        "premiumLink": premium_link,
        "premiumButtonText": button_text,
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
    return {"id": ad["id"], "label": ad["label"], "adCode": ad["ad_code"]}


def serialize_redemption_request(r):
    return {
        "id": r["id"],
        "points": r["points"],
        "pointsYen": points_to_yen(r["points"]),
        "status": r["status"],
        "requestedAt": r.get("requested_at"),
        "fulfilledAt": r.get("fulfilled_at"),
    }


def validate_ads_payload(ads_input):
    """広告設定(2件固定: ad1=動画用, ad2=画像用)の共通バリデーション。

    成功時は (ads_list, None) を、失敗時は (None, error_code) を返す。
    サイト全体の既定設定・動画/画像ごとの個別設定の両方から使い回す。
    """
    if not isinstance(ads_input, list) or len(ads_input) != 2:
        return None, "invalid_ads_count"

    new_ads = []
    for index, ad in enumerate(ads_input):
        label = (ad.get("label") or "").strip() if isinstance(ad, dict) else ""
        ad_code = (ad.get("adCode") or "").strip() if isinstance(ad, dict) else ""

        if not label or len(label) > MAX_AD_LABEL_LENGTH:
            return None, "invalid_ad_label"
        if len(ad_code) > MAX_AD_CODE_LENGTH:
            return None, "invalid_ad_code"

        new_ads.append({
            "id": "ad" + str(index + 1),
            "label": label,
            "ad_code": ad_code,
        })

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


def validate_contact_url(url):
    """クリエイターの連絡先リンク(SNS等)のバリデーション。空文字/Noneは「未設定」として許可する。

    成功時は (url_or_None, None) を、失敗時は (None, error_code) を返す。
    """
    url = (url or "").strip()
    if not url:
        return None, None
    if len(url) > MAX_CONTACT_URL_LENGTH or not re.match(r"^https?://", url):
        return None, "invalid_contact_url"
    return url, None


def validate_content_page_ad_zone_id(zone_id):
    """視聴ページ(動画・画像共通)のバナー広告ゾーンIDのバリデーション。

    空文字/Noneは「非表示」として許可する。成功時は (zone_id_or_None, None) を、
    失敗時は (None, error_code) を返す。
    """
    zone_id = (zone_id or "").strip()
    if not zone_id:
        return None, None
    if len(zone_id) > MAX_CONTENT_PAGE_AD_ZONE_ID_LENGTH:
        return None, "invalid_content_page_ad_zone_id"
    return zone_id, None


def validate_id_rejection_reason(reason):
    """身分証を却下する際の理由(任意入力)のバリデーション。"""
    reason = (reason or "").strip()
    if not reason:
        return None, None
    if len(reason) > MAX_ID_REJECTION_REASON_LENGTH:
        return None, "invalid_reason"
    return reason, None


def _find_iso_bmff_box(data: bytes, target_types, start: int, end: int):
    """ISO-BMFF(MP4/MOV/M4V)のボックス列から、指定タイプのボックスを1つ探す。

    見つかれば (box_type, content_start, content_end) を、無ければNoneを返す。
    """
    pos = start
    while pos + 8 <= end:
        size = int.from_bytes(data[pos:pos + 4], "big")
        box_type = data[pos + 4:pos + 8]
        header_size = 8
        if size == 1:
            if pos + 16 > end:
                return None
            size = int.from_bytes(data[pos + 8:pos + 16], "big")
            header_size = 16
        elif size == 0:
            size = end - pos
        if size < header_size or pos + size > end:
            return None
        if box_type in target_types:
            return box_type, pos + header_size, pos + size
        pos += size
    return None


def get_mp4_duration_seconds(data: bytes):
    """MP4/MOV/M4V(ISO-BMFF)の moov/mvhd ボックスから再生時間(秒)を読み取る。

    パースに失敗した場合(壊れたファイル・未対応の構造等)はNoneを返す。
    """
    moov = _find_iso_bmff_box(data, {b"moov"}, 0, len(data))
    if not moov:
        return None
    _, moov_start, moov_end = moov
    mvhd = _find_iso_bmff_box(data, {b"mvhd"}, moov_start, moov_end)
    if not mvhd:
        return None
    _, mvhd_start, mvhd_end = mvhd
    if mvhd_end - mvhd_start < 4:
        return None
    version = data[mvhd_start]
    try:
        if version == 1:
            # version(1)+flags(3)+creation(8)+modification(8)+timescale(4)+duration(8)
            if mvhd_end - mvhd_start < 32:
                return None
            timescale = int.from_bytes(data[mvhd_start + 20:mvhd_start + 24], "big")
            duration = int.from_bytes(data[mvhd_start + 24:mvhd_start + 32], "big")
        else:
            # version(1)+flags(3)+creation(4)+modification(4)+timescale(4)+duration(4)
            if mvhd_end - mvhd_start < 20:
                return None
            timescale = int.from_bytes(data[mvhd_start + 12:mvhd_start + 16], "big")
            duration = int.from_bytes(data[mvhd_start + 16:mvhd_start + 20], "big")
    except (ValueError, OverflowError):
        return None
    if not timescale:
        return None
    return duration / timescale


def _read_ebml_vint(data: bytes, pos: int, keep_marker: bool):
    """EBMLの可変長整数を読む。(値, 消費バイト数)を返す。読めなければNone。

    keep_marker=True の場合は要素ID用(長さマーカーのビットも値に含めたまま)、
    False の場合はサイズ用(長さマーカーを除去した実際の値)として読む。
    """
    if pos >= len(data):
        return None
    first = data[pos]
    if first == 0:
        return None
    length = 1
    mask = 0x80
    while not (first & mask):
        mask >>= 1
        length += 1
        if length > 8:
            return None
    if pos + length > len(data):
        return None
    if keep_marker:
        value = first
        for i in range(1, length):
            value = (value << 8) | data[pos + i]
    else:
        value = first & (mask - 1)
        for i in range(1, length):
            value = (value << 8) | data[pos + i]
    return value, length


def _find_ebml_child(data: bytes, target_id: bytes, start: int, end: int):
    """EBML(WebM/Matroska)の子要素列から、指定IDの要素を1つ探す。

    見つかれば (content_start, content_end) を、無ければNoneを返す。
    """
    pos = start
    while pos < end:
        id_result = _read_ebml_vint(data, pos, keep_marker=True)
        if not id_result:
            return None
        elem_id_value, id_len = id_result
        elem_id = elem_id_value.to_bytes(id_len, "big")
        pos += id_len
        size_result = _read_ebml_vint(data, pos, keep_marker=False)
        if not size_result:
            return None
        size, size_len = size_result
        pos += size_len
        content_end = min(pos + size, end)
        if elem_id == target_id:
            return pos, content_end
        pos = content_end
    return None


def get_webm_duration_seconds(data: bytes):
    """WebM(Matroska/EBML)の Segment > Info > (TimestampScale, Duration) から再生時間(秒)を読み取る。

    パースに失敗した場合はNoneを返す。
    """
    segment = _find_ebml_child(data, b"\x18\x53\x80\x67", 0, len(data))
    if not segment:
        return None
    info = _find_ebml_child(data, b"\x15\x49\xa9\x66", segment[0], segment[1])
    if not info:
        return None

    timescale_ns = 1_000_000  # 既定(ナノ秒単位)。TimestampScale要素が無い場合はこれを使う
    timescale_range = _find_ebml_child(data, b"\x2a\xd7\xb1", info[0], info[1])
    if timescale_range:
        raw = data[timescale_range[0]:timescale_range[1]]
        if raw:
            timescale_ns = int.from_bytes(raw, "big")

    duration_range = _find_ebml_child(data, b"\x44\x89", info[0], info[1])
    if not duration_range:
        return None
    raw = data[duration_range[0]:duration_range[1]]
    try:
        if len(raw) == 4:
            duration_units = struct.unpack(">f", raw)[0]
        elif len(raw) == 8:
            duration_units = struct.unpack(">d", raw)[0]
        else:
            return None
    except struct.error:
        return None

    if not timescale_ns:
        return None
    return duration_units * timescale_ns / 1_000_000_000


def get_video_duration_seconds(content: bytes, ext: str):
    """拡張子に応じた動画の再生時間(秒)を返す。パース失敗/未対応形式はNoneを返す。"""
    ext = ext.lower()
    if ext in (".mp4", ".mov", ".m4v"):
        return get_mp4_duration_seconds(content)
    if ext == ".webm":
        return get_webm_duration_seconds(content)
    return None


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

    def end_headers(self):
        # ブラウザによるContent-Typeの推測(スニッフィング)を止める。拡張子だけ画像/動画で
        # 中身が異なるファイルが万一保存された場合でも、text/html等として解釈されて
        # 実行されるのを防ぐための保険(全レスポンス共通でここに一箇所だけ書けば済む)。
        self.send_header("X-Content-Type-Options", "nosniff")
        # このサイトは他サイトの<iframe>に埋め込まれる必要が無い。埋め込みを禁止することで、
        # iframe経由でページを読み込ませてJSを実行させ、閲覧数等を人為的に動かす手口を防ぐ
        # (/resolve-videoのReferer判定と合わせた二重の対策)。
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        super().end_headers()

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
            # TOP(素のURL)は本来、共有リンク専用(個別の?v=<動画ID>を知っている相手だけが
            # 動画にたどり着ける)。ただし将来の一般公開に向けたプレビューとして、
            # 管理者ログイン中・?v=無しの場合だけ新着投稿一覧(top.html)を見せる
            # (それ以外の訪問者には今まで通りの挙動のまま)。
            query = parse_qs(split.query)
            if not query.get("v") and self.is_authenticated():
                self.serve_file(os.path.join(BASE_DIR, "top.html"), "text/html; charset=utf-8")
            else:
                self.handle_serve_unlock_page(query)
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
        elif path == "/creator-terms":
            self.serve_file(os.path.join(BASE_DIR, "creator-terms.html"), "text/html; charset=utf-8")
        elif path == "/recruit":
            # クリエイター募集用のPRページ。X等から誰でも見れるよう、ログイン不要・サイト内の
            # 他ページへのリンクも一切含まない単独ページにしてある。
            self.serve_file(os.path.join(BASE_DIR, "recruit.html"), "text/html; charset=utf-8")
        elif path == "/og-image":
            self.handle_serve_og_image()
        elif path == "/favicon.ico":
            self.serve_file(os.path.join(BASE_DIR, "favicon.ico"), "image/x-icon")
        elif path == "/favicon-32x32.png":
            self.serve_file(os.path.join(BASE_DIR, "favicon-32x32.png"), "image/png")
        elif path == "/apple-touch-icon.png":
            self.serve_file(os.path.join(BASE_DIR, "apple-touch-icon.png"), "image/png")
        elif path == "/robots.txt":
            self.serve_file(os.path.join(BASE_DIR, "robots.txt"), "text/plain; charset=utf-8")
        elif path == "/sitemap.xml":
            self.handle_serve_sitemap()
        elif path.startswith("/thumb/"):
            self.handle_serve_thumbnail(path[len("/thumb/"):])
        elif path.startswith("/stats/"):
            self.handle_serve_creator_stats(path[len("/stats/"):])
        elif path.startswith("/creator-posts/"):
            self.handle_serve_creator_posts_page(path[len("/creator-posts/"):])
        elif path == "/api/creator-posts":
            self.handle_api_creator_posts(parse_qs(split.query))
        elif path == "/all-posts":
            # サイト内のどこからもリンクしていない、現在公開中の投稿URL一覧ページ。
            # URLを直接知っている人(管理者)だけが使う想定。
            self.serve_file(os.path.join(BASE_DIR, "all-posts.html"), "text/html; charset=utf-8")
        elif path == "/api/all-posts":
            self.handle_api_all_posts()
        elif path == "/api/top-posts":
            # top.html(TOPページのプレビュー)用のデータ。ページ自体と同じく管理者専用
            # (URLを直接叩かれても一覧が漏れないよう、APIレベルでも認証必須にする)。
            if self.require_auth():
                return
            self.handle_api_top_posts(parse_qs(split.query))
        elif path == "/api/videos":
            if self.require_auth():
                return
            self.handle_list_videos()
        elif path == "/api/dmca-reports":
            if self.require_auth():
                return
            self.handle_list_dmca_reports()
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
        elif path == "/api/creators/id-document":
            if self.require_auth():
                return
            self.handle_creators_id_document(parse_qs(split.query))
        elif path == "/api/creator/content/video-source":
            if self.require_creator_auth():
                return
            self.handle_creator_video_source(parse_qs(split.query))
        else:
            self.send_error(404, "Not Found")

    def handle_site_config(self):
        config = load_config()
        payload = json.dumps({
            "premiumLink": config["premium_link"],
            "premiumButtonText": config["premium_button_text"],
            "ads": [serialize_ad(ad) for ad in config["ads"]],
            "hasCustomOgImage": bool(config.get("og_image_filename")),
            "pointsPerVideoUpload": config.get("points_per_video_upload", DEFAULT_POINTS_PER_VIDEO_UPLOAD),
            "pointsPerImageUpload": config.get("points_per_image_upload", DEFAULT_POINTS_PER_IMAGE_UPLOAD),
            "pointsViewThreshold": config.get("points_view_threshold", DEFAULT_POINTS_VIEW_THRESHOLD),
            "minRedemptionPoints": config.get("min_redemption_points", DEFAULT_MIN_REDEMPTION_POINTS),
            "minRedemptionPointsYen": points_to_yen(config.get("min_redemption_points", DEFAULT_MIN_REDEMPTION_POINTS)),
            "bonusViewThreshold": config.get("bonus_view_threshold", DEFAULT_BONUS_VIEW_THRESHOLD),
            "bonusPointsVideo": config.get("bonus_points_video", DEFAULT_BONUS_POINTS_VIDEO),
            "bonusPointsImage": config.get("bonus_points_image", DEFAULT_BONUS_POINTS_IMAGE),
            "contentPageAdZoneIdMobile": config.get("content_page_ad_zone_id_mobile", DEFAULT_CONTENT_PAGE_AD_ZONE_ID_MOBILE),
            "contentPageAdZoneIdDesktop": config.get("content_page_ad_zone_id_desktop", DEFAULT_CONTENT_PAGE_AD_ZONE_ID_DESKTOP),
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def handle_list_videos(self):
        config = load_config()
        creators = load_creators()
        with VIDEOS_LOCK:
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
                    "viewCount": v.get("view_count", 0),
                    "rawViewCount": v.get("raw_view_count", 0),
                    "hasCustomThumbnail": bool(v.get("og_image_filename")),
                    "statsToken": get_stats_token(v, videos),
                    "contentType": v.get("content_type", "video"),
                    "imageCount": len(v.get("image_filenames") or []) if v.get("content_type") == "image" else None,
                    "ownerDisplayName": (
                        (find_creator(creators, v["owner_creator_id"]) or {}).get("display_name")
                        if v.get("owner_creator_id") else None
                    ),
                    "pointsStatus": get_points_status(v, find_creator(creators, v.get("owner_creator_id")), config),
                    "ctaButtonText": v.get("cta_button_text"),
                    "ctaLinkUrl": v.get("cta_link_url"),
                    "effectiveCtaButtonText": get_effective_cta(v, config, find_creator(creators, v.get("owner_creator_id")))["premiumButtonText"],
                    "effectiveCtaLink": get_effective_cta(v, config, find_creator(creators, v.get("owner_creator_id")))["premiumLink"],
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

        # 他サイトへの埋め込み(iframeや、fetch(..., {mode:'no-cors'})等)からの呼び出しで
        # 24時間カウントダウンの起点や閲覧数だけを人為的に動かされないよう、実際にこのサイト
        # 自身のページから呼ばれたリクエストかどうかで、副作用のある処理を行うか判定する
        # (レスポンス自体はどちらでも同じものを返す。ブロックするのは副作用のみ)。
        trusted_request = is_same_site_referer(self)

        with VIDEOS_LOCK:
            videos_list = load_videos()
            video = next((v for v in videos_list if v["id"] == requested_id), None)
            if not video or not video_file_path(video):
                # 削除済み・存在しないIDへのアクセスは「期限切れ」と同じ画面に統一する。
                # (手動削除なのか自然に24時間経過したのかを外部から区別させないため)
                self.respond_json(200, {"expired": True})
                return

            if trusted_request:
                # 「URLが初めて開かれた瞬間」をこの時点で記録する
                mark_first_access(video, videos_list)

            if get_time_limit_status(video)["expired"]:
                self.respond_json(200, {"expired": True})
                return

            if trusted_request:
                # モザイク越しのロック画面が表示された回数を2種類カウントする
                # (期限切れの場合はロック画面自体を表示しないため、ここではカウントしない)。
                # - raw_view_count(総アクセス数): 読み込むたびに無条件で加算する生の回数
                # - view_count(有効視聴回数): 同一IP+同一コンテンツは直近24時間で1回しかカウントしない
                #   水増し対策版。ポイント付与判定はこちらを使う。
                video["raw_view_count"] = video.get("raw_view_count", 0) + 1
                if should_count_view(requested_id, get_client_ip(self)):
                    video["view_count"] = video.get("view_count", 0) + 1
                save_videos(videos_list)

        config = load_config()
        effective_ads = video.get("ads") or config["ads"]
        owner_creator = find_creator(load_creators(), video.get("owner_creator_id")) if video.get("owner_creator_id") else None
        cta = get_effective_cta(video, config, owner_creator)

        # クリエイターの投稿一覧ページ(/creator-posts/<id>)へのボタン表示判定に使う。
        # 他のクリエイターへの回遊は含めない(投稿者から見て、自分の視聴者が別の
        # 投稿者に流れてしまう導線は避けたいため、一覧自体もowner_creator_idで絞り込む)。
        owner_creator_id = video.get("owner_creator_id")

        content_type = video.get("content_type", "video")
        self.respond_json(200, {
            "expired": False,
            "id": video["id"],
            "contentType": content_type,
            "imageCount": len(video.get("image_filenames") or []) if content_type == "image" else None,
            "uploadedAt": video["uploaded_at"],
            "ads": [serialize_ad(ad) for ad in effective_ads],
            "timeLimit": get_time_limit_status(video),
            "premiumLink": cta["premiumLink"],
            "premiumButtonText": cta["premiumButtonText"],
            "contentPageAdZoneIdMobile": config.get("content_page_ad_zone_id_mobile", DEFAULT_CONTENT_PAGE_AD_ZONE_ID_MOBILE),
            "contentPageAdZoneIdDesktop": config.get("content_page_ad_zone_id_desktop", DEFAULT_CONTENT_PAGE_AD_ZONE_ID_DESKTOP),
            "ownerCreatorId": owner_creator_id,
            "contactUrl": owner_creator.get("contact_url") if owner_creator else None,
        })

    def handle_serve_video(self, video_id):
        with VIDEOS_LOCK:
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
            expired = get_time_limit_status(video)["expired"]

        if expired:
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

        with VIDEOS_LOCK:
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
            expired = get_time_limit_status(video)["expired"]

        if expired:
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
        page_html = page_html.replace("{{RAW_VIEW_COUNT}}", str(video.get("raw_view_count", 0)))
        page_html = page_html.replace("{{UPLOADED_AT}}", html.escape(video["uploaded_at"]))
        page_html = page_html.replace("{{STATUS_TEXT}}", status_text)

        body = page_html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def handle_serve_creator_posts_page(self, creator_id):
        """あるクリエイターの投稿一覧ページ(creator-posts.html)を返す。

        他のクリエイターへは遷移できないよう、常にこの1人分のcreator_idに
        スコープしたままにする(一覧データ自体は/api/creator-postsで別途取得)。
        """
        if not creator_id or not VIDEO_ID_RE.match(creator_id):
            # URLのこの部分はページ内のJSON(script内)にそのまま埋め込むため、
            # 想定外の文字(<等)を含む値がここで弾かれずに通ると埋め込み時の
            # エスケープに不備があった場合にXSSにつながりうる。存在しないIDと
            # 同様に404にしてしまい、形式の時点で弾く。
            self.send_error(404, "Not Found")
            return
        with open(os.path.join(BASE_DIR, "creator-posts.html"), "r", encoding="utf-8") as f:
            page_html = f.read()
        page_html = page_html.replace("{{CREATOR_ID_JSON}}", json_for_script(creator_id))

        body = page_html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def handle_api_creator_posts(self, query):
        """あるクリエイターの投稿を全件返す(公開・認証不要)。

        /resolve-videoのotherContentByCreatorと同じ絞り込み条件(所有者一致・
        実体ファイルが存在・期限切れでない)だが、件数上限を設けず全件返す。
        """
        creator_id = (query.get("creatorId") or [None])[0]
        if not creator_id:
            self.respond_json(200, {"items": []})
            return

        videos_list = load_videos()
        items = [
            v for v in videos_list
            if v.get("owner_creator_id") == creator_id
            and video_file_path(v)
            and not get_time_limit_status(v)["expired"]
            and not v.get("unlisted")
        ]
        items.sort(key=lambda v: v.get("uploaded_at", ""), reverse=True)

        self.respond_json(200, {
            "items": [
                {
                    "id": v["id"],
                    "contentType": v.get("content_type", "video"),
                    "thumbnailUrl": ("/thumb/" + v["id"]) if v.get("og_image_filename") else None,
                }
                for v in items[:60]
            ]
        })

    def handle_api_all_posts(self):
        """サイト全体で現在アクセス可能な投稿のURL一覧を返す(公開・認証不要)。

        削除済み(実体ファイルが無い)・24時間限定で期限切れの投稿は除外する。
        どのページからもリンクしていない(このURLを直接知っている人だけが使う)想定。
        """
        creators = load_creators()
        videos_list = load_videos()
        items = [
            v for v in videos_list
            if video_file_path(v)
            and not get_time_limit_status(v)["expired"]
        ]
        items.sort(key=lambda v: v.get("uploaded_at", ""), reverse=True)

        self.respond_json(200, {
            "generatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "items": [
                {
                    "id": v["id"],
                    "url": PUBLIC_SITE_URL + "/?v=" + v["id"],
                    "contentType": v.get("content_type", "video"),
                    "creatorDisplayName": (
                        find_creator(creators, v.get("owner_creator_id")).get("display_name")
                        if v.get("owner_creator_id") and find_creator(creators, v.get("owner_creator_id"))
                        else None
                    ),
                    "uploadedAt": v.get("uploaded_at"),
                    "viewCount": v.get("view_count", 0),
                    "rawViewCount": v.get("raw_view_count", 0),
                }
                for v in items
            ],
        })

    def handle_serve_sitemap(self):
        """検索エンジン向けのsitemap.xml(公開・認証不要)。

        現時点ではTOPページ(/)自体がまだ管理者プレビュー段階(noindex)のため実質参照
        されないが、一般公開する段になってすぐ使えるよう先に用意しておく。掲載するのは
        現在アクセス可能な投稿の個別URL(/?v=<id>)のみ(削除済み・期限切れ・unlistedは除外)。
        """
        videos_list = load_videos()
        items = [
            v for v in videos_list
            if video_file_path(v)
            and not get_time_limit_status(v)["expired"]
            and not v.get("unlisted")
        ]
        items.sort(key=lambda v: v.get("uploaded_at", ""), reverse=True)

        urls = [PUBLIC_SITE_URL + "/"] + [
            PUBLIC_SITE_URL + "/?v=" + v["id"] for v in items
        ]
        entries = "".join(
            "<url><loc>" + html.escape(u) + "</loc></url>" for u in urls
        )
        body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + entries +
            "</urlset>"
        ).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_api_top_posts(self, query):
        """公開TOPページ(/)の新着投稿一覧用データ。

        /api/creator-postsと同じ条件(所有者不問・実体ファイルが存在・期限切れでない・
        unlisted指定でない)で全投稿を横断して返す。ページ自体(handle_serve_unlock_page)
        を管理者ログイン中しか出さないのと合わせ、このAPIも認証必須にしてある
        (URLを直接叩かれても一覧が漏れないように)。

        新着順(items)だけだと、投稿頻度が低い子の投稿がどんどん下に沈んで実質見えなく
        なってしまうため、同じ母集団から無作為に選んだ「ピックアップ」枠(pickup)も
        一緒に返す。呼ばれるたびに毎回抽選し直すので、特定の投稿が固定で埋もれ続けることはない。

        投稿数が増えても1回のレスポンスが肥大化しないよう、?offset=&limit=でページングする。
        pickupは初回(offset=0)のレスポンスにのみ含める(2ページ目以降で重複して抽選し直す
        意味が無いため)。
        """
        try:
            offset = max(0, int((query.get("offset") or ["0"])[0]))
        except ValueError:
            offset = 0
        try:
            limit = int((query.get("limit") or [str(TOP_POSTS_PAGE_SIZE)])[0])
        except ValueError:
            limit = TOP_POSTS_PAGE_SIZE
        limit = max(1, min(limit, MAX_TOP_POSTS_PAGE_SIZE))

        creators = load_creators()
        videos_list = load_videos()
        items = [
            v for v in videos_list
            if video_file_path(v)
            and not get_time_limit_status(v)["expired"]
            and not v.get("unlisted")
        ]

        serialized = [
            {
                "id": v["id"],
                "contentType": v.get("content_type", "video"),
                "thumbnailUrl": ("/thumb/" + v["id"]) if v.get("og_image_filename") else None,
                "uploadedAt": v.get("uploaded_at"),
                "ownerCreatorId": v.get("owner_creator_id"),
                "creatorDisplayName": (
                    find_creator(creators, v.get("owner_creator_id")).get("display_name")
                    if v.get("owner_creator_id") and find_creator(creators, v.get("owner_creator_id"))
                    else None
                ),
            }
            for v in items
        ]

        pickup = random.sample(serialized, min(len(serialized), MAX_TOP_PICKUP_COUNT)) if offset == 0 else None
        serialized.sort(key=lambda x: x["uploadedAt"] or "", reverse=True)

        page = serialized[offset:offset + limit]
        response = {"items": page, "hasMore": offset + limit < len(serialized)}
        if pickup is not None:
            response["pickup"] = pickup

        self.respond_json(200, response)

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
        elif path == "/api/videos/set-cta-text":
            if self.require_auth():
                return
            self.handle_set_video_cta_text()
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
        elif path == "/api/set-content-page-ad":
            if self.require_auth():
                return
            self.handle_set_content_page_ad()
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
        elif path == "/api/dmca-report":
            # 公開・ログイン不要(/copyright-policyのフォームから誰でも送信できる)
            self.handle_dmca_report()
        elif path == "/api/dmca-reports/resolve":
            if self.require_auth():
                return
            self.handle_resolve_dmca_report()
        elif path == "/api/creator/register":
            self.handle_creator_register()
        elif path == "/api/creator/magic-link-enter":
            self.handle_creator_magic_link_enter()
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
        elif path == "/api/creator/content/set-cta-text":
            if self.require_creator_auth():
                return
            self.handle_creator_set_cta_text()
        elif path == "/api/creator/set-display-name":
            if self.require_creator_auth():
                return
            self.handle_creator_set_display_name()
        elif path == "/api/creator/set-default-cta":
            if self.require_creator_auth():
                return
            self.handle_creator_set_default_cta()
        elif path == "/api/creator/content/set-thumbnail":
            if self.require_creator_auth():
                return
            self.handle_creator_set_thumbnail()
        elif path == "/api/creator/content/reset-thumbnail":
            if self.require_creator_auth():
                return
            self.handle_creator_reset_thumbnail()
        elif path == "/api/creator/content/reorder-images":
            if self.require_creator_auth():
                return
            self.handle_creator_reorder_images()
        elif path == "/api/creator/content/set-unlisted":
            if self.require_creator_auth():
                return
            self.handle_creator_set_unlisted()
        elif path == "/api/creator/request-redemption":
            if self.require_creator_auth():
                return
            self.handle_creator_request_redemption()
        elif path == "/api/creator/submit-id":
            if self.require_creator_auth():
                return
            self.handle_creator_submit_id()
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
        elif path == "/api/creators/approve-all-points":
            if self.require_auth():
                return
            self.handle_creators_approve_all_points()
        elif path == "/api/creators/adjust-points":
            if self.require_auth():
                return
            self.handle_creators_adjust_points()
        elif path == "/api/creators/fulfill-redemption":
            if self.require_auth():
                return
            self.handle_creators_fulfill_redemption()
        elif path == "/api/creators/set-points-override":
            if self.require_auth():
                return
            self.handle_creators_set_points_override()
        elif path == "/api/creators/set-contact":
            if self.require_auth():
                return
            self.handle_creators_set_contact()
        elif path == "/api/creators/set-display-name":
            if self.require_auth():
                return
            self.handle_creators_set_display_name()
        elif path == "/api/creators/reset-password":
            if self.require_auth():
                return
            self.handle_creators_reset_password()
        elif path == "/api/creators/impersonate":
            if self.require_auth():
                return
            self.handle_creators_impersonate()
        elif path == "/api/creators/approve-id":
            if self.require_auth():
                return
            self.handle_creators_approve_id()
        elif path == "/api/creators/reject-id":
            if self.require_auth():
                return
            self.handle_creators_reject_id()
        elif path == "/api/creators/delete":
            if self.require_auth():
                return
            self.handle_creators_delete()
        else:
            self.send_error(404, "Not Found")

    def handle_login(self):
        client_ip = get_client_ip(self)
        locked, retry_after = is_login_locked_out("admin", client_ip)
        if locked:
            self.respond_json(429, {"ok": False, "error": "too_many_attempts", "retryAfterSeconds": retry_after})
            return

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
            record_login_failure("admin", client_ip)
            self.respond_json(401, {"ok": False, "error": "invalid_credentials"})
            return

        record_login_success("admin", client_ip)
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

    def handle_set_content_page_ad(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        zone_id_mobile, error = validate_content_page_ad_zone_id(data.get("zoneIdMobile"))
        if error:
            self.respond_json(400, {"ok": False, "error": error})
            return

        zone_id_desktop, error = validate_content_page_ad_zone_id(data.get("zoneIdDesktop"))
        if error:
            self.respond_json(400, {"ok": False, "error": error})
            return

        config = load_config()
        config["content_page_ad_zone_id_mobile"] = zone_id_mobile
        config["content_page_ad_zone_id_desktop"] = zone_id_desktop
        save_config(config)

        self.respond_json(200, {"ok": True, "zoneIdMobile": zone_id_mobile, "zoneIdDesktop": zone_id_desktop})

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

        points_per_video_upload = data.get("pointsPerVideoUpload")
        points_per_image_upload = data.get("pointsPerImageUpload")
        points_view_threshold = data.get("pointsViewThreshold")
        min_redemption_points = data.get("minRedemptionPoints")
        bonus_view_threshold = data.get("bonusViewThreshold")
        bonus_points_video = data.get("bonusPointsVideo")
        bonus_points_image = data.get("bonusPointsImage")

        def is_positive_int(value):
            return isinstance(value, int) and not isinstance(value, bool) and value > 0

        def is_nonnegative_int(value):
            return isinstance(value, int) and not isinstance(value, bool) and value >= 0

        if (
            not is_positive_int(points_per_video_upload)
            or not is_positive_int(points_per_image_upload)
            or not is_positive_int(points_view_threshold)
            or not is_positive_int(min_redemption_points)
            or not is_positive_int(bonus_view_threshold)
            or not is_nonnegative_int(bonus_points_video)
            or not is_nonnegative_int(bonus_points_image)
        ):
            self.respond_json(400, {"ok": False, "error": "invalid_points_config"})
            return

        config = load_config()
        config["points_per_video_upload"] = points_per_video_upload
        config["points_per_image_upload"] = points_per_image_upload
        config["points_view_threshold"] = points_view_threshold
        config["min_redemption_points"] = min_redemption_points
        config["bonus_view_threshold"] = bonus_view_threshold
        config["bonus_points_video"] = bonus_points_video
        config["bonus_points_image"] = bonus_points_image
        save_config(config)

        self.respond_json(200, {
            "ok": True,
            "pointsPerVideoUpload": points_per_video_upload,
            "pointsPerImageUpload": points_per_image_upload,
            "pointsViewThreshold": points_view_threshold,
            "minRedemptionPoints": min_redemption_points,
            "bonusViewThreshold": bonus_view_threshold,
            "bonusPointsVideo": bonus_points_video,
            "bonusPointsImage": bonus_points_image,
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

        with VIDEOS_LOCK:
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

        with VIDEOS_LOCK:
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
            time_limit_status = get_time_limit_status(video)

        self.respond_json(200, {"ok": True, "timeLimit": time_limit_status})

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

        with VIDEOS_LOCK:
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

    def handle_set_video_cta_text(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        with VIDEOS_LOCK:
            videos = load_videos()
            video = next((v for v in videos if v["id"] == data.get("id")), None)
            if not video:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            cta_text, error = validate_cta_button_text(data.get("ctaButtonText"))
            if error:
                self.respond_json(400, {"ok": False, "error": error})
                return

            cta_link, error = validate_cta_link_url(data.get("ctaLinkUrl"))
            if error:
                self.respond_json(400, {"ok": False, "error": error})
                return

            if cta_text:
                video["cta_button_text"] = cta_text
            else:
                video.pop("cta_button_text", None)

            if cta_link:
                video["cta_link_url"] = cta_link
            else:
                video.pop("cta_link_url", None)
            save_videos(videos)

        self.respond_json(200, {"ok": True, "ctaButtonText": cta_text, "ctaLinkUrl": cta_link})

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

        with VIDEOS_LOCK:
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

            processed = strip_image_metadata(image_file["content"], ext)
            if processed is None:
                self.respond_json(400, {"ok": False, "error": "invalid_image_file"})
                return

            # 拡張子が変わった場合に前のサムネイルが残らないよう、既存分は一旦削除する
            old_filename = video.get("og_image_filename")
            if old_filename:
                old_path = os.path.join(UPLOAD_DIR, old_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)

            new_filename = "thumb_" + video["id"] + ext
            with open(os.path.join(UPLOAD_DIR, new_filename), "wb") as f:
                f.write(processed)

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

        with VIDEOS_LOCK:
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
        if owner_creator_id:
            # 年齢確認(身分証提出→管理者承認)が済むまでは、クリエイターのセルフアップロードを禁止する。
            # 管理者本人のアップロード(owner_creator_id無し)には適用しない。
            creator = find_creator(load_creators(), owner_creator_id)
            if not creator or creator.get("id_verification_status") != "approved":
                self.respond_json(403, {"ok": False, "error": "id_verification_required"})
                return

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
            if owner_creator_id and len(image_files) < MIN_CREATOR_IMAGE_COUNT:
                self.respond_json(400, {
                    "ok": False,
                    "error": "too_few_images",
                    "minImageCount": MIN_CREATOR_IMAGE_COUNT,
                })
                return
            processed_contents = []
            for image_file in image_files:
                ext = os.path.splitext(image_file["filename"] or "")[1].lower()
                if ext not in IMAGE_ALLOWED_EXTENSIONS:
                    self.respond_json(400, {"ok": False, "error": "unsupported_file_type"})
                    return
                if len(image_file["content"]) > MAX_IMAGE_BYTES:
                    self.respond_json(413, {"ok": False, "error": "file_too_large"})
                    return
                # 1枚でも画像として読めないファイルがあれば、他の分もまとめて
                # 書き込む前にアップロード全体を拒否する(部分的な保存を避けるため)。
                processed = strip_image_metadata(image_file["content"], ext)
                if processed is None:
                    self.respond_json(400, {"ok": False, "error": "invalid_image_file"})
                    return
                processed_contents.append(processed)

            content_id = secrets.token_urlsafe(9)
            image_filenames = []
            for index, image_file in enumerate(image_files):
                ext = os.path.splitext(image_file["filename"] or "")[1].lower()
                stored_name = f"{content_id}_{index}{ext}"
                with open(os.path.join(UPLOAD_DIR, stored_name), "wb") as f:
                    f.write(processed_contents[index])
                image_filenames.append(stored_name)

            original_filename = image_files[0]["filename"] or "upload"

            with VIDEOS_LOCK:
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

            if owner_creator_id:
                send_notification_email(
                    "新規投稿(画像) - " + (creator.get("display_name") or "（名前未設定）"),
                    (creator.get("display_name") or "（名前未設定）") + " さんが画像ギャラリーをアップロードしました。\n"
                    + "投稿ID: " + content_id,
                )

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

        if owner_creator_id:
            duration_seconds = get_video_duration_seconds(video_file["content"], ext)
            if duration_seconds is None:
                self.respond_json(400, {"ok": False, "error": "could_not_determine_video_length"})
                return
            if duration_seconds < MIN_CREATOR_VIDEO_DURATION_SECONDS:
                self.respond_json(400, {
                    "ok": False,
                    "error": "video_too_short",
                    "minVideoDurationSeconds": MIN_CREATOR_VIDEO_DURATION_SECONDS,
                })
                return

        video_id = secrets.token_urlsafe(9)
        stored_filename = video_id + ext

        with open(os.path.join(UPLOAD_DIR, stored_filename), "wb") as f:
            f.write(video_file["content"])

        with VIDEOS_LOCK:
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

        if owner_creator_id:
            send_notification_email(
                "新規投稿(動画) - " + (creator.get("display_name") or "（名前未設定）"),
                (creator.get("display_name") or "（名前未設定）") + " さんが動画をアップロードしました。\n"
                + "投稿ID: " + video_id,
            )

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

    def handle_creator_set_cta_text(self):
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

        video_id = data.get("id")
        video = find_video(video_id)
        # 他のクリエイターや管理者本人のコンテンツを変更できないよう、所有者一致を必ず確認する
        if not video or video.get("owner_creator_id") != creator_id:
            self.respond_json(404, {"ok": False, "error": "not_found"})
            return

        cta_text, error = validate_cta_button_text(data.get("ctaButtonText"))
        if error:
            self.respond_json(400, {"ok": False, "error": error})
            return

        cta_link, error = validate_cta_link_url(data.get("ctaLinkUrl"))
        if error:
            self.respond_json(400, {"ok": False, "error": error})
            return

        with VIDEOS_LOCK:
            videos = load_videos()
            target = next((v for v in videos if v["id"] == video_id), None)
            if cta_text:
                target["cta_button_text"] = cta_text
            else:
                target.pop("cta_button_text", None)

            if cta_link:
                target["cta_link_url"] = cta_link
            else:
                target.pop("cta_link_url", None)
            save_videos(videos)

        self.respond_json(200, {"ok": True, "ctaButtonText": cta_text, "ctaLinkUrl": cta_link})

    def handle_creator_set_default_cta(self):
        """自分の投稿全体に使う既定の誘導ボタン文言・リンク先を設定する。

        投稿ごとの個別指定(cta_button_text/cta_link_url)がある投稿にはそちらが優先される。
        """
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

        cta_text, error = validate_cta_button_text(data.get("ctaButtonText"))
        if error:
            self.respond_json(400, {"ok": False, "error": error})
            return

        cta_link, error = validate_cta_link_url(data.get("ctaLinkUrl"))
        if error:
            self.respond_json(400, {"ok": False, "error": error})
            return

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            creator["default_cta_button_text"] = cta_text
            creator["default_cta_link_url"] = cta_link
            save_creators(creators)

        self.respond_json(200, {"ok": True, "defaultCtaButtonText": cta_text, "defaultCtaLinkUrl": cta_link})

    def handle_creator_set_thumbnail(self):
        creator_id = self.get_creator_id()
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

        with VIDEOS_LOCK:
            videos = load_videos()
            video = next((v for v in videos if v["id"] == fields.get("id")), None)
            # 他のクリエイターや管理者本人のコンテンツを変更できないよう、所有者一致を必ず確認する
            if not video or video.get("owner_creator_id") != creator_id:
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

            processed = strip_image_metadata(image_file["content"], ext)
            if processed is None:
                self.respond_json(400, {"ok": False, "error": "invalid_image_file"})
                return

            # 拡張子が変わった場合に前のサムネイルが残らないよう、既存分は一旦削除する
            old_filename = video.get("og_image_filename")
            if old_filename:
                old_path = os.path.join(UPLOAD_DIR, old_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)

            new_filename = "thumb_" + video["id"] + ext
            with open(os.path.join(UPLOAD_DIR, new_filename), "wb") as f:
                f.write(processed)

            video["og_image_filename"] = new_filename
            save_videos(videos)

        self.respond_json(200, {"ok": True})

    def handle_creator_reset_thumbnail(self):
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

        with VIDEOS_LOCK:
            videos = load_videos()
            video = next((v for v in videos if v["id"] == data.get("id")), None)
            if not video or video.get("owner_creator_id") != creator_id:
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

    def handle_creator_reorder_images(self):
        """画像ギャラリーの表示順を変更する。

        クライアントは実際のファイル名を知らない(/image/<id>/<index>という
        位置ベースのURLしか渡していない)ため、「新しい並び順における元のindex」の
        配列(例: [2, 0, 1])を受け取り、image_filenamesをその順に並べ替える。
        元のindexの集合と完全に一致すること(過不足・重複が無いこと)を検証する。
        """
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

        order = data.get("order")

        with VIDEOS_LOCK:
            videos = load_videos()
            video = next((v for v in videos if v["id"] == data.get("id")), None)
            if not video or video.get("owner_creator_id") != creator_id or video.get("content_type") != "image":
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            image_filenames = video.get("image_filenames") or []
            if (
                not isinstance(order, list)
                or sorted(order) != list(range(len(image_filenames)))
            ):
                self.respond_json(400, {"ok": False, "error": "invalid_order"})
                return

            video["image_filenames"] = [image_filenames[i] for i in order]
            save_videos(videos)

        self.respond_json(200, {"ok": True})

    def handle_creator_set_unlisted(self):
        """投稿を自分の投稿一覧ページ(/creator-posts/<id>)から表示するかどうかを切り替える。

        あくまで一覧への掲載可否だけの設定であり、共有リンク(/?v=<id>)自体は
        従来通り誰でも開ける(「限定公開」的に、リンクを知っている人にだけ見せたい
        投稿向け)。
        """
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

        with VIDEOS_LOCK:
            videos = load_videos()
            video = next((v for v in videos if v["id"] == data.get("id")), None)
            if not video or video.get("owner_creator_id") != creator_id:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            video["unlisted"] = bool(data.get("unlisted"))
            save_videos(videos)

        self.respond_json(200, {"ok": True, "unlisted": video["unlisted"]})

    def handle_creator_video_source(self, query):
        """サムネイル自動生成(動画の1フレームをキャプチャ)用に、本人の動画本体を返す。

        公開共有リンク(/video/<id>)と違い、初回アクセス記録(24時間限定の起算)や
        期限切れチェックは行わない。自分の投稿を見るだけなので、それらを
        トリガーしてしまうのは意図しない副作用になるため。
        """
        creator_id = self.get_creator_id()
        video_id = (query.get("id") or [None])[0]
        video = find_video(video_id)
        if not video or video.get("owner_creator_id") != creator_id or video.get("content_type") == "image":
            self.send_error(404, "Not Found")
            return

        path = video_file_path(video)
        if not path:
            self.send_error(404, "Not Found")
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

    def handle_creator_submit_id(self):
        """クリエイター自身による年齢確認用の身分証提出(multipart/form-data)。

        再提出(却下後の再申請等)も同じエンドポイントで受け付け、
        既存の提出物があれば上書きする。承認済みの状態でも再提出は可能。
        """
        creator_id = self.get_creator_id()
        content_type_header = self.headers.get("Content-Type", "")
        boundary_match = re.search(r"boundary=(.+)", content_type_header)
        content_length = int(self.headers.get("Content-Length", 0))

        if not content_type_header.startswith("multipart/form-data") or not boundary_match:
            self.respond_json(400, {"ok": False, "error": "invalid_content_type"})
            return

        if content_length <= 0 or content_length > MAX_ID_DOCUMENT_BYTES:
            self.respond_json(413, {"ok": False, "error": "file_too_large"})
            return

        boundary = boundary_match.group(1).strip('"').encode("utf-8")
        body = self.rfile.read(content_length)
        fields, files = parse_multipart(body, boundary)

        id_file = first_file(files, "idDocument")
        if not id_file:
            self.respond_json(400, {"ok": False, "error": "missing_id_document"})
            return

        ext = os.path.splitext(id_file["filename"] or "")[1].lower()
        if ext not in ID_DOCUMENT_ALLOWED_EXTENSIONS:
            self.respond_json(400, {"ok": False, "error": "unsupported_file_type"})
            return

        document_type = validate_id_document_type(fields.get("documentType"))
        if not document_type:
            self.respond_json(400, {"ok": False, "error": "invalid_document_type"})
            return

        date_of_birth = validate_date_of_birth(fields.get("dateOfBirth"))
        if not date_of_birth:
            self.respond_json(400, {"ok": False, "error": "invalid_date_of_birth"})
            return

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            # 拡張子が変わった場合に前の提出物が残らないよう、既存分は一旦削除する
            old_filename = creator.get("id_document_filename")
            if old_filename:
                old_path = os.path.join(UPLOAD_DIR, old_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)

            new_filename = "iddoc_" + creator_id + ext
            new_path = os.path.join(UPLOAD_DIR, new_filename)
            with open(new_path, "wb") as f:
                f.write(id_file["content"])
            # 本人確認書類という機微情報のため、所有者(サーバープロセス)以外は読めないようにする
            os.chmod(new_path, 0o600)

            creator["id_document_filename"] = new_filename
            creator["id_document_type"] = document_type
            # 生年月日は承認後も保持し続ける個人情報のため、平文では保存せず暗号化して保持する
            creator["id_date_of_birth_encrypted"] = encrypt_pii(date_of_birth)
            creator["id_verification_status"] = "pending"
            creator["id_submitted_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            creator["id_reviewed_at"] = None
            creator["id_rejection_reason"] = None
            save_creators(creators)
            display_name = creator.get("display_name") or "（名前未設定）"

        send_notification_email(
            "身分証提出 - " + display_name,
            display_name + " さんが本人確認の身分証を提出しました。管理画面から確認・承認してください。",
        )

        self.respond_json(200, {"ok": True, "idVerificationStatus": "pending"})

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

        with VIDEOS_LOCK:
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

        processed = strip_image_metadata(image_file["content"], ext)
        if processed is None:
            self.respond_json(400, {"ok": False, "error": "invalid_image_file"})
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
            f.write(processed)

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
        if not invite_token or not VIDEO_ID_RE.match(invite_token):
            # 実際に発行される招待トークンはsecrets.token_urlsafe()の出力なので
            # この文字種にしかならない。ここで弾かず後続のJSON埋め込みに通すと、
            # 存在しないトークンとして「無効なリンクです」画面を出す経路であっても
            # 値がそのままscript内に反映されるため、形式の時点で404にする。
            self.send_error(404, "Not Found")
            return
        creators = load_creators()
        creator = find_creator_by_invite_token(creators, invite_token)
        if creator:
            state = {"valid": True, "token": invite_token, "mode": "password"}
        else:
            magic_creator = find_creator_by_magic_link_token(creators, invite_token)
            if magic_creator:
                state = {
                    "valid": True,
                    "token": invite_token,
                    "mode": "magic_link",
                    "alreadyAgreed": bool(magic_creator.get("terms_agreed_at")),
                }
            else:
                state = {"valid": False, "token": invite_token}

        with open(os.path.join(BASE_DIR, "creator-join.html"), "r", encoding="utf-8") as f:
            page_html = f.read()

        page_html = page_html.replace("{{INVITE_STATE_JSON}}", json_for_script(state))

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
        if data.get("agreedToTerms") is not True:
            self.respond_json(400, {"ok": False, "error": "terms_not_agreed"})
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
            creator["terms_agreed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_creators(creators)
            login_code = creator["login_code"]
            creator_id = creator["id"]
            display_name = creator.get("display_name") or "（名前未設定）"

        send_notification_email(
            "新規登録 - " + display_name,
            display_name + " さんが招待を受諾し、アカウントが有効化されました。",
        )

        token = self.create_creator_session(creator_id)
        self.send_response(200)
        self.set_creator_session_cookie(token)
        payload = json.dumps({"ok": True, "loginCode": login_code}).encode("utf-8")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_creator_magic_link_enter(self):
        """ライト版(パスワード無し)クリエイター向け。招待リンクそのものを恒久的な

        アクセス手段として使い、訪問のたびにセッションを発行する。初回訪問時のみ
        利用規約への同意を必須にする(2回目以降は同意済みなのでスキップ)。
        """
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

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator_by_magic_link_token(creators, invite_token)
            if not creator:
                self.respond_json(400, {"ok": False, "error": "invalid_invite"})
                return

            if not creator.get("terms_agreed_at"):
                if data.get("agreedToTerms") is not True:
                    self.respond_json(400, {"ok": False, "error": "terms_not_agreed"})
                    return
                creator["status"] = "active"
                creator["activated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                creator["terms_agreed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                save_creators(creators)
                send_notification_email(
                    "新規登録 - " + (creator.get("display_name") or "（名前未設定）"),
                    (creator.get("display_name") or "（名前未設定）") + " さんが招待リンク(ライト版)を受諾し、アカウントが有効化されました。",
                )

            creator_id = creator["id"]

        token = self.create_creator_session(creator_id)
        self.send_response(200)
        self.set_creator_session_cookie(token)
        payload = json.dumps({"ok": True}).encode("utf-8")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_creator_login(self):
        client_ip = get_client_ip(self)
        locked, retry_after = is_login_locked_out("creator", client_ip)
        if locked:
            self.respond_json(429, {"ok": False, "error": "too_many_attempts", "retryAfterSeconds": retry_after})
            return

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
            record_login_failure("creator", client_ip)
            self.respond_json(401, {"ok": False, "error": "invalid_credentials"})
            return

        record_login_success("creator", client_ip)
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
        creator = find_creator(load_creators(), creator_id)
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
                "rawViewCount": v.get("raw_view_count", 0),
                "pointsStatus": get_points_status(v, creator, config),
                "ctaButtonText": v.get("cta_button_text"),
                "ctaLinkUrl": v.get("cta_link_url"),
                "effectiveCtaButtonText": get_effective_cta(v, config, creator)["premiumButtonText"],
                "effectiveCtaLink": get_effective_cta(v, config, creator)["premiumLink"],
                "hasThumbnail": bool(v.get("og_image_filename")),
                "thumbnailUrl": ("/thumb/" + v["id"]) if v.get("og_image_filename") else None,
                "imageUrls": (
                    ["/image/" + v["id"] + "/" + str(i) for i in range(len(v.get("image_filenames") or []))]
                    if v.get("content_type") == "image"
                    else None
                ),
                "unlisted": bool(v.get("unlisted")),
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
            "authMode": creator.get("auth_mode", "password"),
            "displayName": creator.get("display_name"),
            "defaultCtaButtonText": creator.get("default_cta_button_text"),
            "defaultCtaLinkUrl": creator.get("default_cta_link_url"),
            "pointsBalance": creator.get("points_balance", 0),
            "pointsBalanceYen": points_to_yen(creator.get("points_balance", 0)),
            "redemptionRequests": [
                serialize_redemption_request(r) for r in creator.get("redemption_requests", [])
            ],
            "idVerificationStatus": creator.get("id_verification_status", "not_submitted"),
            "idRejectionReason": creator.get("id_rejection_reason"),
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

        config = load_config()
        min_redemption_points = config.get("min_redemption_points", DEFAULT_MIN_REDEMPTION_POINTS)
        if points < min_redemption_points:
            self.respond_json(400, {"ok": False, "error": "below_minimum_redemption", "minRedemptionPoints": min_redemption_points})
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
            display_name = creator.get("display_name") or "（名前未設定）"

        send_notification_email(
            "ポイント交換申請 - " + display_name,
            display_name + " さんがギフト券交換を申請しました。\n"
            + str(points) + "pt（" + str(points_to_yen(points)) + "円分）",
        )

        self.respond_json(200, {"ok": True, "pointsBalance": new_balance, "pointsBalanceYen": points_to_yen(new_balance)})

    # ---------- クリエイター(女の子)アカウント: 管理者側の操作 ----------
    def handle_list_creators(self):
        creators = load_creators()
        body = [
            {
                "id": c["id"],
                "displayName": c.get("display_name"),
                "status": c["status"],
                "authMode": c.get("auth_mode", "password"),
                "loginCode": c.get("login_code"),
                "magicLinkUrl": (
                    PUBLIC_SITE_URL + "/join/" + c["invite_token"]
                    if c.get("auth_mode") == "magic_link" and c.get("invite_token")
                    else None
                ),
                "pointsBalance": c.get("points_balance", 0),
                "pointsBalanceYen": points_to_yen(c.get("points_balance", 0)),
                "redemptionRequests": [serialize_redemption_request(r) for r in c.get("redemption_requests", [])],
                "invitedAt": c.get("invited_at"),
                "activatedAt": c.get("activated_at"),
                "pointsPerVideoUpload": c.get("points_per_video_upload"),
                "pointsPerImageUpload": c.get("points_per_image_upload"),
                "contactUrl": c.get("contact_url"),
                "idVerificationStatus": c.get("id_verification_status", "not_submitted"),
                "hasIdDocument": bool(c.get("id_document_filename")),
                "idDocumentType": c.get("id_document_type"),
                "idDocumentTypeLabel": ID_DOCUMENT_TYPES.get(c.get("id_document_type")),
                "idDateOfBirth": decrypt_pii(c.get("id_date_of_birth_encrypted")),
                "idAge": calculate_age(decrypt_pii(c.get("id_date_of_birth_encrypted"))),
                "idSubmittedAt": c.get("id_submitted_at"),
                "idReviewedAt": c.get("id_reviewed_at"),
                "idRejectionReason": c.get("id_rejection_reason"),
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
        contact_url, error = validate_contact_url(data.get("contactUrl"))
        if error:
            self.respond_json(400, {"ok": False, "error": error})
            return

        auth_mode = data.get("authMode") if data.get("authMode") in ("password", "magic_link") else "password"

        with CREATORS_LOCK:
            creators = load_creators()
            creator = {
                "id": secrets.token_urlsafe(9),
                "display_name": display_name or None,
                "invite_token": secrets.token_urlsafe(16),
                "login_code": secrets.token_hex(4).upper(),
                "auth_mode": auth_mode,
                "status": "invited",
                "password_salt": None,
                "password_hash": None,
                "points_balance": 0,
                "points_history": [],
                "redemption_requests": [],
                "invited_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "activated_at": None,
                "points_per_video_upload": None,
                "points_per_image_upload": None,
                "contact_url": contact_url,
                "default_cta_button_text": None,
                "default_cta_link_url": None,
                "id_verification_status": "not_submitted",
                "id_document_filename": None,
                "id_document_type": None,
                "id_date_of_birth_encrypted": None,
                "id_submitted_at": None,
                "id_reviewed_at": None,
                "id_rejection_reason": None,
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

        # 両方のロックが必要な処理なので、デッドロック防止のため必ずCREATORS_LOCKを先に取る
        with CREATORS_LOCK, VIDEOS_LOCK:
            config = load_config()
            videos = load_videos()
            video = next((v for v in videos if v["id"] == content_id), None)
            if not video:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            creators = load_creators()
            creator = find_creator(creators, video.get("owner_creator_id"))
            if not creator:
                self.respond_json(404, {"ok": False, "error": "creator_not_found"})
                return

            amount = approve_points_for_video(video, creator, config)
            if amount is None:
                self.respond_json(400, {"ok": False, "error": "not_eligible"})
                return

            save_creators(creators)
            save_videos(videos)

        self.respond_json(200, {"ok": True, "amount": amount, "amountYen": points_to_yen(amount)})

    def handle_creators_approve_all_points(self):
        # 両方のロックが必要な処理なので、デッドロック防止のため必ずCREATORS_LOCKを先に取る
        with CREATORS_LOCK, VIDEOS_LOCK:
            config = load_config()
            videos = load_videos()
            creators = load_creators()

            approved = []
            for video in videos:
                if not video.get("owner_creator_id"):
                    continue
                creator = find_creator(creators, video["owner_creator_id"])
                if not creator:
                    continue
                amount = approve_points_for_video(video, creator, config)
                if amount is not None:
                    approved.append({
                        "contentId": video["id"],
                        "creatorDisplayName": creator.get("display_name"),
                        "amount": amount,
                        "amountYen": points_to_yen(amount),
                    })

            if approved:
                save_creators(creators)
                save_videos(videos)

        total_amount = sum(a["amount"] for a in approved)
        self.respond_json(200, {
            "ok": True,
            "approvedCount": len(approved),
            "totalAmount": total_amount,
            "totalAmountYen": points_to_yen(total_amount),
            "approved": approved,
        })

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

        self.respond_json(200, {"ok": True, "pointsBalance": new_balance, "pointsBalanceYen": points_to_yen(new_balance)})

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

    # ---------- DMCA/著作権侵害の申し立て(/copyright-policy のフォーム) ----------

    def handle_dmca_report(self):
        client_ip = get_client_ip(self)
        if is_dmca_submission_rate_limited(client_ip):
            self.respond_json(429, {"ok": False, "error": "too_many_requests"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 10_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        # ハニーポット: 通常の利用者には見えない隠しフィールド。埋まっていればボットとみなし、
        # 送信者には成功したように見せつつ実際には保存しない。
        if (data.get("website") or "").strip():
            self.respond_json(200, {"ok": True})
            return

        fields, error = validate_dmca_report(data)
        if error:
            self.respond_json(400, {"ok": False, "error": error})
            return

        with DMCA_REPORTS_LOCK:
            reports = load_dmca_reports()
            reports.append({
                "id": secrets.token_urlsafe(9),
                "name": fields["name"],
                "email": fields["email"],
                "url": fields["url"],
                "message": fields["message"],
                "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "resolved": False,
            })
            save_dmca_reports(reports)

        send_notification_email(
            "DMCA/著作権の申し立て",
            "差出人: " + fields["name"] + " <" + fields["email"] + ">\n"
            + "対象URL: " + fields["url"] + "\n\n"
            + fields["message"],
        )

        self.respond_json(200, {"ok": True})

    def handle_list_dmca_reports(self):
        with DMCA_REPORTS_LOCK:
            reports = load_dmca_reports()
        reports.sort(key=lambda r: r.get("submitted_at", ""), reverse=True)
        self.respond_json(200, [serialize_dmca_report(r) for r in reports])

    def handle_resolve_dmca_report(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0 or content_length > 2_000:
            self.respond_json(400, {"ok": False, "error": "invalid_request"})
            return

        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.respond_json(400, {"ok": False, "error": "invalid_json"})
            return

        report_id = data.get("id")

        with DMCA_REPORTS_LOCK:
            reports = load_dmca_reports()
            report = next((r for r in reports if r["id"] == report_id), None)
            if not report:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return
            report["resolved"] = True
            save_dmca_reports(reports)

        self.respond_json(200, {"ok": True})

    def handle_creators_set_points_override(self):
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
        video_override = data.get("pointsPerVideoUpload")
        image_override = data.get("pointsPerImageUpload")

        def valid_override(value):
            # null(未指定) = サイト既定値を使う、という意味なので許可する
            return value is None or (isinstance(value, int) and not isinstance(value, bool) and value > 0)

        if not valid_override(video_override) or not valid_override(image_override):
            self.respond_json(400, {"ok": False, "error": "invalid_points_override"})
            return

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            creator["points_per_video_upload"] = video_override
            creator["points_per_image_upload"] = image_override
            save_creators(creators)

        self.respond_json(200, {
            "ok": True,
            "pointsPerVideoUpload": video_override,
            "pointsPerImageUpload": image_override,
        })

    def handle_creators_set_contact(self):
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
        contact_url, error = validate_contact_url(data.get("contactUrl"))
        if error:
            self.respond_json(400, {"ok": False, "error": error})
            return

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            creator["contact_url"] = contact_url
            save_creators(creators)

        self.respond_json(200, {"ok": True, "contactUrl": contact_url})

    def handle_creators_set_display_name(self):
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
        display_name = (data.get("displayName") or "").strip()[:40]

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            creator["display_name"] = display_name or None
            save_creators(creators)

        self.respond_json(200, {"ok": True, "displayName": display_name or None})

    def handle_creator_set_display_name(self):
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

        display_name = (data.get("displayName") or "").strip()[:40]

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            creator["display_name"] = display_name or None
            save_creators(creators)

        self.respond_json(200, {"ok": True, "displayName": display_name or None})

    def handle_creators_reset_password(self):
        """本人がパスワードを忘れた場合に、管理者側から強制的にパスワードを再発行する。

        ランダムな新パスワードを生成してハッシュ化・保存し、平文はこのレスポンスでのみ
        一度だけ返す(サーバー側には平文を保持しない)。既存のログインセッションは念のため
        (アカウント乗っ取り等の可能性も考慮し)すべて無効化する。
        """
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

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            new_password = secrets.token_urlsafe(9)
            salt_hex, hash_hex = hash_password(new_password)
            creator["password_salt"] = salt_hex
            creator["password_hash"] = hash_hex
            save_creators(creators)

            for token in [t for t, s in CREATOR_SESSIONS.items() if s["creator_id"] == creator_id]:
                del CREATOR_SESSIONS[token]

        self.respond_json(200, {"ok": True, "newPassword": new_password})

    def handle_creators_impersonate(self):
        """管理者が、パスワードを知らなくても該当クリエイターとしてログインする(なりすまし)。

        サポート対応等で本人視点の画面を確認したい場合用。誰が・いつ・誰に対して
        行ったかを追跡できるよう、標準出力(journalctl)への記録と、クリエイター
        レコード側にも最終実施日時を残す。管理者自身のセッション(sv_session)は
        別Cookieのため、これによりログアウトされることはない。
        """
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

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            creator["last_impersonated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_creators(creators)

        print(
            "[audit] admin impersonated creator", creator_id,
            "(" + (creator.get("display_name") or "") + ")",
            "from", get_client_ip(self),
            "at", time.strftime("%Y-%m-%d %H:%M:%S"),
        )

        token = self.create_creator_session(creator_id)
        self.send_response(200)
        self.set_creator_session_cookie(token)
        payload = json.dumps({"ok": True}).encode("utf-8")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_creators_id_document(self, query):
        """管理者のみが閲覧できる、クリエイター提出の身分証の配信。

        機微情報のため一覧等には一切出さず、このルート経由でのみ(要admin認証)アクセスできる。
        """
        creator_id = (query.get("creatorId") or [None])[0]
        creators = load_creators()
        creator = find_creator(creators, creator_id)
        filename = creator.get("id_document_filename") if creator else None
        if not filename:
            self.send_error(404, "Not Found")
            return
        path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(path):
            self.send_error(404, "Not Found")
            return
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        self.serve_file(path, content_type, extra_headers={"Cache-Control": "no-store"})

    def _delete_id_document_file(self, creator):
        """審査(承認/却下)が終わった身分証の画像そのものは残さず削除する。

        個人情報(本人確認書類)を必要以上に長く保持しないための安全対策。
        「審査した」という事実(状態・日時・却下理由)はcreators.json側に残る。
        """
        filename = creator.get("id_document_filename")
        if filename:
            path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(path):
                os.remove(path)
        creator["id_document_filename"] = None

    def handle_creators_approve_id(self):
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

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator or not creator.get("id_document_filename"):
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            creator["id_verification_status"] = "approved"
            creator["id_reviewed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            creator["id_rejection_reason"] = None
            self._delete_id_document_file(creator)
            save_creators(creators)

        self.respond_json(200, {"ok": True, "idVerificationStatus": "approved"})

    def handle_creators_reject_id(self):
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
        reason, error = validate_id_rejection_reason(data.get("reason"))
        if error:
            self.respond_json(400, {"ok": False, "error": error})
            return

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator or not creator.get("id_document_filename"):
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            creator["id_verification_status"] = "rejected"
            creator["id_reviewed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            creator["id_rejection_reason"] = reason
            self._delete_id_document_file(creator)
            save_creators(creators)

        self.respond_json(200, {"ok": True, "idVerificationStatus": "rejected", "reason": reason})

    def handle_creators_delete(self):
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

        with CREATORS_LOCK:
            creators = load_creators()
            creator = find_creator(creators, creator_id)
            if not creator:
                self.respond_json(404, {"ok": False, "error": "not_found"})
                return

            # アカウント削除時は、そのクリエイターが投稿した全コンテンツ(共有リンク含む)も一緒に削除する
            owned_videos = [v for v in load_videos() if v.get("owner_creator_id") == creator_id]
            for video in owned_videos:
                self._delete_video_entry(video["id"], video)

            # 提出済みの身分証(機微情報)も一緒に削除する
            id_document_filename = creator.get("id_document_filename")
            if id_document_filename:
                id_document_path = os.path.join(UPLOAD_DIR, id_document_filename)
                if os.path.exists(id_document_path):
                    os.remove(id_document_path)

            remaining_creators = [c for c in creators if c["id"] != creator_id]
            save_creators(remaining_creators)

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
