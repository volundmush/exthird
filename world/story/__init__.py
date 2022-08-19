ATTRIBUTES = ["Strength", "Dexterity", "Stamina", "Charisma", "Manipulation", "Appearance", "Perception",
              "Intelligence", "Wits"]


ATTRIBUTES_PSM = {
    "physical": ["Strength", "Dexterity", "Stamina"],
    "social": ["Charisma", "Manipulation", "Appearance"],
    "mental": ["Perception", "Intelligence", "Wits"]
}


ABILITIES = ["Archery", "Athletics", "Awareness", "Brawl", "Bureaucracy", "Craft", "Dodge", "Integrity",
             "Investigation", "Larceny", "Linguistics", "Lore", "Martial Arts", "Medicine", "Melee", "Occult",
             "Performance", "Presence", "Resistance", "Ride", "Sail", "Socialize", "Stealth", "Survival", "Thrown",
             "War"]


MA_STYLES = ["Snake", "Tiger", "Single Point Shining Into the Void", "White Reaper", "Ebon Shadow", "Crane",
             "Silver-Voiced Nightingale", "Righteous Devil", "Black Claw", "Steel Devil", "Dreaming Pearl Courtesan",
             "Air Dragon", "Earth Dragon", "Fire Dragon", "Water Dragon", "Wood Dragon", "Golden Janissary", "Mantis",
             "White Veil", "Centipede", "Falcon", "Laughing Monster", "Swaying Grass Dance"]


CHARM_CATEGORIES = {
    "Solar": ABILITIES,
    "Abyssal": ABILITIES,
    "Lunar": ATTRIBUTES + ["Universal"],
    "Dragon-Blooded": ABILITIES,
    "Martial Arts": MA_STYLES
}

