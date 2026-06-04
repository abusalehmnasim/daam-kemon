from .chaldal import ChaldalScraper
from .shwapno import ShwapnoScraper
from .othoba import OthobaScraper

# Pandamart (Foodpanda grocery) was removed in favour of Othoba: Foodpanda
# gates listings by a delivery-location cookie and aggressively blocks
# headless browsers, which is the wrong battle for an MVP price tracker.
SCRAPERS = {
    "chaldal": ChaldalScraper,
    "shwapno": ShwapnoScraper,
    "othoba":  OthobaScraper,
}

__all__ = ["ChaldalScraper", "ShwapnoScraper", "OthobaScraper", "SCRAPERS"]
