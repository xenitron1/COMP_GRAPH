import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import xml.etree.ElementTree as ET
import math

img = None
img_tk = None
sides = None

PW = 400
PH = 320
W = PW * 2 + 20
H = PH * 2 + 20


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


def read_svg():
    global sides

    path = filedialog.askopenfilename(
        title="Открыть SVG",
        filetypes=[("SVG", "*.svg"), ("Все файлы", "*.*")]
    )

    if path == "":
        return

    try:
        tree = ET.parse(path)
        root = tree.getroot()

        lengths = []

        for elem in root.iter():
            if elem.tag.lower().endswith("line"):
                x1 = float(elem.get("x1", "0"))
                y1 = float(elem.get("y1", "0"))
                x2 = float(elem.get("x2", "0"))
                y2 = float(elem.get("y2", "0"))

                length = math.hypot(x2 - x1, y2 - y1)
                lengths.append(length)

        if len(lengths) < 3:
            messagebox.showwarning(
                "Ошибка",
                "В SVG должно быть минимум 3 отрезка"
            )
            return

        # Первые три отрезка считаем сторонами AB, BC и CA
        c = lengths[0]
        a = lengths[1]
        b = lengths[2]

        if a + b <= c or a + c <= b or b + c <= a:
            messagebox.showwarning(
                "Ошибка",
                "Длины первых трех отрезков не образуют треугольник"
            )
            return

        sides = (a, b, c)

        info.config(
            text=f"a={a:.1f}  b={b:.1f}  c={c:.1f}"
        )

        messagebox.showinfo(
            "Готово",
            "Длины сторон считаны из SVG"
        )

    except:
        messagebox.showerror(
            "Ошибка",
            "Не удалось прочитать SVG файл"
        )


def triangle_data(a, b, c):
    # A=(0,0), B=(c,0), C=(x,y)
    x = (b * b + c * c - a * a) / (2 * c)
    y2 = b * b - x * x

    if y2 <= 0:
        return None

    y = math.sqrt(y2)

    A = (0.0, 0.0)
    B = (c, 0.0)
    C = (x, y)

    s = (a + b + c) / 2
    area = c * y / 2

    ra = area / (s - a)
    rb = area / (s - b)
    rc = area / (s - c)

    ia = (
        (-a * A[0] + b * B[0] + c * C[0]) / (-a + b + c),
        (-a * A[1] + b * B[1] + c * C[1]) / (-a + b + c)
    )

    ib = (
        (a * A[0] - b * B[0] + c * C[0]) / (a - b + c),
        (a * A[1] - b * B[1] + c * C[1]) / (a - b + c)
    )

    ic = (
        (a * A[0] + b * B[0] - c * C[0]) / (a + b - c),
        (a * A[1] + b * B[1] - c * C[1]) / (a + b - c)
    )

    return A, B, C, (ia, ra), (ib, rb), (ic, rc)


def fit_geometry(data):
    A, B, C, ca, cb, cc = data
    circles = [ca, cb, cc]

    xs = [A[0], B[0], C[0]]
    ys = [A[1], B[1], C[1]]

    for center, r in circles:
        xs.extend([center[0] - r, center[0] + r])
        ys.extend([center[1] - r, center[1] + r])

    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)

    margin = 35
    sx = (PW - margin * 2) / (max_x - min_x)
    sy = (PH - margin * 2 - 20) / (max_y - min_y)
    scale = min(sx, sy)

    def tr(p, ox, oy):
        x = ox + margin + (p[0] - min_x) * scale
        y = oy + PH - margin - (p[1] - min_y) * scale
        return round(x), round(y)

    return tr, scale


def put(x, y, color):
    if img is None:
        return

    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), color)


def circle_equation(cx, cy, r, color):
    r = max(1, int(round(r)))

    for x in range(-r, r + 1):
        y2 = r * r - x * x

        if y2 < 0:
            continue

        y = round(math.sqrt(y2))

        put(cx + x, cy + y, color)
        put(cx + x, cy - y, color)


def circle_parametric(cx, cy, r, color):
    r = max(1, int(round(r)))
    steps = max(60, int(2 * math.pi * r * 2))

    for i in range(steps + 1):
        t = 2 * math.pi * i / steps

        x = round(cx + r * math.cos(t))
        y = round(cy + r * math.sin(t))

        put(x, y, color)


def circle_brez(cx, cy, r, color):
    r = max(1, int(round(r)))

    x = 0
    y = r
    d = 3 - 2 * r

    while x <= y:
        pts = [
            (cx + x, cy + y),
            (cx - x, cy + y),
            (cx + x, cy - y),
            (cx - x, cy - y),
            (cx + y, cy + x),
            (cx - y, cy + x),
            (cx + y, cy - x),
            (cx - y, cy - x)
        ]

        for px, py in pts:
            put(px, py, color)

        if d < 0:
            d = d + 4 * x + 6
        else:
            d = d + 4 * (x - y) + 10
            y -= 1

        x += 1


def circle_builtin(cx, cy, r, color):
    r = max(1, int(round(r)))
    d = ImageDraw.Draw(img)

    d.ellipse(
        (cx - r, cy - r, cx + r, cy + r),
        outline=color,
        width=1
    )


def draw_panel(ox, oy, title, method, data):
    d = ImageDraw.Draw(img)

    d.rectangle(
        (ox, oy, ox + PW - 1, oy + PH - 1),
        outline="gray"
    )

    d.text(
        (ox + 12, oy + 8),
        title,
        fill="black",
        font=FONT
    )

    tr, scale = fit_geometry(data)

    A, B, C, ca, cb, cc = data

    pa = tr(A, ox, oy)
    pb = tr(B, ox, oy)
    pc = tr(C, ox, oy)

    # Треугольник
    d.line((pa[0], pa[1], pb[0], pb[1]), fill="black", width=1)
    d.line((pb[0], pb[1], pc[0], pc[1]), fill="black", width=1)
    d.line((pc[0], pc[1], pa[0], pa[1]), fill="black", width=1)

    colors = [
        (220, 0, 0),
        (0, 140, 0),
        (0, 0, 220)
    ]

    for (center, r), color in zip([ca, cb, cc], colors):
        cp = tr(center, ox, oy)
        rr = r * scale
        method(cp[0], cp[1], rr, color)


def build():
    global img

    if sides is None:
        messagebox.showwarning(
            "Ошибка",
            "Сначала откройте SVG файл"
        )
        return

    a, b, c = sides
    data = triangle_data(a, b, c)

    if data is None:
        messagebox.showerror(
            "Ошибка",
            "Не удалось построить треугольник"
        )
        return

    img = Image.new("RGB", (W, H), "white")

    draw_panel(
        5, 5,
        "По уравнению окружности",
        circle_equation,
        data
    )

    draw_panel(
        PW + 15, 5,
        "Параметрическое уравнение",
        circle_parametric,
        data
    )

    draw_panel(
        5, PH + 15,
        "Брезенхем",
        circle_brez,
        data
    )

    draw_panel(
        PW + 15, PH + 15,
        "Встроенный метод",
        circle_builtin,
        data
    )

    show_img()


def show_img():
    global img_tk

    if img is None:
        return

    temp = img.copy()
    temp.thumbnail((980, 720))

    img_tk = ImageTk.PhotoImage(temp)
    picture.config(image=img_tk, text="")


def save_img():
    if img is None:
        messagebox.showwarning(
            "Ошибка",
            "Сначала постройте рисунок"
        )
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
        messagebox.showinfo(
            "Готово",
            "Файл сохранен"
        )
    except:
        messagebox.showerror(
            "Ошибка",
            "Не удалось сохранить файл"
        )


def save_pbm():
    if img is None:
        messagebox.showwarning(
            "Ошибка",
            "Сначала постройте рисунок"
        )
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

                    bright = (
                        0.299 * r +
                        0.587 * g +
                        0.114 * b
                    )

                    if bright < 200:
                        row.append("1")
                    else:
                        row.append("0")

                f.write(" ".join(row) + "\n")

        messagebox.showinfo(
            "Готово",
            "PBM файл сохранен"
        )
    except:
        messagebox.showerror(
            "Ошибка",
            "Не удалось сохранить PBM"
        )


root = tk.Tk()
root.title("Лаба 4. Вариант 12")
root.geometry("1030x780")

top = tk.Frame(root)
top.pack(pady=8)

tk.Button(
    top,
    text="Открыть SVG",
    width=15,
    command=read_svg
).pack(side=tk.LEFT, padx=4)

tk.Button(
    top,
    text="Построить",
    width=15,
    command=build
).pack(side=tk.LEFT, padx=4)

tk.Button(
    top,
    text="Сохранить",
    width=15,
    command=save_img
).pack(side=tk.LEFT, padx=4)

tk.Button(
    top,
    text="PBM",
    width=10,
    command=save_pbm
).pack(side=tk.LEFT, padx=4)

info = tk.Label(
    top,
    text="Стороны не считаны"
)
info.pack(side=tk.LEFT, padx=10)

picture = tk.Label(
    root,
    text="Откройте SVG с тремя сторонами треугольника",
    bg="white",
    bd=1,
    relief=tk.SOLID
)
picture.pack(
    fill=tk.BOTH,
    expand=True,
    padx=10,
    pady=10
)

root.mainloop()
