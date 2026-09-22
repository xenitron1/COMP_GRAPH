import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk


class ImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №1 — вариант 12")
        self.root.geometry("1000x700")
        self.root.minsize(760, 520)

        self.image = None
        self.preview = None

        top = tk.Frame(root, padx=10, pady=10)
        top.pack(fill=tk.X)

        tk.Button(top, text="Открыть", width=16, command=self.open_image).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Обработать", width=16, command=self.process_image).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Сохранить", width=16, command=self.save_image).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Сохранить PBM", width=16, command=self.save_pbm).pack(side=tk.LEFT, padx=5)

        self.info = tk.Label(top, text="Вариант 12")
        self.info.pack(side=tk.LEFT, padx=15)

        self.image_label = tk.Label(
            root,
            text="Откройте изображение",
            bg="#eeeeee",
            relief=tk.SUNKEN,
            bd=1
        )
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def open_image(self):
        filename = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.bmp *.ppm *.pgm *.pbm"),
                ("Все файлы", "*.*")
            ]
        )

        if not filename:
            return

        try:
            self.image = Image.open(filename).convert("RGB")
            self.info.config(text=f"Размер: {self.image.width} x {self.image.height}")
            self.show_image()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть изображение:\n{e}")

    def process_image(self):
        if self.image is None:
            messagebox.showwarning("Внимание", "Сначала откройте изображение.")
            return

        w, h = self.image.size

        # Вариант 12
        self.image.putpixel((0, 0), (64, 64, 127))              # левый верхний угол
        self.image.putpixel((w - 1, 0), (127, 64, 127))        # правый верхний угол
        self.image.putpixel((w - 1, h - 1), (127, 127, 64))    # правый нижний угол

        self.show_image()

        messagebox.showinfo(
            "Готово",
            "Обработка выполнена по варианту 12:\n"
            "• (64, 64, 127) — левый верхний угол\n"
            "• (127, 64, 127) — правый верхний угол\n"
            "• (127, 127, 64) — правый нижний угол"
        )

    def save_image(self):
        if self.image is None:
            messagebox.showwarning("Внимание", "Нет изображения для сохранения.")
            return

        filename = filedialog.asksaveasfilename(
            title="Сохранить изображение",
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png"),
                ("JPEG", "*.jpg"),
                ("BMP", "*.bmp")
            ]
        )

        if not filename:
            return

        try:
            self.image.save(filename)
            messagebox.showinfo("Сохранение", "Изображение успешно сохранено.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изображение:\n{e}")

    def save_pbm(self):
        if self.image is None:
            messagebox.showwarning("Внимание", "Нет изображения для сохранения.")
            return

        filename = filedialog.asksaveasfilename(
            title="Сохранить в текстовом формате PBM",
            defaultextension=".pbm",
            filetypes=[("PBM ASCII (P1)", "*.pbm"), ("Текстовый файл", "*.txt")]
        )

        if not filename:
            return

        try:
            rgb = self.image.convert("RGB")
            w, h = rgb.size

            # ASCII PBM (P1): 1 = чёрный, 0 = белый
            # Цветное изображение предварительно переводим в ч/б по яркости.
            with open(filename, "w", encoding="ascii") as f:
                f.write("P1\n")
                f.write(f"{w} {h}\n")

                for y in range(h):
                    row = []
                    for x in range(w):
                        r, g, b = rgb.getpixel((x, y))

                        # Относительная яркость
                        brightness = 0.299 * r + 0.587 * g + 0.114 * b

                        # PBM: 1 = чёрный, 0 = белый
                        row.append("1" if brightness < 128 else "0")

                    f.write(" ".join(row) + "\n")

            messagebox.showinfo(
                "PBM сохранён",
                "Изображение сохранено в текстовом PBM-формате P1."
            )

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить PBM:\n{e}")

    def show_image(self):
        if self.image is None:
            return

        preview = self.image.copy()
        preview.thumbnail((940, 570))

        self.preview = ImageTk.PhotoImage(preview)
        self.image_label.config(image=self.preview, text="")

    def close(self):
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()
