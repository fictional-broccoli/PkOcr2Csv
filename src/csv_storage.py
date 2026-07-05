"""ポケモン情報をCSVへ保存するための処理。

CSVは現時点の正規データとして扱い、1行につき1匹のポケモン情報を保存します。
"""

import csv
from pathlib import Path


# CSVに出力する列の順番を固定する。
FIELDNAMES = [
    "name",
    "nickname",
    "type",
    "hp",
    "hp_effort",
    "attack",
    "attack_effort",
    "defense",
    "defense_effort",
    "sp_attack",
    "sp_attack_effort",
    "sp_defense",
    "sp_defense_effort",
    "speed",
    "speed_effort",
    "nature",
    "ability",
    "moves1",
    "moves2",
    "moves3",
    "moves4",
]


def append_pokemon(csv_path: Path, row: dict[str, str]) -> None:
    """ポケモン情報をCSVへ1行追記する。

    Args:
        csv_path: 保存先CSVファイルのパス。
        row: 保存するポケモン情報。存在しない列は空文字として保存する。
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    if csv_path.is_dir():
        raise IsADirectoryError(
            f"CSV保存先がフォルダになっています。フォルダを削除するか、保存先を変更してください: {csv_path}"
        )

    file_exists = csv_path.exists()

    with csv_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)

        if not file_exists:
            writer.writeheader()

        writer.writerow({field: row.get(field, "") for field in FIELDNAMES})
