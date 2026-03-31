#!/usr/bin/env python3
"""
月次カレンダー差し替えスクリプト（GitHub Actions用）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 今日が当月の最終営業日かどうかを判定
- 最終営業日であれば、翌月のカレンダー画像を docs/images/calendar.png にコピー
- 対象期間: 2026年4月 〜 2026年9月
"""

import datetime
import os
import shutil
import sys
import jpholiday

# ─── 会社独自の休業日 ─────────────────────────
COMPANY_HOLIDAYS = {
    datetime.date(2026, 4, 30),
    datetime.date(2026, 5, 1),
    datetime.date(2026, 8, 12),
    datetime.date(2026, 8, 13),
    datetime.date(2026, 8, 14),
    datetime.date(2026, 12, 29),
    datetime.date(2026, 12, 30),
    datetime.date(2026, 12, 31),
    datetime.date(2027, 1, 4),
}

MONTHS_EN = [
    '', 'JANUARY', 'FEBRUARY', 'MARCH',
    'APRIL', 'MAY', 'JUNE', 'JULY',
    'AUGUST', 'SEPTEMBER', 'OCTOBER',
    'NOVEMBER', 'DECEMBER'
]

# 対象期間: 翌月が2026年4月〜2026年9月になる月末
# つまり 2026年3月末〜2026年8月末に実行
VALID_NEXT_MONTHS = [
    (2026, 4), (2026, 5), (2026, 6),
    (2026, 7), (2026, 8), (2026, 9),
]


def is_business_day(d):
    """営業日かどうか判定"""
    if d.weekday() >= 5:  # 土日
        return False
    if jpholiday.is_holiday(d):
        return False
    if d in COMPANY_HOLIDAYS:
        return False
    return True


def get_last_business_day(year, month):
    """指定月の最終営業日を返す"""
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    d = datetime.date(year, month, last_day)
    while not is_business_day(d):
        d -= datetime.timedelta(days=1)
    return d


def get_next_month(year, month):
    """翌月の年月を返す"""
    if month == 12:
        return year + 1, 1
    return year, month + 1


def main():
    today = datetime.date.today()
    print(f"実行日: {today}")

    # 今日がこの月の最終営業日か判定
    last_biz = get_last_business_day(today.year, today.month)
    print(f"今月の最終営業日: {last_biz}")

    if today != last_biz:
        print("→ 今日は最終営業日ではありません。スキップします。")
        return

    # 翌月を計算
    next_year, next_month = get_next_month(today.year, today.month)
    print(f"→ 翌月: {next_year}年{next_month}月")

    # 対象期間チェック
    if (next_year, next_month) not in VALID_NEXT_MONTHS:
        print(f"→ {next_year}年{next_month}月は対象期間外です。スキップします。")
        return

    # 画像ファイルのパス
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(base_dir, "output",
                       f"{next_year}_{next_month:02d}_{MONTHS_EN[next_month]}.png")
    dst = os.path.join(base_dir, "docs", "images", "calendar.png")

    if not os.path.exists(src):
        print(f"エラー: {src} が見つかりません")
        sys.exit(1)

    shutil.copy2(src, dst)
    print(f"✅ カレンダー画像を差し替えました: {MONTHS_EN[next_month]} {next_year}")
    print(f"   {os.path.basename(src)} → docs/images/calendar.png")


if __name__ == "__main__":
    main()
