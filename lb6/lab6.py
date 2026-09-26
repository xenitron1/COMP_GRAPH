import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import math

src = None
aff = None
back = None
func = None

p1 = None
p2 = None
p3 = None
p4 = None


def show(img, label, num):
    global p1, p2, p3, p4

    if img is None:
        return

    temp = img.copy()
    temp.thumbnail((330, 240))
    photo = ImageTk.PhotoImage(temp)

    label.config(image=photo, text="")

    if num == 1:
        p1 = photo
    elif num == 2:
        p2 = photo
    elif num == 3:
        p3 = photo
    else:
        p4 = photo


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
        show(src, box1, 1)
        info.config(text=f"{src.width} x {src.height}")
    except:
        messagebox.showerror("Ошибка", "Не удалось открыть файл")


def get_shift():
    try:
        dx = int(dx_entry.get())
        dy = int(dy_entry.get())
        return dx, dy
    except:
        messagebox.showerror("Ошибка", "Смещение должно быть целым числом")
        return None


def affine():
    global aff

    if src is None:
        messagebox.showwarning("Ошибка", "Сначала откройте изображение")
        return

    shift = get_shift()

    if shift is None:
        return

    dx, dy = shift
    w, h = src.size

    aff = Image.new("RGB", (w, h), "white")

    # Вариант 12: перенос и отражение.
    # Прямое преобразование:
    # i = w - 1 - x - dx
    # j = y + dy
    #
    # Для заполнения результата используем обратную функцию:
    # x = w - 1 - i - dx
    # y = j - dy

    for j in range(h):
        for i in range(w):
            x = w - 1 - i - dx
            y = j - dy

            if 0 <= x < w and 0 <= y < h:
                aff.putpixel((i, j), src.getpixel((x, y)))

    show(aff, box2, 2)


def inverse_affine():
    global back

    if aff is None:
        messagebox.showwarning("Ошибка", "Сначала выполните аффинное преобразование")
        return

    shift = get_shift()

    if shift is None:
        return

    dx, dy = shift
    w, h = aff.size

    back = Image.new("RGB", (w, h), "white")

    # Восстановление исходного изображения.
    # Для каждой точки результата берем точку
    # прямого преобразования из aff.

    for y in range(h):
        for x in range(w):
            i = w - 1 - x - dx
            j = y + dy

            if 0 <= i < w and 0 <= j < h:
                back.putpixel((x, y), aff.getpixel((i, j)))

    show(back, box3, 3)


def functional():
    global func

    if src is None:
        messagebox.showwarning("Ошибка", "Сначала откройте изображение")
        return

    w, h = src.size
    func = Image.new("RGB", (w, h), "white")

    # Вариант 12:
    # i = x^2 / (1 + x)
    # j = y
    #
    # Обратная функция:
    # x = (i + sqrt(i^2 + 4*i)) / 2

    for j in range(h):
        for i in range(w):
            x = (i + math.sqrt(i * i + 4 * i)) / 2
            y = j

            x = round(x)

            if 0 <= x < w:
                func.putpixel((i, j), src.getpixel((x, y)))

    show(func, box4, 4)


def save_img(img, title):
    if img is None:
        messagebox.showwarning("Ошибка", "Нет изображения для сохранения")
        return

    path = filedialog.asksaveasfilename(
        title=title,
        defaultextension=".png",
        filetypes=[
            ("PNG", "*.png"),
            ("BMP", "*.bmp"),
            ("JPEG", "*.jpg")
        ]
    )

    if path == "":
        return

    try:
        img.save(path)
        messagebox.showinfo("Готово", "Файл сохранен")
    except:
        messagebox.showerror("Ошибка", "Не удалось сохранить файл")


root = tk.Tk()
root.title("Лаба 6. Вариант 12")
root.geometry("900x690")

top = tk.Frame(root)
top.pack(pady=8)

tk.Button(top, text="Открыть", width=11, command=open_img).pack(side=tk.LEFT, padx=3)

tk.Label(top, text="dx:").pack(side=tk.LEFT)
dx_entry = tk.Entry(top, width=5)
dx_entry.insert(0, "30")
dx_entry.pack(side=tk.LEFT, padx=3)

tk.Label(top, text="dy:").pack(side=tk.LEFT)
dy_entry = tk.Entry(top, width=5)
dy_entry.insert(0, "20")
dy_entry.pack(side=tk.LEFT, padx=3)

tk.Button(top, text="Аффинное", width=11, command=affine).pack(side=tk.LEFT, padx=3)
tk.Button(top, text="Обратное", width=11, command=inverse_affine).pack(side=tk.LEFT, padx=3)
tk.Button(top, text="Функция", width=11, command=functional).pack(side=tk.LEFT, padx=3)

info = tk.Label(top, text="")
info.pack(side=tk.LEFT, padx=8)

main = tk.Frame(root)
main.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

left = tk.Frame(main)
left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

right = tk.Frame(main)
right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

tk.Label(left, text="Исходное изображение").pack()
box1 = tk.Label(left, text="Откройте файл", bg="white", relief=tk.SOLID, bd=1)
box1.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

tk.Label(left, text="Обратное аффинное").pack()
box3 = tk.Label(left, text="Результат", bg="white", relief=tk.SOLID, bd=1)
box3.pack(fill=tk.BOTH, expand=True)

tk.Label(right, text="Перенос + отражение").pack()
box2 = tk.Label(right, text="Результат", bg="white", relief=tk.SOLID, bd=1)
box2.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

tk.Label(right, text="Функциональное преобразование").pack()
box4 = tk.Label(right, text="Результат", bg="white", relief=tk.SOLID, bd=1)
box4.pack(fill=tk.BOTH, expand=True)

bottom = tk.Frame(root)
bottom.pack(pady=7)

tk.Button(
    bottom,
    text="Сохранить аффинное",
    command=lambda: save_img(aff, "Сохранить аффинное преобразование")
).pack(side=tk.LEFT, padx=3)

tk.Button(
    bottom,
    text="Сохранить обратное",
    command=lambda: save_img(back, "Сохранить обратное преобразование")
).pack(side=tk.LEFT, padx=3)

tk.Button(
    bottom,
    text="Сохранить функцию",
    command=lambda: save_img(func, "Сохранить функциональное преобразование")
).pack(side=tk.LEFT, padx=3)

root.mainloop()
