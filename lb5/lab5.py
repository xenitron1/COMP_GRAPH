import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import colorsys
import math

img1 = None
img2 = None
log_img = None
mix_img = None

pic1 = None
pic2 = None
pic3 = None
pic4 = None


def show_img(img, label, num):
    global pic1, pic2, pic3, pic4

    if img is None:
        return

    temp = img.copy()
    temp.thumbnail((360, 250))
    photo = ImageTk.PhotoImage(temp)

    label.config(image=photo, text="")

    if num == 1:
        pic1 = photo
    elif num == 2:
        pic2 = photo
    elif num == 3:
        pic3 = photo
    else:
        pic4 = photo


def open1():
    global img1

    path = filedialog.askopenfilename(
        title="Открыть первое изображение",
        filetypes=[
            ("Netpbm", "*.ppm *.pgm *.pbm"),
            ("Все файлы", "*.*")
        ]
    )

    if path == "":
        return

    try:
        img1 = Image.open(path).convert("RGB")
        show_img(img1, box1, 1)
        info1.config(text=f"{img1.width} x {img1.height}")
    except:
        messagebox.showerror("Ошибка", "Не удалось открыть файл")


def open2():
    global img2

    path = filedialog.askopenfilename(
        title="Открыть второе изображение",
        filetypes=[
            ("Netpbm", "*.ppm *.pgm *.pbm"),
            ("Все файлы", "*.*")
        ]
    )

    if path == "":
        return

    try:
        img2 = Image.open(path).convert("RGB")
        show_img(img2, box2, 2)
        info2.config(text=f"{img2.width} x {img2.height}")
    except:
        messagebox.showerror("Ошибка", "Не удалось открыть файл")


def do_log():
    global log_img

    if img1 is None:
        messagebox.showwarning("Ошибка", "Сначала откройте первое изображение")
        return

    log_img = Image.new("RGB", img1.size)

    for y in range(img1.height):
        for x in range(img1.width):
            r, g, b = img1.getpixel((x, y))

            rf = r / 255
            gf = g / 255
            bf = b / 255

            h, s, v = colorsys.rgb_to_hsv(rf, gf, bf)

            v = math.log(1 + v) / math.log(2)

            nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)

            log_img.putpixel(
                (x, y),
                (
                    int(nr * 255),
                    int(ng * 255),
                    int(nb * 255)
                )
            )

    show_img(log_img, box3, 3)
    messagebox.showinfo("Готово", "Логарифмирование яркости выполнено")


def do_mix():
    global mix_img

    if img1 is None or img2 is None:
        messagebox.showwarning("Ошибка", "Сначала откройте два изображения")
        return

    if img1.size != img2.size:
        messagebox.showwarning("Ошибка", "Изображения должны быть одного размера")
        return

    mix_img = Image.new("RGB", img1.size)

    for y in range(img1.height):
        for x in range(img1.width):
            p1 = img1.getpixel((x, y))
            p2 = img2.getpixel((x, y))

            result = []

            for c1, c2 in zip(p1, p2):
                a = c1 / 255
                b = c2 / 255

                if b < 0.5:
                    c = a * b
                else:
                    c = 1 - (1 - a) * (1 - b)

                c = max(0, min(1, c))
                result.append(int(c * 255))

            mix_img.putpixel((x, y), tuple(result))

    show_img(mix_img, box4, 4)
    messagebox.showinfo("Готово", "Наложение Перекрытие выполнено")


def save_netpbm(img, title):
    if img is None:
        messagebox.showwarning("Ошибка", "Нет изображения для сохранения")
        return

    path = filedialog.asksaveasfilename(
        title=title,
        defaultextension=".ppm",
        filetypes=[
            ("PPM P3", "*.ppm")
        ]
    )

    if path == "":
        return

    try:
        w, h = img.size

        with open(path, "w", encoding="ascii") as f:
            f.write("P3\n")
            f.write(f"{w} {h}\n")
            f.write("255\n")

            for y in range(h):
                row = []

                for x in range(w):
                    r, g, b = img.getpixel((x, y))
                    row.append(f"{r} {g} {b}")

                f.write(" ".join(row) + "\n")

        messagebox.showinfo("Готово", "Файл Netpbm сохранен")
    except:
        messagebox.showerror("Ошибка", "Не удалось сохранить файл")


root = tk.Tk()
root.title("Лаба 5. Вариант 12")
root.geometry("900x700")

top = tk.Frame(root)
top.pack(pady=8)

tk.Button(top, text="Открыть 1", width=12, command=open1).pack(side=tk.LEFT, padx=3)
tk.Button(top, text="Открыть 2", width=12, command=open2).pack(side=tk.LEFT, padx=3)
tk.Button(top, text="Логарифм", width=12, command=do_log).pack(side=tk.LEFT, padx=3)
tk.Button(top, text="Перекрытие", width=12, command=do_mix).pack(side=tk.LEFT, padx=3)
tk.Button(
    top,
    text="Сохранить 1",
    width=12,
    command=lambda: save_netpbm(log_img, "Сохранить результат логарифмирования")
).pack(side=tk.LEFT, padx=3)
tk.Button(
    top,
    text="Сохранить 2",
    width=12,
    command=lambda: save_netpbm(mix_img, "Сохранить результат наложения")
).pack(side=tk.LEFT, padx=3)

main = tk.Frame(root)
main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

left = tk.Frame(main)
left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

right = tk.Frame(main)
right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

tk.Label(left, text="Исходное изображение 1").pack()
info1 = tk.Label(left, text="")
info1.pack()
box1 = tk.Label(left, text="Откройте Netpbm файл", bg="white", relief=tk.SOLID, bd=1)
box1.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

tk.Label(left, text="Логарифмирование яркости").pack()
box3 = tk.Label(left, text="Результат обработки", bg="white", relief=tk.SOLID, bd=1)
box3.pack(fill=tk.BOTH, expand=True)

tk.Label(right, text="Исходное изображение 2").pack()
info2 = tk.Label(right, text="")
info2.pack()
box2 = tk.Label(right, text="Откройте Netpbm файл", bg="white", relief=tk.SOLID, bd=1)
box2.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

tk.Label(right, text="Перекрытие").pack()
box4 = tk.Label(right, text="Результат наложения", bg="white", relief=tk.SOLID, bd=1)
box4.pack(fill=tk.BOTH, expand=True)

root.mainloop()
