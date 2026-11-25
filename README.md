# Nur Pastanesi · WEZ Dortmund — tek sayfalık site

Kaydırdıkça katman katman kurulan pasta animasyonu, gerçek menü (fotoğraf + fiyat), arama, TR/DE dil seçimi.

## Yapı
| Dosya | Görevi |
|---|---|
| `index.html` | Sayfanın tamamı (tasarım, animasyon, menü arayüzü) |
| `assets/menu-data.js` | Menü verisi — **otomatik üretilir**, elle düzenlemeyin |
| `assets/menu/*.webp` | Ürün fotoğrafları (560×560) |
| `scripts/update_menu.py` | Menüyü nurpastanesi.com'dan çekip yukarıdaki iki öğeyi yeniler |
| `.github/workflows/pages.yml` | `main`'e her push'ta siteyi GitHub Pages'e yayınlar |
| `.github/workflows/menu-sync.yml` | Her gece menüyü kontrol eder, değiştiyse commit'ler |

## Menüyü güncellemek
Menüdeki fiyat/ürün değişikliklerini nurpastanesi.com'daki menü panelinden yapın. Site her gece kendini günceller.
Hemen güncellemek için: GitHub → **Actions → Menüyü güncelle → Run workflow**, ya da yerelde:

```bash
pip install pillow
python3 scripts/update_menu.py
```

## Yayına alma (bir kerelik)
1. Bu dalı `main`'e birleştirin.
2. GitHub → **Settings → Pages → Source: GitHub Actions**.
3. Kendi alan adınız için Settings → Pages → Custom domain.

## Metinleri değiştirmek
`index.html` içindeki `const T = { tr:{…}, de:{…} }` sözlüğü tüm Türkçe/Almanca metinleri tutar.
Favoriler listesi: `HIGHLIGHTS` dizisi (ürünlerin Türkçe adları).
