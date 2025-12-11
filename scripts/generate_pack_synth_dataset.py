import random
from pathlib import Path
from typing import Tuple, List

from PIL import Image, ImageDraw, ImageFont

# YOLO classes
CLASSES = [
    "brand_product_panel",         # 0
    "mrp_panel",                   # 1
    "net_quantity_panel",          # 2
    "mfg_or_packed_date_panel",    # 3
    "best_before_or_expiry_panel", # 4
    "manufacturer_importer_panel", # 5
    "country_of_origin_panel",     # 6
    "customer_care_panel",         # 7
]


# -------- text generators --------
def get_font(size: int = 26) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def random_brand() -> str:
    brands = ["NexaFresh", "DailyMax", "UrbanBite", "PureLite", "SunRise",
              "NutriPlus", "QuickMart", "ValueKart", "FarmChoice", "CityGro"]
    prods = ["Atta", "Shampoo", "Snack Mix", "Masala", "Cold Drink",
             "Face Wash", "Cooking Oil", "Toothpaste"]
    return f"{random.choice(brands)} {random.choice(prods)}"


def random_mrp() -> str:
    price = random.randint(5, 999)
    style = random.choice(
        [
            f"MRP ₹{price}.00 (Incl. of all taxes)",
            f"M.R.P. Rs. {price}/- (Inc. all taxes)",
            f"Maximum Retail Price Rs {price}.00",
        ]
    )
    return style


def random_net_qty() -> str:
    units = ["g", "kg", "ml", "L"]
    unit = random.choice(units)
    if unit in ["g", "ml"]:
        qty = random.choice([50, 100, 200, 250, 500, 750, 1000])
    else:
        qty = random.choice([0.25, 0.5, 1, 1.5, 2])
    return f"Net Qty: {qty}{unit}"


def random_mfg_date() -> str:
    # very rough random date
    d = random.randint(1, 28)
    m = random.randint(1, 12)
    y = random.choice([2022, 2023, 2024])
    return f"Mfg: {d:02d}-{m:02d}-{y}"


def random_best_before() -> str:
    months = random.choice([6, 9, 12, 18, 24])
    return f"Best before {months} months from Mfg."


def random_manufacturer() -> str:
    return "Mfd. by: ABC Foods Pvt. Ltd.\nPlot 12, Industrial Area\nMumbai, India"


def random_importer() -> str:
    return "Imported by: XYZ Traders LLP\nNew Delhi, India"


def random_country() -> str:
    return random.choice(
        [
            "Country of Origin: India",
            "Made in India",
            "Product of India",
            "Country of Origin: China",
        ]
    )


def random_customer_care() -> str:
    return (
        "Customer Care: 1800-123-4567\n"
        "Email: care@example.com"
    )


# -------- geometry helpers --------
def yolo_from_xyxy(x1: float, y1: float, x2: float, y2: float,
                   img_w: int, img_h: int) -> Tuple[float, float, float, float]:
    cx = (x1 + x2) / 2.0 / img_w
    cy = (y1 + y2) / 2.0 / img_h
    w = (x2 - x1) / img_w
    h = (y2 - y1) / img_h
    return cx, cy, w, h


# -------- main image generator --------
def generate_pack_image(
    idx: int,
    out_root: Path,
    subset: str,
    img_size: Tuple[int, int] = (640, 640),
) -> None:
    img_w, img_h = img_size
    bg_colors = [
        (255, 255, 255),
        (250, 250, 240),
        (245, 250, 255),
        (255, 248, 235),
    ]
    bg = random.choice(bg_colors)
    img = Image.new("RGB", img_size, bg)
    draw = ImageDraw.Draw(img)

    # fonts
    font_brand = get_font(size=random.randint(32, 40))
    font_mid = get_font(size=random.randint(24, 30))
    font_small = get_font(size=random.randint(20, 24))

    # margins
    margin_x = 40
    margin_y = 40

    # define rough layout rows
    # row 0: brand/product
    # row 1: mrp + net qty
    # row 2: dates
    # row 3: manufacturer/importer + country + customer care

    label_lines: List[str] = []

    # ---------- 0: brand_product_panel ----------
    brand_text = random_brand()
    x1 = margin_x + random.randint(-10, 10)
    x2 = img_w - margin_x + random.randint(-10, 10)
    y1 = margin_y + random.randint(-10, 5)
    y2 = y1 + random.randint(70, 110)

    draw.rectangle([x1, y1, x2, y2], outline=(0, 0, 0), width=3)
    # center text
    tw, th = draw.textbbox((0, 0), brand_text, font=font_brand)[2:]
    tx = x1 + (x2 - x1 - tw) / 2
    ty = y1 + (y2 - y1 - th) / 2
    draw.text((tx, ty), brand_text, fill=(0, 0, 0), font=font_brand)
    cx, cy, w, h = yolo_from_xyxy(x1, y1, x2, y2, img_w, img_h)
    label_lines.append(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    # ---------- 1 & 2: mrp_panel + net_quantity_panel ----------
    row2_top = y2 + random.randint(10, 20)
    row2_bottom = row2_top + random.randint(70, 100)

    # left: net qty
    qty_text = random_net_qty()
    nx1 = margin_x + random.randint(-5, 5)
    nx2 = img_w / 2 - 10
    ny1 = row2_top
    ny2 = row2_bottom

    draw.rectangle([nx1, ny1, nx2, ny2], outline=(0, 0, 0), width=2)
    tw, th = draw.textbbox((0, 0), qty_text, font=font_mid)[2:]
    tx = nx1 + (nx2 - nx1 - tw) / 2
    ty = ny1 + (ny2 - ny1 - th) / 2
    draw.text((tx, ty), qty_text, fill=(0, 0, 0), font=font_mid)
    cx, cy, w, h = yolo_from_xyxy(nx1, ny1, nx2, ny2, img_w, img_h)
    label_lines.append(f"2 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    # right: mrp
    mrp_text = random_mrp()
    mx1 = img_w / 2 + 10
    mx2 = img_w - margin_x + random.randint(-5, 5)
    my1 = row2_top
    my2 = row2_bottom

    draw.rectangle([mx1, my1, mx2, my2], outline=(0, 0, 0), width=2)
    tw, th = draw.textbbox((0, 0), mrp_text, font=font_mid)[2:]
    tx = mx1 + (mx2 - mx1 - tw) / 2
    ty = my1 + (my2 - my1 - th) / 2
    draw.text((tx, ty), mrp_text, fill=(0, 0, 0), font=font_mid)
    cx, cy, w, h = yolo_from_xyxy(mx1, my1, mx2, my2, img_w, img_h)
    label_lines.append(f"1 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    # ---------- 3 & 4: dates row ----------
    row3_top = row2_bottom + random.randint(10, 20)
    row3_bottom = row3_top + random.randint(60, 90)

    # left: mfg/packed date
    mfg_text = random_mfg_date()
    dx1 = margin_x + random.randint(-5, 5)
    dx2 = img_w / 2 - 10
    dy1 = row3_top
    dy2 = row3_bottom

    draw.rectangle([dx1, dy1, dx2, dy2], outline=(0, 0, 0), width=2)
    tw, th = draw.textbbox((0, 0), mfg_text, font=font_small)[2:]
    tx = dx1 + (dx2 - dx1 - tw) / 2
    ty = dy1 + (dy2 - dy1 - th) / 2
    draw.text((tx, ty), mfg_text, fill=(0, 0, 0), font=font_small)
    cx, cy, w, h = yolo_from_xyxy(dx1, dy1, dx2, dy2, img_w, img_h)
    label_lines.append(f"3 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    # right: best-before / expiry
    bb_text = random_best_before()
    bx1 = img_w / 2 + 10
    bx2 = img_w - margin_x + random.randint(-5, 5)
    by1 = row3_top
    by2 = row3_bottom

    draw.rectangle([bx1, by1, bx2, by2], outline=(0, 0, 0), width=2)
    tw, th = draw.textbbox((0, 0), bb_text, font=font_small)[2:]
    tx = bx1 + (bx2 - bx1 - tw) / 2
    ty = by1 + (by2 - by1 - th) / 2
    draw.text((tx, ty), bb_text, fill=(0, 0, 0), font=font_small)
    cx, cy, w, h = yolo_from_xyxy(bx1, by1, bx2, by2, img_w, img_h)
    label_lines.append(f"4 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    # ---------- 5, 6, 7: bottom info panels ----------
    row4_top = row3_bottom + random.randint(10, 20)
    row4_bottom = img_h - margin_y

    # manufacturer / importer: left 2/3
    man_text = random_manufacturer() + "\n" + random_importer()
    mx1 = margin_x
    mx2 = img_w * 0.65
    my1 = row4_top
    my2 = row4_bottom

    draw.rectangle([mx1, my1, mx2, my2], outline=(0, 0, 0), width=2)
    draw.multiline_text((mx1 + 8, my1 + 8), man_text, fill=(0, 0, 0), font=font_small, spacing=2)
    cx, cy, w, h = yolo_from_xyxy(mx1, my1, mx2, my2, img_w, img_h)
    label_lines.append(f"5 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    # right side column: country + customer care
    col_right_x1 = img_w * 0.68
    col_right_x2 = img_w - margin_x

    # country_of_origin_panel
    co_text = random_country()
    cy1 = row4_top
    cy2 = cy1 + (row4_bottom - row4_top) / 2 - 5
    draw.rectangle([col_right_x1, cy1, col_right_x2, cy2], outline=(0, 0, 0), width=2)
    draw.text((col_right_x1 + 6, cy1 + 8), co_text, fill=(0, 0, 0), font=font_small)
    cx, cy, w, h = yolo_from_xyxy(col_right_x1, cy1, col_right_x2, cy2, img_w, img_h)
    label_lines.append(f"6 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    # customer_care_panel
    cc_text = random_customer_care()
    cy1b = cy2 + 5
    cy2b = row4_bottom
    draw.rectangle([col_right_x1, cy1b, col_right_x2, cy2b], outline=(0, 0, 0), width=2)
    draw.multiline_text((col_right_x1 + 6, cy1b + 8), cc_text, fill=(0, 0, 0), font=font_small, spacing=2)
    cx, cy, w, h = yolo_from_xyxy(col_right_x1, cy1b, col_right_x2, cy2b, img_w, img_h)
    label_lines.append(f"7 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    # ---------- save image & label ----------
    img_dir = out_root / "images" / subset
    lbl_dir = out_root / "labels" / subset
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    img_name = f"pack_{idx:05d}.jpg"
    lbl_name = f"pack_{idx:05d}.txt"

    img.save(img_dir / img_name, quality=95)
    (lbl_dir / lbl_name).write_text("\n".join(label_lines), encoding="utf-8")


def main(num_images: int = 10000, train_split: float = 0.9) -> None:
    project_root = Path(__file__).resolve().parents[1]
    out_root = project_root / "data" / "yolo_pack"
    out_root.mkdir(parents=True, exist_ok=True)

    print(f"Saving synthetic pack dataset to: {out_root}")

    indices = list(range(num_images))
    random.shuffle(indices)

    n_train = int(num_images * train_split)
    train_idx = set(indices[:n_train])

    for idx in indices:
        subset = "train" if idx in train_idx else "val"
        generate_pack_image(idx, out_root, subset)

    # create dataset.yaml
    dataset_yaml = f"""# Synthetic packaging dataset for YOLO

path: .
train: data/yolo_pack/images/train
val: data/yolo_pack/images/val

nc: {len(CLASSES)}
names:
"""
    for i, name in enumerate(CLASSES):
        dataset_yaml += f"  {i}: {name}\n"

    (out_root / "dataset.yaml").write_text(dataset_yaml, encoding="utf-8")

    print("Done!")
    print(f"Train images: {n_train}, Val images: {num_images - n_train}")
    print(f"Dataset YAML: {out_root / 'dataset.yaml'}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic packaging YOLO dataset.")
    parser.add_argument("--num_images", type=int, default=10000, help="Total images (train+val).")
    parser.add_argument("--train_split", type=float, default=0.9, help="Fraction for train.")
    args = parser.parse_args()

    main(num_images=args.num_images, train_split=args.train_split)
