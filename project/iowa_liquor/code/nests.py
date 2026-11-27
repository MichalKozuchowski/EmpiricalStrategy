"""
nests.py: map Iowa ABD category names to (1) demand nests (spirit type) and (2) 2025 tariff exposure by origin.
Kept in one place so every script uses the same definitions.
"""


def nest_of(cat):
    """Spirit-type nests from the ABD category name."""
    c = cat.upper() if isinstance(cat, str) else ""          # some items have a blank category (NaN)
    if "LIQUEUR" in c or "SCHNAPPS" in c or "CORDIAL" in c or "TRIPLE SEC" in c:
        return "Liqueur/Schnapps"        # includes Whiskey Liqueur (Fireball), cream, coffee
    if "VODKA" in c:
        return "Vodka"
    if "WHISK" in c or "BOURBON" in c or "SCOTCH" in c:
        return "Whiskey"
    if "RUM" in c:
        return "Rum"
    if "TEQUILA" in c or "MEZCAL" in c:
        return "Tequila/Mezcal"
    if "GIN" in c:
        return "Gin"
    if "BRAND" in c:
        return "Brandy"
    return "Other"                        # RTD cocktails, specialty packages, neutral grain, special orders


# ---------------------------------------------------------------------------------------------------------------------
# Country-of-origin -> 2025 tariff group. ABD categories have no origin, and "imported" categories mix origins
# (e.g. IMPORTED SCHNAPPS is mostly Dr. McGillicuddy's from CANADA = tariff-exempt; Bushmills is Northern Ireland = UK).
# Brand rules below were hand-coded for the top imported products by dollars 2024-26 (they cover ~92% of the $223M
# spent on imported-category spirits). Unmatched imported-category items fall back to the category default or "Unknown".
# ---------------------------------------------------------------------------------------------------------------------
BRAND_ORIGIN = [
    # United Kingdom (10% from Apr 5 2025; UK whisky 0% from Jul 24 2026)
    ("BUSHMILLS", "UK"), ("TANQUERAY", "UK"), ("BOMBAY", "UK"), ("HENDRICKS", "UK"), ("BEEFEATER", "UK"),
    ("BOODLES", "UK"), ("BROKERS", "UK"), ("BOTANIST", "UK"), ("THREE OLIVES", "UK"), ("DRAMBUIE", "UK"),
    ("JOHNNIE WALKER", "UK"), ("DEWARS", "UK"), ("BUCHANAN", "UK"), ("CHIVAS", "UK"), ("J & B", "UK"),
    ("MONKEY SHOULDER", "UK"), ("MACALLAN", "UK"),          # (Glen* single malts are caught by the SCOTCH category rule) ("BALVENIE", "UK"), ("LAPHROAIG", "UK"),
    ("LAGAVULIN", "UK"), ("OBAN", "UK"), ("ABERLOUR", "UK"), ("ARDBEG", "UK"), ("DALMORE", "UK"),
    ("TULLIBARDINE", "UK"), ("LAUDERS", "UK"), ("SCORESBY", "UK"), ("CLAN MACGREGOR", "UK"),
    ("KIRKLAND SIGNATURE BLENDED SCOTCH", "UK"),
    # European Union (10% Apr 5 2025, 15% from Aug 7 2025, 10% from Feb 24 2026)
    ("JAMESON", "EU"), ("REDBREAST", "EU"), ("GREEN SPOT", "EU"), ("TULLAMORE", "EU"), ("PROPER NO", "EU"),
    ("TEELING", "EU"), ("PADDY", "EU"), ("KIRKLAND SIGNATURE IRISH", "EU"), ("DRUMSHANBO", "EU"), ("CASHEL", "EU"),
    ("FIVE FARMS", "EU"), ("CAROLANS", "EU"), ("BAILEYS", "EU"), ("RYANS", "EU"),
    ("ABSOLUT", "EU"), ("GREY GOOSE", "EU"), ("FRIS", "EU"), ("KETEL ONE", "EU"), ("CIROC", "EU"),
    ("BELVEDERE", "EU"), ("CHOPIN", "EU"), ("SOBIESKI", "EU"), ("SVEDKA", "EU"), ("STOLICHNAYA", "EU"),
    ("PINNACLE", "EU"), ("EFFEN", "EU"), ("FRENCH VODKA", "EU"), ("NOLETS", "EU"),
    ("HENNESSY", "EU"), ("REMY MARTIN", "EU"), ("COURVOISIER", "EU"), ("MARTELL", "EU"), ("D'USSE", "EU"),
    ("ST REMY", "EU"), ("JAGERMEISTER", "EU"), ("RUMPLE MINZE", "EU"), ("COINTREAU", "EU"), ("GRAND MARNIER", "EU"),
    ("LICOR 43", "EU"), ("APEROL", "EU"), ("CAMPARI", "EU"), ("DISARONNO", "EU"), ("FRANGELICO", "EU"),
    ("AVERNA", "EU"), ("NONINO", "EU"), ("FERNET BRANCA", "EU"), ("LUXARDO", "EU"), ("ROMANA", "EU"),
    ("CARAVELLA", "EU"), ("GRANGALA", "EU"), ("ST GERMAIN", "EU"), ("CHAMBORD", "EU"), ("B&B", "EU"),
    ("HPNOTIQ", "EU"), ("ABSENTE", "EU"), ("DOMAINE DE CANTON", "EU"), ("METAXA", "EU"),
    # Canada / Mexico: USMCA-qualifying -> exempt
    ("MCGILLICUDDY", "USMCA"), ("KAHLUA", "USMCA"), ("TORTILLA", "USMCA"), ("JUAREZ GOLD", "USMCA"),
    ("DON AGAVE", "USMCA"), ("MI CAMPO", "USMCA"), ("CHICA CHIDA", "USMCA"),
    # Other origins (10% baseline, 15% for Japan/Korea/Iceland from Aug 7 2025): not used as treated or control
    ("ROKU", "Other"), ("HAKU", "Other"), ("SOJU", "Other"), ("REYKA", "Other"), ("MR. BLACK", "Other"),
    # Domestic products sitting in "imported"-looking or cream categories
    ("RUMCHATA", "US"), ("TEQUILA ROSE", "US"), ("BUFFALO TRACE", "US"), ("TIPPY COW", "US"), ("IOWISH", "US"),
    ("REVELTON", "US"), ("JACKSON MORGAN", "US"), ("CEDAR RIDGE", "US"), ("PARAMOUNT", "US"), ("DEKUYPER", "US"),
]
DOMESTIC_HINT = ("AMERICAN", "BOURBON", "TENNESSEE", "STRAIGHT RYE", "BLENDED WHISKIES", "CORN WHISK", "IOWA")


def origin_of(desc, cat):
    """Best-guess origin group for the 2025 tariffs: 'UK', 'EU', 'USMCA', 'US', 'Other' or 'Unknown'."""
    d = desc.upper() if isinstance(desc, str) else ""
    c = cat.upper() if isinstance(cat, str) else ""
    for key, org in BRAND_ORIGIN:
        if key in d:
            return org
    if "SCOTCH" in c:
        return "UK"
    if "IRISH" in c:
        return "EU"
    if "TEQUILA" in c or "MEZCAL" in c or "CANADIAN" in c:
        return "USMCA"
    if any(h in c for h in DOMESTIC_HINT):
        return "US"
    return "Unknown"
