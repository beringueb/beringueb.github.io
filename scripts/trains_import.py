"""Turn the "Rail travels" Google Sheet export into the stats shown on /misc/trains/.

Usage:
    python3 scripts/trains_import.py ~/Downloads/"Rail travels - Feuille 1.csv"

Reads the CSV export (File > Download > CSV) and writes data/trains.json.
Only totals, rankings and month-level records are written: the raw log with exact
dates and times never enters the (public) repository. Standard library only.

Expected columns: date (dd/mm/yy), HEURE, TYPE/COMPAGNIE, RAME, PARCOURS ("A - B"),
KM, TEMPS (hh:mm), COMMENTAIRES ("Retard ~10min", "Retard ~1h20").
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "trains.json"

# Station spelling fixes and clearer public names. Left: as typed in the sheet.
STATION_ALIASES = {
    "Sarrbrücken HBF": "Saarbrücken Hbf",
    "Saarbrucken HBF": "Saarbrücken Hbf",
    "Saarbrücken HBF": "Saarbrücken Hbf",
    "Stutgart HBF": "Stuttgart Hbf",
    "Stutgart Untertürckeim": "Stuttgart-Untertürkheim",
    "Stugart Untertürckeim": "Stuttgart-Untertürkheim",
    "Nurnberg HBF": "Nürnberg Hbf",
    "Radofzell": "Radolfzell",
    "Bristol": "Bristol Temple Meads",
    "Lyon Part Dieu": "Lyon Part-Dieu",
    "Genève Cornacin": "Genève Cornavin",
    "B'ham New Street": "Birmingham New Street",
    "Manchester Picadilly": "Manchester Piccadilly",
    "Bath SPA": "Bath Spa",
    "Fishguard/Goodwich": "Fishguard & Goodwick",
    "St Charles": "Marseille St-Charles",
    "Blancarde": "Marseille Blancarde",
    "Paris Lyon": "Paris Gare de Lyon",
    "St Pancras": "London St Pancras",
    "Paddington": "London Paddington",
    "Charing Cross": "London Charing Cross",
    "Farringdon": "London Farringdon",
}

OPERATOR_NAMES = {
    "TfW": "Transport for Wales",
    "SBB - CFF": "SBB CFF",
    "OUIGO Espana": "OUIGO España",
    "Cross Country": "CrossCountry",
}

TYPE_NAMES = {
    "ICE 3 407": "ICE 3 (Class 407)",
    "Prima 2": "Prima II",
    "4010": "ÖBB Class 4010",
    "Class 390 - Pendolino": "Class 390 Pendolino",
}

EARTH_KM = 40075
MOON_KM = 384400
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def station(name):
    name = name.strip()
    name = STATION_ALIASES.get(name, name)
    return re.sub(r"\bHBF\b", "Hbf", name)


def operator(raw):
    """'SNCF (TGV)' -> ('SNCF', 'TGV'); 'ÖBB (nightjet)' -> ('ÖBB', 'Nightjet')."""
    raw = raw.strip()
    m = re.match(r"^(.*?)\s*\((.*)\)\s*$", raw)
    company, service = (m.group(1), m.group(2)) if m else (raw, "")
    company = OPERATOR_NAMES.get(company.strip(), company.strip())
    return company, service[:1].upper() + service[1:]


def rolling_stock(raw):
    """'800031 (Class 800)' -> ('800031', 'Class 800'); 'BB 7268 (loco)' -> ('BB 7268', 'Locomotive-hauled')."""
    raw = raw.strip()
    if raw.strip("-") == "":
        return None, None
    parens = [p.strip() for p in re.findall(r"\(([^)]*)\)", raw)]
    unit = re.sub(r"\([^)]*\)", "", raw).strip(" -") or None
    kinds = [p for p in parens if p.lower() != "loco"]
    if kinds:
        kind = TYPE_NAMES.get(kinds[0], kinds[0])
        if any(p.lower() == "loco" for p in parens):
            kind += " (loco)"
    elif parens:
        kind = "Locomotive-hauled"
    else:
        kind = None
    return unit, kind


def minutes(hhmm):
    m = re.match(r"^\s*(\d+):(\d\d)", hhmm or "")
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def delay_minutes(comment):
    m = re.search(r"Retard\s*~\s*(?:(\d+)\s*h\s*(\d+)?|(\d+)\s*min)", comment or "", re.I)
    if not m:
        return None
    if m.group(3):
        return int(m.group(3))
    return int(m.group(1)) * 60 + int(m.group(2) or 0)


def fmt_duration(mins):
    return f"{mins // 60}h{mins % 60:02d}"


def month_label(d):
    return f"{MONTHS[d.month - 1]} {d.year}"


def read_trips(path):
    trips = []
    with open(path, encoding="utf-8") as f:
        rows = list(csv.reader(f))
    for r in rows[1:]:
        if len(r) < 7 or not re.match(r"\d\d/\d\d/\d\d", r[0].strip()):
            continue
        d, m, y = (int(x) for x in r[0].strip().split("/"))
        a, b = re.split(r"\s+-\s*|\s*-\s+", r[4].strip(), maxsplit=1)
        company, service = operator(r[2])
        unit, kind = rolling_stock(r[3])
        trips.append({
            "date": date(2000 + y, m, d),
            "company": company,
            "service": service,
            "unit": unit,
            "type": kind,
            "from": station(a),
            "to": station(b),
            "km": int(r[5]) if r[5].strip() else 0,
            "minutes": minutes(r[6]),
            "delay": delay_minutes(r[7] if len(r) > 7 else ""),
        })
    return trips


def ranking(counter_trips, counter_km=None, top=10):
    items = counter_trips.most_common()
    out = [{"name": k, "trips": v, **({"km": counter_km[k]} if counter_km else {})} for k, v in items]
    return out[:top]


def main(path):
    trips = read_trips(path)
    trips.sort(key=lambda t: t["date"])
    n = len(trips)
    km = sum(t["km"] for t in trips)
    timed = [t for t in trips if t["minutes"]]
    mins = sum(t["minutes"] for t in timed)
    delayed = [t for t in trips if t["delay"]]

    # rankings
    op_trips, op_km = Counter(), Counter()
    type_trips, type_km = Counter(), Counter()
    visits = Counter()
    routes = Counter()
    for t in trips:
        op_trips[t["company"]] += 1
        op_km[t["company"]] += t["km"]
        if t["type"]:
            type_trips[t["type"]] += 1
            type_km[t["type"]] += t["km"]
        visits[t["from"]] += 1
        visits[t["to"]] += 1
        routes[" ↔ ".join(sorted((t["from"], t["to"])))] += 1

    # units ridden more than once (the sheet's original question)
    unit_rides = defaultdict(list)
    for t in trips:
        if t["unit"]:
            unit_rides[(t["company"], t["unit"], t["type"])].append(t)
    repeats = sorted(
        ({"unit": u, "type": k or "", "operator": c, "times": len(v),
          "first": month_label(v[0]["date"]), "last": month_label(v[-1]["date"])}
         for (c, u, k), v in unit_rides.items() if len(v) > 1),
        key=lambda x: (-x["times"], x["operator"], x["unit"]))

    # by year
    years = defaultdict(lambda: {"trips": 0, "km": 0, "minutes": 0})
    for t in trips:
        y = years[t["date"].year]
        y["trips"] += 1
        y["km"] += t["km"]
        y["minutes"] += t["minutes"] or 0
    by_year = [{"year": y, "trips": v["trips"], "km": v["km"], "hours": round(v["minutes"] / 60)}
               for y, v in sorted(years.items())]

    # records
    def trip_desc(t, value):
        return {"route": f"{t['from']} → {t['to']}", "value": value, "when": month_label(t["date"]),
                "operator": f"{t['company']} {t['service']}".strip()}

    longest = max(trips, key=lambda t: t["km"])
    longest_t = max(timed, key=lambda t: t["minutes"])
    fast_pool = [t for t in timed if t["km"] >= 100]
    fastest = max(fast_pool, key=lambda t: t["km"] / t["minutes"])
    shortest = min(trips, key=lambda t: t["km"])
    worst = max(delayed, key=lambda t: t["delay"]) if delayed else None
    months = Counter()
    for t in trips:
        months[(t["date"].year, t["date"].month)] += t["km"]
    (by, bm), bkm = months.most_common(1)[0]

    records = [
        {"label": "Longest trip", **trip_desc(longest, f"{longest['km']:,} km")},
        {"label": "Longest time on board", **trip_desc(longest_t, fmt_duration(longest_t["minutes"]))},
        {"label": "Fastest trip (average)", **trip_desc(fastest, f"{fastest['km'] / fastest['minutes'] * 60:.0f} km/h")},
        {"label": "Shortest trip", **trip_desc(shortest, f"{shortest['km']} km")},
    ]
    if worst:
        records.append({"label": "Biggest delay", **trip_desc(worst, f"~{fmt_duration(worst['delay'])}")})
    records.append({"label": "Busiest month", "route": "", "value": f"{bkm:,} km",
                    "when": f"{MONTHS[bm - 1]} {by}", "operator": ""})

    out = {
        "period": {"first": month_label(trips[0]["date"]), "last": month_label(trips[-1]["date"])},
        "totals": {
            "trips": n,
            "km": km,
            "hours": round(mins / 60),
            "avg_speed": round(sum(t["km"] for t in timed) / mins * 60),
            "earth_laps": round(km / EARTH_KM, 2),
            "moon_share": round(100 * km / MOON_KM),
            "stations": len(visits),
            "operators": len(op_trips),
            "units": len(unit_rides),
            "repeat_units": len(repeats),
            "delayed_trips": len(delayed),
            "delayed_share": round(100 * len(delayed) / n),
            "delay_hours": round(sum(t["delay"] for t in delayed) / 60, 1),
            "untimed_trips": n - len(timed),
        },
        "by_year": by_year,
        "operators": ranking(op_trips, op_km),
        "types": ranking(type_trips, type_km),
        "stations": ranking(visits, top=10),
        "routes": ranking(routes, top=5),
        "repeat_units": repeats,
        "records": records,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{n} trips, {km:,} km, {len(repeats)} units ridden more than once -> {OUT}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
