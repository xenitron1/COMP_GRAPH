import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import colorsys

src = None
low_img = None
high_img = None

p1 = None
p2 = None
p3 = None

gauss = [
    [0, 1, 2, 1, 0],
    [1, 6, 10, 6, 1],
    [2, 10, 16, 10, 2],
    [1, 6, 10, 6, 1],
    [0, 1, 2, 1, 0]
]

log_mask = [
    [-1, -2, -3, -2, -1],
    [-2,  0,  4,  0, -2],
    [-3,  4, 16,  4, -3],
    [-2,  0,  4,  0, -2],
    [-1, -2, -3, -2, -1]
]


def show_img(img, label, num):
    global p1, p2, p3

    if img is None:
        return

    temp = img.copy()
    temp.thumbnail((360, 260))
    photo = ImageTk.PhotoImage(temp)

    label.config(image=photo, text="")

    if num == 1:
        p1 = photo
    elif num == 2:
        p2 = photo
    else:
        p3 = photo


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
        show_img(src, box1, 1)
        info.config(text=f"{src.width} x {src.height}")
    except:
        messagebox.showerror("Ошибка", "Не удалось открыть файл")


def get_rect():
    try:
        a = int(a_entry.get())
        b = int(b_entry.get())

        if a <= 0 or b <= 0:
            raise ValueError

        return a, b
    except:
        messagebox.showerror("Ошибка", "a и b должны быть положительными числами")
        return None


def gauss_filter():
    global low_img

    if src is None:
        messagebox.showwarning("Ошибка", "Сначала откройте изображение")
        return

    size = get_rect()

    if size is None:
        return

    a, b = size
    w, h = src.size

    if a > w or b > h:
        messagebox.showwarning("Ошибка", "Прямоугольник больше изображения")
        return

    left = (w - a) // 2
    right = left + a
    top = (h - b) // 2
    bottom = top + b

    low_img = src.copy()
    norm = sum(sum(row) for row in gauss)

    for y in range(2, h - 2):
        for x in range(2, w - 2):
            inside = left <= x < right and top <= y < bottom

            if inside:
                continue

            rr = 0
            gg = 0
            bb = 0

            for ky in range(5):
                for kx in range(5):
                    r, g, b0 = src.getpixel((x + kx - 2, y + ky - 2))
                    k = gauss[ky][kx]

                    rr += r * k
                    gg += g * k
                    bb += b0 * k

            low_img.putpixel(
                (x, y),
                (
                    round(rr / norm),
                    round(gg / norm),
                    round(bb / norm)
                )
            )

    show_img(low_img, box2, 2)


def conv(data, x, y, mask):
    s = 0.0

    for ky in range(5):
        for kx in range(5):
            s += data[y + ky - 2][x + kx - 2] * mask[ky][kx]

    return s


def normalize(values):
    flat = [v for row in values for v in row]

    if len(flat) == 0:
        return values

    mn = min(flat)
    mx = max(flat)

    if mx == mn:
        return [[0.0 for _ in row] for row in values]

    result = []

    for row in values:
        new_row = []

        for v in row:
            new_row.append((v - mn) / (mx - mn))

        result.append(new_row)

    return result


def log_filter():
    global high_img

    if src is None:
        messagebox.showwarning("Ошибка", "Сначала откройте изображение")
        return

    w, h = src.size

    hh = [[0.0] * w for _ in range(h)]
    ss = [[0.0] * w for _ in range(h)]
    vv = [[0.0] * w for _ in range(h)]

    for y in range(h):
        for x in range(w):
            r, g, b = src.getpixel((x, y))

            h0, s0, v0 = colorsys.rgb_to_hsv(
                r / 255,
                g / 255,
                b / 255
            )

            hh[y][x] = h0
            ss[y][x] = s0
            vv[y][x] = v0

    h_left = []
    v_left = []
    s_right = []
    v_right = []

    for y in range(2, h - 2):
        row_h = []
        row_vl = []
        row_s = []
        row_vr = []

        for x in range(2, w // 2):
            row_h.append(conv(hh, x, y, log_mask))
            row_vl.append(conv(vv, x, y, log_mask))

        for x in range(w // 2, w - 2):
            row_s.append(conv(ss, x, y, log_mask))
            row_vr.append(conv(vv, x, y, log_mask))

        h_left.append(row_h)
        v_left.append(row_vl)
        s_right.append(row_s)
        v_right.append(row_vr)

    h_left = normalize(h_left)
    v_left = normalize(v_left)
    s_right = normalize(s_right)
    v_right = normalize(v_right)

    high_img = src.copy()

    for y in range(2, h - 2):
        ly = y - 2

        for x in range(2, w // 2):
            lx = x - 2

            h0 = h_left[ly][lx]
            s0 = ss[y][x]
            v0 = v_left[ly][lx]

            r, g, b = colorsys.hsv_to_rgb(h0, s0, v0)

            high_img.putpixel(
                (x, y),
                (
                    round(r * 255),
                    round(g * 255),
                    round(b * 255)
                )
            )

        for x in range(w // 2, w - 2):
            rx = x - w // 2

            h0 = hh[y][x]
            s0 = s_right[ly][rx]
            v0 = v_right[ly][rx]

            r, g, b = colorsys.hsv_to_rgb(h0, s0, v0)

            high_img.putpixel(
                (x, y),
                (
                    round(r * 255),
                    round(g * 255),
                    round(b * 255)
                )
            )

    show_img(high_img, box3, 3)


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
root.title("Лаба 7. Вариант 12")
root.geometry("1180x650")

top = tk.Frame(root)
top.pack(pady=8)

tk.Button(
    top,
    text="Открыть",
    width=11,
    command=open_img
).pack(side=tk.LEFT, padx=3)

tk.Label(top, text="a:").pack(side=tk.LEFT)

a_entry = tk.Entry(top, width=6)
a_entry.insert(0, "220")
a_entry.pack(side=tk.LEFT, padx=3)

tk.Label(top, text="b:").pack(side=tk.LEFT)

b_entry = tk.Entry(top, width=6)
b_entry.insert(0, "160")
b_entry.pack(side=tk.LEFT, padx=3)

tk.Button(
    top,
    text="ФНЧ",
    width=11,
    command=gauss_filter
).pack(side=tk.LEFT, padx=3)

tk.Button(
    top,
    text="ФВЧ",
    width=11,
    command=log_filter
).pack(side=tk.LEFT, padx=3)

tk.Button(
    top,
    text="Сохранить ФНЧ",
    width=14,
    command=lambda: save_img(low_img, "Сохранить результат ФНЧ")
).pack(side=tk.LEFT, padx=3)

tk.Button(
    top,
    text="Сохранить ФВЧ",
    width=14,
    command=lambda: save_img(high_img, "Сохранить результат ФВЧ")
).pack(side=tk.LEFT, padx=3)

info = tk.Label(top, text="")
info.pack(side=tk.LEFT, padx=8)

main = tk.Frame(root)
main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

col1 = tk.Frame(main)
col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

col2 = tk.Frame(main)
col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

col3 = tk.Frame(main)
col3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

tk.Label(col1, text="Исходное изображение").pack()
box1 = tk.Label(
    col1,
    text="Откройте файл",
    bg="white",
    relief=tk.SOLID,
    bd=1
)
box1.pack(fill=tk.BOTH, expand=True)

tk.Label(col2, text="ФНЧ: гауссиан за пределами axb").pack()
box2 = tk.Label(
    col2,
    text="Результат ФНЧ",
    bg="white",
    relief=tk.SOLID,
    bd=1
)
box2.pack(fill=tk.BOTH, expand=True)

tk.Label(col3, text="ФВЧ: лапласиан гауссиана").pack()
box3 = tk.Label(
    col3,
    text="Результат ФВЧ",
    bg="white",
    relief=tk.SOLID,
    bd=1
)
box3.pack(fill=tk.BOTH, expand=True)

root.mainloop()
