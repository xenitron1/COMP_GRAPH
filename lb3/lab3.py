import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import xml.etree.ElementTree as ET

img = None
img_tk = None
lines = []


W = 760
H = 580


def get_font(size=14):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf"
    ]

    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            pass

    return ImageFont.load_default()


FONT = get_font(14)


def put(x, y, color):
    if img is None:
        return

    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), color)


def dda(x1, y1, x2, y2, color):
    dx = x2 - x1
    dy = y2 - y1

    steps = max(abs(dx), abs(dy))

    if steps == 0:
        put(x1, y1, color)
        return

    sx = dx / steps
    sy = dy / steps

    x = x1
    y = y1

    for _ in range(steps + 1):
        put(round(x), round(y), color)
        x += sx
        y += sy


def brez(x1, y1, x2, y2, color):
    dx = x2 - x1
    dy = y2 - y1

    sx = 1 if dx >= 0 else -1
    sy = 1 if dy >= 0 else -1

    dx = abs(dx)
    dy = abs(dy)

    x = x1
    y = y1

    if dx >= dy:
        f = dy / dx - 0.5 if dx != 0 else 0

        for _ in range(dx + 1):
            put(x, y, color)

            if f >= 0:
                y += sy
                f -= 1

            x += sx

            if dx != 0:
                f += dy / dx
    else:
        f = dx / dy - 0.5 if dy != 0 else 0

        for _ in range(dy + 1):
            put(x, y, color)

            if f >= 0:
                x += sx
                f -= 1

            y += sy

            if dy != 0:
                f += dx / dy


def brez_int(x1, y1, x2, y2, color):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)

    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1

    err = dx - dy
    x = x1
    y = y1

    while True:
        put(x, y, color)

        if x == x2 and y == y2:
            break

        e2 = 2 * err

        if e2 > -dy:
            err -= dy
            x += sx

        if e2 < dx:
            err += dx
            y += sy


def built_in(x1, y1, x2, y2, color):
    d = ImageDraw.Draw(img)
    d.line((x1, y1, x2, y2), fill=color, width=1)


def draw_frame():
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, img.width - 1, img.height - 1), outline="gray")
    d.line((380, 0, 380, 579), fill="gray")
    d.line((0, 290, 759, 290), fill="gray")
    d.text((20, 10), "ЦДА", fill="black", font=FONT)
    d.text((400, 10), "Брезенхем", fill="black", font=FONT)
    d.text((20, 300), "Целочисленный Брезенхем", fill="black", font=FONT)
    d.text((400, 300), "Встроенный метод", fill="black", font=FONT)


def read_svg():
    global lines

    path = filedialog.askopenfilename(
        title="Открыть SVG",
        filetypes=[("SVG", "*.svg"), ("Все файлы", "*.*")]
    )

    if path == "":
        return

    try:
        tree = ET.parse(path)
        root = tree.getroot()

        found = []

        for elem in root.iter():
            tag = elem.tag.lower()

            if tag.endswith("line"):
                x1 = round(float(elem.get("x1", "0")))
                y1 = round(float(elem.get("y1", "0")))
                x2 = round(float(elem.get("x2", "0")))
                y2 = round(float(elem.get("y2", "0")))
                found.append((x1, y1, x2, y2))

        if len(found) == 0:
            messagebox.showwarning("Ошибка", "В SVG не найдено ни одного отрезка")
            return

        lines = found
        info.config(text=f"Отрезков: {len(lines)}")
        messagebox.showinfo("Готово", "SVG файл считан")
    except:
        messagebox.showerror("Ошибка", "Не удалось прочитать SVG файл")


def build():
    global img

    if len(lines) == 0:
        messagebox.showwarning("Ошибка", "Сначала откройте SVG файл")
        return

    img = Image.new("RGB", (W, H), "white")
    draw_frame()

    for x1, y1, x2, y2 in lines:
        dda(x1, y1, x2, y2, (0, 0, 0))
        brez(x1 + 380, y1, x2 + 380, y2, (0, 0, 0))
        brez_int(x1, y1 + 290, x2, y2 + 290, (0, 0, 0))
        built_in(x1 + 380, y1 + 290, x2 + 380, y2 + 290, (0, 0, 0))

    show_img()


def show_img():
    global img_tk

    if img is None:
        return

    temp = img.copy()
    temp.thumbnail((930, 700))

    img_tk = ImageTk.PhotoImage(temp)
    picture.config(image=img_tk, text="")


def save_img():
    if img is None:
        messagebox.showwarning("Ошибка", "Сначала постройте рисунок")
        return

    path = filedialog.asksaveasfilename(
        title="Сохранить изображение",
        defaultextension=".png",
        filetypes=[
            ("PNG", "*.png"),
            ("BMP", "*.bmp")
        ]
    )

    if path == "":
        return

    try:
        img.save(path)
        messagebox.showinfo("Готово", "Файл сохранен")
    except:
        messagebox.showerror("Ошибка", "Не удалось сохранить файл")


def save_pbm():
    if img is None:
        messagebox.showwarning("Ошибка", "Сначала постройте рисунок")
        return

    path = filedialog.asksaveasfilename(
        title="Сохранить PBM",
        defaultextension=".pbm",
        filetypes=[
            ("PBM", "*.pbm"),
            ("Текстовый файл", "*.txt")
        ]
    )

    if path == "":
        return

    try:
        w, h = img.size

        with open(path, "w", encoding="ascii") as f:
            f.write("P1\n")
            f.write(f"{w} {h}\n")

            for y in range(h):
                row = []

                for x in range(w):
                    r, g, b = img.getpixel((x, y))
                    bright = 0.299 * r + 0.587 * g + 0.114 * b

                    if bright < 128:
                        row.append("1")
                    else:
                        row.append("0")

                f.write(" ".join(row) + "\n")

        messagebox.showinfo("Готово", "PBM файл сохранен")
    except:
        messagebox.showerror("Ошибка", "Не удалось сохранить PBM")


root = tk.Tk()
root.title("Лаба 3. Вариант 12")
root.geometry("980x760")

top = tk.Frame(root)
top.pack(pady=8)

tk.Button(top, text="Открыть SVG", width=15, command=read_svg).pack(side=tk.LEFT, padx=4)
tk.Button(top, text="Построить", width=15, command=build).pack(side=tk.LEFT, padx=4)
tk.Button(top, text="Сохранить", width=15, command=save_img).pack(side=tk.LEFT, padx=4)
tk.Button(top, text="PBM", width=10, command=save_pbm).pack(side=tk.LEFT, padx=4)

info = tk.Label(top, text="Отрезков: 0")
info.pack(side=tk.LEFT, padx=10)

picture = tk.Label(
    root,
    text="Откройте SVG файл и нажмите Построить",
    bg="white",
    bd=1,
    relief=tk.SOLID
)
picture.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

root.mainloop()
