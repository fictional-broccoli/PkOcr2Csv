"""画像から固定領域を切り出し、Pythonライブラリだけで文字を読み取る処理。"""

from functools import lru_cache
from pathlib import Path
import re

from PIL import Image


# Pillow の crop に渡す座標。順番は (left, upper, right, lower)。
Region = tuple[int, int, int, int]


@lru_cache(maxsize=3)
def get_reader(languages: tuple[str, ...] = ("ja")):
    """EasyOCRのReaderを作成する。

    Args:
        languages: OCRで使用する言語コード。

    Returns:
        EasyOCRのReader。

    Raises:
        RuntimeError: 必要なPythonライブラリがインストールされていない場合。
    """
    try:
        import easyocr
    except ImportError as error:
        raise RuntimeError(
            "EasyOCRがインストールされていません。"
            " .venv を有効化した状態で `pip install -r requirements.txt` を実行してください。"
        ) from error

    return easyocr.Reader(list(languages), gpu=False)


def crop_region(image: Image.Image, region: Region) -> Image.Image:
    """画像から指定された矩形領域を切り出す。"""
    return image.crop(region)


def parse_and_validate(raw_text: str, rule: dict) -> str:
    """取得した文字列を、スキーマのtypeルールに基づいて補正・検証する。"""
    rule_type = rule.get("type")
    min_len = rule.get("min_len", 0)
    max_len = rule.get("max_len", 99)

    # ----------------------------------------------------
    # 1. effort: 数字のみ（0～32）
    # ----------------------------------------------------
    if rule_type == "effort":
        clean_text = re.sub(r"\D", "", raw_text)
        if not clean_text:
            return ""
        try:
            val = int(clean_text)
            # 0 〜 32 の正常範囲内
            if 0 <= val <= 32:
                return str(val)
            # 救済ロジック：桁が増えてしまった場合（例：「322」など）、先頭2桁を検証
            if len(clean_text) >= 2:
                short_val = int(clean_text[:2])
                if 0 <= short_val <= 32:
                    return str(short_val)
            return ""
        except ValueError:
            return ""

    # ----------------------------------------------------
    # 2. status: 数字のみ（2もしくは3桁）
    # ----------------------------------------------------
    elif rule_type == "status":
        clean_text = re.sub(r"\D", "", raw_text)
        if min_len <= len(clean_text) <= max_len:
            return clean_text
        return ""

    # ----------------------------------------------------
    # 3. katakana: カタカナのみ（2～6文字）
    # ----------------------------------------------------
    elif rule_type == "katakana":
        # カタカナと長音記号「ー」のみを抽出（スペースや誤認英数字を削除）
        clean_text = re.sub(r"[^ァ-ヶー]", "", raw_text)
        if min_len <= len(clean_text) <= max_len:
            return clean_text
        return ""

    # ----------------------------------------------------
    # 4. hiragana_katakana: ひらがな、カタカナ（2～9文字）
    # ----------------------------------------------------
    elif rule_type == "hiragana_katakana":
        # ひらがな、カタカナ、長音記号「ー」のみを抽出
        # ※もし「10まんボルト」などの数字混じりの技に対応させる場合は、
        # 　正規表現を r"[^ぁ-んァ-ヶー0-9０-９]" に変更してください。
        clean_text = re.sub(r"[^ぁ-んァ-ヶー0-9０-９]", "", raw_text)
        if min_len is not None and max_len is not None:
            if min_len <= len(clean_text) <= max_len:
                return clean_text
        return ""

    # ----------------------------------------------------
    # 5. any_text: 制限なし（ニックネームなど）
    # ----------------------------------------------------
    else:
        return raw_text.strip()


def read_field_with_rule(image: Image.Image, rule: dict) -> str:
    """項目のルールに最適なEasyOCR設定を選び、文字を読み取る。"""
    try:
        import numpy as np
    except ImportError as error:
        raise RuntimeError("NumPyがインストールされていません。") from error

    rule_type = rule.get("type")

    # ルールに合わせてOCRの「言語」と「許可文字」を設定
    if rule_type in ("status", "effort"):
        # 数字系は英語のみ＋数字限定にして「り」への文字化けを100%シャットアウト
        reader = get_reader(("en",))
        results = reader.readtext(np.array(image), allowlist="0123456789", detail=0)
    elif rule_type == "katakana":
        reader = get_reader(("ja",))
        results = reader.readtext(np.array(image), detail=0, paragraph=True)
    else:
        # ひらがな混じりやany_textは日本語＋英語（汎用）
        reader = get_reader(("ja", "en"))
        results = reader.readtext(np.array(image), detail=0, paragraph=True)

    raw_text = "\n".join(text.strip() for text in results if text.strip())

    return parse_and_validate(raw_text, rule)


def extract_pokemon_fields(
    image_path: Path, regions: dict[str, Region], schema: dict[str, dict]
) -> dict[str, str]:
    """画像内の複数領域を、提示されたポケモンスキーマに従ってOCR・バリデーションする。"""
    image = Image.open(image_path)
    result: dict[str, str] = {}

    for field_name, region in regions.items():
        cropped = crop_region(image, region)

        # スキーマから該当項目のルール（typeや文字数）を取得
        rule = schema.get(field_name, {"type": "any_text"})

        result[field_name] = read_field_with_rule(cropped, rule)

    return result
