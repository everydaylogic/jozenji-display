#!/usr/bin/env python3
"""定禅寺通りイベントカレンダーのデータ（sources/*.json）から、
表示用ページが読む公開用の events.json を作る。

使い方:
  python3 build_events_json.py <sourcesフォルダ> <出力するevents.json> --clinic <clinic/calendar.json>

月間カレンダーでも使うので、今月1日以降に終わる予定は（先の月の分も）すべて載せる。
健診の受付状況は約5か月先まで載せる。

公開されるファイルなので、載せるのはイベント名・日時・会場・色だけにする
（問い合わせ先などのメモやURLは載せない）。
"""
import argparse
import datetime as dt
import json
import pathlib
import sys

JST = dt.timezone(dt.timedelta(hours=9))

# 暗い背景で見やすい色（カレンダー本体の色を少し明るくしたもの）
DARK_COLORS = {
    "rensa": "#b197fc",
    "miyagi-hall": "#4dabf7",
    "mitsukoshi": "#f06595",
    "kotodai": "#f2b705",
    "morisanho": "#51cf66",
}

SHORT_NAMES = {
    "rensa": "Rensa",
    "miyagi-hall": "東京エレクトロンホール宮城",
    "mitsukoshi": "仙台三越",
    "kotodai": "勾当台公園",
    "morisanho": "一番町健診クリニック",
}


def parse_date(s):
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s[:10])
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sources_dir")
    ap.add_argument("out")
    ap.add_argument("--days", type=int, default=0, help="今日から何日先まで載せるか（0 = 制限なし）")
    ap.add_argument("--clinic-days", type=int, default=150, help="健診を今日から何日先まで載せるか")
    ap.add_argument("--today", help="基準日（テスト用, YYYY-MM-DD）")
    ap.add_argument("--clinic", help="健診の年間スケジュール（clinic/calendar の JSON）")
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(JST).date()
    window_start = today.replace(day=1)
    window_end = today + dt.timedelta(days=args.days) if args.days else dt.date.max

    sources = []
    events = []
    for path in sorted(pathlib.Path(args.sources_dir).glob("*.json")):
        sid = path.stem
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"skip {path}: {e}", file=sys.stderr)
            continue
        kind = "clinic" if doc.get("kind") == "clinic_calendar" else "event"
        sources.append({
            "id": sid,
            "name": SHORT_NAMES.get(sid, doc.get("name", sid)),
            "color": DARK_COLORS.get(sid, doc.get("color", "#adb5bd")),
            "kind": kind,
            "order": doc.get("order", 99),
            "ok": bool(doc.get("ok", True)),
            "fetched_at": doc.get("fetched_at", ""),
        })
        for ev in doc.get("events", []) or []:
            start = parse_date(ev.get("date_start"))
            if not start:
                continue
            end = parse_date(ev.get("date_end")) or start
            if end < window_start or start > window_end:
                continue
            events.append({
                "s": sid,
                "title": (ev.get("title") or "").strip(),
                "venue": (ev.get("venue") or "").strip(),
                "time": (ev.get("time") or "").strip(),
                "start": start.isoformat(),
                "end": end.isoformat(),
            })

    # 健診：フロアごとの日別の状態（open=終日 / pm_closed=午前のみ / closed=休診）
    clinic = None
    if args.clinic:
        try:
            cal = json.loads(pathlib.Path(args.clinic).read_text(encoding="utf-8"))
            floors = [f for f in ("women", "men") if f in cal.get("floors", {})]
            labels = {"women": "女性", "men": "男性"}
            days = {}
            d = window_start
            clinic_end = today + dt.timedelta(days=args.clinic_days)
            while d <= clinic_end:
                k = d.isoformat()
                st = [cal["floors"][f]["days"].get(k) for f in floors]
                if any(st):
                    days[k] = st
                d += dt.timedelta(days=1)
            clinic = {
                "name": cal.get("name", "一番町健診クリニック"),
                "color": DARK_COLORS["morisanho"],
                "floors": [labels.get(f, f) for f in floors],
                "days": days,
            }
        except (OSError, json.JSONDecodeError, KeyError) as e:
            print(f"clinic skipped: {e}", file=sys.stderr)

    sources.sort(key=lambda s: s["order"])
    events.sort(key=lambda e: (e["start"], e["s"], e["title"]))
    fetched = [s["fetched_at"] for s in sources if s["fetched_at"]]
    last_end = max((e["end"] for e in events), default=today.isoformat())
    out = {
        "v": 1,
        "generated_at": dt.datetime.now(JST).isoformat(timespec="minutes"),
        "data_updated_at": max(fetched) if fetched else "",
        "range": [window_start.isoformat(), last_end],
        "sources": sources,
        "events": events,
        "clinic": clinic,
    }
    outp = pathlib.Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {outp} ({len(events)} events, {len(sources)} sources)")


if __name__ == "__main__":
    main()
