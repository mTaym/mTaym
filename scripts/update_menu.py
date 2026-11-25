#!/usr/bin/env python3
"""Nur Pastanesi menüsünü nurpastanesi.com'dan çekip siteye işler.

Kullanım:  python3 scripts/update_menu.py
Gerekli:   Python 3.9+, Pillow  (pip install pillow)

Yaptığı iş:
  1. menu-data.json dosyasını indirir (kategoriler, ürünler, fiyatlar, açıklamalar).
  2. Ürün fotoğraflarını indirir, 560x560 webp'ye çevirir -> assets/menu/<hash>.webp
  3. assets/menu-data.js dosyasını yeniden yazar (window.NUR_MENU).
  4. Artık kullanılmayan eski fotoğrafları siler.
Fotoğraf adları kaynak adresin özetinden üretilir; menü değişmedikçe dosyalar değişmez.
"""
import concurrent.futures as cf
import hashlib
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://nurpastanesi.com"
BRANCH = "/menu/subeler/kaufland/"
ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "assets" / "menu"
OUT_JS = ROOT / "assets" / "menu-data.js"
SIZE = 560
UA = {"User-Agent": "Mozilla/5.0 (menu-sync)"}


def fetch(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def bundled_images():
    """Bazı ürünlerin görseli uygulama paketinin içinde ("78 maras dondurmasi" gibi anahtarlarla)."""
    html = fetch(BASE + BRANCH)[0].decode("utf-8", "replace")
    out = {}
    for js in re.findall(r'src="([^"]+\.js)"', html):
        code = fetch(urllib.parse.urljoin(BASE + BRANCH, js))[0].decode("utf-8", "replace")
        for p in set(re.findall(r'/menu/subeler/kaufland/assets/[^"\' )]+\.(?:webp|png|jpe?g)', code)):
            name = urllib.parse.unquote(p.rsplit("/", 1)[1])
            out[name.rsplit("-", 1)[0]] = p
    return out


def slug(s):
    s = s.lower()
    for a, b in zip("çğıöşü", "cgiosu"):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]", "", s)


def convert(url):
    from PIL import Image, ImageOps

    name = hashlib.sha1(url.encode()).hexdigest()[:12] + ".webp"
    dest = IMG_DIR / name
    if dest.exists():
        return name
    try:
        data, ctype = fetch(BASE + urllib.parse.quote(url))
        if "html" in ctype:
            return None
        im = Image.open(io.BytesIO(data))
        im = ImageOps.exif_transpose(im).convert("RGB")
        im = ImageOps.fit(im, (SIZE, SIZE), Image.LANCZOS)
        im.save(dest, "WEBP", quality=72, method=6)
        return name
    except Exception as e:  # bozuk / eksik görsel: ürün yer tutucuyla gösterilir
        print("  ! görsel alınamadı:", url, "-", e, file=sys.stderr)
        return None


def main():
    print("menu-data.json indiriliyor…")
    data = json.loads(fetch(BASE + BRANCH + "menu-data.json")[0])
    bundled = bundled_images()
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    cats, urls = [], set()
    for c in data.get("categories", []):
        items = []
        for it in (c.get("panel") or {}).get("featured", []):
            key = it.get("imageKey") or ""
            url = key if key.startswith("/") else bundled.get(key)
            if url:
                urls.add(url)
            d = it.get("description") or {}
            n = it.get("name") or {}
            items.append({
                "tr": (n.get("tr") or "").strip(), "de": (n.get("de") or n.get("tr") or "").strip(),
                "dtr": (d.get("tr") or "").strip(), "dde": (d.get("de") or "").strip(),
                "p": it.get("price") if isinstance(it.get("price"), (int, float)) else None,
                "_src": url,
            })
        if items:
            t = c.get("title") or {}
            cats.append({"id": slug(c.get("id", "")), "tr": (t.get("tr") or "").strip(),
                         "de": (t.get("de") or "").strip(), "items": items})

    print(f"{len(urls)} görsel işleniyor…")
    with cf.ThreadPoolExecutor(8) as ex:
        done = dict(zip(urls, ex.map(convert, urls)))

    used = set()
    for c in cats:
        for it in c["items"]:
            name = done.get(it.pop("_src"))
            it["img"] = f"assets/menu/{name}" if name else None
            if name:
                used.add(name)

    for f in IMG_DIR.glob("*.webp"):
        if f.name not in used:
            f.unlink()

    body = json.dumps(cats, ensure_ascii=False, separators=(",", ":"))
    OUT_JS.write_text(
        "/* Otomatik üretildi: scripts/update_menu.py — elle düzenlemeyin.\n"
        f"   Kaynak: {BASE}{BRANCH}menu-data.json  ·  p = fiyat (€) */\n"
        f"window.NUR_MENU={body};\n", encoding="utf-8")
    n = sum(len(c["items"]) for c in cats)
    print(f"Tamam: {len(cats)} kategori, {n} ürün, {len(used)} fotoğraf.")


if __name__ == "__main__":
    main()
