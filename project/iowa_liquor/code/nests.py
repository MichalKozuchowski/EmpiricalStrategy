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
