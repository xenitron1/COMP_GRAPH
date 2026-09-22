import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

img = None
img_tk = None


def open_img():
    global img

    path = filedialog.askopenfilename(
        title="Открыть изображение",
        filetypes=[
            ("Изображения", "*.png *.jpg *.jpeg *.bmp *.pbm *.pgm *.ppm"),
            ("Все файлы", "*.*")
        ]
    )

    if path == "":
        return

    try:
        img = Image.open(path).convert("RGB")
        show_img()
        info.config(text=f"{img.width} x {img.height}")
    except:
        messagebox.showerror("Ошибка", "Не удалось открыть файл")


def edit_img():
    global img

    if img is None:
        messagebox.showwarning("Ошибка", "Сначала откройте изображение")
        return

    w, h = img.size

    # Вариант 12
    img.putpixel((0, 0), (64, 64, 127))
    img.putpixel((w - 1, 0), (127, 64, 127))
    img.putpixel((w - 1, h - 1), (127, 127, 64))

    show_img()
    messagebox.showinfo("Готово", "Изображение обработано")


def save_img():
    if img is None:
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
        img.save(path)
        messagebox.showinfo("Готово", "Файл сохранен")
    except:
        messagebox.showerror("Ошибка", "Не удалось сохранить файл")


def save_pbm():
    if img is None:
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
        w, h = img.size

        with open(path, "w") as f:
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


def show_img():
    global img_tk

    if img is None:
        return

    temp = img.copy()
    temp.thumbnail((900, 550))

    img_tk = ImageTk.PhotoImage(temp)
    picture.config(image=img_tk, text="")


root = tk.Tk()
root.title("Лаба 1. Вариант 12")
root.geometry("950x650")

top = tk.Frame(root)
top.pack(pady=10)

tk.Button(top, text="Открыть", width=15, command=open_img).pack(side=tk.LEFT, padx=5)
tk.Button(top, text="Обработать", width=15, command=edit_img).pack(side=tk.LEFT, padx=5)
tk.Button(top, text="Сохранить", width=15, command=save_img).pack(side=tk.LEFT, padx=5)
tk.Button(top, text="Сохранить PBM", width=15, command=save_pbm).pack(side=tk.LEFT, padx=5)

info = tk.Label(top, text="Вариант 12")
info.pack(side=tk.LEFT, padx=10)

picture = tk.Label(root, text="Откройте изображение", bg="white", bd=1, relief=tk.SOLID)
picture.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

root.mainloop()
