#!/usr/bin/env python3
"""
Exif除去機能の導入(server.pyのstrip_image_metadata)より前にアップロードされた
既存画像に、遡って同じ処理を適用する一回限りのメンテナンススクリプト。

対象: 画像ギャラリーの各画像・動画/投稿ごとの個別サムネイル・サイト共通OGP画像。
GIF・アニメーションWEBPはアニメーションが壊れるおそれがあるため対象外(strip_image_metadata側で判定)。

実行前に必ずバックアップを取ること(scripts/backup-data.sh)。
再実行しても安全(既にExifが無い画像はstrip_image_metadataが再エンコードするだけ)。

使い方: server.pyと同じディレクトリで `python3 scripts/strip-existing-exif.py` を実行。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import strip_image_metadata, UPLOAD_DIR, VIDEOS_META_PATH, CONFIG_PATH  # noqa: E402


def process_file(filename, stats):
    if not filename:
        return
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        stats["missing"] += 1
        return
    ext = os.path.splitext(filename)[1].lower()
    with open(path, "rb") as f:
        original = f.read()
    stripped = strip_image_metadata(original, ext)
    if stripped == original:
        stats["skipped"] += 1
        return
    with open(path, "wb") as f:
        f.write(stripped)
    stats["processed"] += 1


def main():
    stats = {"processed": 0, "skipped": 0, "missing": 0}

    with open(VIDEOS_META_PATH, "r", encoding="utf-8") as f:
        videos = json.load(f)

    for video in videos:
        if video.get("content_type") == "image":
            for filename in video.get("image_filenames") or []:
                process_file(filename, stats)
        process_file(video.get("og_image_filename"), stats)

    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        process_file(config.get("og_image_filename"), stats)

    print(f"processed={stats['processed']} skipped(no-op/gif/failed)={stats['skipped']} missing={stats['missing']}")


if __name__ == "__main__":
    main()
