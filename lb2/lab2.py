import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw

src = None
dst = None
src_tk = None
dst_tk = None


def show_src():
    global src_tk
    if src is None:
        return
    temp = src.copy()
    temp.thumbnail((420, 320))
    src_tk = ImageTk.PhotoImage(temp)
    src_box.config(image=src_tk, text="")


def show_dst():
    global dst_tk
    if dst is None:
        return
    temp = dst.copy()
    temp.thumbnail((420, 320))
    dst_tk = ImageTk.PhotoImage(temp)
    dst_box.config(image=dst_tk, text="")


def create_img():
    global dst
    try:
        w = int(width_entry.get())
        h = int(height_entry.get())

        if w < 200 or h < 200:
            messagebox.showwarning("Ошибка", "Размер должен быть не меньше 200 x 200")
            return

        dst = Image.new("RGB", (w, h), "white")
        show_dst()
    except:
        messagebox.showerror("Ошибка", "Неверно указан размер")


def open_img():
    global src

    path = filedialog.askopenfilename(
        title="Открыть изображение",
        filetypes=[
            ("Изображения", "*.png *.jpg *.jpeg *.bmp *.ppm *.pgm *.pbm"),
            ("Все файлы", "*.*")
        ]
    )

    if path == "":
        return

    try:
        src = Image.open(path).convert("RGB")
        show_src()
    except:
        messagebox.showerror("Ошибка", "Не удалось открыть файл")


def copy_part():
    global dst

    if src is None or dst is None:
        messagebox.showwarning("Ошибка", "Сначала откройте и создайте изображения")
        return

    sw, sh = src.size
    dw, dh = dst.size

    cx = sw // 2
    cy = sh // 2

    th = min(100, sh // 3)
    half = min(60, sw // 4)

    if th < 10 or half < 10:
        messagebox.showwarning("Ошибка", "Исходное изображение слишком маленькое")
        return

    start_x = 20
    start_y = dh - th - 20

    for y in range(th + 1):
        part = int(half * y / th)

        for x in range(-part, part + 1):
            sx = cx + x
            sy = cy + y

            dx = start_x + half + x
            dy = start_y + y

            if 0 <= sx < sw and 0 <= sy < sh:
                if 0 <= dx < dw and 0 <= dy < dh:
                    dst.putpixel((dx, dy), src.getpixel((sx, sy)))

    show_dst()


def draw_axes():
    if dst is None:
        messagebox.showwarning("Ошибка", "Сначала создайте новое изображение")
        return

    w, h = dst.size
    d = ImageDraw.Draw(dst)

    x0 = w // 2
    y0 = h // 2

    d.line((20, y0, w - 20, y0), fill="black", width=1)
    d.line((x0, 20, x0, h - 20), fill="black", width=1)

    d.line((w - 30, y0 - 5, w - 20, y0), fill="black")
    d.line((w - 30, y0 + 5, w - 20, y0), fill="black")
    d.line((x0 - 5, 30, x0, 20), fill="black")
    d.line((x0 + 5, 30, x0, 20), fill="black")

    step = 40

    for x in range(x0, w - 20, step):
        d.line((x, y0 - 3, x, y0 + 3), fill="black")

    for x in range(x0, 20, -step):
        d.line((x, y0 - 3, x, y0 + 3), fill="black")

    for y in range(y0, h - 20, step):
        d.line((x0 - 3, y, x0 + 3, y), fill="black")

    for y in range(y0, 20, -step):
        d.line((x0 - 3, y, x0 + 3, y), fill="black")

    d.text((w - 18, y0 + 5), "x", fill="black")
    d.text((x0 + 5, 5), "y", fill="black")
    d.text((x0 + 5, y0 + 5), "0", fill="black")

    show_dst()


def draw_graph():
    if dst is None:
        messagebox.showwarning("Ошибка", "Сначала создайте новое изображение")
        return

    w, h = dst.size
    d = ImageDraw.Draw(dst)

    x0 = w // 2
    y0 = h // 2
    scale = 40
    old = None

    for px in range(20, w - 20):
        x = (px - x0) / scale

        if abs(x) < 0.15:
            old = None
            continue

        y = 1 / (x * x)
        py = y0 - int(y * scale)

        if 20 <= py < h - 20:
            if old is not None:
                d.line((old[0], old[1], px, py), fill=(0, 0, 255), width=2)
            old = (px, py)
        else:
            old = None

    d.text((w - 120, 25), "y = (1/x)^2", fill=(0, 0, 255))
    show_dst()


def save_img():
    if dst is None:
        messagebox.showwarning("Ошибка", "Нет изображения для сохранения")
        return

    path = filedialog.asksaveasfilename(
        title="Сохранить изображение",
        defaultextension=".png",
        filetypes=[
            ("PNG", "*.png"),
            ("JPG", "*.jpg"),
            ("BMP", "*.bmp")
        ]
    )

    if path == "":
        return

    try:
        dst.save(path)
        messagebox.showinfo("Готово", "Изображение сохранено")
    except:
        messagebox.showerror("Ошибка", "Не удалось сохранить файл")


def save_pbm():
    if dst is None:
        messagebox.showwarning("Ошибка", "Нет изображения для сохранения")
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
        w, h = dst.size

        with open(path, "w", encoding="ascii") as f:
            f.write("P1\n")
            f.write(f"{w} {h}\n")

            for y in range(h):
                row = []

                for x in range(w):
                    r, g, b = dst.getpixel((x, y))
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
root.title("Лаба 2. Вариант 12")
root.geometry("1020x610")

top = tk.Frame(root)
top.pack(pady=8)

tk.Label(top, text="Ширина:").pack(side=tk.LEFT)
width_entry = tk.Entry(top, width=7)
width_entry.insert(0, "600")
width_entry.pack(side=tk.LEFT, padx=4)

tk.Label(top, text="Высота:").pack(side=tk.LEFT)
height_entry = tk.Entry(top, width=7)
height_entry.insert(0, "400")
height_entry.pack(side=tk.LEFT, padx=4)

tk.Button(top, text="Создать", width=10, command=create_img).pack(side=tk.LEFT, padx=2)
tk.Button(top, text="Открыть", width=10, command=open_img).pack(side=tk.LEFT, padx=2)
tk.Button(top, text="Перенести", width=10, command=copy_part).pack(side=tk.LEFT, padx=2)
tk.Button(top, text="Оси", width=8, command=draw_axes).pack(side=tk.LEFT, padx=2)
tk.Button(top, text="График", width=8, command=draw_graph).pack(side=tk.LEFT, padx=2)
tk.Button(top, text="Сохранить", width=10, command=save_img).pack(side=tk.LEFT, padx=2)
tk.Button(top, text="PBM", width=8, command=save_pbm).pack(side=tk.LEFT, padx=2)

main = tk.Frame(root)
main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

left = tk.Frame(main)
left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

right = tk.Frame(main)
right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

tk.Label(left, text="Исходное изображение").pack()
src_box = tk.Label(left, text="Откройте файл", bg="white", relief=tk.SOLID, bd=1)
src_box.pack(fill=tk.BOTH, expand=True)

tk.Label(right, text="Новое изображение").pack()
dst_box = tk.Label(right, text="Создайте изображение", bg="white", relief=tk.SOLID, bd=1)
dst_box.pack(fill=tk.BOTH, expand=True)

root.mainloop()
