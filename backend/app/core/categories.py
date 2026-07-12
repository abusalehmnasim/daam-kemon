"""
Category & brand vocabulary for Bangladesh grocery.

Each category has:
  - display:   human-readable name shown in the UI
  - group:     top-level browsing group (department) — drives /categories
  - keywords:  substrings (lowercased, English or Bangla) that signal the category
  - brands:    known brands — used to extract a brand from a noisy product name
  - units:     allowed canonical units (drives "did we parse this right?")
  - subcategories: keyword sets that resolve to a subcategory key

Keep this file plain Python (not the DB) so the normalizer can run at scrape
time without a DB round-trip. New categories belong here.

Vocabulary sourced from the Daam Kemon category-tree/taxonomy reference
(2026-07-07): a 16-department grocery taxonomy covering staples, cooking
essentials, fish/meat/dairy, produce, packaged foods, and non-food aisles.
The DB schema still stores only (category, subcategory) — department is a
display-only grouping here, same as `group` always was; adopting the deeper
department/category/type tree into the schema itself is a separate, larger
change (out of scope for this vocabulary pass).

Collision discipline: `find_category` scores by keyword-hit count across ALL
categories, so a new category's top-level `keywords` must never use a bare
generic word that could out-score an existing, narrower category on its own
typical listings (e.g. a "chicken" meat category must never match on bare
"chicken", or "Kazi Farms Chicken Egg 12pcs" would stop resolving to `eggs`).
Prefer multi-word phrases for anything that overlaps an existing domain.
"""

import re

# Top-level groups / departments (preserves declared order; drives /categories UI)
CATEGORY_GROUPS: list[str] = [
    "Staples & Grains",
    "Cooking Essentials",
    "Fish & Seafood",
    "Meat & Poultry",
    "Dairy",
    "Vegetables",
    "Fruits",
    "Dry Fruits & Nuts",
    "Packaged & Instant Foods",
    "Snacks & Confectionery",
    "Bakery",
    "Beverages",
    "Baby Care",
    "Personal Care",
    "Home Care & Cleaning",
    "Frozen Foods",
    "Utilities",
]


CATEGORIES = {
    # ─── Staples & Grains ──────────────────────────────────────────────────
    "rice": {
        "display": "Rice",
        "group": "Staples & Grains",
        "keywords": ["rice", "chal", "miniket", "najirshail", "basmati",
                     "polao", "kalijira", "irri", "kataribhog", "katari",
                     "chinigura", "aromatic rice", "biryani rice",
                     "br-28", "br28", "br-29", "br29", "paijam", "guti",
                     "swarna", "brown rice", "red rice", "lal chal",
                     "চাল", "মিনিকেট", "নাজিরশাইল", "বাসমতি", "পোলাও",
                     "কাটারিভোগ", "চিনিগুঁড়া"],
        "brands": ["aci pure", "aci", "pran", "rashid", "diamond", "chashi",
                   "acm", "fresh", "teer", "bashundhara", "aarong", "ispahani",
                   "green field"],
        "units": ["KG", "G"],
        "subcategories": {
            "miniket":    ["miniket", "মিনিকেট"],
            "najirshail": ["najirshail", "najir", "নাজিরশাইল"],
            "basmati":    ["basmati", "বাসমতি"],
            "kalijira":   ["kalijira rice", "kalijira", "কালিজিরা"],
            "kataribhog": ["kataribhog", "katari", "কাটারিভোগ"],
            "chinigura":  ["chinigura", "polao", "polau", "aromatic rice",
                           "biryani rice", "পোলাও", "চিনিগুঁড়া"],
            "atap":       ["atap", "আতপ"],
            "irri":       ["irri"],
            "br28":       ["br-28", "br28", "atash"],
            "br29":       ["br-29", "br29"],
            "paijam":     ["paijam", "পাইজাম"],
            "guti_swarna":["guti", "swarna", "coarse rice", "mota chal"],
            "brown_red":  ["brown rice", "red rice", "lal chal"],
        },
    },
    "muri": {
        "display": "Puffed Rice (Muri)",
        "group": "Staples & Grains",
        "keywords": ["muri", "puffed rice", "মুড়ি"],
        "brands": ["pran", "fresh", "teer", "bombay sweets"],
        "units": ["G", "KG"],
        "subcategories": {},
    },
    "chira": {
        "display": "Chira (Flattened Rice)",
        "group": "Staples & Grains",
        "keywords": ["chira", "flattened rice", "beaten rice", "চিড়া"],
        "brands": ["pran", "fresh", "teer"],
        "units": ["G", "KG"],
        "subcategories": {},
    },
    "khoi": {
        "display": "Khoi (Popped Rice)",
        "group": "Staples & Grains",
        "keywords": ["khoi", "popped rice", "খৈ"],
        "brands": ["pran", "fresh"],
        "units": ["G", "KG"],
        "subcategories": {},
    },
    "flour": {
        "display": "Flour & Atta",
        "group": "Staples & Grains",
        "keywords": ["atta", "maida", "flour", "suji", "semolina",
                     "rice flour", "corn flour", "cornstarch", "corn starch",
                     "besan", "gram flour",
                     "আটা", "ময়দা", "সুজি", "চালের গুঁড়া", "বেসন"],
        "brands": ["teer", "fresh", "acm", "pran", "rupchanda", "bashundhara",
                   "ifad", "pusti", "muskan", "shaad", "foodela", "akij"],
        "units": ["KG", "G"],
        "subcategories": {
            "atta":  ["atta", "whole wheat", "আটা"],
            "maida": ["maida", "all purpose", "all-purpose", "ময়দা"],
            "suji":  ["suji", "semolina", "সুজি"],
            "rice_flour": ["rice flour", "chaler gura", "চালের গুঁড়া"],
            "corn_flour": ["corn flour", "cornstarch", "corn starch"],
            "besan": ["besan", "gram flour", "বেসন"],
        },
    },
    "lentils": {
        "display": "Lentils (Dal)",
        "group": "Staples & Grains",
        "keywords": ["dal", "lentil", "lentils", "ডাল", "মসুর", "মুগ", "ছোলা",
                     "motor", "মটর", "chickpea", "boot", "khesari", "anchor dal",
                     "mash kalai", "maskalai", "black gram", "felon"],
        "brands": ["pran", "fresh", "teer", "radhuni", "acm", "aarong"],
        "units": ["KG", "G"],
        "subcategories": {
            "masoor":  ["masoor", "mosur", "red lentil", "মসুর"],
            "mung":    ["moog", "mug", "mung", "মুগ"],
            "chola":   ["chola", "chana", "chickpea", "boot", "ছোলা"],
            "khesari": ["khesari", "খেসারি"],
            "anchor":  ["anchor", "অ্যাঙ্কর"],
            "motor":   ["motor", "মটর"],
            "mash_kalai": ["mash kalai", "maskalai", "black gram", "মাষকলাই"],
            "felon":   ["felon", "ফেলন"],
        },
    },
    "breakfast_cereals": {
        "display": "Breakfast Cereals & Oats",
        "group": "Staples & Grains",
        "keywords": ["oats", "oat", "cornflakes", "corn flakes", "muesli"],
        "brands": ["quaker", "kelloggs", "kellogg's", "pran", "nestle"],
        "units": ["G", "KG"],
        "subcategories": {
            "oats":       ["oats", "oat"],
            "cornflakes": ["cornflakes", "corn flakes"],
            "muesli":     ["muesli"],
        },
    },

    # ─── Cooking Essentials ────────────────────────────────────────────────
    "cooking_oil": {
        "display": "Cooking Oil",
        "group": "Cooking Essentials",
        "keywords": [
            "soybean oil", "soyabean oil", "soya oil", "soybean", "soyabean",
            "sunflower oil", "rice bran oil", "mustard oil", "palm oil",
            "cooking oil", "vegetable oil", "olive oil", "sesame oil",
            "til oil", "canola oil", "coconut oil", "blended oil", "mixed oil",
            "তেল", "সয়াবিন", "সরিষার তেল", "সরিষা", "নারিকেল তেল"
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
            "sesame":    ["sesame", "til oil"],
            "coconut":   ["coconut oil", "নারিকেল তেল"],
            "canola":    ["canola"],
            "blended":   ["blended oil", "vegetable oil", "mixed oil"],
        },
    },
    "ghee": {
        "display": "Ghee & Solid Fat",
        "group": "Cooking Essentials",
        "keywords": ["ghee", "dalda", "vanaspati", "butter oil",
                     "ঘি", "ডালডা"],
        "brands": ["fresh", "milk vita", "aarong", "rupchanda"],
        "units": ["KG", "G"],
        "subcategories": {
            "ghee":  ["ghee", "ঘি"],
            "dalda": ["dalda", "vanaspati", "ডালডা"],
        },
    },
    "sugar": {
        "display": "Sugar",
        "group": "Cooking Essentials",
        "keywords": ["sugar", "chini", "চিনি", "akher chini", "misri", "মিছরি",
                     "sugar free", "sugar-free"],
        "brands": ["fresh", "city", "deshbandhu", "pran", "meghna", "rapid"],
        "units": ["KG", "G"],
        "subcategories": {
            "white":  ["white", "refined", "সাদা"],
            "brown":  ["brown", "lal", "লাল", "raw"],
            "misri":  ["misri", "মিছরি"],
            "sugar_free": ["sugar free", "sugar-free", "sweetener"],
        },
    },
    "molasses": {
        "display": "Molasses (Gur)",
        "group": "Cooking Essentials",
        "keywords": ["molasses", "gur", "jaggery", "akher gur", "khejur gur",
                     "patali", "গুড়", "আখের গুড়", "খেজুরের গুড়"],
        "brands": ["pran", "khaas food", "fresh", "rongin"],
        "units": ["KG", "G"],
        "subcategories": {
            "akher":  ["akher", "sugarcane", "আখের"],
            "khejur": ["khejur gur", "date molasses", "খেজুরের গুড়"],
            "tal":    ["tal gur", "palm molasses", "তালের গুড়"],
            "patali": ["patali", "পাটালি"],
        },
    },
    "honey": {
        "display": "Honey",
        "group": "Cooking Essentials",
        "keywords": ["honey", "modhu", "মধু"],
        "brands": ["pran", "dabur", "apis", "khaas food"],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "salt": {
        "display": "Salt",
        "group": "Cooking Essentials",
        "keywords": ["salt", "lobon", "labon", "লবণ", "iodized salt"],
        "brands": ["acm", "fresh", "pran", "molla", "confidence"],
        "units": ["KG", "G"],
        "subcategories": {
            "iodized": ["iodized", "iodine"],
            "bit":     ["bit lobon", "rock salt"],
            "loose":   ["loose", "khola", "খোলা"],
        },
    },
    "spices": {
        "display": "Spices",
        "group": "Cooking Essentials",
        "keywords": [
            "turmeric", "haldi", "holud", "হলুদ",
            "chili powder", "chilli powder", "lal mirch", "morich", "মরিচ",
            "dried chili", "shukna morich",
            "cumin", "jira", "জিরা", "cumin powder",
            "coriander", "dhone", "dhane", "ধনে", "coriander powder",
            "ginger powder", "garlic powder",
            "cardamom", "elach", "এলাচ", "cinnamon", "daruchini", "দারুচিনি",
            "clove", "লবঙ্গ", "bay leaf", "tejpata", "black pepper", "golmorich",
            "fenugreek", "methi", "mustard seed", "nigella", "kalojira",
            "star anise", "nutmeg", "mace", "jayfol", "joyitri",
        ],
        "brands": ["radhuni", "pran", "fresh", "bd", "acm", "ifad", "shaad",
                   "kazi", "potash", "ahmed"],
        "units": ["G", "KG"],
        "subcategories": {
            "turmeric":  ["turmeric", "haldi", "holud", "হলুদ"],
            "chili":     ["chili", "chilli", "lal mirch", "morich",
                          "dried chili", "shukna morich", "মরিচ"],
            "cumin":     ["cumin", "jira", "জিরা"],
            "coriander": ["coriander", "dhone", "dhane", "ধনে"],
            "cardamom":  ["cardamom", "elach", "এলাচ"],
            "cinnamon":  ["cinnamon", "daruchini", "দারুচিনি"],
            "clove":     ["clove", "লবঙ্গ"],
            "bay_leaf":  ["bay leaf", "tejpata"],
            "black_pepper": ["black pepper", "golmorich"],
            "fenugreek": ["fenugreek", "methi"],
            "mustard_seed": ["mustard seed"],
            "nigella":   ["nigella", "kalojira"],
            "star_anise":["star anise"],
            "nutmeg_mace": ["nutmeg", "mace", "jayfol", "joyitri"],
        },
    },
    "garam_masala": {
        "display": "Garam Masala & Spice Blends",
        "group": "Cooking Essentials",
        "keywords": ["garam masala", "mixed spice", "biriyani masala",
                     "biryani masala", "tehari masala", "meat masala",
                     "chicken masala", "beef masala", "fish masala",
                     "curry powder", "kabab masala", "haleem mix",
                     "roast masala", "মসলা"],
        "brands": ["radhuni", "pran", "ahmed", "shaad", "kazi", "fresh", "potash"],
        "units": ["G"],
        "subcategories": {
            "biryani": ["biryani", "biriyani", "tehari"],
            "meat":    ["meat masala", "beef masala"],
            "chicken": ["chicken masala"],
            "fish":    ["fish masala"],
            "curry":   ["curry powder"],
            "kabab":   ["kabab masala"],
            "haleem":  ["haleem mix"],
            "roast":   ["roast masala"],
        },
    },
    "spice_paste": {
        "display": "Spice Pastes",
        "group": "Cooking Essentials",
        "keywords": ["ginger paste", "ada bata", "আদা বাটা",
                     "garlic paste", "roshun bata", "রসুন বাটা",
                     "ginger garlic paste", "ginger-garlic paste"],
        "brands": ["pran", "ahmed", "radhuni"],
        "units": ["G", "KG"],
        "subcategories": {
            "ginger": ["ginger paste", "ada bata", "আদা বাটা"],
            "garlic": ["garlic paste", "roshun bata", "রসুন বাটা"],
            "ginger_garlic": ["ginger garlic paste", "ginger-garlic paste"],
        },
    },
    "baking_addons": {
        "display": "Baking & Cooking Add-ons",
        "group": "Cooking Essentials",
        "keywords": ["yeast", "baking powder", "baking soda", "vinegar",
                     "সিরকা", "food colour", "food color", "custard powder"],
        "brands": ["pran", "radhuni", "ifad"],
        "units": ["G", "ML"],
        "subcategories": {
            "yeast":         ["yeast"],
            "baking_powder": ["baking powder"],
            "baking_soda":   ["baking soda"],
            "vinegar":       ["vinegar", "sirka", "সিরকা"],
            "food_colour":   ["food colour", "food color"],
            "custard_powder":["custard powder"],
        },
    },

    # ─── Fish & Seafood ────────────────────────────────────────────────────
    "fish_rui_katla": {
        "display": "Rui / Katla",
        "group": "Fish & Seafood",
        "keywords": ["rui", "rohu", "রুই", "katla", "catla", "কাতলা",
                     "mrigel", "kalbaus", "মৃগেল", "কালবাউশ"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {
            "rui":   ["rui", "rohu", "রুই"],
            "katla": ["katla", "catla", "কাতলা"],
        },
    },
    "fish_ilish": {
        "display": "Hilsa (Ilish)",
        "group": "Fish & Seafood",
        "keywords": ["ilish", "hilsa", "ইলিশ"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "fish_pangas": {
        "display": "Pangas",
        "group": "Fish & Seafood",
        "keywords": ["pangas", "pangash", "পাঙ্গাশ"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "fish_tilapia": {
        "display": "Tilapia",
        "group": "Fish & Seafood",
        "keywords": ["tilapia", "তেলাপিয়া"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "fish_shing_magur": {
        "display": "Shing / Magur",
        "group": "Fish & Seafood",
        "keywords": ["shing", "magur", "koi fish", "শিং", "মাগুর", "কই"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {
            "koi":   ["koi fish", "কই"],
            "shing_magur": ["shing", "magur", "শিং", "মাগুর"],
        },
    },
    "fish_small": {
        "display": "Small Fish",
        "group": "Fish & Seafood",
        "keywords": ["choto mach", "puti", "tengra", "mola", "টেংরা", "পুঁটি"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "shrimp": {
        "display": "Shrimp / Prawn (Chingri)",
        "group": "Fish & Seafood",
        "keywords": ["shrimp", "prawn", "chingri", "চিংড়ি", "golda", "bagda"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {
            "golda": ["golda"],
            "bagda": ["bagda"],
        },
    },
    "shutki": {
        "display": "Dried Fish (Shutki)",
        "group": "Fish & Seafood",
        "keywords": ["shutki", "dried fish", "শুঁটকি"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "fish_sea": {
        "display": "Sea Fish & Other Seafood",
        "group": "Fish & Seafood",
        "keywords": ["sea fish", "marine fish", "crab", "কাঁকড়া"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {
            "crab": ["crab", "কাঁকড়া"],
        },
    },

    # ─── Meat & Poultry ────────────────────────────────────────────────────
    "chicken": {
        "display": "Chicken",
        "group": "Meat & Poultry",
        "keywords": ["broiler chicken", "broiler", "sonali chicken", "sonali",
                     "deshi chicken", "deshi murgi", "layer chicken",
                     "chicken meat", "whole chicken", "chicken breast",
                     "chicken thigh", "chicken leg", "মুরগির মাংস", "ব্রয়লার",
                     "সোনালী"],
        "brands": ["kazi", "paragon", "aftab", "cp", "provita"],
        "units": ["KG", "G"],
        "subcategories": {
            "broiler": ["broiler", "ব্রয়লার"],
            "sonali":  ["sonali", "cock", "সোনালী"],
            "deshi":   ["deshi murgi", "deshi chicken", "দেশি মুরগি"],
            "layer":   ["layer chicken", "layer"],
        },
    },
    "beef": {
        "display": "Beef",
        "group": "Meat & Poultry",
        "keywords": ["beef", "goru", "গরুর মাংস", "গরু"],
        "brands": ["kazi", "provita"],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "mutton": {
        "display": "Mutton / Goat",
        "group": "Meat & Poultry",
        "keywords": ["mutton", "khashi", "খাসির মাংস", "goat meat"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "duck": {
        "display": "Duck",
        "group": "Meat & Poultry",
        "keywords": ["duck meat", "hasher mangsho", "হাঁসের মাংস"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "processed_meat": {
        "display": "Processed Meat",
        "group": "Meat & Poultry",
        "keywords": ["sausage", "salami", "meatball", "nuggets", "hot dog",
                     "pepperoni"],
        "brands": ["kazi", "provita", "aftab"],
        "units": ["G", "KG"],
        "subcategories": {
            "sausage":  ["sausage", "hot dog"],
            "salami":   ["salami", "pepperoni"],
            "meatball": ["meatball"],
            "nuggets":  ["nuggets"],
        },
    },
    "eggs": {
        "display": "Eggs",
        "group": "Meat & Poultry",
        "keywords": ["egg", "eggs", "ডিম", "dim"],
        "brands": ["kazi", "paragon", "aftab", "cp", "diamond", "quality"],
        "units": ["PCS"],
        "subcategories": {
            "chicken": ["chicken", "farm", "layer", "মুরগি"],
            "duck":    ["duck", "হাঁস"],
            "desi":    ["desi", "deshi", "দেশি"],
            "omega":   ["omega", "o3", "o3+"],
            "quail":   ["quail", "কোয়েল"],
        },
    },

    # ─── Dairy ──────────────────────────────────────────────────────────────
    "milk": {
        "display": "Liquid Milk",
        "group": "Dairy",
        "keywords": ["uht milk", "liquid milk", "pasteurized milk",
                     "doodh", "দুধ", "condensed milk", "evaporated milk"],
        "brands": ["pran", "arong", "aarong", "milk vita", "milkvita",
                   "farm fresh", "danish", "amul", "cowhead"],
        "units": ["L", "ML"],
        "subcategories": {
            "uht":          ["uht"],
            "pasteurized":  ["pasteurized", "pasteurised"],
            "flavored":     ["chocolate", "strawberry", "flavored", "flavoured"],
            "condensed":    ["condensed milk", "evaporated milk"],
        },
    },
    "powdered_milk": {
        "display": "Powdered Milk",
        "group": "Dairy",
        "keywords": ["powder milk", "powdered milk", "milk powder",
                     "full cream milk powder", "f.c.m.p", "fcmp", "গুঁড়া দুধ"],
        "brands": ["diploma", "dano", "nido", "marks", "fresh", "milk vita",
                   "milkvita", "anchor", "starship", "farm fresh"],
        "units": ["G", "KG"],
        "subcategories": {
            "full_cream": ["full cream", "fcmp", "f.c.m.p"],
            "skimmed":    ["skimmed", "skim"],
            "instant":    ["instant"],
        },
    },
    "yogurt": {
        "display": "Yogurt (Doi)",
        "group": "Dairy",
        "keywords": ["yogurt", "yoghurt", "doi", "দই", "mishti doi", "tok doi",
                     "drinking yogurt"],
        "brands": ["aarong", "pran", "milk vita", "farm fresh"],
        "units": ["KG", "G"],
        "subcategories": {
            "sweet": ["mishti doi", "sweet yogurt"],
            "sour":  ["tok doi", "sour yogurt"],
            "drinking": ["drinking yogurt", "yogurt drink"],
        },
    },
    "butter": {
        "display": "Butter",
        "group": "Dairy",
        "keywords": ["butter", "মাখন"],
        "brands": ["amul", "farm fresh", "aarong", "president"],
        "units": ["G", "KG"],
        "subcategories": {},
    },
    "cheese": {
        "display": "Cheese",
        "group": "Dairy",
        "keywords": ["cheese", "পনির", "mozzarella", "cheddar"],
        "brands": ["aarong", "amul", "arla", "almarai", "president"],
        "units": ["G", "KG"],
        "subcategories": {
            "mozzarella": ["mozzarella"],
            "cheddar":    ["cheddar"],
        },
    },

    # ─── Vegetables ─────────────────────────────────────────────────────────
    "onion": {
        "display": "Onion",
        "group": "Vegetables",
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
        "group": "Vegetables",
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
        "group": "Vegetables",
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
        "group": "Vegetables",
        "keywords": ["green chili", "green chilli", "kacha morich", "কাঁচা মরিচ"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "potato": {
        "display": "Potato",
        "group": "Vegetables",
        "keywords": ["potato", "alu", "আলু", "sweet potato", "মিষ্টি আলু"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {
            "sweet_potato": ["sweet potato", "মিষ্টি আলু"],
        },
    },
    "tomato": {
        "display": "Tomato",
        "group": "Vegetables",
        "keywords": ["tomato", "tometo", "টমেটো"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "brinjal": {
        "display": "Brinjal (Begun)",
        "group": "Vegetables",
        "keywords": ["brinjal", "begun", "eggplant", "বেগুন"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "lau": {
        "display": "Bottle Gourd (Lau)",
        "group": "Vegetables",
        "keywords": ["lau", "bottle gourd", "লাউ"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "leafy_greens": {
        "display": "Leafy Greens (Shak)",
        "group": "Vegetables",
        "keywords": ["shak", "spinach", "palong", "lal shak", "শাক", "পালং"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {},
    },
    "cauliflower_cabbage": {
        "display": "Cauliflower / Cabbage",
        "group": "Vegetables",
        "keywords": ["cauliflower", "cabbage", "fulkopi", "badhakopi",
                     "ফুলকপি", "বাঁধাকপি"],
        "brands": [],
        "units": ["KG", "G"],
        "subcategories": {
            "cauliflower": ["cauliflower", "fulkopi", "ফুলকপি"],
            "cabbage":     ["cabbage", "badhakopi", "বাঁধাকপি"],
        },
    },

    # ─── Fruits ─────────────────────────────────────────────────────────────
    "mango": {
        "display": "Mango",
        "group": "Fruits",
        "keywords": ["mango", "aam", "আম"],
        "brands": [],
        "units": ["KG", "PCS"],
        "subcategories": {},
    },
    "banana": {
        "display": "Banana",
        "group": "Fruits",
        "keywords": ["banana", "kola", "কলা"],
        "brands": [],
        "units": ["KG", "PCS"],
        "subcategories": {},
    },
    "jackfruit": {
        "display": "Jackfruit",
        "group": "Fruits",
        "keywords": ["jackfruit", "kathal", "কাঁঠাল"],
        "brands": [],
        "units": ["KG", "PCS"],
        "subcategories": {},
    },
    "guava": {
        "display": "Guava",
        "group": "Fruits",
        "keywords": ["guava", "peyara", "পেয়ারা"],
        "brands": [],
        "units": ["KG"],
        "subcategories": {},
    },
    "apple": {
        "display": "Apple",
        "group": "Fruits",
        "keywords": ["apple", "apel", "আপেল"],
        "brands": [],
        "units": ["KG", "PCS"],
        "subcategories": {},
    },
    "orange_malta": {
        "display": "Orange / Malta",
        "group": "Fruits",
        "keywords": ["orange", "malta", "komola", "কমলা"],
        "brands": [],
        "units": ["KG", "PCS"],
        "subcategories": {
            "malta":  ["malta"],
            "orange": ["orange", "komola", "কমলা"],
        },
    },
    "grapes": {
        "display": "Grapes",
        "group": "Fruits",
        "keywords": ["grapes", "angur", "আঙুর"],
        "brands": [],
        "units": ["KG"],
        "subcategories": {},
    },
    "watermelon": {
        "display": "Watermelon",
        "group": "Fruits",
        "keywords": ["watermelon", "tarmuj", "তরমুজ"],
        "brands": [],
        "units": ["KG", "PCS"],
        "subcategories": {},
    },

    # ─── Dry Fruits & Nuts ──────────────────────────────────────────────────
    "almond": {
        "display": "Almond (Kath Badam)",
        "group": "Dry Fruits & Nuts",
        "keywords": ["almond", "kath badam", "কাঠবাদাম"],
        "brands": ["pran", "fresh"],
        "units": ["G", "KG"],
        "subcategories": {},
    },
    "cashew": {
        "display": "Cashew (Kaju)",
        "group": "Dry Fruits & Nuts",
        "keywords": ["cashew", "kaju", "কাজু"],
        "brands": ["pran", "fresh"],
        "units": ["G", "KG"],
        "subcategories": {},
    },
    "peanut": {
        "display": "Peanut (Chinabadam)",
        "group": "Dry Fruits & Nuts",
        "keywords": ["peanut", "chinabadam", "chena badam", "চিনাবাদাম"],
        "brands": ["pran", "fresh"],
        "units": ["G", "KG"],
        "subcategories": {},
    },
    "raisins": {
        "display": "Raisins (Kishmish)",
        "group": "Dry Fruits & Nuts",
        "keywords": ["raisins", "kishmish", "কিশমিশ"],
        "brands": ["pran", "fresh"],
        "units": ["G", "KG"],
        "subcategories": {},
    },
    "dates_dry": {
        "display": "Dates (Khejur)",
        "group": "Dry Fruits & Nuts",
        "keywords": ["dates", "khejur", "খেজুর"],
        "brands": ["pran", "fresh"],
        "units": ["G", "KG"],
        "subcategories": {},
    },

    # ─── Packaged & Instant Foods ───────────────────────────────────────────
    "noodles": {
        "display": "Noodles & Pasta",
        "group": "Packaged & Instant Foods",
        "keywords": ["noodle", "noodles", "ramen", "instant noodles", "নুডলস",
                     "pasta", "macaroni", "vermicelli", "semai"],
        "brands": ["mr. noodles", "mr noodles", "knorr", "maggi", "pran",
                   "doodles", "ifad", "cocola"],
        "units": ["G"],
        "subcategories": {
            "instant": ["instant", "cup"],
            "egg":     ["egg"],
            "chicken": ["chicken"],
            "masala":  ["masala", "curry"],
            "pasta":   ["pasta", "macaroni"],
            "vermicelli": ["vermicelli", "semai"],
        },
    },
    "soy_sauce": {
        "display": "Soy Sauce",
        "group": "Packaged & Instant Foods",
        "keywords": ["soy sauce", "soya sauce", "soyabean sauce", "kikkoman",
                     "oyster sauce", "সয়া সস"],
        "brands": ["pran", "kikkoman", "lee kum kee", "ahmed", "ruchi", "good day"],
        "units": ["ML", "L"],
        "subcategories": {
            "light":  ["light"],
            "dark":   ["dark"],
            "oyster": ["oyster sauce"],
        },
    },
    "tomato_sauce": {
        "display": "Tomato Sauce & Ketchup",
        "group": "Packaged & Instant Foods",
        "keywords": ["tomato sauce", "ketchup", "tomato ketchup", "chili sauce",
                     "chilli sauce", "টমেটো সস"],
        "brands": ["pran", "ahmed", "ruchi", "heinz", "kissan", "tasty", "danish"],
        "units": ["ML", "G", "KG"],
        "subcategories": {
            "ketchup": ["ketchup"],
            "sauce":   ["sauce"],
            "chili":   ["chili sauce", "chilli sauce"],
        },
    },
    "sauces_other": {
        "display": "Mayonnaise & Dressings",
        "group": "Packaged & Instant Foods",
        "keywords": ["mayonnaise", "salad dressing", "island dressing"],
        "brands": ["pran", "remia", "naples", "herman"],
        "units": ["ML", "G"],
        "subcategories": {
            "mayonnaise": ["mayonnaise"],
            "dressing":   ["salad dressing", "island dressing"],
        },
    },
    "pickles": {
        "display": "Pickles (Achar)",
        "group": "Packaged & Instant Foods",
        "keywords": ["pickle", "achar", "আচার", "jolpai", "mango pickle",
                     "garlic pickle"],
        "brands": ["pran", "ahmed", "rader", "shezan"],
        "units": ["G", "KG"],
        "subcategories": {
            "mango":  ["mango pickle"],
            "olive":  ["jolpai", "olive pickle"],
            "garlic": ["garlic pickle"],
            "mixed":  ["mixed pickle"],
        },
    },
    "spreads": {
        "display": "Jam / Jelly / Spreads",
        "group": "Packaged & Instant Foods",
        "keywords": ["jam", "jelly", "marmalade", "peanut butter",
                     "chocolate spread", "nutella"],
        "brands": ["pran", "danish", "nutella", "kissan"],
        "units": ["G", "KG"],
        "subcategories": {
            "jam":            ["jam"],
            "jelly":          ["jelly", "marmalade"],
            "peanut_butter":  ["peanut butter"],
            "chocolate_spread": ["chocolate spread", "nutella"],
        },
    },
    "canned": {
        "display": "Canned & Preserved Foods",
        "group": "Packaged & Instant Foods",
        "keywords": ["canned fish", "tuna", "sardine", "sweet corn",
                     "mushroom", "baked beans"],
        "brands": ["pran", "sea gold", "fresh catch"],
        "units": ["G", "KG"],
        "subcategories": {
            "fish":   ["canned fish", "tuna", "sardine"],
            "corn":   ["sweet corn"],
            "mushroom": ["mushroom"],
            "beans":  ["baked beans"],
        },
    },
    "ready_mix": {
        "display": "Ready Mixes",
        "group": "Packaged & Instant Foods",
        "keywords": ["cake mix", "jelly mix", "pudding", "custard",
                     "firni mix", "payesh mix", "haleem mix"],
        "brands": ["pran", "ifad", "danish"],
        "units": ["G"],
        "subcategories": {},
    },
    "soups_stock": {
        "display": "Soups & Stock",
        "group": "Packaged & Instant Foods",
        "keywords": ["packet soup", "stock cube", "soup mix"],
        "brands": ["knorr", "maggi"],
        "units": ["G"],
        "subcategories": {},
    },

    # ─── Snacks & Confectionery ─────────────────────────────────────────────
    "biscuits": {
        "display": "Biscuits",
        "group": "Snacks & Confectionery",
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
    "chips": {
        "display": "Chips & Crisps",
        "group": "Snacks & Confectionery",
        "keywords": ["chips", "crisps", "potato chips"],
        "brands": ["lays", "pringles", "bombay sweets", "mr chips"],
        "units": ["G"],
        "subcategories": {},
    },
    "chanachur": {
        "display": "Chanachur",
        "group": "Snacks & Confectionery",
        "keywords": ["chanachur", "chanachoor", "চানাচুর", "jhalmuri mix"],
        "brands": ["bombay sweets", "haque", "pran", "danish", "ahmed", "ruchi",
                   "potato crackers", "potato"],
        "units": ["G", "KG"],
        "subcategories": {
            "regular": ["regular"],
            "spicy":   ["hot", "spicy", "jhal"],
        },
    },
    "chocolate_candy": {
        "display": "Chocolate & Candy",
        "group": "Snacks & Confectionery",
        "keywords": ["chocolate bar", "candy", "toffee", "chewing gum",
                     "lozenge"],
        "brands": ["cadbury", "nestle", "orion", "haldiram"],
        "units": ["G", "PCS"],
        "subcategories": {
            "chocolate": ["chocolate bar"],
            "candy":     ["candy", "toffee", "lozenge"],
            "gum":       ["chewing gum"],
        },
    },
    "rusk_toast": {
        "display": "Cake & Rusk",
        "group": "Snacks & Confectionery",
        "keywords": ["bar cake", "toast biscuit", "rusk biscuit", "টোস্ট"],
        "brands": ["olympia", "pran"],
        "units": ["G", "PCS"],
        "subcategories": {},
    },
    "supari_pan": {
        "display": "Supari & Pan Masala",
        "group": "Snacks & Confectionery",
        "keywords": ["supari", "betel nut", "pan masala", "paan masala",
                     "সুপারি", "পান মসলা"],
        "brands": ["rajnigandha", "pan parag", "kamal", "shahi"],
        "units": ["G"],
        "subcategories": {
            "supari": ["supari", "betel"],
            "pan":    ["pan masala", "paan"],
        },
    },

    # ─── Bakery ─────────────────────────────────────────────────────────────
    "bread": {
        "display": "Bread (Pauruti)",
        "group": "Bakery",
        "keywords": ["bread", "pauruti", "পাউরুটি"],
        "brands": ["bimbo", "olympia", "cook up"],
        "units": ["PCS", "G"],
        "subcategories": {
            "white":  ["white bread"],
            "brown":  ["brown bread"],
            "milk":   ["milk bread"],
        },
    },
    "bun_roll": {
        "display": "Bun / Roll",
        "group": "Bakery",
        "keywords": ["bun", "roll", "croissant"],
        "brands": ["olympia", "cook up"],
        "units": ["PCS"],
        "subcategories": {},
    },
    "cake_pastry": {
        "display": "Cake / Pastry",
        "group": "Bakery",
        "keywords": ["fresh cake", "pastry"],
        "brands": ["cooper's", "coopers", "kings confectionery"],
        "units": ["PCS", "G"],
        "subcategories": {},
    },

    # ─── Beverages ──────────────────────────────────────────────────────────
    "tea": {
        "display": "Tea",
        "group": "Beverages",
        "keywords": ["tea", "cha", "chai", "tea bag", "tea leaf", "tea leaves",
                     "green tea", "চা", "চা পাতা"],
        "brands": ["ispahani", "taaza", "fresh", "kazi", "lipton", "halda valley",
                   "seylon", "danedar", "twinings", "vitacare"],
        "units": ["G", "KG"],
        "subcategories": {
            "black":   ["black"],
            "green":   ["green"],
            "bag":     ["bag", "sachet"],
            "premium": ["premium", "gold", "elite"],
        },
    },
    "coffee": {
        "display": "Coffee",
        "group": "Beverages",
        "keywords": ["coffee", "kofi", "কফি", "instant coffee"],
        "brands": ["nescafe", "nestle", "bru"],
        "units": ["G"],
        "subcategories": {
            "instant": ["instant coffee"],
            "ground":  ["ground coffee"],
            "sachet":  ["3 in 1", "3-in-1 sachet"],
        },
    },
    "soft_drink": {
        "display": "Soft / Carbonated Drinks",
        "group": "Beverages",
        "keywords": ["soft drink", "cola", "carbonated"],
        "brands": ["coca-cola", "coca cola", "pepsi", "mojo", "fanta", "sprite", "7up"],
        "units": ["L", "ML"],
        "subcategories": {},
    },
    "juice": {
        "display": "Juice & Nectar",
        "group": "Beverages",
        "keywords": ["juice", "nectar", "mango drink"],
        "brands": ["pran", "shezan", "fresh", "danish", "frutika"],
        "units": ["L", "ML"],
        "subcategories": {},
    },
    "drink_mix": {
        "display": "Drink Mixes / Syrup",
        "group": "Beverages",
        "keywords": ["tang", "rooh afza", "sharbat", "drink mix"],
        "brands": ["tang", "rooh afza", "pran"],
        "units": ["G", "ML"],
        "subcategories": {},
    },
    "energy_drink": {
        "display": "Energy Drinks",
        "group": "Beverages",
        "keywords": ["energy drink"],
        "brands": ["speed", "tiger", "red bull"],
        "units": ["ML", "L"],
        "subcategories": {},
    },
    "bottled_water": {
        "display": "Bottled Water",
        "group": "Beverages",
        "keywords": ["bottled water", "drinking water", "mineral water", "pani",
                     "পানি"],
        "brands": ["mum", "aquafina", "jibon", "fresh"],
        "units": ["L", "ML"],
        "subcategories": {},
    },
    "traditional_drinks": {
        "display": "Traditional Drinks",
        "group": "Beverages",
        "keywords": ["lassi", "borhani", "matha"],
        "brands": ["aarong", "farm fresh"],
        "units": ["ML", "L"],
        "subcategories": {
            "lassi":   ["lassi"],
            "borhani": ["borhani"],
            "matha":   ["matha"],
        },
    },

    # ─── Baby Care ──────────────────────────────────────────────────────────
    "infant_formula": {
        "display": "Infant Formula",
        "group": "Baby Care",
        "keywords": ["infant formula", "baby milk"],
        "brands": ["nan", "lactogen", "cerelac", "similac", "s-26"],
        "units": ["G"],
        "subcategories": {
            "stage_1": ["stage 1"],
            "stage_2": ["stage 2"],
            "stage_3": ["stage 3"],
        },
    },
    "baby_food": {
        "display": "Baby Cereal / Food",
        "group": "Baby Care",
        "keywords": ["baby food", "baby cereal", "cerelac"],
        "brands": ["cerelac", "nestle"],
        "units": ["G"],
        "subcategories": {},
    },
    "diapers": {
        "display": "Diapers & Wipes",
        "group": "Baby Care",
        "keywords": ["diaper", "nappy", "baby wipes", "baby toiletries"],
        "brands": ["huggies", "pampers", "molfix"],
        "units": ["PCS"],
        "subcategories": {
            "diaper": ["diaper", "nappy"],
            "wipes":  ["baby wipes"],
        },
    },

    # ─── Personal Care ──────────────────────────────────────────────────────
    "soap": {
        "display": "Bath Soap & Body Wash",
        "group": "Personal Care",
        "keywords": ["bath soap", "bathing soap", "beauty soap", "body soap",
                     "soap bar", "bath bar", "soap", "সাবান", "body wash",
                     "handwash", "hand wash"],
        "brands": ["lux", "lifebuoy", "dove", "tibet", "meril", "savlon",
                   "dettol", "keya", "sandalina", "cute", "yardley", "rexona"],
        "units": ["G", "KG", "ML"],
        "subcategories": {
            "beauty":          ["beauty", "body", "glow", "soft"],
            "antibacterial":   ["antibacterial", "germ", "dettol", "savlon", "lifebuoy"],
            "body_wash":       ["body wash"],
            "handwash":        ["handwash", "hand wash"],
        },
    },
    "shampoo": {
        "display": "Shampoo & Conditioner",
        "group": "Personal Care",
        "keywords": ["shampoo", "conditioner", "শ্যাম্পু"],
        "brands": ["sunsilk", "clear", "head & shoulders", "dove", "pantene",
                   "tresemme", "garnier", "loreal", "himalaya"],
        "units": ["ML", "L", "G"],
        "subcategories": {
            "sachet": ["sachet", "mini"],
            "bottle": ["bottle"],
            "anti_dandruff": ["anti dandruff", "anti-dandruff", "dandruff"],
            "conditioner": ["conditioner"],
        },
    },
    "hair_oil": {
        "display": "Hair Oil",
        "group": "Personal Care",
        "keywords": ["hair oil", "coconut hair oil", "চুলের তেল"],
        "brands": ["parachute", "dabur amla", "keo karpin", "vatika"],
        "units": ["ML", "L"],
        "subcategories": {},
    },
    "oral_care": {
        "display": "Oral Care",
        "group": "Personal Care",
        "keywords": ["toothpaste", "toothbrush", "mouthwash"],
        "brands": ["close up", "closeup", "pepsodent", "sensodyne", "colgate", "medicam"],
        "units": ["G", "ML", "PCS"],
        "subcategories": {
            "toothpaste":  ["toothpaste"],
            "toothbrush":  ["toothbrush"],
            "mouthwash":   ["mouthwash"],
        },
    },
    "skin_care": {
        "display": "Skin Care",
        "group": "Personal Care",
        "keywords": ["lotion", "face wash", "face cream", "petroleum jelly",
                     "vaseline"],
        "brands": ["nivea", "ponds", "vaseline", "himalaya", "garnier"],
        "units": ["ML", "G"],
        "subcategories": {
            "lotion":     ["lotion"],
            "face_wash":  ["face wash"],
            "cream":      ["face cream", "cream"],
            "petroleum_jelly": ["petroleum jelly", "vaseline"],
        },
    },
    "shaving_grooming": {
        "display": "Shaving & Grooming",
        "group": "Personal Care",
        "keywords": ["shaving cream", "razor", "aftershave", "shaving foam"],
        "brands": ["gillette", "old spice"],
        "units": ["G", "ML", "PCS"],
        "subcategories": {},
    },
    "deodorant_perfume": {
        "display": "Deodorant / Perfume",
        "group": "Personal Care",
        "keywords": ["deodorant", "body spray", "perfume", "attar"],
        "brands": ["axe", "rexona", "old spice", "fogg"],
        "units": ["ML"],
        "subcategories": {},
    },
    "feminine_hygiene": {
        "display": "Feminine Hygiene",
        "group": "Personal Care",
        "keywords": ["sanitary napkin", "sanitary pad"],
        "brands": ["whisper", "always", "freedom"],
        "units": ["PCS"],
        "subcategories": {},
    },

    # ─── Home Care & Cleaning ───────────────────────────────────────────────
    "detergent": {
        "display": "Washing Detergent",
        "group": "Home Care & Cleaning",
        "keywords": ["detergent", "washing powder", "washing liquid",
                     "laundry detergent", "fabric softener", "bleach",
                     "ডিটারজেন্ট"],
        "brands": ["surf excel", "rin", "wheel", "chaka", "tide", "ariel",
                   "jet", "keya", "shuvro", "shwapno", "fast wash", "attack"],
        "units": ["KG", "G", "L", "ML"],
        "subcategories": {
            "powder": ["powder"],
            "liquid": ["liquid"],
            "bar":    ["bar"],
            "softener": ["fabric softener"],
            "bleach": ["bleach"],
        },
    },
    "dishwash": {
        "display": "Dishwashing",
        "group": "Home Care & Cleaning",
        "keywords": ["dishwash", "dish wash", "vim", "trix", "scrubber",
                     "dish soap"],
        "brands": ["vim", "trix"],
        "units": ["ML", "G", "PCS"],
        "subcategories": {
            "bar":       ["dish wash bar"],
            "liquid":    ["dish wash liquid"],
            "scrubber":  ["scrubber"],
        },
    },
    "surface_cleaners": {
        "display": "Surface Cleaners",
        "group": "Home Care & Cleaning",
        "keywords": ["floor cleaner", "toilet cleaner", "harpic",
                     "glass cleaner", "multi-surface cleaner"],
        "brands": ["harpic", "lizol"],
        "units": ["ML", "L"],
        "subcategories": {
            "floor":  ["floor cleaner"],
            "toilet": ["toilet cleaner", "harpic"],
            "glass":  ["glass cleaner"],
        },
    },
    "pest_control": {
        "display": "Air & Pest Control",
        "group": "Home Care & Cleaning",
        "keywords": ["air freshener", "mosquito coil", "aerosol",
                     "insect spray"],
        "brands": ["odomos", "aerogard", "good knight"],
        "units": ["ML", "PCS"],
        "subcategories": {},
    },
    "paper_disposables": {
        "display": "Paper & Disposables",
        "group": "Home Care & Cleaning",
        "keywords": ["tissue", "toilet paper", "kitchen towel", "facial tissue",
                     "napkin", "aluminum foil", "cling film", "garbage bag"],
        "brands": ["kleenex", "fresh"],
        "units": ["PCS", "G"],
        "subcategories": {},
    },

    # ─── Frozen Foods ───────────────────────────────────────────────────────
    "frozen_snacks": {
        "display": "Frozen Snacks",
        "group": "Frozen Foods",
        "keywords": ["frozen paratha", "samosa", "singara", "spring roll",
                     "frozen kabab", "wonton"],
        "brands": ["golden fry", "khan's"],
        "units": ["G", "KG"],
        "subcategories": {},
    },
    "frozen_veg": {
        "display": "Frozen Vegetables",
        "group": "Frozen Foods",
        "keywords": ["frozen vegetables", "frozen peas"],
        "brands": [],
        "units": ["G", "KG"],
        "subcategories": {},
    },
    "ice_cream": {
        "display": "Ice Cream & Dessert",
        "group": "Frozen Foods",
        "keywords": ["ice cream", "frozen dessert"],
        "brands": ["igloo", "polar", "movenpick", "kwality wall's"],
        "units": ["L", "ML"],
        "subcategories": {},
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
