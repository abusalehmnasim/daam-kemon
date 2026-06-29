"""
Category & brand vocabulary for Bangladesh grocery.

Each category has:
  - display:   human-readable name shown in the UI
  - group:     top-level browsing group (Staples & Grains, Spices, …) — drives /categories
  - keywords:  substrings (lowercased, English or Bangla) that signal the category
  - brands:    known brands — used to extract a brand from a noisy product name
  - units:     allowed canonical units (drives "did we parse this right?")
  - subcategories: keyword sets that resolve to a subcategory key

Keep this file plain Python (not the DB) so the normalizer can run at scrape
time without a DB round-trip. New categories belong here.
"""

import re

# Top-level groups (preserves user-specified order)
CATEGORY_GROUPS: list[str] = [
    "Staples & Grains",
    "Oils & Fats",
    "Spices & Condiments",
    "Sugar & Sweeteners",
    "Packaged & Daily Use",
    "Canned / Bottled",
    "Fresh / Semi-fresh",
    "Snacks & Extras",
    "Utilities",
]


CATEGORIES = {
    # ─── Staples & Grains ──────────────────────────────────────────────────
    "rice": {
        "display": "Rice",
        "group": "Staples & Grains",
        "keywords": ["rice", "chal", "miniket", "najirshail", "basmati",
                     "polao", "kalijira", "irri",
                     "চাল", "মিনিকেট", "নাজিরশাইল", "বাসমতি", "পোলাও"],
        "brands": ["aci pure", "aci", "pran", "rashid", "diamond", "chashi",
                   "acm", "fresh", "teer", "bashundhara", "aarong", "ispahani"],
        "units": ["KG", "G"],
        "subcategories": {
            "miniket":    ["miniket", "মিনিকেট"],
            "najirshail": ["najirshail", "najir", "নাজিরশাইল"],
            "basmati":    ["basmati", "বাসমতি"],
            "kalijira":   ["kalijira", "kataribhog", "কালিজিরা"],
            "polao":      ["polao", "polau", "পোলাও"],
            "atap":       ["atap", "আতপ"],
            "irri":       ["irri"],
        },
    },
    "flour": {
        "display": "Flour & Atta",
        "group": "Staples & Grains",
        "keywords": ["atta", "maida", "flour", "আটা", "ময়দা", "সুজি"],
        "brands": ["teer", "fresh", "acm", "pran", "rupchanda", "bashundhara",
                   "ifad", "pusti", "muskan", "shaad", "foodela", "akij"],
        "units": ["KG", "G"],
        "subcategories": {
            "atta":  ["atta", "whole wheat", "আটা"],
            "maida": ["maida", "all purpose", "all-purpose", "ময়দা"],
            "suji":  ["suji", "semolina", "সুজি"],
        },
    },
    "lentils": {
        "display": "Lentils (Dal)",
        "group": "Staples & Grains",
        "keywords": ["dal", "lentil", "lentils", "ডাল", "মসুর", "মুগ", "ছোলা",
                     "motor", "মটর"],
        "brands": ["pran", "fresh", "teer", "radhuni", "acm", "aarong"],
        "units": ["KG", "G"],
        "subcategories": {
            "masoor":  ["masoor", "mosur", "red lentil", "মসুর"],
            "mung":    ["moog", "mug", "mung", "মুগ"],
            "chola":   ["chola", "chana", "chickpea", "ছোলা"],
            "khesari": ["khesari", "খেসারি"],
            "anchor":  ["anchor", "অ্যাঙ্কর"],
            "motor":   ["motor", "মটর"],
        },
    },

    # ─── Oils & Fats ───────────────────────────────────────────────────────
    "cooking_oil": {
        "display": "Cooking Oil",
        "group": "Oils & Fats",
        "keywords": [
            "soybean oil", "soyabean oil", "soya oil", "soybean", "soyabean",
            "sunflower oil", "rice bran oil", "mustard oil", "palm oil",
            "cooking oil", "vegetable oil", "olive oil", "sesame oil",
            "তেল", "সয়াবিন", "সরিষার তেল", "সরিষা",
        ],
        "brands": ["rupchanda", "fresh", "teer", "pusti", "veola", "mojo",
                   "radhuni", "acm", "bashundhara", "kings", "fortune",
                   "starship", "saffola", "olio orolio", "luglio",
                   "ecorganic", "sena", "muskan gold", "aci pure"],
        "units": ["L", "ML"],
        "subcategories": {
            "soybean":   ["soybean", "soyabean", "soya", "সয়াবিন"],
            "sunflower": ["sunflower"],
            "rice_bran": ["rice bran"],
            "mustard":   ["mustard", "সরিষা"],
            "palm":      ["palm"],
            "olive":     ["olive", "extra virgin"],
            "sesame":    ["sesame"],
        },
    },

    # ─── Spices & Condiments ───────────────────────────────────────────────
    "spices": {
        "display": "Spices",
        "group": "Spices & Condiments",
        "keywords": [
            "turmeric", "haldi", "holud", "হলুদ",
            "chili powder", "chilli powder", "lal mirch", "morich", "মরিচ",
            "cumin", "jira", "জিরা",
            "coriander", "dhone", "dhane", "ধনে",
            "ginger powder", "garlic powder",
        ],
        "brands": ["radhuni", "pran", "fresh", "bd", "acm", "ifad", "shaad",
                   "kazi", "potash", "ahmed"],
        "units": ["G", "KG"],
        "subcategories": {
            "turmeric":  ["turmeric", "haldi", "holud", "হলুদ"],
            "chili":     ["chili", "chilli", "lal mirch", "morich", "মরিচ"],
            "cumin":     ["cumin", "jira", "জিরা"],
            "coriander": ["coriander", "dhone", "dhane", "ধনে"],
        },
    },
    "salt": {
        "display": "Salt",
        "group": "Spices & Condiments",
        "keywords": ["salt", "lobon", "labon", "লবণ", "iodized salt"],
        "brands": ["acm", "fresh", "pran", "molla", "confidence"],
        "units": ["KG", "G"],
        "subcategories": {
            "iodized": ["iodized", "iodine"],
            "loose":   ["loose", "khola", "খোলা"],
        },
    },
    "garam_masala": {
        "display": "Garam Masala & Spice Blends",
        "group": "Spices & Condiments",
        "keywords": ["garam masala", "mixed spice", "biriyani masala",
                     "biryani masala", "meat masala", "chicken masala",
                     "beef masala", "fish masala", "মসলা"],
        "brands": ["radhuni", "pran", "ahmed", "shaad", "kazi", "fresh", "potash"],
        "units": ["G"],
        "subcategories": {
            "biryani": ["biryani", "biriyani"],
            "meat":    ["meat", "beef"],
            "chicken": ["chicken"],
            "fish":    ["fish"],
        },
    },

    # ─── Sugar & Sweeteners ────────────────────────────────────────────────
    "sugar": {
        "display": "Sugar",
        "group": "Sugar & Sweeteners",
        "keywords": ["sugar", "chini", "চিনি", "akher chini"],
        "brands": ["fresh", "city", "deshbandhu", "pran", "meghna", "rapid"],
        "units": ["KG", "G"],
        "subcategories": {
            "white": ["white", "refined", "সাদা"],
            "brown": ["brown", "lal", "লাল", "raw"],
        },
    },
    "molasses": {
        "display": "Molasses (Gur)",
        "group": "Sugar & Sweeteners",
        "keywords": ["molasses", "gur", "jaggery", "akher gur", "khejur gur",
                     "patali", "গুড়", "আখের গুড়", "খেজুরের গুড়"],
        "brands": ["pran", "khaas food", "fresh", "rongin"],
        "units": ["KG", "G"],
        "subcategories": {
            "akher":  ["akher", "sugarcane", "আখের"],
            "khejur": ["khejur", "date", "খেজুর"],
            "patali": ["patali", "পাটালি"],
        },
    },

    # ─── Packaged & Daily Use ──────────────────────────────────────────────
    "biscuits": {
        "display": "Biscuits",
        "group": "Packaged & Daily Use",
        "keywords": ["biscuit", "biscuits", "cookie", "cookies", "cracker",
                     "বিস্কুট"],
        "brands": ["tiger", "olympia", "olimpia", "nabisco", "pran", "danish",
                   "bisk club", "bisk", "haque", "ifad", "fu wang", "bourbon",
                   "energy plus", "horlicks"],
        "units": ["G", "KG"],
        "subcategories": {
            "energy":     ["energy", "glucose"],
            "chocolate":  ["chocolate", "choco"],
            "milk":       ["milk"],
            "salty":      ["salty", "cream cracker"],
        },
    },
    "noodles": {
        "display": "Noodles",
        "group": "Packaged & Daily Use",
        "keywords": ["noodle", "noodles", "ramen", "instant noodles", "নুডলস"],
        "brands": ["mr. noodles", "mr noodles", "knorr", "maggi", "pran",
                   "doodles", "ifad", "cocola"],
        "units": ["G"],
        "subcategories": {
            "instant": ["instant", "cup"],
            "egg":     ["egg"],
            "chicken": ["chicken"],
            "masala":  ["masala", "curry"],
        },
    },
    "tea": {
        "display": "Tea",
        "group": "Packaged & Daily Use",
        "keywords": ["tea", "cha", "chai", "tea bag", "tea leaf", "tea leaves",
                     "চা", "চা পাতা"],
        "brands": ["ispahani", "taaza", "fresh", "kazi", "lipton", "halda valley",
                   "seylon", "danedar", "twinings"],
        "units": ["G", "KG"],
        "subcategories": {
            "black":   ["black"],
            "green":   ["green"],
            "bag":     ["bag", "sachet"],
            "premium": ["premium", "gold", "elite"],
        },
    },
    "powdered_milk": {
        "display": "Powdered Milk",
        "group": "Packaged & Daily Use",
        "keywords": ["powder milk", "powdered milk", "milk powder",
                     "full cream milk powder", "গুঁড়া দুধ"],
        "brands": ["diploma", "dano", "nido", "marks", "fresh", "milk vita",
                   "milkvita", "anchor", "starship", "farm fresh"],
        "units": ["G", "KG"],
        "subcategories": {
            "full_cream": ["full cream", "fcmp"],
            "skimmed":    ["skimmed", "skim"],
            "instant":    ["instant"],
        },
    },
    "milk": {
        "display": "Liquid Milk",
        "group": "Packaged & Daily Use",
        "keywords": ["uht milk", "liquid milk", "pasteurized milk",
                     "doodh", "দুধ"],
        "brands": ["pran", "arong", "milk vita", "milkvita", "farm fresh",
                   "danish", "amul", "cowhead"],
        "units": ["L", "ML"],
        "subcategories": {
            "uht":          ["uht"],
            "pasteurized":  ["pasteurized", "pasteurised"],
            "flavored":     ["chocolate", "strawberry", "flavored", "flavoured"],
            "condensed":    ["condensed"],
        },
    },
    "detergent": {
        "display": "Washing Detergent",
        "group": "Packaged & Daily Use",
        "keywords": ["detergent", "washing powder", "washing liquid",
                     "laundry detergent", "ডিটারজেন্ট"],
        "brands": ["surf excel", "rin", "wheel", "chaka", "tide", "ariel",
                   "jet", "keya", "shuvro", "shwapno", "fast wash", "attack"],
        "units": ["KG", "G", "L", "ML"],
        "subcategories": {
            "powder": ["powder"],
            "liquid": ["liquid"],
            "bar":    ["bar"],
        },
    },
    "soap": {
        "display": "Bath Soap",
        "group": "Packaged & Daily Use",
        "keywords": ["bath soap", "bathing soap", "beauty soap", "body soap",
                     "soap bar", "bath bar", "soap", "সাবান"],
        "brands": ["lux", "lifebuoy", "dove", "tibet", "meril", "savlon",
                   "dettol", "keya", "sandalina", "cute", "yardley", "rexona"],
        "units": ["G", "KG"],
        "subcategories": {
            "beauty":          ["beauty", "body", "glow", "soft"],
            "antibacterial":   ["antibacterial", "germ", "dettol", "savlon", "lifebuoy"],
        },
    },

    # ─── Canned / Bottled ──────────────────────────────────────────────────
    "soy_sauce": {
        "display": "Soy Sauce",
        "group": "Canned / Bottled",
        "keywords": ["soy sauce", "soya sauce", "soyabean sauce", "kikkoman",
                     "সয়া সস"],
        "brands": ["pran", "kikkoman", "lee kum kee", "ahmed", "ruchi", "good day"],
        "units": ["ML", "L"],
        "subcategories": {
            "light": ["light"],
            "dark":  ["dark"],
        },
    },
    "tomato_sauce": {
        "display": "Tomato Sauce & Ketchup",
        "group": "Canned / Bottled",
        "keywords": ["tomato sauce", "ketchup", "tomato ketchup", "টমেটো সস"],
        "brands": ["pran", "ahmed", "ruchi", "heinz", "kissan", "tasty", "danish"],
        "units": ["ML", "G", "KG"],
        "subcategories": {
            "ketchup": ["ketchup"],
            "sauce":   ["sauce"],
        },
    },

    # ─── Fresh / Semi-fresh ────────────────────────────────────────────────
    "onion": {
        "display": "Onion",
        "group": "Fresh / Semi-fresh",
        "keywords": ["onion", "piyaj", "peyaj", "peyaaj", "পেঁয়াজ"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {
            "deshi":    ["deshi", "desi", "দেশি"],
            "imported": ["imported", "indian", "indonesian", "pakistani"],
        },
    },
    "garlic": {
        "display": "Garlic",
        "group": "Fresh / Semi-fresh",
        "keywords": ["garlic", "roshun", "roson", "রসুন"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {
            "deshi":    ["deshi", "desi", "দেশি"],
            "imported": ["imported", "chinese", "indian"],
        },
    },
    "ginger": {
        "display": "Ginger",
        "group": "Fresh / Semi-fresh",
        "keywords": ["ginger", "ada", "আদা"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {
            "deshi":    ["deshi", "desi", "দেশি"],
            "imported": ["imported", "chinese", "indian"],
        },
    },
    "green_chili": {
        "display": "Green Chili",
        "group": "Fresh / Semi-fresh",
        "keywords": ["green chili", "green chilli", "kacha morich", "কাঁচা মরিচ"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "eggs": {
        "display": "Eggs",
        "group": "Fresh / Semi-fresh",
        "keywords": ["egg", "eggs", "ডিম", "dim"],
        "brands": ["kazi", "paragon", "aftab", "cp", "diamond", "quality"],
        "units": ["PCS"],
        "subcategories": {
            "chicken": ["chicken", "farm", "layer", "মুরগি"],
            "duck":    ["duck", "হাঁস"],
            "desi":    ["desi", "deshi", "দেশি"],
            "omega":   ["omega", "o3", "o3+"],
        },
    },

    # ─── Snacks & Extras ───────────────────────────────────────────────────
    "chanachur": {
        "display": "Chanachur",
        "group": "Snacks & Extras",
        "keywords": ["chanachur", "chanachoor", "চানাচুর"],
        "brands": ["bombay sweets", "haque", "pran", "danish", "ahmed", "ruchi",
                   "potato crackers", "potato"],
        "units": ["G", "KG"],
        "subcategories": {
            "regular": ["regular"],
            "spicy":   ["hot", "spicy", "jhal"],
        },
    },
    "muri": {
        "display": "Puffed Rice (Muri)",
        "group": "Snacks & Extras",
        "keywords": ["muri", "puffed rice", "মুড়ি"],
        "brands": ["pran", "fresh", "teer", "bombay sweets"],
        "units": ["G", "KG"],
        "subcategories": {},
    },
    "supari_pan": {
        "display": "Supari & Pan Masala",
        "group": "Snacks & Extras",
        "keywords": ["supari", "betel nut", "pan masala", "paan masala",
                     "সুপারি", "পান মসলা"],
        "brands": ["rajnigandha", "pan parag", "kamal", "shahi"],
        "units": ["G"],
        "subcategories": {
            "supari": ["supari", "betel"],
            "pan":    ["pan masala", "paan"],
        },
    },

    # ─── Utilities ─────────────────────────────────────────────────────────
    "matchstick": {
        "display": "Matchsticks",
        "group": "Utilities",
        "keywords": ["matchstick", "match stick", "matches", "match box",
                     "matchbox", "দেশলাই"],
        "brands": ["dhaka match", "sun match", "magnum", "bd match"],
        "units": ["PCS"],
        "subcategories": {},
    },
    "candle": {
        "display": "Candles",
        "group": "Utilities",
        "keywords": ["candle", "candles", "মোমবাতি"],
        "brands": ["pran", "diamond", "fresh"],
        "units": ["PCS", "G"],
        "subcategories": {
            "scented":  ["scented", "aroma"],
            "emergency": ["emergency", "long burn"],
        },
    },
    "shampoo": {
        "display": "Shampoo",
        "group": "Utilities",
        "keywords": ["shampoo", "শ্যাম্পু"],
        "brands": ["sunsilk", "clear", "head & shoulders", "dove", "pantene",
                   "tresemme", "garnier", "loreal", "himalaya"],
        "units": ["ML", "L", "G"],
        "subcategories": {
            "sachet": ["sachet", "mini"],
            "bottle": ["bottle"],
            "anti_dandruff": ["anti dandruff", "anti-dandruff", "dandruff"],
        },
    },
}


# Reverse lookups built once at import time
ALL_BRANDS = sorted(
    {b for c in CATEGORIES.values() for b in c["brands"]},
    key=len,
    reverse=True,  # match "milk vita" before "milk"
)

# Word-boundary patterns, compiled once. Substring matching would let a short
# brand token false-match inside another word ("rin" in "spring", "bd" in
# "abdul", "city" in "velocity"). \b...\b requires the brand to stand as a
# whole word/phrase.
_BRAND_PATTERNS = {b: re.compile(r"\b" + re.escape(b) + r"\b") for b in ALL_BRANDS}


def find_category(text_lower: str) -> str | None:
    """Return the best-matching category key, or None.

    Heuristic: pick the category with the most distinct keyword hits.
    Ties broken by total character overlap (longer keywords win).
    """
    best, best_score = None, 0
    for key, cfg in CATEGORIES.items():
        hits = [kw for kw in cfg["keywords"] if kw in text_lower]
        if not hits:
            continue
        score = len(hits) * 10 + sum(len(h) for h in hits)
        if score > best_score:
            best, best_score = key, score
    return best


def find_subcategory(category: str, text_lower: str) -> str | None:
    cfg = CATEGORIES.get(category)
    if not cfg:
        return None
    for sub, kws in cfg.get("subcategories", {}).items():
        if any(kw in text_lower for kw in kws):
            return sub
    return None


def find_brand(text_lower: str, category: str | None = None) -> str | None:
    """Match a known brand as a whole word. If category given, prefer brands
    declared for it. Returns None when no vocabulary brand is present — we never
    guess (a product-type word like "sunflower" is not a brand)."""
    candidates = CATEGORIES[category]["brands"] if category and category in CATEGORIES else ALL_BRANDS
    # match longest first to avoid "fresh" eating "fresh maida" before "rupchanda"
    for b in sorted(candidates, key=len, reverse=True):
        pat = _BRAND_PATTERNS.get(b) or re.compile(r"\b" + re.escape(b) + r"\b")
        if pat.search(text_lower):
            return b
    return None


# ─── Public helpers used by /categories endpoint ──────────────────────────

def categories_grouped() -> list[dict]:
    """Return categories grouped by their top-level `group` field, in the
    declared order. Each category includes its display name + subcategories."""
    by_group: dict[str, list[dict]] = {g: [] for g in CATEGORY_GROUPS}
    for key, cfg in CATEGORIES.items():
        group = cfg.get("group", "Other")
        by_group.setdefault(group, []).append({
            "key":           key,
            "display":       cfg["display"],
            "subcategories": [
                {"key": sk, "display": sk.replace("_", " ").title()}
                for sk in cfg.get("subcategories", {}).keys()
            ],
        })
    return [
        {"group": g, "categories": cats}
        for g, cats in by_group.items()
        if cats
    ]
