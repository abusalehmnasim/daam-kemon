from .chaldal import ChaldalScraper
from .shwapno import ShwapnoScraper
from .othoba import OthobaScraper
from .unimart import UnimartScraper
from .daraz import DarazScraper

# Pandamart (Foodpanda grocery) was removed in favour of Othoba: Foodpanda
# gates listings by a delivery-location cookie and aggressively blocks
# headless browsers, which is the wrong battle for an MVP price tracker.
SCRAPERS = {
    "chaldal": ChaldalScraper,
    "shwapno": ShwapnoScraper,
    "othoba":  OthobaScraper,
    "unimart": UnimartScraper,
    "daraz":   DarazScraper,
}

__all__ = ["ChaldalScraper", "ShwapnoScraper", "OthobaScraper", "UnimartScraper", "DarazScraper", "SCRAPERS"]
