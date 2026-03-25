"""Match EsportFire 300 items to our data and rebuild esportfire300.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Full EF300 list (all 300 items from the article)
EF300_RAW = [
    "★ Bayonet | Autotronic (Field-Tested)", "★ Bayonet | Damascus Steel (Field-Tested)",
    "★ Bayonet | Freehand (Field-Tested)", "★ Bayonet | Marble Fade (Factory New)",
    "★ Bowie Knife | Autotronic (Field-Tested)", "★ Bowie Knife | Black Laminate (Field-Tested)",
    "★ Bowie Knife | Lore (Field-Tested)", "★ Broken Fang Gloves | Needle Point (Field-Tested)",
    "★ Broken Fang Gloves | Yellow-banded (Field-Tested)", "★ Butterfly Knife | Autotronic (Field-Tested)",
    "★ Butterfly Knife | Bright Water (Field-Tested)", "★ Butterfly Knife | Freehand (Field-Tested)",
    "★ Classic Knife | Blue Steel (Field-Tested)", "★ Driver Gloves | Black Tie (Field-Tested)",
    "★ Driver Gloves | King Snake (Field-Tested)", "★ Driver Gloves | Racing Green (Field-Tested)",
    "★ Falchion Knife | Autotronic (Field-Tested)", "★ Falchion Knife | Damascus Steel (Field-Tested)",
    "★ Falchion Knife | Freehand (Field-Tested)", "★ Flip Knife | Black Laminate (Field-Tested)",
    "★ Flip Knife | Bright Water (Field-Tested)", "★ Flip Knife | Marble Fade (Minimal Wear)",
    "★ Gut Knife | Autotronic (Field-Tested)", "★ Gut Knife | Bright Water (Field-Tested)",
    "★ Gut Knife | Freehand (Field-Tested)", "★ Hand Wraps | Cobalt Skulls (Field-Tested)",
    "★ Hand Wraps | Overprint (Field-Tested)", "★ Huntsman Knife | Autotronic (Field-Tested)",
    "★ Huntsman Knife | Bright Water (Field-Tested)", "★ Huntsman Knife | Doppler (Factory New)",
    "★ Huntsman Knife | Forest DDPAT (Field-Tested)", "★ Hydra Gloves | Emerald (Field-Tested)",
    "★ Hydra Gloves | Mangrove (Field-Tested)", "★ Karambit | Black Laminate (Field-Tested)",
    "★ Karambit | Damascus Steel (Field-Tested)", "★ Karambit | Lore (Field-Tested)",
    "★ M9 Bayonet | Black Laminate (Field-Tested)", "★ M9 Bayonet | Lore (Field-Tested)",
    "★ M9 Bayonet | Slaughter (Field-Tested)", "★ Moto Gloves | Cool Mint (Field-Tested)",
    "★ Moto Gloves | Smoke Out (Field-Tested)", "★ Navaja Knife | Blue Steel (Field-Tested)",
    "★ Navaja Knife | Damascus Steel (Field-Tested)", "★ Navaja Knife | Tiger Tooth (Factory New)",
    "★ Nomad Knife | Blue Steel (Field-Tested)", "★ Nomad Knife | Night Stripe (Field-Tested)",
    "★ Nomad Knife | Slaughter (Field-Tested)", "★ Paracord Knife | Blue Steel (Field-Tested)",
    "★ Paracord Knife | Slaughter (Field-Tested)", "★ Shadow Daggers | Autotronic (Field-Tested)",
    "★ Shadow Daggers | Boreal Forest (Field-Tested)", "★ Shadow Daggers | Damascus Steel (Field-Tested)",
    "★ Shadow Daggers | Slaughter (Field-Tested)", "★ Skeleton Knife | Blue Steel (Field-Tested)",
    "★ Skeleton Knife | Scorched (Field-Tested)", "★ Specialist Gloves | Crimson Kimono (Field-Tested)",
    "★ Specialist Gloves | Fade (Field-Tested)", "★ Specialist Gloves | Field Agent (Field-Tested)",
    "★ Sport Gloves | Big Game (Field-Tested)", "★ Sport Gloves | Omega (Field-Tested)",
    "★ Sport Gloves | Scarlet Shamagh (Field-Tested)", "★ Stiletto Knife | Blue Steel (Field-Tested)",
    "★ Stiletto Knife | Doppler (Factory New)", "★ Stiletto Knife | Urban Masked (Field-Tested)",
    "★ Survival Knife | Blue Steel (Field-Tested)", "★ Survival Knife | Slaughter (Field-Tested)",
    "★ Talon Knife | Damascus Steel (Field-Tested)", "★ Talon Knife | Night Stripe (Field-Tested)",
    "★ Talon Knife | Tiger Tooth (Factory New)", "★ Ursus Knife | Blue Steel (Field-Tested)",
    "★ Ursus Knife | Damascus Steel (Field-Tested)", "★ Ursus Knife | Tiger Tooth (Factory New)",
    # Weapon skins
    "AK-47 | Case Hardened (Field-Tested)", "AK-47 | Fire Serpent (Field-Tested)",
    "AK-47 | Fuel Injector (Field-Tested)", "AK-47 | Ice Coaled (Field-Tested)",
    "AK-47 | Redline (Field-Tested)", "AK-47 | Vulcan (Field-Tested)",
    "AWP | Asiimov (Battle-Scarred)", "AWP | BOOM (Field-Tested)",
    "AWP | Graphite (Factory New)", "AWP | Lightning Strike (Factory New)",
    "AWP | Redline (Field-Tested)", "AWP | Wildfire (Field-Tested)",
    "CS20 Case", "Danger Zone Case",
    "Desert Eagle | Blaze (Factory New)", "Desert Eagle | Conspiracy (Factory New)",
    "Desert Eagle | Crimson Web (Field-Tested)", "Desert Eagle | Kumicho Dragon (Field-Tested)",
    "Desert Eagle | Mecha Industries (Factory New)",
    "FAMAS | Commemoration (Field-Tested)", "FAMAS | Mecha Industries (Field-Tested)",
    "FAMAS | Survivor Z (Field-Tested)",
    "Five-SeveN | Case Hardened (Field-Tested)", "Five-SeveN | Copper Galaxy (Field-Tested)",
    "Galil AR | Cerberus (Field-Tested)", "Galil AR | Rocket Pop (Field-Tested)",
    "Gamma 2 Case",
    "Glock-18 | Candy Apple (Factory New)", "Glock-18 | Twilight Galaxy (Field-Tested)",
    "Glock-18 | Water Elemental (Field-Tested)",
    "Glove Case", "Horizon Case", "Huntsman Weapon Case",
    "M4A1-S | Bright Water (Field-Tested)", "M4A1-S | Cyrex (Field-Tested)",
    "M4A1-S | Golden Coil (Field-Tested)", "M4A1-S | Guardian (Field-Tested)",
    "M4A1-S | Hot Rod (Factory New)", "M4A1-S | Player Two (Field-Tested)",
    "M4A4 | Asiimov (Battle-Scarred)", "M4A4 | Buzz Kill (Field-Tested)",
    "M4A4 | Desolate Space (Field-Tested)", "M4A4 | Evil Daimyo (Field-Tested)",
    "M4A4 | Hellfire (Field-Tested)", "M4A4 | Royal Paladin (Field-Tested)",
    "M4A4 | The Emperor (Field-Tested)",
    "MAC-10 | Amber Fade (Field-Tested)", "MAC-10 | Disco Tech (Field-Tested)",
    "MAC-10 | Neon Rider (Field-Tested)",
    "MP7 | Asterion (Field-Tested)", "MP7 | Bloodsport (Field-Tested)",
    "MP9 | Bulldozer (Field-Tested)",
    "Nova | Candy Apple (Field-Tested)", "Nova | Hyper Beast (Field-Tested)",
    "Operation Breakout Weapon Case",
    "P2000 | Corticera (Field-Tested)", "P2000 | Fire Elemental (Field-Tested)",
    "P2000 | Imperial Dragon (Field-Tested)", "P2000 | Scorpion (Factory New)",
    "P250 | Asiimov (Field-Tested)", "P250 | Cartel (Field-Tested)",
    "P250 | Franklin (Field-Tested)", "P250 | Inferno (Field-Tested)",
    "P250 | Mehndi (Field-Tested)", "P250 | Muertos (Field-Tested)",
    "P250 | See Ya Later (Field-Tested)",
    "P90 | Asiimov (Field-Tested)", "P90 | Elite Build (Field-Tested)",
    "P90 | Emerald Dragon (Field-Tested)", "P90 | Sunset Lily (Field-Tested)",
    "PP-Bizon | Antique (Field-Tested)", "PP-Bizon | Chemical Green (Field-Tested)",
    "R8 Revolver | Blaze (Factory New)", "R8 Revolver | Crimson Web (Field-Tested)",
    "R8 Revolver | Fade (Field-Tested)", "R8 Revolver | Skull Crusher (Field-Tested)",
    "Sawed-Off | Kiss Love (Field-Tested)", "Sawed-Off | Origami (Field-Tested)",
    "Sawed-Off | The Kraken (Field-Tested)",
    "SCAR-20 | Bloodsport (Field-Tested)", "SCAR-20 | Crimson Web (Field-Tested)",
    "SCAR-20 | Cyrex (Field-Tested)",
    "SG 553 | Bulldozer (Factory New)", "SG 553 | Colony IV (Field-Tested)",
    "SG 553 | Cyrex (Field-Tested)", "SG 553 | Pulse (Field-Tested)",
    "SG 553 | Tornado (Field-Tested)",
    # Souvenirs
    "Souvenir AK-47 | Black Laminate (Field-Tested)",
    "Souvenir AWP | Pink DDPAT (Field-Tested)",
    "Souvenir Desert Eagle | Fennec Fox (Field-Tested)",
    "Souvenir FAMAS | Styx (Field-Tested)",
    "Souvenir Five-SeveN | Fall Hazard (Field-Tested)",
    "Souvenir Galil AR | Cerberus (Field-Tested)",
    "Souvenir Glock-18 | Candy Apple (Field-Tested)",
    "Souvenir Glock-18 | Night (Field-Tested)",
    "Souvenir Glock-18 | Reactor (Field-Tested)",
    "Souvenir M4A1-S | Master Piece (Field-Tested)",
    "Souvenir M4A4 | Mainframe (Field-Tested)",
    "Souvenir MP7 | Gunsmoke (Field-Tested)",
    "Souvenir P2000 | Grassland (Field-Tested)",
    "Souvenir P250 | Gunsmoke (Field-Tested)",
    "Souvenir SG 553 | Fallout Warning (Field-Tested)",
    "Souvenir Tec-9 | Groundwater (Field-Tested)",
    # SSG
    "SSG 08 | Big Iron (Field-Tested)", "SSG 08 | Blood in the Water (Field-Tested)",
    "SSG 08 | Dragonfire (Field-Tested)", "SSG 08 | Turbo Peek (Field-Tested)",
    # StatTrak
    "StatTrak AK-47 | Aquamarine Revenge (Field-Tested)", "StatTrak AK-47 | Bloodsport (Field-Tested)",
    "StatTrak AK-47 | Jaguar (Field-Tested)", "StatTrak AK-47 | Legion of Anubis (Field-Tested)",
    "StatTrak AK-47 | Wasteland Rebel (Field-Tested)", "StatTrak AUG | Chameleon (Field-Tested)",
    "StatTrak AWP | BOOM (Field-Tested)", "StatTrak AWP | Fever Dream (Field-Tested)",
    "StatTrak AWP | Redline (Field-Tested)",
    "StatTrak Desert Eagle | Kumicho Dragon (Field-Tested)", "StatTrak Desert Eagle | Printstream (Field-Tested)",
    "StatTrak FAMAS | Commemoration (Field-Tested)", "StatTrak FAMAS | Mecha Industries (Field-Tested)",
    "StatTrak Five-SeveN | Hyper Beast (Field-Tested)",
    "StatTrak Galil AR | Rocket Pop (Field-Tested)", "StatTrak Galil AR | Sugar Rush (Field-Tested)",
    "StatTrak Glock-18 | Bullet Queen (Field-Tested)", "StatTrak Glock-18 | Moonrise (Field-Tested)",
    "StatTrak M4A1-S | Decimator (Field-Tested)", "StatTrak M4A1-S | Guardian (Field-Tested)",
    "StatTrak M4A1-S | Player Two (Field-Tested)",
    "StatTrak M4A4 | Asiimov (Field-Tested)", "StatTrak M4A4 | In Living Color (Field-Tested)",
    "StatTrak M4A4 | Dragon King (Field-Tested)",
    "StatTrak MAC-10 | Heat (Field-Tested)", "StatTrak MAC-10 | Monkeyflage (Field-Tested)",
    "StatTrak MAG-7 | Heat (Field-Tested)", "StatTrak MAG-7 | Justice (Field-Tested)",
    "StatTrak MP7 | Bloodsport (Field-Tested)", "StatTrak MP7 | Impire (Field-Tested)",
    "StatTrak MP9 | Deadly Poison (Field-Tested)", "StatTrak MP9 | Food Chain (Field-Tested)",
    "StatTrak MP9 | Starlight Protector (Field-Tested)",
    "StatTrak Negev | Man-o-war (Field-Tested)",
    "StatTrak Nova | Hyper Beast (Field-Tested)",
    "StatTrak P250 | Cartel (Field-Tested)", "StatTrak P250 | Nevermore (Field-Tested)",
    "StatTrak P90 | Elite Build (Field-Tested)", "StatTrak P90 | Vent Rush (Field-Tested)",
    "StatTrak PP-Bizon | Judgement of Anubis (Field-Tested)",
    "StatTrak SCAR-20 | Cyrex (Field-Tested)",
    "StatTrak Tec-9 | Avalanche (Field-Tested)", "StatTrak Tec-9 | Decimator (Field-Tested)",
    "StatTrak Tec-9 | Fuel Injector (Field-Tested)",
    "StatTrak UMP-45 | Momentum (Field-Tested)",
    "StatTrak USP-S | Blueprint (Field-Tested)", "StatTrak USP-S | Orion (Field-Tested)",
    "StatTrak USP-S | The Traitor (Field-Tested)", "StatTrak USP-S | Ticket to Hell (Field-Tested)",
    # Stickers
    "Sticker | 3DMAX | Katowice 2014", "Sticker | 3DMAX | Katowice 2015",
    "Sticker | Astralis | Katowice 2019", "Sticker | BIG | Boston 2018",
    "Sticker | BIG | Katowice 2019", "Sticker | Bravado Gaming | DreamHack 2014",
    "Sticker | Clan-Mystik | Katowice 2014", "Sticker | Cloud9 | Cologne 2014",
    "Sticker | Cloud9 | DreamHack 2014", "Sticker | Cloud9 | Katowice 2019",
    "Sticker | Cloud9 G2A | Cologne 2015", "Sticker | compLexity Gaming | Katowice 2019",
    "Sticker | Copenhagen Wolves | Cologne 2014",
    "Sticker | Counter Logic Gaming (Foil) | Cologne 2015",
    "Sticker | Counter Logic Gaming | Katowice 2015",
    "Sticker | dAT team | Cologne 2014", "Sticker | ENCE | Katowice 2019",
    "Sticker | Epsilon eSports | Cologne 2014", "Sticker | FaZe Clan | Katowice 2019",
    "Sticker | FaZe Clan | MLG Columbus 2016",
    "Sticker | Flipsid3 Tactics | Cologne 2015", "Sticker | Flipsid3 Tactics | Katowice 2015",
    "Sticker | Flipsid3 Tactics | Krakow 2017",
    "Sticker | Fnatic | Boston 2018", "Sticker | Fnatic | Cologne 2014",
    "Sticker | Fnatic | Cologne 2015", "Sticker | Fnatic | DreamHack 2014",
    "Sticker | Fnatic | Katowice 2014", "Sticker | Fnatic | Katowice 2015",
    "Sticker | Fnatic | Krakow 2017",
    "Sticker | G2 Esports | Krakow 2017", "Sticker | Gambit | Krakow 2017",
    "Sticker | HellRaisers | DreamHack 2014", "Sticker | HellRaisers | Katowice 2014",
    "Sticker | HellRaisers | Katowice 2015",
    "Sticker | iBUYPOWER | Cologne 2014", "Sticker | Keyd Stars | Katowice 2015",
    "Sticker | mousesports | Katowice 2014", "Sticker | mousesports | Krakow 2017",
    "Sticker | Natus Vincere | Cologne 2014", "Sticker | Natus Vincere | DreamHack 2014",
    "Sticker | Natus Vincere | Katowice 2014", "Sticker | Natus Vincere | Katowice 2015",
    "Sticker | Natus Vincere | Krakow 2017", "Sticker | Natus Vincere | MLG Columbus 2016",
    "Sticker | Ninjas in Pyjamas | Cologne 2014", "Sticker | Ninjas in Pyjamas | Cologne 2015",
    "Sticker | Ninjas in Pyjamas | DreamHack 2014", "Sticker | Ninjas in Pyjamas | Katowice 2014",
    "Sticker | Ninjas in Pyjamas | MLG Columbus 2016",
    "Sticker | PENTA Sports | Katowice 2015", "Sticker | PENTA Sports | Krakow 2017",
    "Sticker | Splyce | MLG Columbus 2016", "Sticker | Team Dignitas | DreamHack 2014",
    "Sticker | Team EnVyUs | Cologne 2015",
    "Sticker | Tyloo | Boston 2018",
    "Sticker | Virtus.Pro | Boston 2018", "Sticker | Virtus.Pro | Katowice 2014",
    "Sticker | Virtus.pro | Katowice 2015",
    # Remaining weapons
    "Tec-9 | Decimator (Field-Tested)", "Tec-9 | Fuel Injector (Field-Tested)",
    "Tec-9 | Remote Control (Field-Tested)", "UMP-45 | Blaze (Factory New)",
    "USP-S | Black Lotus (Field-Tested)", "USP-S | Kill Confirmed (Field-Tested)",
    "USP-S | Monster Mashup (Field-Tested)", "USP-S | Neo-Noir (Field-Tested)",
    "USP-S | Orion (Field-Tested)", "USP-S | The Traitor (Field-Tested)",
    "XM1014 | Fallout Warning (Field-Tested)", "XM1014 | Oxide Blaze (Field-Tested)",
    "XM1014 | XOXO (Field-Tested)",
]


def normalize(name):
    """Normalize EF300 name to match our data format."""
    n = name.strip()
    n = n.replace("\u2605 ", "")  # ★
    n = n.replace("StatTrak\u2122 ", "ST ").replace("StatTrak ", "ST ")
    n = n.replace(" | ", " - ")
    n = n.replace("\u2665", "")  # ♥
    return n


def main():
    print(f"EF300 raw items: {len(EF300_RAW)}")

    with open(ROOT / "data" / "precomputed" / "frontier.json") as f:
        our_items = json.load(f)["items"]

    # Build normalized lookup
    norm_lookup = {}
    for item_name in our_items:
        norm_lookup[normalize(item_name).lower()] = item_name

    matched = []
    unmatched = []
    for ef_name in EF300_RAW:
        norm = normalize(ef_name).lower()
        if norm in norm_lookup:
            matched.append(norm_lookup[norm])
        else:
            # Try fuzzy: strip "Case" suffix, check partial
            found = False
            for norm_key, item_name in norm_lookup.items():
                if norm in norm_key or norm_key in norm:
                    matched.append(item_name)
                    found = True
                    break
            if not found:
                unmatched.append(ef_name)

    print(f"Matched: {len(matched)}/{len(EF300_RAW)}")
    print(f"Unmatched: {len(unmatched)}")
    for u in unmatched:
        print(f"  {u}")

    output = {
        "name": "EsportFire 300",
        "description": f"300 hand-selected liquid CS2 items ({len(matched)} matched to our data)",
        "source": "https://esportfire.com/article/introducing-the-esportfire300-index",
        "items": matched
    }
    out_file = ROOT / "data" / "esportfire300.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=1)
    print(f"\nSaved {len(matched)} items to {out_file}")


if __name__ == "__main__":
    main()
