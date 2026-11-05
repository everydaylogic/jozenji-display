#!/usr/bin/env python3
"""定禅寺通りイベントカレンダーのデータ（sources/*.json）から、
表示用ページが読む公開用の events.json を作る。

使い方:
  python3 build_events_json.py <sourcesフォルダ> <出力するevents.json> [--days 21]

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
    ap.add_argument("--days", type=int, default=21, help="今日から何日先まで載せるか")
    ap.add_argument("--today", help="基準日（テスト用, YYYY-MM-DD）")
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(JST).date()
    window_start = today - dt.timedelta(days=1)
    window_end = today + dt.timedelta(days=args.days)

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

    sources.sort(key=lambda s: s["order"])
    events.sort(key=lambda e: (e["start"], e["s"], e["title"]))
    fetched = [s["fetched_at"] for s in sources if s["fetched_at"]]
    out = {
        "v": 1,
        "generated_at": dt.datetime.now(JST).isoformat(timespec="minutes"),
        "data_updated_at": max(fetched) if fetched else "",
        "range": [window_start.isoformat(), window_end.isoformat()],
        "sources": sources,
        "events": events,
    }
    outp = pathlib.Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {outp} ({len(events)} events, {len(sources)} sources)")


if __name__ == "__main__":
    main()
