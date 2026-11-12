import argparse
import math
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


LEFT, RIGHT, TOP, BOTTOM = 1, 2, 4, 8


def region_code(x, y, rect):
    xmin, ymin, xmax, ymax = rect
    code = 0
    if x < xmin:
        code |= LEFT
    elif x > xmax:
        code |= RIGHT
    if y < ymin:
        code |= TOP
    elif y > ymax:
        code |= BOTTOM
    return code


def cohen_sutherland(segment, rect):
    """Отсечение отрезка алгоритмом Сазерленда — Коэна."""
    x1, y1, x2, y2 = map(float, segment)
    xmin, ymin, xmax, ymax = rect
    code1 = region_code(x1, y1, rect)
    code2 = region_code(x2, y2, rect)

    for _ in range(16):
        if not (code1 | code2):
            return x1, y1, x2, y2
        if code1 & code2:
            return None

        outside = code1 or code2
        if outside & TOP:
            if y2 == y1:
                return None
            x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
            y = ymin
        elif outside & BOTTOM:
            if y2 == y1:
                return None
            x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)
            y = ymax
        elif outside & RIGHT:
            if x2 == x1:
                return None
            y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
            x = xmax
        else:
            if x2 == x1:
                return None
            y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
            x = xmin

        if outside == code1:
            x1, y1 = x, y
            code1 = region_code(x1, y1, rect)
        else:
            x2, y2 = x, y
            code2 = region_code(x2, y2, rect)
    return None


def midpoint_subdivision(segment, rect, tolerance=0.25, max_depth=32):
    """Отсечение двоичным разбиением отрезка средней точкой."""
    x1, y1, x2, y2 = map(float, segment)
    pieces = []

    def point(t):
        return x1 + (x2 - x1) * t, y1 + (y2 - y1) * t

    def split(t0, t1, depth):
        p0, p1 = point(t0), point(t1)
        c0 = region_code(*p0, rect)
        c1 = region_code(*p1, rect)
        if not (c0 | c1):
            pieces.append((t0, t1))
            return
        if c0 & c1:
            return
        length = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        if depth >= max_depth or length <= tolerance:
            tm = (t0 + t1) / 2
            if region_code(*point(tm), rect) == 0:
                pieces.append((t0, t1))
            return
        tm = (t0 + t1) / 2
        split(t0, tm, depth + 1)
        split(tm, t1, depth + 1)

    split(0.0, 1.0, 0)
    if not pieces:
        return None
    pieces.sort()
    start, end = pieces[0]
    merged = []
    for left, right in pieces[1:]:
        if left - end <= 1e-6:
            end = max(end, right)
        else:
            merged.append((start, end))
            start, end = left, right
    merged.append((start, end))
    # Пересечение выпуклого прямоугольника с отрезком связно.
    start, end = max(merged, key=lambda item: item[1] - item[0])
    a, b = point(start), point(end)
    return a[0], a[1], b[0], b[1]


DEFAULT_SEGMENTS = [
    (80, 90, 750, 490),
    (120, 420, 780, 130),
    (350, 250, 560, 330),
    (40, 170, 180, 115),
    (690, 80, 790, 180),
    (250, 60, 250, 520),
    (90, 480, 720, 480),
    (540, 40, 620, 540),
]


class ClippingApp:
    def __init__(self, root):
        self.root = root
        self.segments = list(DEFAULT_SEGMENTS)
        self.first_click = None
        self.last_results = []
        root.title("Лабораторная работа № 9 — Отсечение отрезков")
        root.geometry("1100x600")
        root.minsize(950, 560)
        self.build_ui()
        self.refresh_list()
        self.clip_all()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill=tk.BOTH, expand=True)
        panel = ttk.Frame(main, width=300)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        panel.pack_propagate(False)
        view = ttk.Frame(main)
        view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        window_box = ttk.LabelFrame(panel, text="Отсекающее окно", padding=6)
        window_box.pack(fill=tk.X)
        self.window_entries = {}
        defaults = (("X", "200"), ("Y", "130"), ("Ширина", "430"), ("Высота", "300"))
        for index, (label, value) in enumerate(defaults):
            ttk.Label(window_box, text=label).grid(row=index // 2, column=(index % 2) * 2, sticky="e", padx=2, pady=2)
            entry = ttk.Entry(window_box, width=8)
            entry.insert(0, value)
            entry.grid(row=index // 2, column=(index % 2) * 2 + 1, padx=2, pady=2)
            self.window_entries[label] = entry

        algorithm_box = ttk.LabelFrame(panel, text="Алгоритм", padding=6)
        algorithm_box.pack(fill=tk.X, pady=6)
        self.algorithm = ttk.Combobox(
            algorithm_box,
            values=("Сазерленд — Коэн", "Разбиение средней точкой"),
            state="readonly",
        )
        self.algorithm.set("Сазерленд — Коэн")
        self.algorithm.pack(fill=tk.X)
        ttk.Button(algorithm_box, text="Выполнить отсечение", command=self.clip_all).pack(fill=tk.X, pady=(5, 0))

        segment_box = ttk.LabelFrame(panel, text="Координаты отрезка", padding=6)
        segment_box.pack(fill=tk.X)
        self.segment_entries = []
        for index, label in enumerate(("x₁", "y₁", "x₂", "y₂")):
            ttk.Label(segment_box, text=label).grid(row=0, column=index)
            entry = ttk.Entry(segment_box, width=7)
            entry.grid(row=1, column=index, padx=2)
            self.segment_entries.append(entry)
        ttk.Button(segment_box, text="Добавить", command=self.add_segment).grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Button(segment_box, text="Изменить", command=self.update_segment).grid(row=2, column=2, columnspan=2, sticky="ew", pady=5)

        list_box = ttk.LabelFrame(panel, text="Список отрезков", padding=5)
        list_box.pack(fill=tk.BOTH, expand=True, pady=6)
        self.listbox = tk.Listbox(list_box, height=9, font=("Consolas", 9), exportselection=False)
        scroll = ttk.Scrollbar(list_box, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", self.select_segment)

        row = ttk.Frame(panel)
        row.pack(fill=tk.X)
        ttk.Button(row, text="Удалить", command=self.delete_segment).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="Очистить", command=self.clear_segments).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        ttk.Button(panel, text="Вернуть пример", command=self.restore_example).pack(fill=tk.X, pady=(5, 0))
        ttk.Button(panel, text="Сохранить рисунок", command=self.save_canvas).pack(fill=tk.X, pady=(5, 0))

        self.canvas = tk.Canvas(view, bg="white", highlightthickness=1, highlightbackground="#888")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.canvas_click)
        self.status = ttk.Label(view, text="", padding=(2, 5))
        self.status.pack(fill=tk.X)
        ttk.Label(view, text="Серый пунктир — исходные отрезки; красный — видимые части; синяя рамка — окно.").pack(anchor="w")

    def get_rect(self):
        try:
            x = float(self.window_entries["X"].get())
            y = float(self.window_entries["Y"].get())
            width = float(self.window_entries["Ширина"].get())
            height = float(self.window_entries["Высота"].get())
            if width <= 0 or height <= 0:
                raise ValueError
            return x, y, x + width, y + height
        except ValueError:
            messagebox.showerror("Ошибка", "Координаты должны быть числами, размеры окна — положительными")
            return None

    def get_segment_fields(self):
        try:
            return tuple(float(entry.get()) for entry in self.segment_entries)
        except ValueError:
            messagebox.showerror("Ошибка", "Введите четыре числовые координаты отрезка")
            return None

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for index, segment in enumerate(self.segments, 1):
            values = tuple(round(v, 1) for v in segment)
            self.listbox.insert(tk.END, f"{index:02}: ({values[0]}, {values[1]})–({values[2]}, {values[3]})")

    def add_segment(self):
        segment = self.get_segment_fields()
        if segment:
            self.segments.append(segment)
            self.refresh_list()
            self.clip_all()

    def update_segment(self):
        selected = self.listbox.curselection()
        segment = self.get_segment_fields()
        if not selected:
            messagebox.showwarning("Отрезок не выбран", "Выберите отрезок в списке")
        elif segment:
            self.segments[selected[0]] = segment
            self.refresh_list()
            self.clip_all()

    def select_segment(self, _event=None):
        selected = self.listbox.curselection()
        if selected:
            for entry, value in zip(self.segment_entries, self.segments[selected[0]]):
                entry.delete(0, tk.END)
                entry.insert(0, f"{value:g}")

    def delete_segment(self):
        selected = self.listbox.curselection()
        if selected:
            del self.segments[selected[0]]
            self.refresh_list()
            self.clip_all()

    def clear_segments(self):
        self.segments.clear()
        self.refresh_list()
        self.clip_all()

    def restore_example(self):
        self.segments = list(DEFAULT_SEGMENTS)
        self.refresh_list()
        self.clip_all()

    def canvas_click(self, event):
        if self.first_click is None:
            self.first_click = (event.x, event.y)
            self.status.configure(text=f"Первая точка: ({event.x}, {event.y}). Укажите вторую точку.")
            self.canvas.create_oval(event.x - 3, event.y - 3, event.x + 3, event.y + 3, fill="#e67e22", tags="click_marker")
        else:
            x1, y1 = self.first_click
            self.segments.append((x1, y1, event.x, event.y))
            self.first_click = None
            self.canvas.delete("click_marker")
            self.refresh_list()
            self.clip_all()

    def clip_all(self):
        rect = self.get_rect()
        if rect is None:
            return
        algorithm = cohen_sutherland if self.algorithm.get() == "Сазерленд — Коэн" else midpoint_subdivision
        self.last_results = [algorithm(segment, rect) for segment in self.segments]
        self.draw(rect)

    def draw(self, rect):
        self.canvas.delete("all")
        xmin, ymin, xmax, ymax = rect
        self.canvas.create_rectangle(xmin, ymin, xmax, ymax, outline="#1565c0", width=3)
        self.canvas.create_text(xmin + 6, ymin + 6, text="Окно отсечения", fill="#1565c0", anchor="nw", font=("Arial", 10, "bold"))
        accepted = rejected = partial = 0
        for index, (source, result) in enumerate(zip(self.segments, self.last_results), 1):
            self.canvas.create_line(*source, fill="#999", width=2, dash=(5, 4))
            self.canvas.create_text(source[0] + 4, source[1] - 5, text=str(index), fill="#666", anchor="sw")
            if result is None:
                rejected += 1
                continue
            self.canvas.create_line(*result, fill="#d32f2f", width=4)
            if all(abs(a - b) < 0.3 for a, b in zip(source, result)):
                accepted += 1
            else:
                partial += 1
            for x, y in ((result[0], result[1]), (result[2], result[3])):
                self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#d32f2f", outline="")
        self.status.configure(
            text=f"Алгоритм: {self.algorithm.get()}. Полностью видимых: {accepted}; частично видимых: {partial}; невидимых: {rejected}."
        )

    def save_canvas(self):
        path = filedialog.asksaveasfilename(title="Сохранить рисунок", defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not path:
            return
        try:
            from PIL import ImageGrab
            self.root.update()
            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            scale = self.root.winfo_fpixels("1i") / 96
            box = (round(x * scale), round(y * scale), round((x + self.canvas.winfo_width()) * scale), round((y + self.canvas.winfo_height()) * scale))
            ImageGrab.grab().crop(box).save(path)
        except Exception as error:
            messagebox.showerror("Ошибка", f"Не удалось сохранить рисунок:\n{error}")


def save_window_screenshot(root, path):
    from PIL import ImageGrab
    root.update()
    screen = ImageGrab.grab()
    scale_x = screen.width / root.winfo_screenwidth()
    scale_y = screen.height / root.winfo_screenheight()
    x, y = root.winfo_rootx(), root.winfo_rooty()
    box = (
        round(x * scale_x), round(y * scale_y),
        round((x + root.winfo_width()) * scale_x), round((y + root.winfo_height()) * scale_y),
    )
    screen.crop(box).save(path)


def main():
    parser = argparse.ArgumentParser(description="ЛР9: алгоритмы отсечения отрезков")
    parser.add_argument("--screenshot", help="сохранить снимок окна с примером и завершить работу")
    parser.add_argument("--algorithm", choices=("cohen", "midpoint"), default="cohen")
    args = parser.parse_args()
    root = tk.Tk()
    app = ClippingApp(root)
    if args.algorithm == "midpoint":
        app.algorithm.set("Разбиение средней точкой")
        app.clip_all()
    if args.screenshot:
        root.geometry("1100x600+0+0")
        root.attributes("-topmost", True)
        root.lift()
        root.focus_force()
        root.after(900, lambda: (save_window_screenshot(root, args.screenshot), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
