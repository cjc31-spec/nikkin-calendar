#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日金カレンダー自動生成スクリプト
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HTML/CSS + jpholiday + Playwright で正確なカレンダーPNGを生成

【使い方】
  python3 generate_calendar.py

【カスタマイズ】
  - START_YEAR / START_MONTH : 開始年月
  - END_YEAR   / END_MONTH   : 終了年月
  - header.jpg / footer.jpg  : 配管写真（スクリプトと同じフォルダに配置）
  - logo.png                 : 会社ロゴ（スクリプトと同じフォルダに配置）
"""

import os
import sys
import calendar
import datetime
import base64
import jpholiday
from playwright.sync_api import sync_playwright

# ─── 設定 ────────────────────────────────────
START_YEAR, START_MONTH = 2026, 4
END_YEAR,   END_MONTH   = 2027, 3

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

HEADER_IMAGE = os.path.join(BASE_DIR, "header.jpg")
FOOTER_IMAGE = os.path.join(BASE_DIR, "footer.jpg")
LOGO_IMAGE   = os.path.join(BASE_DIR, "logo.png")

MONTHS_EN = [
    '', 'JANUARY', 'FEBRUARY', 'MARCH',
    'APRIL', 'MAY', 'JUNE', 'JULY',
    'AUGUST', 'SEPTEMBER', 'OCTOBER',
    'NOVEMBER', 'DECEMBER'
]

# ─── 画像をbase64エンコード ──────────────────
def img_to_data_uri(path):
    if not os.path.exists(path):
        return None
    ext = os.path.splitext(path)[1].lower()
    mime = {'jpg': 'image/jpeg', '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', '.png': 'image/png'}.get(ext, 'image/jpeg')
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"


# ─── 会社独自の休業日（土日・国民の祝日以外） ────
COMPANY_HOLIDAYS = {
    # GWブリッジ休暇
    datetime.date(2026, 4, 30),   # 昭和の日翌日
    datetime.date(2026, 5, 1),    # GW連結
    # お盆休み
    datetime.date(2026, 8, 12),
    datetime.date(2026, 8, 13),
    datetime.date(2026, 8, 14),
    # 年末休み
    datetime.date(2026, 12, 29),
    datetime.date(2026, 12, 30),
    datetime.date(2026, 12, 31),
    # 年始休み
    datetime.date(2027, 1, 4),    # 年始休業
}

# ─── 祝日取得 ────────────────────────────────
def get_holidays(year, month):
    """指定月の祝日 + 会社休業日のセットを返す"""
    holidays = set()
    d = datetime.date(year, month, 1)
    while d.month == month:
        if jpholiday.is_holiday(d) or d in COMPANY_HOLIDAYS:
            holidays.add(d.day)
        d += datetime.timedelta(days=1)
    return holidays


# ─── CSS ─────────────────────────────────────
CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: "Hiragino Kaku Gothic ProN", "Hiragino Sans", "Yu Gothic",
               "Noto Sans JP", sans-serif;
  background: #fff;
  width: 840px;
  overflow: hidden;
}

.calendar {
  width: 840px;
  background: #fff;
  display: flex;
  flex-direction: column;
}

/* ── ヘッダー画像 ── */
.header-img {
  width: 100%;
  height: 195px;
  background: linear-gradient(135deg, #6b5b4f 0%, #8a7a6e 40%, #6b5b4f 100%);
  flex-shrink: 0;
}
.header-img.has-image {
  background-size: cover;
  background-position: center;
}

/* ── 年月タイトル ── */
.month-header {
  padding: 28px 0 10px;
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 6px;
  flex-shrink: 0;
}
.year {
  font-size: 32px;
  font-weight: 300;
  color: #2d2a28;
  letter-spacing: 5px;
  margin-right: 8px;
}
.month-num {
  font-size: 112px;
  font-weight: 300;
  color: #2d2a28;
  line-height: 1;
  margin: 0 8px;
}
.month-name {
  font-size: 40px;
  font-weight: 300;
  color: #2d2a28;
  letter-spacing: 7px;
  margin-left: 8px;
}

/* ── カレンダーグリッド ── */
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  padding: 10px 28px 0;
  align-content: start;
}

.day-name {
  text-align: center;
  font-size: 20px;
  font-weight: 400;
  padding: 6px 0 10px;
  letter-spacing: 2px;
  border-bottom: 1px solid #ddd8d2;
}
.day-name.sun { color: #c84432; }
.day-name.sat { color: #3c5db0; }
.day-name.wd  { color: #2d2a28; }

.day-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 98px;
  position: relative;
  font-size: 42px;
  font-weight: 300;
  color: #2d2a28;
}
.day-cell.sun, .day-cell.holiday { color: #c84432; }
.day-cell.sat { color: #3c5db0; }
.day-cell.sat.holiday { color: #c84432; }

/* ×印 */
.day-cell.off::before,
.day-cell.off::after {
  content: '';
  position: absolute;
  width: 58px;
  height: 4px;
  background: #cda230;
  border-radius: 2px;
  top: 50%;
  left: 50%;
}
.day-cell.off::before { transform: translate(-50%, -50%) rotate(45deg); }
.day-cell.off::after  { transform: translate(-50%, -50%) rotate(-45deg); }

/* ── 凡例 ── */
.legend-box {
  margin: 6px 48px;
  padding: 14px 28px;
  background: #f8f3e8;
  border-radius: 14px;
  font-size: 24px;
  color: #2d2a28;
  line-height: 2.2;
  flex-shrink: 0;
}
.x-icon {
  display: inline-block;
  width: 22px;
  height: 22px;
  position: relative;
  vertical-align: middle;
  margin-right: 2px;
}
.x-icon::before,
.x-icon::after {
  content: '';
  position: absolute;
  width: 18px;
  height: 3px;
  background: #cda230;
  border-radius: 1px;
  top: 50%;
  left: 50%;
}
.x-icon::before { transform: translate(-50%, -50%) rotate(45deg); }
.x-icon::after  { transform: translate(-50%, -50%) rotate(-45deg); }

/* ── ロゴ・会社名 ── */
.company {
  text-align: center;
  padding: 6px 0;
  font-size: 26px;
  color: #2d2a28;
  letter-spacing: 3px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.company-logo {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}
.company-logo-placeholder {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: radial-gradient(circle, #2d6ad0 40%, #fff 40%, #fff 55%, #2d6ad0 55%);
}

"""


# ─── HTML生成 ─────────────────────────────────
def build_month_html(year: int, month: int) -> str:
    holidays = get_holidays(year, month)

    # ヘッダー/フッター画像
    hdr_uri = img_to_data_uri(HEADER_IMAGE)
    ftr_uri = img_to_data_uri(FOOTER_IMAGE)
    logo_uri = img_to_data_uri(LOGO_IMAGE)

    hdr_style = f' has-image" style="background-image:url({hdr_uri})' if hdr_uri else ''
    ftr_style = f' has-image" style="background-image:url({ftr_uri})' if ftr_uri else ''

    # 曜日ヘッダー
    day_names = [
        ("SUN", "sun"), ("MON", "wd"), ("TUE", "wd"),
        ("WED", "wd"), ("THU", "wd"), ("FRI", "wd"), ("SAT", "sat"),
    ]
    header_cells = ''.join(
        f'<div class="day-name {cls}">{name}</div>'
        for name, cls in day_names
    )

    # 日付セル（日曜始まりのカレンダー）
    sun_cal = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)
    day_cells = ''

    for week in sun_cal:
        for col, day in enumerate(week):
            if day == 0:
                day_cells += '<div class="day-cell"></div>'
                continue

            is_sun = (col == 0)
            is_sat = (col == 6)
            is_hol = day in holidays
            is_off = is_sun or is_sat or is_hol

            cls = ['day-cell']
            if is_sun: cls.append('sun')
            if is_sat: cls.append('sat')
            if is_hol: cls.append('holiday')
            if is_off: cls.append('off')

            day_cells += f'<div class="{" ".join(cls)}">{day}</div>'

    # ロゴ部分
    if logo_uri:
        logo_html = f'<img class="company-logo" src="{logo_uri}" alt="logo">'
    else:
        logo_html = '<div class="company-logo-placeholder"></div>'

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{year}年{month}月 日金カレンダー</title>
<style>{CSS}</style>
</head>
<body>
<div class="calendar">
  <div class="header-img{hdr_style}"></div>
  <div class="month-header">
    <span class="year">{year}</span>
    <span class="month-num">{month}</span>
    <span class="month-name">{MONTHS_EN[month]}</span>
  </div>
  <div class="cal-grid">
    {header_cells}
    {day_cells}
  </div>
  <div class="legend-box">
    <div>営業時間 ： 8:00〜17:00</div>
    <div><span class="x-icon"></span> ： お休み</div>
  </div>
  <div class="company">{logo_html} 株式会社 日金</div>
</div>
</body>
</html>"""


# ─── メイン ───────────────────────────────────
def generate_months():
    months = []
    y, m = START_YEAR, START_MONTH
    while (y < END_YEAR) or (y == END_YEAR and m <= END_MONTH):
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    months = generate_months()

    print("=" * 55)
    print("  日金カレンダー 自動生成（HTML + Playwright）")
    print(f"  期間: {START_YEAR}年{START_MONTH}月 〜 {END_YEAR}年{END_MONTH}月")
    print("=" * 55)

    # 画像素材の確認
    for label, path in [("ヘッダー写真", HEADER_IMAGE),
                        ("フッター写真", FOOTER_IMAGE),
                        ("ロゴ画像", LOGO_IMAGE)]:
        status = "✓" if os.path.exists(path) else "⚠ なし（プレースホルダー使用）"
        print(f"  {label}: {status}")
    print()

    # 祝日・休業日一覧を表示
    print("  【休業日一覧（土日除く）】")
    for year, month in months:
        d = datetime.date(year, month, 1)
        while d.month == month:
            wd = ['月','火','水','木','金','土','日'][d.weekday()]
            if jpholiday.is_holiday(d):
                name = jpholiday.is_holiday_name(d)
                print(f"    {d} ({wd}) {name}")
            elif d in COMPANY_HOLIDAYS:
                print(f"    {d} ({wd}) 会社休業日")
            d += datetime.timedelta(days=1)
    print()

    # HTML生成 → Playwright でスクリーンショット
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 840, "height": 1200})

        for year, month in months:
            # HTML 生成
            html = build_month_html(year, month)
            html_path = os.path.join(OUTPUT_DIR, f"{year}_{month:02d}_{MONTHS_EN[month]}.html")
            png_path  = os.path.join(OUTPUT_DIR, f"{year}_{month:02d}_{MONTHS_EN[month]}.png")

            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)

            # PNG スクリーンショット
            page.goto(f"file://{html_path}")
            page.wait_for_load_state("networkidle")
            # コンテンツの実際の高さを取得してクリップ
            content_height = page.evaluate("document.querySelector('.calendar').offsetHeight")
            page.screenshot(path=png_path, full_page=False,
                            clip={"x": 0, "y": 0, "width": 840, "height": content_height})

            print(f"  ✓ {year}年{month:02d}月 → {os.path.basename(png_path)}")

        browser.close()

    print(f"\n✅ {len(months)}ヶ月分を生成しました！")
    print(f"   PNG: {OUTPUT_DIR}/*.png")
    print(f"   HTML: {OUTPUT_DIR}/*.html")


if __name__ == "__main__":
    main()
