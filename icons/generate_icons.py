from PIL import Image, ImageDraw

SIZE = 64

def make_icon(color, name):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # cerc central
    draw.ellipse((8, 8, SIZE-8, SIZE-8), fill=color)

    img.save(f"icons/{name}.png")

make_icon((120, 120, 120, 255), "idle")      # gri
make_icon((59, 178, 74, 255), "active")      # verde
make_icon((217, 164, 65, 255), "warning")    # galben
make_icon((178, 59, 59, 255), "error")       # roșu

print("Icons generated.")