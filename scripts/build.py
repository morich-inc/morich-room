"""
morichの部屋 - Notion → GitHub Pages ビルドスクリプト
Notionのデータベースからイベント情報を取得してindex.htmlを生成する
"""

import os
import json
import requests
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

# ===== 設定 =====
NOTION_TOKEN    = os.environ["NOTION_TOKEN"]           # GitHub Secretsから取得
NOTION_DB_ID    = os.environ["NOTION_DB_ID"]           # イベントデータベースのID
OUTPUT_PATH     = Path(__file__).parent.parent / "index.html"

JST = timezone(timedelta(hours=9))
TODAY = date.today()

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# ===== Notion API =====

def fetch_events():
    """Notionデータベースからイベント一覧を取得（日付降順）"""
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    payload = {
        "sorts": [{"property": "開催日", "direction": "ascending"}],
    }
    res = requests.post(url, headers=NOTION_HEADERS, json=payload)

    # デバッグ: レスポンスの内容を出力
    print(f"  APIステータス: {res.status_code}")
    data = res.json()
    if res.status_code != 200:
        print(f"  エラー内容: {data}")
        res.raise_for_status()

    results = data.get("results", [])
    if results:
        # 最初の1件のプロパティ名を表示して列名を確認
        print(f"  取得件数（フィルターなし）: {len(results)}")
        print(f"  Notionの列名一覧: {list(results[0]['properties'].keys())}")
    else:
        print(f"  レスポンス全体: {data}")

    return results

def parse_event(page):
    """Notionページのプロパティを辞書に変換"""
    props = page["properties"]

    def text(key):
        p = props.get(key, {})
        if p.get("type") == "rich_text":
            return "".join(t["plain_text"] for t in p.get("rich_text", []))
        if p.get("type") == "title":
            return "".join(t["plain_text"] for t in p.get("title", []))
        return ""

    def url(key):
        p = props.get(key, {})
        return p.get("url") or ""

    def select(key):
        p = props.get(key, {})
        return (p.get("select") or {}).get("name", "")

    def number(key):
        p = props.get(key, {})
        return p.get("number")

    def date_val(key):
        p = props.get(key, {})
        d = (p.get("date") or {}).get("start")
        if not d:
            return None
        try:
            return datetime.fromisoformat(d).date()
        except Exception:
            return None

    # 「会社名・役職」が1列にまとまっている場合と、分かれている場合の両方に対応
    company_role_combined = text("会社名・役職")   # 1列にまとまっている場合
    company = text("会社名") or company_role_combined
    role    = text("役職")   # 別列があればそちらを使う、なければ空

    # Vol番号：テキスト型・列名「Vol.」に対応
    vol_raw = text("Vol.") or text("Vol")
    vol_num = None
    if vol_raw:
        try:
            vol_num = int(str(vol_raw).replace("Vol.", "").replace("Vol", "").strip())
        except ValueError:
            vol_num = vol_raw  # 変換できなければそのまま表示

    event_date = date_val("開催日")
    return {
        "vol":        vol_num,
        "date":       event_date,
        "date_str":   event_date.strftime("%-m月%-d日(%a)") if event_date else "",
        "guest_name": text("ゲスト名"),
        "company":    company,
        "role":       role,
        "apply_url":  url("申込URL"),
        "youtube_url":url("YouTubeURL"),
        "status":     select("ステータス"),   # 募集中 / 満員 / 終了 / キャンセル
        "description":text("説明"),
    }

# ===== HTML生成 =====

WEEKDAY_JP = {"Mon":"月","Tue":"火","Wed":"水","Thu":"木","Fri":"金","Sat":"土","Sun":"日"}

def fmt_date(d: date) -> str:
    wd = d.strftime("%a")
    return f"{d.month}月{d.day}日({WEEKDAY_JP.get(wd, wd)})"

def event_card(ev, highlight=False):
    """イベントカードHTML（次回 or 今後の予定）"""
    status = ev["status"]
    vol_label = f"Vol.{ev['vol']}" if ev["vol"] else ""

    if status == "終了":
        btn = ""
    elif status == "満員":
        btn = '<span class="btn btn--full">満員御礼</span>'
    elif ev["apply_url"]:
        btn = f'<a href="{ev["apply_url"]}" class="btn btn--apply" target="_blank" rel="noopener">申し込みはこちら →</a>'
    else:
        btn = '<span class="btn btn--soon">近日公開</span>'

    desc_html = f'<p class="card__desc">{ev["description"]}</p>' if ev["description"] else ""
    yt_html = f'<a href="{ev["youtube_url"]}" class="card__yt" target="_blank" rel="noopener">▶ YouTube で視聴</a>' if ev["youtube_url"] else ""

    cls = "card card--highlight" if highlight else "card"
    next_badge = '<span class="badge">次回開催</span>' if highlight else ""

    return f"""
    <div class="{cls}">
      <div class="card__header">
        {next_badge}
        <span class="card__vol">{vol_label}</span>
        <span class="card__date">{ev['date_str']}</span>
        <span class="card__status card__status--{status}">{status}</span>
      </div>
      <div class="card__body">
        <p class="card__company">{ev['company']}</p>
        {'<p class="card__role">' + ev['role'] + '</p>' if ev['role'] else ''}
        <p class="card__guest">{ev['guest_name']} 様</p>
        {desc_html}
      </div>
      <div class="card__footer">
        {btn}
        {yt_html}
      </div>
    </div>"""

def past_row(ev):
    yt = f'<a href="{ev["youtube_url"]}" target="_blank" rel="noopener">▶ 視聴</a>' if ev["youtube_url"] else ""
    return f"""
    <tr>
      <td>{f'Vol.{ev["vol"]}' if ev["vol"] else ""}</td>
      <td>{ev['date_str']}</td>
      <td>{ev['company']}</td>
      <td>{ev['guest_name']} 様</td>
      <td>{yt}</td>
    </tr>"""

def build_html(events):
    upcoming = [e for e in events if e["date"] and e["date"] >= TODAY and e["status"] != "キャンセル"]
    past     = [e for e in events if e["date"] and e["date"] < TODAY  and e["status"] != "キャンセル"]
    past.sort(key=lambda e: e["date"], reverse=True)

    next_event_html = event_card(upcoming[0], highlight=True) if upcoming else "<p>次回の日程は準備中です。</p>"
    upcoming_cards  = "\n".join(event_card(e) for e in upcoming[1:]) if len(upcoming) > 1 else ""
    past_rows       = "\n".join(past_row(e) for e in past)

    upcoming_section = f"""
    <section class="section" id="upcoming">
      <h2 class="section__title">今後の開催スケジュール</h2>
      <div class="cards">{upcoming_cards}</div>
    </section>""" if upcoming_cards else ""

    past_section = f"""
    <section class="section" id="past">
      <h2 class="section__title">過去の出演者</h2>
      <table class="past-table">
        <thead><tr><th>Vol</th><th>日付</th><th>会社</th><th>ゲスト</th><th>アーカイブ</th></tr></thead>
        <tbody>{past_rows}</tbody>
      </table>
    </section>""" if past_rows else ""

    updated = datetime.now(JST).strftime("%Y年%m月%d日 %H:%M")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex, nofollow">
  <title>morichの部屋｜上場企業の社長が立ち寄る空間</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>

  <!-- ヘッダー -->
  <header class="hero">
    <div class="hero__inner">
      <img src="assets/logo.png" alt="morichの部屋" class="hero__logo">
      <p class="hero__tagline">上場企業の社長が立ち寄る空間<br>～森本千賀子とリアルトーク～</p>
      <p class="hero__sub">リアル参加 &amp; YouTube配信 ／ 毎月開催</p>
    </div>
  </header>

  <main class="main">

    <!-- 企画について -->
    <section class="section section--about">
      <h2 class="section__title">morichの部屋とは</h2>
      <p class="about__text">
        「morichの部屋」は、上場企業の代表をゲストにお招きし、<br>
        森本千賀子と共にビジネス成功の秘訣や経営哲学について<br>
        深く掘り下げる対談企画です。
      </p>
      <div class="features">
        <div class="feature">
          <span class="feature__icon">💬</span>
          <h3>直接質問できる</h3>
          <p>上場企業の社長との貴重な対談。質疑応答の機会あり。</p>
        </div>
        <div class="feature">
          <span class="feature__icon">📡</span>
          <h3>ハイブリッド開催</h3>
          <p>リアル参加もYouTubeライブ視聴も可能。</p>
        </div>
        <div class="feature">
          <span class="feature__icon">🤝</span>
          <h3>ネットワーキング</h3>
          <p>同業者・異業種との交流チャンス。</p>
        </div>
      </div>
    </section>

    <!-- 次回開催 -->
    <section class="section" id="next">
      <h2 class="section__title">次回開催</h2>
      {next_event_html}
    </section>

    {upcoming_section}

    <!-- 参加方法 -->
    <section class="section section--how">
      <h2 class="section__title">参加方法</h2>
      <div class="how-grid">
        <div class="how-card">
          <h3>🏢 リアル参加</h3>
          <ul>
            <li>東京都杉並区高円寺</li>
            <li>定員：20名（先着順）</li>
            <li>参加費：<strong>8,000円</strong></li>
          </ul>
        </div>
        <div class="how-card">
          <h3>📺 オンライン参加</h3>
          <ul>
            <li>YouTubeライブ配信</li>
            <li>チャンネル登録者限定</li>
            <li>視聴費：<strong>無料</strong></li>
          </ul>
        </div>
      </div>
    </section>

    {past_section}

  </main>

  <!-- フッター -->
  <footer class="footer">
    <p>主催：株式会社morich　／　お問い合わせ：<a href="mailto:info@morich.jp">info@morich.jp</a></p>
    <p><a href="https://morich.jp/" target="_blank" rel="noopener">morich.jp</a></p>
    <p class="footer__updated">最終更新：{updated}</p>
  </footer>

</body>
</html>"""

# ===== メイン =====

def main():
    print("Notionからデータを取得中...")
    raw_events = fetch_events()
    events = [parse_event(e) for e in raw_events]
    events = [e for e in events if e["date"]]  # 日付なしは除外
    events.sort(key=lambda e: e["date"])
    print(f"  取得: {len(events)}件")

    print("HTMLを生成中...")
    html = build_html(events)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"  出力: {OUTPUT_PATH}")
    print("完了！")

if __name__ == "__main__":
    main()
