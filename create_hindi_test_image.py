from PIL import Image, ImageDraw, ImageFont

text = "नमस्ते विश्व\nयह एक परीक्षण है"
font_path = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
font = ImageFont.truetype(font_path, 40)
lines = text.split("\n")

# Use textbbox for accurate measurements
bbox_sizes = [ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), line, font=font) for line in lines]
width = max(b[2] - b[0] for b in bbox_sizes) + 40
height = sum(b[3] - b[1] for b in bbox_sizes) + 40
img = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(img)
y = 20
for line, bbox in zip(lines, bbox_sizes):
    draw.text((20, y), line, font=font, fill="black")
    y += bbox[3] - bbox[1] + 10
img.save("hindi_test.png")
print("Created hindi_test.png")
