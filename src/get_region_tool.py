import glob
import os
import cv2

# スクリプトがあるフォルダ（src）を基準にする
base_dir = os.path.dirname(os.path.abspath(__file__))

# ターゲットとなるフォルダのパス（getPokemonStatus/images）
target_dir = os.path.join(base_dir, "..", "images")

# フォルダ内のすべてのPNGおよびJPGファイルのパスをリストで取得
image_files = glob.glob(os.path.join(target_dir, "*.png")) + glob.glob(
    os.path.join(target_dir, "*.jpg")
)

# ファイル名順でソート（昇順）
image_files.sort()

# ファイルが存在するかチェック
if not image_files:
    print(
        f"【エラー】指定されたフォルダ内に画像ファイル（.png/.jpg）が見つかりません:\n{os.path.abspath(target_dir)}"
    )
    exit()

# 一番最初（インデックス 0）のファイルのパスを取得
image_path = image_files[0]
print(f"読み込み中の画像: {os.path.basename(image_path)}")

# 画像の読み込み
img = cv2.imread(image_path)

if img is None:
    print(f"【エラー】画像の読み込みに失敗しました: {image_path}")
    exit()

img_display = img.copy()


# マウスクリック時のイベントリスナー
def click_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # ターミナルに座標を表示 (xmin=x, ymin=y)
        # print(f"クリックした座標 ➡ X(xmin): {x}, Y(ymin): {y}")
        print(f"クリックした座標 ➡ {x}, {y}")

        # 画像上にクリックした座標を視覚的に描画
        cv2.circle(img_display, (x, y), 5, (0, 0, 255), -1)
        cv2.putText(
            img_display,
            f"{x},{y}",
            (x + 10, y + 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            1,
        )
        cv2.imshow("Coordinate Finder", img_display)


# ウィンドウを表示してマウスイベントを待機
cv2.imshow("Coordinate Finder", img_display)
cv2.setMouseCallback("Coordinate Finder", click_event)

print("画像上の赤枠の【左上】と【右下】をクリックしてください。")
print("終了するには画像ウィンドウを選択した状態で 'q' キーを押してください。")

cv2.waitKey(0)
cv2.destroyAllWindows()
