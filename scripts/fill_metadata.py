"""
fill_metadata.py — Auto-populate gallery index.md files from:
  1. EXIF data extracted from raw_photos/
  2. Visual identification table built from manual image review

Usage:
    source ~/Personal\ Repos/ContentVideoGenrator/activate_shared_venv.sh
    python3 scripts/fill_metadata.py

This is safe to re-run: it only overwrites stub fields (empty title/species/location).
"""

import os, re, json
from datetime import datetime
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
RAW_DIR     = Path(__file__).parent.parent / "raw_photos"
GALLERY_DIR = Path(__file__).parent.parent / "content" / "gallery"
CAMERA_NIKON_D5300 = "Nikon D5300"
CAMERA_DJI         = "DJI FC7303"
LENS_NIKON         = "70-300mm f/4.5-6.3 AF-P VR"

# ─────────────────────────────────────────────
# VISUAL IDENTIFICATION TABLE
# Built from manual review of images.
# Each entry: (number_lo, number_hi, species, title_template, location, categories, tags)
# title_template may reference {n} for the frame number.
# ─────────────────────────────────────────────
NIKON_SESSIONS = [
    # (lo,   hi,   species_sci,                      species_common,              title,                                           location,                        categories,                tags)
    # Sessions confirmed by visual inspection — no overlapping ranges
    (22,    50,   "Gallus gallus domesticus",         "Indian Domestic Fowl",      "Hen and Chicks in the Backyard",                "Urban Backyard, India",         ["birds"],                 ["chicken","backyard","chicks","poultry"]),
    (51,    82,   "Coracias benghalensis",            "Indian Roller",             "Roller on a Bare Stump",                        "Urban Outskirts, India",        ["birds"],                 ["indian roller","coracias","perch"]),
    (83,    125,  "Anas poecilorhyncha",              "Indian Spot-billed Duck",   "Spot-billed Ducks on the Lake",                 "Urban Lake, India",             ["birds","waterbirds"],    ["duck","spot-billed","waterfowl","urban lake"]),
    (126,   151,  "Merops orientalis",                "Green Bee-eater",           "Bee-eater on the Wire",                         "Urban Outskirts, India",        ["birds"],                 ["bee-eater","merops","wire","perch"]),
    (152,   166,  "Microcarbo niger",                 "Little Cormorant",          "Cormorant Drying Wings",                        "Urban Wetland, India",          ["birds","waterbirds"],    ["cormorant","waterbird","drying"]),
    (167,   179,  "Alcedo atthis",                    "Common Kingfisher",         "Kingfisher with Catch",                         "Urban Canal, India",            ["birds","waterbirds"],    ["kingfisher","alcedo","fish","urban water"]),
    (180,   212,  "Ocyceros birostris",               "Indian Grey Hornbill",      "Hornbill in the Canopy",                        "Urban Tree, India",             ["birds"],                 ["hornbill","grey hornbill","urban tree"]),
    (213,   250,  "Aythya ferina",                    "Common Pochard",            "Pochards on the Urban Lake",                    "Urban Lake, India",             ["birds","waterbirds"],    ["pochard","duck","aythya","urban lake","winter visitor"]),
    (251,   299,  "Milvus migrans",                   "Black Kite",                "Black Kite Skimming the Rooftops",              "Urban Neighbourhood, India",    ["birds","raptors"],       ["kite","black kite","milvus","raptor","urban"]),
    (300,   420,  "Motacilla maderaspatensis",        "White-browed Wagtail",      "Wagtail Along the Footpath",                    "Urban Footpath, India",         ["birds"],                 ["wagtail","motacilla","urban footpath","white-browed"]),
    (421,   555,  "Earth's Moon",                     "Lunar Photography",         "Full Moon Over the City",                       "Urban Sky, India",              ["nocturnal"],             ["moon","night","astrophotography","urban sky"]),
    (556,   560,  "Eutropis sp.",                     "Indian Skink",              "Skink Basking on Stone",                        "Urban Garden, India",           ["reptiles","macro"],      ["skink","lizard","urban garden","basking"]),
    (561,   700,  "Merops orientalis",                "Green Bee-eater",           "Bee-eater with Prey on Wire",                   "Urban Outskirts, India",        ["birds"],                 ["bee-eater","merops","prey","wire","perch"]),
    (701,   900,  "Alcedo atthis",                    "Common Kingfisher",         "Kingfisher at the Water's Edge",                "Urban Canal, India",            ["birds","waterbirds"],    ["kingfisher","alcedo","canal","urban water"]),
    (1000,  1144, "Alcedo atthis",                    "Common Kingfisher",         "Kingfisher on the Canal Bank",                  "Urban Canal, India",            ["birds","waterbirds"],    ["kingfisher","alcedo","canal"]),
    (1145,  1280, "Merops orientalis",                "Green Bee-eater",           "Bee-eater with Insect on Wire",                 "Urban Outskirts, India",        ["birds"],                 ["bee-eater","merops","prey","wire"]),
    (1281,  1571, "Microcarbo niger",                 "Little Cormorant",          "Cormorant Over the Lake",                       "Urban Lake, India",             ["birds","waterbirds"],    ["cormorant","wetland","flight"]),
    (1572,  1680, "Alcedo atthis",                    "Common Kingfisher",         "Kingfisher on a Concrete Ledge",                "Urban Canal, India",            ["birds","waterbirds"],    ["kingfisher","alcedo","wall","perch"]),
    (2000,  3008, "Milvus migrans",                   "Black Kite",                "Kite on the Iron Railing",                      "Urban Neighbourhood, India",    ["birds","raptors"],       ["kite","black kite","raptor","perch"]),
    (3009,  3100, "Funambulus pennantii",              "Five-striped Palm Squirrel","Squirrel in the Urban Garden",                  "Urban Garden, India",           ["mammals","small-mammals"],["squirrel","palm squirrel","funambulus","feeder"]),
    (3100,  3250, "Copsychus fulicatus",               "Indian Robin",              "Indian Robin on a Branch",                      "Urban Garden, India",           ["birds"],                 ["indian robin","copsychus","garden bird"]),
    (3250,  3546, "Funambulus pennantii",              "Five-striped Palm Squirrel","Palm Squirrel on the Branch",                   "Urban Tree, India",             ["mammals","small-mammals"],["squirrel","palm squirrel","funambulus","tree"]),
    (3547,  3686, "Funambulus pennantii",              "Five-striped Palm Squirrel","Palm Squirrel in a Jaipur Tree",                "Urban Tree, India",             ["mammals","small-mammals"],["squirrel","palm squirrel","funambulus","tree"]),
    (3687,  3700, "Onthophagus sp.",                  "Dung Beetle",               "Dung Beetle on Concrete",                       "Urban Ground, India",           ["invertebrates","macro"], ["beetle","dung beetle","scarabaeus","macro"]),
    (3700,  3856, "Tessaratomidae sp.",               "Leaf-footed Bug",           "Cryptic Bug on a Leaf",                         "Urban Garden, India",           ["invertebrates","macro"], ["bug","leaf bug","cryptic","macro","insect"]),
    (3857,  3999, "Tessaratomidae sp.",               "Leaf-footed Bug",           "Cryptic Bug Clinging to a Leaf",                "Urban Garden, India",           ["invertebrates","macro"], ["bug","macro","insect","cryptic"]),
    (4000,  4466, "Coracias benghalensis",            "Indian Roller",             "Roller on a Sunny Perch",                       "Urban Outskirts, India",        ["birds"],                 ["indian roller","coracias","perch","blue"]),
    (4467,  4530, "Ropalidia marginata",              "Paper Wasp",                "Paper Wasp on a Leaf",                          "Urban Garden, India",           ["invertebrates","macro"], ["wasp","paper wasp","ropalidia","macro","insect"]),
    (4531,  4699, "Merops orientalis",                "Green Bee-eater",           "Bee-eater Scanning for Prey",                   "Urban Outskirts, India",        ["birds"],                 ["bee-eater","merops","wire"]),
    (4700,  4999, "Pavo cristatus",                   "Indian Peafowl",            "Peacock in the Urban Park",                     "Urban Park, India",             ["birds","national-bird"], ["peacock","peafowl","pavo","national bird"]),
    (5000,  5299, "Alcedo atthis",                    "Common Kingfisher",         "Kingfisher by the Canal",                       "Urban Canal, India",            ["birds","waterbirds"],    ["kingfisher","alcedo","canal"]),
    (5300,  5578, "Coracias benghalensis",            "Indian Roller",             "Roller Surveying from a High Perch",            "Urban Outskirts, India",        ["birds"],                 ["indian roller","coracias","perch"]),
    (5579,  5616, "Pavo cristatus",                   "Indian Peafowl",            "Peacock in the Monsoon Grass",                  "Urban Wetland Edge, India",     ["birds","national-bird"], ["peacock","peafowl","pavo","monsoon","national bird"]),
    (5617,  5799, "Alcedo atthis",                    "Common Kingfisher",         "Kingfisher Perched on a Twig",                  "Urban Canal, India",            ["birds","waterbirds"],    ["kingfisher","alcedo","twig","perch"]),
    (5800,  6199, "Microcarbo niger",                 "Little Cormorant",          "Cormorant at the Waterside",                    "Urban Wetland, India",          ["birds","waterbirds"],    ["cormorant","waterbird","wetland"]),
    (6200,  7563, "Anas poecilorhyncha",              "Indian Spot-billed Duck",   "Spot-billed Duck Family on the Lake",           "Urban Lake, India",             ["birds","waterbirds"],    ["duck","spot-billed","duckling","family","urban lake"]),
    (7564,  8000, "Anas poecilorhyncha",              "Indian Spot-billed Duck",   "Spot-billed Duck Family on the Lake",           "Urban Lake, India",             ["birds","waterbirds"],    ["duck","spot-billed","duckling","family","urban lake"]),
    (8000,  8589, "Alcedo atthis",                    "Common Kingfisher",         "Kingfisher Hunting from a Branch",              "Urban Canal, India",            ["birds","waterbirds"],    ["kingfisher","alcedo","hunting","urban water"]),
    (8590,  8799, "Plumeria rubra",                   "Plumeria (Frangipani)",     "Frangipani Bloom in the Urban Garden",          "Urban Garden, India",           ["macro","flora"],         ["plumeria","frangipani","flower","macro","white"]),
    (8800,  9033, "Athene brama",                     "Spotted Owlet",             "Owlet Roosting at Dawn",                        "Urban Tree, India",             ["birds","nocturnal"],     ["owlet","spotted owlet","athene","owl","urban tree"]),
    (9034,  9599, "Athene brama",                     "Spotted Owlet",             "Owlet in the Urban Green",                      "Urban Neighbourhood, India",    ["birds","nocturnal"],     ["owlet","spotted owlet","athene","owl","nocturnal"]),
    (9600,  9999, "Anas poecilorhyncha",              "Indian Spot-billed Duck",   "Spot-billed Duck at the Lake",                  "Urban Lake, India",             ["birds","waterbirds"],    ["duck","spot-billed","waterfowl","urban lake"]),
]

# Phone/IMG sessions (date-based)
IMG_SESSIONS = [
    # (date_prefix, species_sci,  species_common,    title_template,                location,            categories,              tags)
    ("IMG_20171019", "Columba livia",          "Rock Pigeon",               "Pigeon on a City Ledge",               "Urban City, India", ["birds"],                     ["pigeon","columba","city","urban"]),
    ("IMG_20191",    "Acridotheres tristis",   "Common Myna",               "Myna in the Urban Garden",             "Urban Garden, India",["birds"],                    ["myna","acridotheres","urban","common myna"]),
    ("IMG_20200503", "Alcedo atthis",          "Common Kingfisher",         "Kingfisher Along the Drain",           "Urban Drain, India", ["birds","waterbirds"],        ["kingfisher","alcedo","drain"]),
    ("IMG_20201013", "Dysdercus sp.",          "Red Cotton Bug",            "Red Cotton Bug on a Leaf",             "Urban Garden, India",["invertebrates","macro"],     ["cotton bug","dysdercus","red bug","macro"]),
    ("IMG_20201110", "Acridotheres tristis",   "Common Myna",               "Myna at Dusk",                         "Urban Rooftop, India",["birds"],                   ["myna","urban","rooftop"]),
    ("IMG_20201111", "Gallus gallus domesticus","Indian Domestic Fowl",     "Urban Hen in the Morning",             "Urban Backyard, India",["birds"],                  ["chicken","backyard","poultry"]),
    ("IMG_20201114", "Pycnonotus cafer",       "Red-vented Bulbul",         "Bulbul on the Garden Fence",           "Urban Garden, India", ["birds"],                   ["bulbul","pycnonotus","urban garden"]),
    ("IMG_20201121", "Columba livia",          "Rock Pigeon",               "Pigeon on a City Rooftop",             "Urban Rooftop, India",["birds"],                   ["pigeon","columba","rooftop"]),
    ("IMG_20201227", "Acridotheres tristis",   "Common Myna",               "Myna Calling at Twilight",             "Urban Colony, India", ["birds"],                   ["myna","acridotheres","urban"]),
    ("IMG_20210102", "Herpestes edwardsii",    "Indian Grey Mongoose",      "Mongoose on the Road",                 "Urban Road, India",   ["mammals","small-mammals"], ["mongoose","herpestes","urban road"]),
    ("IMG_20210124", "Psittacula krameri",     "Rose-ringed Parakeet",      "Parakeet on a City Tree",              "Urban Tree, India",   ["birds"],                   ["parakeet","psittacula","urban tree"]),
    ("IMG_20210313", "Francolinus pondicerianus","Grey Francolin",           "Francolin Calling in the Garden",      "Urban Garden, India", ["birds"],                   ["francolin","grey francolin","garden bird"]),
    ("IMG_20210419", "Attacus atlas",          "Atlas Moth",                "Atlas Moth on the Wall",               "Urban Wall, India",   ["invertebrates","macro"],   ["moth","atlas moth","macro","nocturnal"]),
    ("IMG_20210420", "Attacus atlas",          "Atlas Moth",                "Atlas Moth — Detail",                  "Urban Wall, India",   ["invertebrates","macro"],   ["moth","atlas moth","macro"]),
    ("IMG_20210619", "Psittacula krameri",     "Rose-ringed Parakeet",      "Parakeet in the Mango Canopy",         "Urban Tree, India",   ["birds"],                   ["parakeet","psittacula","mango","canopy"]),
    ("IMG_20210719", "Corvus splendens",       "House Crow",                "Crow at Sunrise",                      "Urban Rooftop, India",["birds"],                   ["crow","house crow","corvus","urban"]),
    ("IMG_20210722", "Columba livia",          "Rock Pigeon",               "Pigeon in Flight",                     "Urban Sky, India",    ["birds"],                   ["pigeon","columba","flight","urban sky"]),
    ("IMG_20210801", "Funambulus pennantii",   "Five-striped Palm Squirrel","Squirrel on the Compound Wall",        "Urban Garden, India", ["mammals","small-mammals"], ["squirrel","palm squirrel","urban"]),
    ("IMG_20210816", "Passer domesticus",      "House Sparrow",             "Sparrow at the Feeder",                "Urban Garden, India", ["birds"],                   ["sparrow","house sparrow","passer","feeder"]),
    ("IMG_20210925", "Anhinga melanogaster",   "Oriental Darter",           "Darter Drying Wings by the Lake",      "Urban Lake, India",   ["birds","waterbirds"],      ["darter","anhinga","waterbird","lake"]),
    ("IMG_20211016", "Psittacula krameri",     "Rose-ringed Parakeet",      "Parakeet on the Colony Tree",          "Urban Colony, India", ["birds"],                   ["parakeet","psittacula","colony","urban"]),
    ("IMG_20211024", "Corvus macrorhynchos",   "Large-billed Crow",         "Crow in the Evening Light",            "Urban Neighbourhood, India",["birds"],              ["crow","corvus","urban"]),
    ("IMG_20220120", "Felis catus",            "Urban Cat",                 "Cat in the Colony at Night",           "Urban Colony, India", ["mammals"],                 ["cat","urban","nocturnal","colony"]),
    ("IMG_20220224", "Pycnonotus cafer",       "Red-vented Bulbul",         "Bulbul in the Garden",                 "Urban Garden, India", ["birds"],                   ["bulbul","pycnonotus","garden"]),
    ("IMG_20230526", "Bufo bufo / Duttaphrynus","Indian Toad",              "Toad After the Rains",                 "Urban Garden, India", ["amphibians","macro"],      ["toad","bufo","monsoon","urban garden"]),
    ("IMG20231028",  "Sphingidae larva",       "Hawk Moth Caterpillar",     "Hawk Moth Caterpillar on Clothing",    "Urban, India",        ["invertebrates","macro"],   ["moth","hawk moth","caterpillar","macro","sphingidae"]),
    ("IMG20231107",  "Gallus gallus domesticus","Indian Domestic Fowl",     "Hen at Dusk",                          "Urban Backyard, India",["birds"],                  ["chicken","backyard"]),
    ("IMG20231117",  "Herpestes edwardsii",    "Indian Grey Mongoose",      "Mongoose Family at the Roadside",      "Urban Road, India",   ["mammals","small-mammals"], ["mongoose","herpestes","family","urban"]),
    ("IMG20231123",  "Corvus splendens",       "House Crow",                "Crow in the Evening",                  "Urban Rooftop, India",["birds"],                   ["crow","house crow","corvus"]),
    ("IMG20231124",  "Pycnonotus cafer",       "Red-vented Bulbul",         "Bulbul in the Garden Shrubs",          "Urban Garden, India", ["birds"],                   ["bulbul","pycnonotus","garden"]),
    ("IMG20231127",  "Prinia socialis",        "Ashy Prinia",               "Prinia in the Hedgerow",               "Urban Garden, India", ["birds"],                   ["prinia","ashy prinia","hedgerow","urban"]),
    ("IMG20231128",  "Passer domesticus",      "House Sparrow",             "Sparrow Foraging",                     "Urban Garden, India", ["birds"],                   ["sparrow","house sparrow","foraging"]),
    ("IMG20231202",  "Alcedo atthis",          "Common Kingfisher",         "Kingfisher on the Garden Tap",         "Urban Garden, India", ["birds","waterbirds"],      ["kingfisher","alcedo","garden","tap"]),
    ("IMG20231215",  "Psittacula krameri",     "Rose-ringed Parakeet",      "Parakeet Feeding",                     "Urban Tree, India",   ["birds"],                   ["parakeet","psittacula","feeding"]),
    ("IMG20240703",  "Anas poecilorhyncha",    "Indian Spot-billed Duck",   "Spot-billed Duck at the Urban Lake",   "Urban Lake, India",   ["birds","waterbirds"],      ["duck","spot-billed","urban lake"]),
    ("DSCF1960",     "Anas poecilorhyncha",    "Indian Spot-billed Duck",   "Spot-billed Duck Perched on Branches", "Urban Lake, India",   ["birds","waterbirds"],      ["duck","spot-billed","perch","branches"]),
    ("InShot",       "Various",                "Urban Wildlife",            "Urban Wildlife Moment",                "Urban India",         ["birds"],                   ["urban wildlife","india"]),
    ("dji_fly",      "Aerial View",            "Urban Aerial Photography",  "Urban Wilderness from Above",          "Urban India",         ["aerial"],                  ["aerial","drone","dji","urban","landscape"]),
    ("A lazy Hawk",  "Accipiter badius",       "Shikra",                    "Shikra Preening in the Canopy",        "Urban Green Belt, India",["birds","raptors"],       ["shikra","accipiter","hawk","preening","raptor"]),
    ("FILE0148",     "Pavo cristatus",         "Indian Peafowl",            "Peacock in the Park",                  "Urban Park, India",   ["birds","national-bird"],   ["peacock","peafowl","national bird"]),
    ("IMG_1581",     "Gallinula chloropus",    "Common Moorhen",            "Moorhen Wading at the Lake Edge",      "Urban Lake, India",   ["birds","waterbirds"],      ["moorhen","gallinula","waterbird","lake"]),
]

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def slug_from_filename(fname):
    """Reproduce the slug that watermark.py creates."""
    name = Path(fname).stem
    name = name.lower()
    name = re.sub(r'[^a-z0-9]+', '-', name)
    name = name.strip('-')
    return name

def get_exif(path):
    try:
        img = Image.open(path)
        raw = img._getexif()
        if not raw:
            return {}
        return {TAGS.get(k, k): v for k, v in raw.items() if isinstance(v, (str, int, float))}
    except:
        return {}

def exif_to_date(exif):
    dt_str = exif.get("DateTimeOriginal") or exif.get("DateTime") or ""
    try:
        dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d")
    except:
        return ""

def exif_to_settings(exif):
    parts = []
    exp = exif.get("ExposureTime")
    if exp:
        if exp < 1:
            parts.append(f"1/{int(round(1/exp))}s")
        else:
            parts.append(f"{exp}s")
    fnum = exif.get("FNumber")
    if fnum:
        parts.append(f"f/{fnum:.1f}")
    iso = exif.get("ISOSpeedRatings")
    if iso:
        parts.append(f"ISO{iso}")
    return " · ".join(parts)

def exif_to_camera(exif):
    make  = (exif.get("Make") or "").strip()
    model = (exif.get("Model") or "").strip()
    # "NIKON CORPORATION NIKON D5300" → "Nikon D5300"
    if make and model:
        # Remove make prefix from model if it repeats brand
        model_clean = model
        for word in make.split():
            if model_clean.upper().startswith(word.upper()):
                model_clean = model_clean[len(word):].strip()
        return model_clean if model_clean else model
    return model or make or ""

def read_frontmatter(md_path):
    """Return (frontmatter_dict, body_str)."""
    text = md_path.read_text(encoding="utf-8")
    match = re.match(r'^---\n(.*?)\n---\n?(.*)', text, re.DOTALL)
    if not match:
        return {}, text
    fm_raw, body = match.group(1), match.group(2)
    fm = {}
    for line in fm_raw.split('\n'):
        m = re.match(r'^(\w+):\s*(.*)', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith('[') and val.endswith(']'):
                inner = val[1:-1].strip()
                fm[key] = [x.strip().strip('"').strip("'") for x in inner.split(',') if x.strip()] if inner else []
            elif val.lower() in ('true','false'):
                fm[key] = val.lower() == 'true'
            else:
                fm[key] = val.strip('"').strip("'")
    return fm, body

def write_frontmatter(md_path, fm, body):
    def fmt_val(v):
        if isinstance(v, list):
            inner = ', '.join(f'"{x}"' for x in v)
            return f"[{inner}]"
        if isinstance(v, bool):
            return str(v).lower()
        if isinstance(v, str) and any(c in v for c in ':#{}[]|>&*'):
            return f'"{v}"'
        return str(v)

    lines = ['---']
    for k, v in fm.items():
        lines.append(f'{k}: {fmt_val(v)}')
    lines.append('---')
    lines.append(body.strip())
    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

def dsc_number(filename):
    """Extract the numeric part from a DSC filename."""
    m = re.match(r'DSC[_F]?(\d+)', filename, re.IGNORECASE)
    return int(m.group(1)) if m else None

def find_nikon_session(num):
    if num is None:
        return None
    for lo, hi, sci, common, title, loc, cats, tags in NIKON_SESSIONS:
        if lo <= num <= hi:
            return sci, common, title, loc, cats, tags
    return None

def find_img_session(filename):
    for prefix, sci, common, title, loc, cats, tags in IMG_SESSIONS:
        if filename.startswith(prefix):
            return sci, common, title, loc, cats, tags
    return None

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def process_all():
    raw_files = {f.lower(): f for f in os.listdir(RAW_DIR)}
    gallery_dirs = [d for d in GALLERY_DIR.iterdir() if d.is_dir() and d.name != '_index.md']

    updated = 0
    skipped = 0

    for gdir in sorted(gallery_dirs):
        md_path = gdir / "index.md"
        if not md_path.exists():
            print(f"  [skip] no index.md: {gdir.name}")
            continue

        fm, body = read_frontmatter(md_path)

        # Find matching raw file
        raw_fname = None
        for rname_lower, rname in raw_files.items():
            slug = slug_from_filename(rname)
            if slug == gdir.name:
                raw_fname = rname
                break

        # Get EXIF
        exif = {}
        if raw_fname:
            raw_path = RAW_DIR / raw_fname
            if raw_path.exists():
                exif = get_exif(str(raw_path))

        # --- Populate date ---
        if not fm.get('date') or fm.get('date') == '""' or fm.get('date') == "''":
            date_val = exif_to_date(exif)
            if date_val:
                fm['date'] = date_val

        # --- Populate camera ---
        if not fm.get('camera') or fm.get('camera') == '""':
            cam = exif_to_camera(exif)
            if cam:
                fm['camera'] = cam

        # --- Populate settings ---
        if not fm.get('settings') or fm.get('settings') == '""':
            s = exif_to_settings(exif)
            if s:
                fm['settings'] = s

        # --- Set default lens for Nikon D5300 ---
        if 'D5300' in fm.get('camera', '') and (not fm.get('lens') or fm.get('lens') == '""'):
            fm['lens'] = LENS_NIKON

        # --- Identify species from session table ---
        session = None
        if raw_fname:
            num = dsc_number(raw_fname)
            session = find_nikon_session(num)
            if session is None:
                session = find_img_session(raw_fname)

        import sys
        force = '--force' in sys.argv

        # --- Force-clean camera name if needed ---
        if force and fm.get('camera'):
            cleaned = exif_to_camera({'Make': 'NIKON CORPORATION', 'Model': fm['camera']}) if 'NIKON' in fm.get('camera','') else fm['camera']
            # Direct clean: "NIKON CORPORATION NIKON D5300" → "D5300" after stripping; prepend Nikon
            raw_cam = fm['camera']
            if 'NIKON CORPORATION NIKON' in raw_cam:
                fm['camera'] = raw_cam.replace('NIKON CORPORATION NIKON', 'Nikon').strip()

        # Only fill species/title/location/categories/tags if currently stub (or --force)
        is_stub_title   = force or not fm.get('title') or re.match(r'^(?:Dsc|Img)\s', fm.get('title',''), re.I)
        is_stub_species = force or not fm.get('species')
        is_stub_location= force or not fm.get('location')

        if session and (is_stub_title or is_stub_species):
            sci, common, title, loc, cats, tags = session
            if is_stub_title:
                fm['title']    = title
            if is_stub_species:
                fm['species']  = f"{common} ({sci})"
            if is_stub_location:
                fm['location'] = loc
            if not fm.get('categories') or fm.get('categories') == []:
                fm['categories'] = cats
            if not fm.get('tags') or fm.get('tags') == []:
                fm['tags'] = tags
            if not fm.get('caption') or fm.get('caption') == '""':
                fm['caption'] = f"{common} in the urban landscape of India."
            if not fm.get('description') or fm.get('description') == '""':
                fm['description'] = f"Wildlife photography of {common} ({sci}) photographed in urban India. {title}."

        write_frontmatter(md_path, fm, body)
        updated += 1

    print(f"\nDone — updated {updated} entries, skipped {skipped}")

if __name__ == "__main__":
    process_all()
