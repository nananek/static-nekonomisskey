import os
import json
from psd_tools import PSDImage
from PIL import Image, ImageFilter, ImageOps
import numpy as np
import math

psd_path = 'map.psd'
output_dir = 'slides'
html_path = 'index.html'
margin = 20

outline_width = 5  # px
outline_color = (0, 0, 0, 0xcc) # RGBAで指定可能

os.makedirs(output_dir, exist_ok=True)

psd = PSDImage.open(psd_path)
base = psd[0].topil()
canvas_size = base.size

slide_files = []
for i, layer in enumerate(psd[1:], start=1):
    layer_img = layer.topil()
    w, h = layer_img.size
    double_size = (w * 2, h * 2)
    double_img = Image.new('RGBA', double_size, (0, 0, 0, 0))
    double_img.paste(layer_img, (w // 2, h // 2), layer_img)
    # --- アウトライン処理 ---
    alpha = double_img.split()[-1]
    outline_mask = ImageOps.expand(alpha, border=outline_width, fill=0)
    outline_mask = outline_mask.filter(ImageFilter.MaxFilter(outline_width * 2 + 1))
    outline_mask = outline_mask.crop((outline_width, outline_width, alpha.width + outline_width, alpha.height + outline_width))
    outline_img = Image.new('RGBA', double_img.size, (0, 0, 0, 0))
    outline_arr = np.array(outline_img)
    mask_arr = np.array(outline_mask)
    # RGBA対応
    if len(outline_color) == 4:
        rgba = np.array(outline_color, dtype=np.uint8)
        outline_arr[mask_arr > 0] = rgba
    else:
        # 3要素(RGB)の場合はアルファ255
        rgb = np.array(list(outline_color) + [255], dtype=np.uint8)
        outline_arr[mask_arr > 0] = rgb
    outline_img = Image.fromarray(outline_arr, 'RGBA')
    orig_alpha = np.array(alpha)
    outline_arr[..., 3] = np.where(orig_alpha > 0, 0, outline_arr[..., 3])
    outline_img = Image.fromarray(outline_arr, 'RGBA')
    outline_img.paste(double_img, (0, 0), double_img)
    # --- 余白トリミング ---
    bbox = outline_img.getbbox()
    if not bbox:
        continue
    trimmed_img = outline_img.crop(bbox)
    trim_w, trim_h = trimmed_img.size
    # --- offset調整 ---
    offset_x, offset_y = layer.offset
    # 元レイヤーの中心（キャンバス座標）
    center_x = offset_x + w // 2
    center_y = offset_y + h // 2
    # トリミング後画像の中心（ローカル座標）
    bbox_left, bbox_top, bbox_right, bbox_bottom = bbox
    trim_center_x = (bbox_right - bbox_left) // 2
    trim_center_y = (bbox_bottom - bbox_top) // 2
    # キャンバス上の貼り付け位置
    paste_x = center_x - trim_center_x
    paste_y = center_y - trim_center_y
    # full_layerにアウトライン→元画像の順で合成
    full_layer = Image.new('RGBA', canvas_size, (0, 0, 0, 0))
    full_layer.paste(trimmed_img, (paste_x, paste_y), trimmed_img)  # アウトライン
    # 元画像も2倍・トリミングして同じ位置に貼る（RGB部分は完全不透明で上書き）
    trimmed_orig = double_img.crop(bbox)
    # RGB部分だけをfull_layerに上書き
    rgb = trimmed_orig.convert('RGB')
    mask = trimmed_orig.split()[-1].point(lambda a: 255 if a > 0 else 0)
    rgb_img = Image.new('RGBA', trimmed_orig.size)
    rgb_img.paste(rgb, (0, 0))
    full_layer.paste(rgb_img, (paste_x, paste_y), mask)

    bbox = layer.bbox
    if not bbox:
        continue
    x1, y1, x2, y2 = bbox
    # bbox中心
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    crop_w, crop_h = 1280, 720
    bbox_w = x2 - x1
    bbox_h = y2 - y1
    # bboxが1280x720より大きい場合は、bbox全体が収まる最小の16:9サイズに拡大
    scale_w = bbox_w / 1280
    scale_h = bbox_h / 720
    scale = max(1, max(scale_w, scale_h))
    crop_w = math.ceil(1280 * scale)
    crop_h = math.ceil(720 * scale)
    # 切り出し範囲を決定
    left = max(center_x - crop_w // 2, 0)
    top = max(center_y - crop_h // 2, 0)
    right = min(left + crop_w, canvas_size[0])
    bottom = min(top + crop_h, canvas_size[1])
    # 右端・下端が足りない場合はleft/topを調整
    if right - left < crop_w:
        left = max(right - crop_w, 0)
    if bottom - top < crop_h:
        top = max(bottom - crop_h, 0)

    bg_crop = base.crop((left, top, right, bottom))
    overlay_crop = full_layer.crop((left, top, right, bottom))

    result = Image.new('RGBA', bg_crop.size)
    result.paste(bg_crop, (0, 0))
    result.paste(overlay_crop, (0, 0), overlay_crop)

    filename = f'slide_{i:02}.png'
    filepath = os.path.join(output_dir, filename)
    result.save(filepath)

    slide_files.append(f"{output_dir}/{filename}")

# slides.jsonとして保存
slides_json_path = 'slides.json'
with open(slides_json_path, 'w', encoding='utf-8') as f:
    json.dump(slide_files, f, ensure_ascii=False, indent=2)

print(f'✅ slides.json を出力しました: {slides_json_path}')
