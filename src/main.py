"""Pokémon Champions のステータス画像をOCRしてCSVへ保存する入口処理。

このモジュールは、imagesフォルダ内の画像取得、OCR対象領域の読み込み、OCR結果の確認、
CSV保存までの一連の流れを担当します。
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from .csv_storage import FIELDNAMES, append_pokemon
    from .ocr import extract_pokemon_fields
except ImportError:
    from csv_storage import FIELDNAMES, append_pokemon
    from ocr import extract_pokemon_fields

# EXE実行時とスクリプト実行時で、基準となるROOTフォルダを切り替える
if getattr(sys, "frozen", False):
    # EXEファイル（PokemonStatusTool.exe）として実行されている場合
    # sys.executable は「EXEファイル自体のパス」を指すため、その親フォルダになります。
    ROOT = Path(sys.executable).resolve().parent
else:
    # 開発環境（src/main.py）として実行されている場合
    ROOT = Path(__file__).resolve().parent.parent

DEFAULT_IMAGES_DIR = ROOT / "images"
DEFAULT_DATABASE_DIR = ROOT / "database"
REGIONS_PATH = ROOT / "config" / "regions.json"
SCHEMA_PATH = ROOT / "config" / "fields_schema.json"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def resolve_paths() -> tuple[Path, Path]:
    """実行時引数、環境変数、または対話入力から images と出力先を解決する。"""
    if len(sys.argv) >= 3:
        images_dir = Path(sys.argv[1]).expanduser().resolve()
        database_dir = Path(sys.argv[2]).expanduser().resolve()
    else:
        images_dir = (
            Path(os.getenv("POKEMON_IMAGES_DIR", DEFAULT_IMAGES_DIR))
            .expanduser()
            .resolve()
        )
        database_dir = (
            Path(os.getenv("POKEMON_DATABASE_DIR", DEFAULT_DATABASE_DIR))
            .expanduser()
            .resolve()
        )

    if (
        len(sys.argv) == 1
        and os.getenv("POKEMON_IMAGES_DIR") is None
        and os.getenv("POKEMON_DATABASE_DIR") is None
    ):
        print("画像フォルダを入力してください（空欄で既定値を使用）")
        raw_images = input(f"[{images_dir}] : ").strip()
        if raw_images:
            images_dir = Path(raw_images).expanduser().resolve()

        print("出力先フォルダを入力してください（空欄で既定値を使用）")
        raw_database = input(f"[{database_dir}] : ").strip()
        if raw_database:
            database_dir = Path(raw_database).expanduser().resolve()

    return images_dir, database_dir


def select_device_config(
    config: dict,
) -> tuple[str, dict[str, tuple[int, int, int, int]]]:
    """端末を番号で選択し、対応するOCR領域を返す。"""
    devices = config.get("devices", {})
    if not devices:
        raise ValueError("設定ファイルに devices が存在しません")

    device_names = list(devices.keys())
    if len(device_names) == 1:
        selected_device_name = device_names[0]
    else:
        print("使用するデバイスを選択してください。")
        for index, device_name in enumerate(device_names, start=1):
            device_config = devices[device_name]
            display_name = device_config.get("display_name", device_name)
            print(f"{index}. {display_name}")

        default_index = 1
        while True:
            choice = input(
                f"番号を入力してください [default: {default_index}]: "
            ).strip()
            if not choice:
                choice = str(default_index)

            if choice.isdigit():
                choice_index = int(choice)
                if 1 <= choice_index <= len(device_names):
                    selected_device_name = device_names[choice_index - 1]
                    break

            print(f"1〜{len(device_names)} の数字を入力してください。")

    device_config = devices[selected_device_name]
    regions = device_config.get("regions", {})
    if not regions:
        raise ValueError(
            f"{selected_device_name} のOCR座標が未設定です: {REGIONS_PATH}"
        )

    display_name = device_config.get("display_name", selected_device_name)
    return display_name, {key: tuple(value) for key, value in regions.items()}


def load_region_config() -> tuple[str, dict[str, tuple[int, int, int, int]]]:
    """有効な端末のOCR対象領域をJSONファイルから読み込む。"""
    with REGIONS_PATH.open("r", encoding="utf-8") as f:
        config = json.load(f)

    if "devices" not in config:
        regions = {key: tuple(value) for key, value in config.items()}
        return "legacy", regions

    return select_device_config(config)


def load_fields_schema() -> dict[str, dict]:
    """項目ごとの文字形式ルール（スキーマ）をJSONファイルから読み込む。

    Returns:
        フィールド名をキー、文字制限ルールを値にした辞書。
    """
    if not SCHEMA_PATH.exists():
        # 将来的に新しい項目が増えても動くよう、ファイルがない場合は汎用テキスト(空辞書)を返す安全設計
        print(
            f"警告: スキーマファイルが見つかりません。汎用テキストとして処理します: {SCHEMA_PATH}"
        )
        return {}

    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema: dict[str, dict] = json.load(f)
    return schema


def confirm_fields(fields: dict[str, str], fieldnames: list[str]) -> dict[str, str]:
    """OCR結果をコンソールで確認し、必要なら手入力で修正する。"""
    confirmed: dict[str, str] = {}

    for key in fieldnames:
        value = fields.get(key, "")
        edited = input(f"{key} [{value}]: ").strip()
        confirmed[key] = edited if edited else value

    return confirmed


def find_image_paths(images_dir: Path) -> list[Path]:
    """指定されたimagesフォルダ内からOCR対象の画像をすべて取得する。"""
    if not images_dir.exists():
        raise FileNotFoundError(f"画像フォルダが見つかりません: {images_dir}")

    image_paths = sorted(
        path
        for path in images_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not image_paths:
        raise FileNotFoundError(f"imagesフォルダ内に画像が見つかりません: {images_dir}")

    return image_paths


def main() -> None:
    """画像からポケモン情報を抽出し、確認後にCSVへ追記する。"""
    images_dir, database_dir = resolve_paths()
    print(f"画像フォルダ: {images_dir}")
    print(f"出力先フォルダ: {database_dir}")

    image_paths = find_image_paths(images_dir)
    print(f"OCR対象画像数: {len(image_paths)}")

    # 1. 端末固有の「座標」を読み込む
    device_name, regions = load_region_config()
    print(f"OCR座標設定: {device_name}")

    # 2. 項目固有の「文字形式ルール」を読み込む
    schema = load_fields_schema()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    database_dir.mkdir(parents=True, exist_ok=True)
    csv_path = database_dir / f"{timestamp}.csv"

    for image_path in image_paths:
        print(f"\nOCR対象画像: {image_path}")

        # 3. 座標と文字ルールを両方渡してOCR実行
        fields = extract_pokemon_fields(image_path, regions, schema)

        confirmed = confirm_fields(fields, FIELDNAMES)
        append_pokemon(csv_path, confirmed)

        print(f"CSVへ保存しました: {csv_path}")


if __name__ == "__main__":
    main()
