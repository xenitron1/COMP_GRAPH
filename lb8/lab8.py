import argparse
import math
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageGrab, ImageTk


INTERPOLATIONS = ("Ближайший сосед", "Билинейная", "Бикубическая")


def clamp(value, low, high):
    return max(low, min(high, value))


def cubic_weight(x):
    """Кубическое ядро Катмулла — Рома (a = -0.5)."""
    x = abs(x)
    if x <= 1:
        return 1.5 * x**3 - 2.5 * x**2 + 1
    if x < 2:
        return -0.5 * x**3 + 2.5 * x**2 - 4 * x + 2
    return 0.0


def sample_nearest(pixels, width, height, x, y):
    xi = clamp(round(x), 0, width - 1)
    yi = clamp(round(y), 0, height - 1)
    return pixels[xi, yi]


def sample_bilinear(pixels, width, height, x, y):
    x0 = math.floor(x)
    y0 = math.floor(y)
    a = x - x0
    b = y - y0
    x1 = x0 + 1
    y1 = y0 + 1
    x0 = clamp(x0, 0, width - 1)
    x1 = clamp(x1, 0, width - 1)
    y0 = clamp(y0, 0, height - 1)
    y1 = clamp(y1, 0, height - 1)
    p00, p10 = pixels[x0, y0], pixels[x1, y0]
    p01, p11 = pixels[x0, y1], pixels[x1, y1]
    result = []
    for channel in range(3):
        value = (
            (1 - a) * (1 - b) * p00[channel]
            + a * (1 - b) * p10[channel]
            + (1 - a) * b * p01[channel]
            + a * b * p11[channel]
        )
        result.append(clamp(round(value), 0, 255))
    return tuple(result)


def sample_bicubic(pixels, width, height, x, y):
    x0 = math.floor(x)
    y0 = math.floor(y)
    result = []
    for channel in range(3):
        value = 0.0
        weight_sum = 0.0
        for dy in range(-1, 3):
            py = clamp(y0 + dy, 0, height - 1)
            wy = cubic_weight(y - (y0 + dy))
            for dx in range(-1, 3):
                px = clamp(x0 + dx, 0, width - 1)
                weight = cubic_weight(x - (x0 + dx)) * wy
                value += pixels[px, py][channel] * weight
                weight_sum += weight
        if weight_sum:
            value /= weight_sum
        result.append(clamp(round(value), 0, 255))
    return tuple(result)


def get_sampler(method):
    if method == INTERPOLATIONS[0]:
        return sample_nearest
    if method == INTERPOLATIONS[1]:
        return sample_bilinear
    return sample_bicubic


def inverse_map(source, out_size, inverse, method, background=(255, 255, 255)):
    """Формирует результат обратным отображением координат."""
    source = source.convert("RGB")
    width, height = source.size
    out_width, out_height = out_size
    result = Image.new("RGB", out_size, background)
    src_pixels = source.load()
    dst_pixels = result.load()
    sampler = get_sampler(method)
    for y_out in range(out_height):
        for x_out in range(out_width):
            x, y = inverse(x_out, y_out)
            if -0.5 <= x <= width - 0.5 and -0.5 <= y <= height - 0.5:
                dst_pixels[x_out, y_out] = sampler(src_pixels, width, height, x, y)
    return result


def scale_image(source, scale_x, scale_y, method):
    if scale_x <= 0 or scale_y <= 0:
        raise ValueError("Коэффициенты масштаба должны быть больше нуля")
    width, height = source.size
    out_size = (max(1, round(width * scale_x)), max(1, round(height * scale_y)))

    def inverse(x, y):
        return (x + 0.5) / scale_x - 0.5, (y + 0.5) / scale_y - 0.5

    return inverse_map(source, out_size, inverse, method)


def rotate_image(source, angle_degrees, method):
    width, height = source.size
    angle = math.radians(angle_degrees)
    cosine, sine = math.cos(angle), math.sin(angle)
    cx, cy = (width - 1) / 2, (height - 1) / 2
    corners = []
    for x, y in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        dx, dy = x - cx, y - cy
        corners.append((cosine * dx - sine * dy, sine * dx + cosine * dy))
    min_x = math.floor(min(p[0] for p in corners))
    max_x = math.ceil(max(p[0] for p in corners))
    min_y = math.floor(min(p[1] for p in corners))
    max_y = math.ceil(max(p[1] for p in corners))
    out_size = (max_x - min_x + 1, max_y - min_y + 1)

    def inverse(x_out, y_out):
        xr, yr = x_out + min_x, y_out + min_y
        return cosine * xr + sine * yr + cx, -sine * xr + cosine * yr + cy

    return inverse_map(source, out_size, inverse, method)


def shear_image(source, shear_x, method):
    width, height = source.size
    cy = (height - 1) / 2
    shifts = (shear_x * (0 - cy), shear_x * (height - 1 - cy))
    min_shift = math.floor(min(shifts))
    max_shift = math.ceil(max(shifts))
    out_size = (width + max_shift - min_shift, height)

    def inverse(x_out, y_out):
        x_shifted = x_out + min_shift
        return x_shifted - shear_x * (y_out - cy), y_out

    return inverse_map(source, out_size, inverse, method)


class Lab8App:
    def __init__(self, root):
        self.root = root
        self.source = None
        self.results = [None, None, None]
        self.photos = [None, None, None, None]
        root.title("Лабораторная работа № 8 — Интерполяция изображений")
        root.geometry("1100x650")
        root.minsize(900, 600)
        self._build_controls()
        self._build_images()

    def _build_controls(self):
        controls = ttk.Frame(self.root, padding=8)
        controls.pack(fill=tk.X)
        ttk.Button(controls, text="Открыть изображение", command=self.open_image).grid(
            row=0, column=0, rowspan=3, padx=(0, 18), sticky="ns"
        )
        ttk.Label(controls, text="Масштаб X / Y:").grid(row=0, column=1, sticky="w")
        self.scale_x = ttk.Entry(controls, width=6)
        self.scale_y = ttk.Entry(controls, width=6)
        self.scale_x.insert(0, "1.5")
        self.scale_y.insert(0, "1.5")
        self.scale_x.grid(row=0, column=2, padx=2)
        self.scale_y.grid(row=0, column=3, padx=2)
        self.scale_method = ttk.Combobox(controls, values=INTERPOLATIONS, state="readonly", width=17)
        self.scale_method.set(INTERPOLATIONS[0])
        self.scale_method.grid(row=0, column=4, padx=4)
        ttk.Button(controls, text="Масштабировать", command=self.apply_scale).grid(row=0, column=5, padx=4)

        ttk.Label(controls, text="Угол поворота, °:").grid(row=1, column=1, sticky="w")
        self.angle = ttk.Entry(controls, width=8)
        self.angle.insert(0, "30")
        self.angle.grid(row=1, column=2, columnspan=2, padx=2, sticky="w")
        self.rotate_method = ttk.Combobox(controls, values=INTERPOLATIONS, state="readonly", width=17)
        self.rotate_method.set(INTERPOLATIONS[1])
        self.rotate_method.grid(row=1, column=4, padx=4)
        ttk.Button(controls, text="Повернуть", command=self.apply_rotate).grid(row=1, column=5, padx=4, sticky="ew")

        ttk.Label(controls, text="Коэффициент скоса X:").grid(row=2, column=1, sticky="w")
        self.shear = ttk.Entry(controls, width=8)
        self.shear.insert(0, "0.35")
        self.shear.grid(row=2, column=2, columnspan=2, padx=2, sticky="w")
        self.shear_method = ttk.Combobox(controls, values=INTERPOLATIONS, state="readonly", width=17)
        self.shear_method.set(INTERPOLATIONS[2])
        self.shear_method.grid(row=2, column=4, padx=4)
        ttk.Button(controls, text="Выполнить скос", command=self.apply_shear).grid(row=2, column=5, padx=4, sticky="ew")
        self.status = ttk.Label(self.root, text="Откройте изображение", padding=(10, 0))
        self.status.pack(fill=tk.X)

    def _build_images(self):
        body = ttk.Frame(self.root, padding=8)
        body.pack(fill=tk.BOTH, expand=True)
        titles = (
            "Исходное изображение",
            "Масштабирование\n(ближайший сосед)",
            "Поворот\n(билинейная)",
            "Скос\n(бикубическая)",
        )
        self.labels = []
        for column, title in enumerate(titles):
            frame = ttk.LabelFrame(body, text=title, padding=5)
            frame.grid(row=0, column=column, padx=4, sticky="nsew")
            body.columnconfigure(column, weight=1)
            body.rowconfigure(0, weight=1)
            label = tk.Label(frame, text="Нет изображения", bg="white", relief=tk.SOLID, bd=1)
            label.pack(fill=tk.BOTH, expand=True)
            self.labels.append(label)
        buttons = ttk.Frame(self.root, padding=(8, 0, 8, 10))
        buttons.pack(fill=tk.X)
        for i, text in enumerate(("Сохранить масштаб", "Сохранить поворот", "Сохранить скос")):
            ttk.Button(buttons, text=text, command=lambda n=i: self.save_result(n)).pack(side=tk.LEFT, padx=4)

    def display(self, image, index):
        preview = image.copy()
        preview.thumbnail((245, 440), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(preview)
        self.photos[index] = photo
        self.labels[index].configure(image=photo, text="")

    def load_path(self, path):
        self.source = Image.open(path).convert("RGB")
        self.display(self.source, 0)
        self.status.configure(text=f"{Path(path).name}: {self.source.width} × {self.source.height} пикселей")

    def open_image(self):
        path = filedialog.askopenfilename(
            title="Открыть изображение",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.ppm *.pgm *.pbm"), ("Все файлы", "*.*")],
        )
        if path:
            try:
                self.load_path(path)
            except Exception as error:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{error}")

    def require_source(self):
        if self.source is None:
            messagebox.showwarning("Нет изображения", "Сначала откройте исходное изображение")
            return False
        return True

    def apply_scale(self):
        if not self.require_source():
            return
        try:
            self.results[0] = scale_image(
                self.source, float(self.scale_x.get()), float(self.scale_y.get()), self.scale_method.get()
            )
            self.display(self.results[0], 1)
        except ValueError as error:
            messagebox.showerror("Неверные параметры", str(error))

    def apply_rotate(self):
        if not self.require_source():
            return
        try:
            self.results[1] = rotate_image(self.source, float(self.angle.get()), self.rotate_method.get())
            self.display(self.results[1], 2)
        except ValueError:
            messagebox.showerror("Неверные параметры", "Угол должен быть числом")

    def apply_shear(self):
        if not self.require_source():
            return
        try:
            self.results[2] = shear_image(self.source, float(self.shear.get()), self.shear_method.get())
            self.display(self.results[2], 3)
        except ValueError:
            messagebox.showerror("Неверные параметры", "Коэффициент скоса должен быть числом")

    def run_all(self):
        self.apply_scale()
        self.apply_rotate()
        self.apply_shear()

    def save_result(self, index):
        image = self.results[index]
        if image is None:
            messagebox.showwarning("Нет результата", "Сначала выполните преобразование")
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить результат", defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")]
        )
        if path:
            image.save(path)


def generate_demo(input_path, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    source = Image.open(input_path).convert("RGB")
    scale_image(source, 1.5, 1.5, INTERPOLATIONS[0]).save(output_dir / "result_scale_nearest.png")
    rotate_image(source, 30, INTERPOLATIONS[1]).save(output_dir / "result_rotate_bilinear.png")
    shear_image(source, 0.35, INTERPOLATIONS[2]).save(output_dir / "result_shear_bicubic.png")


def main():
    parser = argparse.ArgumentParser(description="ЛР8: аффинные преобразования с интерполяцией")
    parser.add_argument("--input", help="изображение, автоматически открываемое при запуске")
    parser.add_argument("--demo", metavar="DIR", help="создать три результата без запуска интерфейса")
    parser.add_argument("--screenshot", help="сохранить снимок заполненного окна и завершить работу")
    args = parser.parse_args()
    if args.demo:
        if not args.input:
            parser.error("для --demo требуется --input")
        generate_demo(args.input, args.demo)
        return
    root = tk.Tk()
    app = Lab8App(root)
    if args.input:
        app.load_path(args.input)
        app.run_all()
    if args.screenshot:
        root.geometry("1100x600+0+0")
        root.attributes("-topmost", True)
        root.lift()
        root.focus_force()
        def save_screenshot():
            root.update()
            x, y = root.winfo_rootx(), root.winfo_rooty()
            width, height = root.winfo_width(), root.winfo_height()
            screen = ImageGrab.grab()
            scale_x = screen.width / root.winfo_screenwidth()
            scale_y = screen.height / root.winfo_screenheight()
            box = (
                round(x * scale_x), round(y * scale_y),
                round((x + width) * scale_x), round((y + height) * scale_y),
            )
            screen.crop(box).save(args.screenshot)
            root.destroy()
        root.after(1200, save_screenshot)
    root.mainloop()


if __name__ == "__main__":
    main()
