"""Draw the route heatmap shown on /misc/trains/ as a static SVG.

Called by trains_import.py. Writes assets/images/trains_map.svg, which the page
inlines (so hovering a route shows its native tooltip): stations merged by city,
routes as gentle arcs, Iberia and Morocco in an inset. It sits on a faint
coastline/border background, scripts/trains_basemap.json, cut from Natural Earth
(public domain) by:
    python3 scripts/trains_map.py basemap ne_50m_admin_0_countries.geojson
Standard library only.
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGES = HERE.parent / "assets" / "images"
BASEMAP = HERE / "trains_basemap.json"
BBOX = (31.5, 54.0, -8.5, 15.5)   # lat_min, lat_max, lon_min, lon_max kept in the basemap

# (lat, lon), station names as normalised by trains_import.station()
COORDS = {
    "Algeciras": (36.131, -5.462), "Amstetten": (48.122, 14.873), "Annecy": (45.902, 6.122),
    "Aurillac": (44.921, 2.437), "Avignon TGV": (43.922, 4.786), "Aéroport CDG": (49.004, 2.571),
    "Bandol": (43.139, 5.750), "Barcelona Sants": (41.379, 2.140), "Bath Spa": (51.378, -2.357),
    "Ben Guérir": (32.236, -7.954), "Birmingham New Street": (52.478, -1.899), "Blois": (47.586, 1.322),
    "Bordeaux St Jean": (44.826, -0.556), "Boussens": (43.176, 0.973), "Bregenz": (47.503, 9.739),
    "Bregenz Hafen": (47.505, 9.744), "Bristol Temple Meads": (51.449, -2.581),
    "Briton Ferry": (51.638, -3.818), "Bruxelles Midi": (50.836, 4.336), "Béning": (49.136, 6.836),
    "Calais Ville": (50.953, 1.852), "Cambridge": (52.194, 0.137), "Cardiff": (51.475, -3.179),
    "Casa Voyageurs": (33.590, -7.591), "Cerbère": (42.442, 3.166), "Chambéry": (45.571, 5.920),
    "Clermont Ferrand": (45.779, 3.100), "Collioure": (42.526, 3.078), "Dax": (43.721, -1.050),
    "Deal": (51.223, 1.399), "Didcot Parkway": (51.611, -1.243), "Dijon Ville": (47.323, 5.027),
    "Dover Priory": (51.126, 1.305), "Edale": (53.365, -1.817), "Exeter St Davids": (50.729, -3.544),
    "Facture Biganos": (44.640, -0.976), "Figeac": (44.609, 2.035),
    "Fishguard & Goodwick": (52.004, -4.994), "Fleurville/Pont de Vaux": (46.444, 4.881),
    "Forbach": (49.188, 6.898), "Friedrichshafen": (47.653, 9.473), "Genève Cornavin": (46.210, 6.142),
    "Grenoble": (45.191, 5.715), "Götzis": (47.336, 9.643), "Haverfordwest": (51.802, -4.962),
    "Hohenems": (47.364, 9.683), "Hope": (53.346, -1.730), "Karlsruhe Hbf": (48.994, 8.402),
    "La Hume": (44.646, -1.115), "Les Aubrais": (47.927, 1.907), "Leucate La Franqui": (42.906, 3.026),
    "Lille Europe": (50.639, 3.075), "Lille Flandres": (50.637, 3.071), "Linz Hbf": (48.290, 14.292),
    "London Charing Cross": (51.508, -0.125), "London Euston": (51.528, -0.134),
    "London Farringdon": (51.520, -0.105), "London Paddington": (51.516, -0.177),
    "London St Pancras": (51.531, -0.126), "Luzern HB": (47.050, 8.310),
    "Lyon Part-Dieu": (45.761, 4.859), "Lyon Perrache": (45.749, 4.826), "Madrid Atocha": (40.407, -3.689),
    "Manchester Piccadilly": (53.477, -2.231), "Mannheim Hbf": (49.479, 8.469),
    "Marseille Blancarde": (43.296, 5.401), "Marseille St-Charles": (43.303, 5.380),
    "Metz Ville": (49.110, 6.177), "Mont de Marsan": (43.891, -0.501),
    "Montpellier St Roch": (43.6047, 3.8807), "Montpellier Sud France": (43.595, 3.923),
    "Morbier": (46.537, 6.017), "Morez": (46.522, 6.025), "Morlaix": (48.578, -3.832),
    "Mâcon Loché TGV": (46.282, 4.779), "Nancy Ville": (48.690, 6.174), "Nantes": (47.217, -1.542),
    "Narbonne": (43.191, 3.006), "Neustadt (Weinstrasse)": (49.350, 8.140), "Newport": (51.589, -2.999),
    "Nogent sur Seine": (48.495, 3.497), "Nîmes Centre": (43.833, 4.366), "Nürnberg Hbf": (49.446, 11.082),
    "Orléans": (47.908, 1.905), "Oxford": (51.753, -1.270), "Paris Austerlitz": (48.842, 2.365),
    "Paris Bercy": (48.839, 2.383), "Paris Est": (48.877, 2.359), "Paris Gare de Lyon": (48.844, 2.374),
    "Paris Montparnasse": (48.841, 2.320), "Paris Nord": (48.881, 2.355), "Perpignan": (42.696, 2.879),
    "Plymouth": (50.378, -4.143), "Port Bou": (42.425, 3.159), "Port Talbot Parkway": (51.592, -3.781),
    "Radolfzell": (47.736, 8.969), "Remiremont": (48.016, 6.591), "Rivesaltes": (42.770, 2.874),
    "Saarbrücken Hbf": (49.241, 6.991), "St Avold": (49.104, 6.707), "St Claude": (46.387, 5.864),
    "St Nazaire": (47.287, -2.212), "St Pierre des Corps": (47.386, 0.724),
    "Stuttgart Hbf": (48.784, 9.182), "Stuttgart-Untertürkheim": (48.781, 9.253),
    "Swansea": (51.625, -3.942), "Swindon": (51.565, -1.785), "Tanger Ville": (35.769, -5.789),
    "Thionville": (49.355, 6.169), "Toulouse Matabiau": (43.611, 1.454), "Valence TGV": (44.991, 4.978),
    "Vendôme": (47.793, 1.065), "Wetzikon": (47.321, 8.797), "Worcester Forgate Street": (52.195, -2.221),
    "Worcester Shrub Hill": (52.195, -2.209), "Zürich HB": (47.378, 8.540),
}

# Stations merged into one point per city (version A). Others keep their own name.
CITIES = {
    "Paris": ["Paris Austerlitz", "Paris Bercy", "Paris Est", "Paris Gare de Lyon",
              "Paris Montparnasse", "Paris Nord"],
    "London": ["London Charing Cross", "London Euston", "London Farringdon",
               "London Paddington", "London St Pancras"],
    "Lille": ["Lille Europe", "Lille Flandres"],
    "Lyon": ["Lyon Part-Dieu", "Lyon Perrache"],
    "Marseille": ["Marseille Blancarde", "Marseille St-Charles"],
    "Montpellier": ["Montpellier St Roch", "Montpellier Sud France"],
    "Stuttgart": ["Stuttgart Hbf", "Stuttgart-Untertürkheim"],
    "Worcester": ["Worcester Forgate Street", "Worcester Shrub Hill"],
    "Bregenz": ["Bregenz", "Bregenz Hafen"],
}
CITY_OF = {st: c for c, sts in CITIES.items() for st in sts}

# Labels drawn on the map: text -> (point it sits on, text anchor). Points are
# city names (merged map) or station names; a label is skipped if its point is unused.
LABELS = {
    "Paris": (["Paris", "Paris Nord"], "end"), "London": (["London", "London St Pancras"], "start"),
    "Metz": (["Metz Ville"], "start"), "Marseille": (["Marseille", "Marseille St-Charles"], "start"),
    "Lyon": (["Lyon", "Lyon Part-Dieu"], "start"), "Cardiff": (["Cardiff"], "end"),
    "Madrid": (["Madrid Atocha"], "start"), "Barcelona": (["Barcelona Sants"], "start"),
    "Tangier": (["Tanger Ville"], "start"), "Casablanca": (["Casa Voyageurs"], "start"),
    "Zürich": (["Zürich HB"], "start"), "Linz": (["Linz Hbf"], "end"),
    "Bordeaux": (["Bordeaux St Jean"], "end"), "Toulouse": (["Toulouse Matabiau"], "end"),
    "Manchester": (["Manchester Piccadilly"], "start"),
    "Stuttgart": (["Stuttgart", "Stuttgart Hbf"], "start"), "Perpignan": (["Perpignan"], "end"),
}

# Sequential blue ramp (light -> dark), one step per trip-count bin
BINS = [(1, 1, "#9ec5f4"), (2, 3, "#5598e7"), (4, 7, "#256abf"), (8, 10**6, "#0d366b")]
WIDTH = 960                       # SVG units = CSS px at full column width
MAIN = (40.9, 53.7, -5.3, 15.2)   # lat_min, lat_max, lon_min, lon_max of the main view
INSET = (32.0, 41.6, -9.5, 3.4)   # Iberia and Morocco, drawn smaller in the bottom-left corner
INSET_W = 190                     # inset width in px


def project(lat, lon):
    """Mercator, unscaled."""
    return math.radians(lon), -math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def bin_of(n):
    return next(i for i, (lo, hi, _) in enumerate(BINS) if lo <= n <= hi)


def city_coords():
    out = dict(COORDS)
    for c, sts in CITIES.items():
        out[c] = (sum(COORDS[s][0] for s in sts) / len(sts), sum(COORDS[s][1] for s in sts) / len(sts))
    return out


def count_routes(trips, merge):
    routes, km = Counter(), {}
    for t in trips:
        a, b = t["from"], t["to"]
        if a not in COORDS or b not in COORDS:
            continue
        if merge:
            a, b = CITY_OF.get(a, a), CITY_OF.get(b, b)
        if a == b:
            continue
        key = tuple(sorted((a, b)))
        routes[key] += 1
        km[key] = t["km"]
    return routes, km


class View:
    """A Mercator window: lat/lon box -> pixel box (x, y, width), height follows."""

    def __init__(self, box, x, y, w):
        la0, la1, lo0, lo1 = box
        self.box, self.x, self.y = box, x, y
        (self.x0, self.y0), (x1, y1) = project(la1, lo0), project(la0, lo1)
        self.scale = w / (x1 - self.x0)
        self.w, self.h = w, (y1 - self.y0) * self.scale

    def __call__(self, lat, lon):
        x, y = project(lat, lon)
        return self.x + (x - self.x0) * self.scale, self.y + (y - self.y0) * self.scale

    def has(self, lat, lon, margin=0.0):
        la0, la1, lo0, lo1 = self.box
        return la0 - margin <= lat <= la1 + margin and lo0 - margin <= lon <= lo1 + margin


def draw(view, routes, km, coords, clip_id, label_size, unlabelled=lambda lat, lon: False):
    """Basemap, routes, stations and labels of one view, clipped to its box."""
    land = []
    if BASEMAP.exists():
        for ring in json.loads(BASEMAP.read_text()):
            pp, last = [], None
            for lon, lat in ring:
                x, y = view(lat, lon)   # clamp far-off outline points to just outside the view
                p = (round(min(max(x, view.x - 10), view.x + view.w + 10), 1),
                     round(min(max(y, view.y - 10), view.y + view.h + 10), 1))
                if p != last:
                    pp.append(p)
                    last = p
            if len(pp) > 2 and len({p[0] for p in pp}) > 1 and len({p[1] for p in pp}) > 1:
                land.append("M" + " ".join(f"{x:g},{y:g}" for x, y in pp) + "Z")

    def line_of(k):
        return [coords[k[0]], coords[k[1]]]

    paths = []
    for k, n in sorted(routes.items(), key=lambda kv: kv[1]):
        line = line_of(k)
        if not any(view.has(lat, lon, 1.0) for lat, lon in line):
            continue
        (xa, ya), (xb, yb) = view(*line[0]), view(*line[1])
        dx, dy = xb - xa, yb - ya
        cx, cy = (xa + xb) / 2 - 0.12 * dy, (ya + yb) / 2 + 0.12 * dx   # bow to one side
        d = f"M{xa:.1f},{ya:.1f} Q{cx:.1f},{cy:.1f} {xb:.1f},{yb:.1f}"
        i = bin_of(n)
        w = 1.5 + 1.2 * i
        a, b = k
        tip = f"{a} ↔ {b}: {n} trip{'s' if n > 1 else ''} · {km[k]} km"
        paths.append(
            f'<g class="route"><title>{tip}</title>'
            f'<path d="{d}" stroke="#fff" stroke-width="{w + 2:.1f}"/>'
            f'<path d="{d}" stroke="{BINS[i][2]}" stroke-width="{w:.1f}"/>'
            f'<path d="{d}" stroke="transparent" stroke-width="12"/></g>')

    used = {s for k in routes for s in k if view.has(*coords[s])}
    dots = "".join(f'<circle cx="{view(*coords[s])[0]:.1f}" cy="{view(*coords[s])[1]:.1f}" r="2.5">'
                   f'<title>{s}</title></circle>' for s in sorted(used))
    labels = []
    for text, (cands, anchor) in LABELS.items():
        s = next((c for c in cands if c in used), None)
        if s and not unlabelled(*coords[s]):
            x, y = view(*coords[s])
            dx = 7 if anchor == "start" else -7
            labels.append(f'<text x="{x + dx:.1f}" y="{y + 4:.1f}" text-anchor="{anchor}" '
                          f'font-size="{label_size}">{text}</text>')

    return (f'<clipPath id="{clip_id}"><rect x="{view.x}" y="{view.y}" width="{view.w:.0f}" '
            f'height="{view.h:.0f}"/></clipPath><g clip-path="url(#{clip_id})">'
            + (f'<path class="land" d="{" ".join(land)}"/>' if land else "")
            + "".join(paths) + dots + "".join(labels) + "</g>")


def render(routes, km, coords, out):
    name = out.stem
    main = View(MAIN, 0, 0, WIDTH)
    height = round(main.h)
    inset = View(INSET, 8, 0, INSET_W)
    inset.y = height - inset.h - 8
    body = draw(main, routes, km, coords, f"{name}-main", 14)
    body += (f'<rect class="inset-bg" x="{inset.x}" y="{inset.y:.0f}" width="{inset.w:.0f}" '
             f'height="{inset.h:.0f}"/>'
             + draw(inset, routes, km, coords, f"{name}-inset", 12, main.has)   # labelled on the main map already
             + f'<rect class="inset-frame" x="{inset.x}" y="{inset.y:.0f}" width="{inset.w:.0f}" '
               f'height="{inset.h:.0f}"/>')

    lx, ly = WIDTH - 130, 34   # top-right corner (North Sea / Germany) is empty
    legend = [f'<text x="{lx}" y="{ly - 10}" class="legend-title">Trips on a route</text>']
    for i, (lo, hi, c) in enumerate(BINS):
        y = ly + i * 20
        lab = str(lo) if lo == hi else (f"{lo}+" if hi > 1000 else f"{lo}–{hi}")
        legend.append(f'<line x1="{lx}" y1="{y}" x2="{lx + 28}" y2="{y}" stroke="{c}" '
                      f'stroke-width="{1.5 + 1.2 * i:.1f}" stroke-linecap="round"/>'
                      f'<text x="{lx + 36}" y="{y + 5}">{lab}</text>')

    svg = (f'<svg class="trains-map" viewBox="0 0 {WIDTH} {height}" xmlns="http://www.w3.org/2000/svg" '
           f'role="img" aria-label="Map of {len(routes)} train routes I have taken, coloured by number of trips">'
           '<style>.trains-map path{fill:none;stroke-linecap:round;stroke-linejoin:round}'
           '.trains-map .land{fill:#000;fill-opacity:.035;stroke:#000;stroke-opacity:.15;stroke-width:.6}'
           '.trains-map .inset-bg{fill:#f5f5f5}'
           '.trains-map .inset-frame{fill:none;stroke:#bbb;stroke-width:1}'
           '.trains-map .route:hover path:nth-child(3){stroke:#f5a623;stroke-opacity:.35}'
           '.trains-map circle{fill:#333}'
           '.trains-map text{font-family:sans-serif;font-size:14px;fill:#333;paint-order:stroke;stroke:#fff;stroke-width:3px}'
           '.trains-map .legend-title{font-weight:600}</style>'
           + body + "".join(legend) + "</svg>\n")
    out.write_text(svg, encoding="utf-8")
    print(f"{len(routes)} routes -> {out} ({len(svg) // 1024} KB)")


def write_svg(trips):
    missing = sorted({s for t in trips for s in (t["from"], t["to"]) if s not in COORDS})
    if missing:
        print("trains_map: no coordinates for", ", ".join(missing), "- add them to COORDS")
    IMAGES.mkdir(parents=True, exist_ok=True)

    routes, km = count_routes(trips, merge=True)
    render(routes, km, city_coords(), IMAGES / "trains_map.svg")


def make_basemap(geojson):
    """Cut country outlines to BBOX and round them, so the repo keeps a small file."""
    la0, la1, lo0, lo1 = BBOX
    rings = []
    for f in json.loads(Path(geojson).read_text())["features"]:
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            ring = poly[0]
            if not any(la0 <= lat <= la1 and lo0 <= lon <= lo1 for lon, lat in ring):
                continue
            pts, last = [], None
            for lon, lat in ring:
                p = (round(lon, 2), round(lat, 2))
                if p != last:
                    pts.append(p)
                    last = p
            if len(pts) > 3:
                rings.append(pts)
    BASEMAP.write_text(json.dumps(rings, separators=(",", ":")) + "\n")
    print(f"{len(rings)} rings -> {BASEMAP} ({BASEMAP.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "basemap":
        make_basemap(sys.argv[2])
    else:
        sys.exit(__doc__)
