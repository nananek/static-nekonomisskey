import os
import json
from psd_tools import PSDImage
from PIL import Image

psd_path = 'map.psd'
output_dir = 'slides'
html_path = 'index.html'
margin = 20

os.makedirs(output_dir, exist_ok=True)

psd = PSDImage.open(psd_path)
base = psd[0].topil()
canvas_size = base.size

slide_files = []
for i, layer in enumerate(psd[1:], start=1):
    layer_img = layer.topil()
    offset_x, offset_y = layer.offset
    full_layer = Image.new('RGBA', canvas_size, (0, 0, 0, 0))
    full_layer.paste(layer_img, (offset_x, offset_y), layer_img)

    bbox = layer.bbox
    if not bbox:
        continue
    x1, y1, x2, y2 = bbox
    left = max(x1 - margin, 0)
    top = max(y1 - margin, 0)
    right = min(x2 + margin, canvas_size[0])
    bottom = min(y2 + margin, canvas_size[1])

    bg_crop = base.crop((left, top, right, bottom))
    overlay_crop = full_layer.crop((left, top, right, bottom))

    result = Image.new('RGBA', bg_crop.size)
    result.paste(bg_crop, (0, 0))
    result.paste(overlay_crop, (0, 0), overlay_crop)

    filename = f'slide_{i:02}.png'
    filepath = os.path.join(output_dir, filename)
    result.save(filepath)

    slide_files.append(f"{output_dir}/{filename}")

# HTML全体
slides_json = json.dumps(slide_files, ensure_ascii=False, indent=2)
html_content = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>スライドショー</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    html, body {{
      height: 100%;
    }}
    body {{
      background-color: #f8f9fa;
      text-align: center;
      padding: 0;
      margin: 0;
      height: 100vh;
    }}
    .container {{
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}
    .slide-wrapper {{
      flex-grow: 1;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    #slide {{
      max-height: 90vh;
      max-width: 100%;
      object-fit: contain;
      border: 1px solid #ccc;
      background: white;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="slide-wrapper">
      <img id="slide" src="" alt="Slide" class="rounded shadow">
    </div>
    <div class="mt-4 d-flex justify-content-center align-items-center gap-3">
      <button class="btn btn-secondary" onclick="prev()">前へ</button>
      <span id="counter"></span>
      <button class="btn btn-primary" onclick="next()">次へ</button>
    </div>
  </div>

  <script id="slides-json" type="application/json">
{slides_json}
  </script>

  <script>
    const slides = JSON.parse(document.getElementById("slides-json").textContent.trim());
    let current = 0;

    const img = document.getElementById('slide');
    const counter = document.getElementById('counter');

    function update() {{
      img.src = slides[current];
      counter.textContent = (current + 1) + ' / ' + slides.length;
    }}

    function prev() {{
      current = (current - 1 + slides.length) % slides.length;
      update();
    }}

    function next() {{
      current = (current + 1) % slides.length;
      update();
    }}

    update();
  </script>
</body>
</html>
'''

# HTML出力
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f'✅ index.html を出力しました: {html_path}')
