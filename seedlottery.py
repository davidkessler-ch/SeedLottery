#!/usr/bin/env python3
"""
SeedLottery - draw a Bitcoin seed phrase by lot, with 3D-printed tokens for all
2048 BIP39 words.

Each token carries the first four letters of one BIP39 word on one face and of
another word on the other face (four letters are unique across the list), so 1024
tokens cover every word once. Both faces are identical: flat, with the letters
engraved. The tokens are laid out in sheets that fill a printer's bed and are
joined by small breakaway tabs, so a sheet prints as one object and can be
checked against its word map before the tokens are snapped apart.

For every sheet the script writes an OpenSCAD model and a word map. With --stl it
renders the model for any printer; with --gcode it also makes a PrusaSlicer project
(.3mf) with all print settings and the print file (.bgcode) sliced from it.

Examples:
    python3 seedlottery.py --gcode                   # the full set: 4 sheets for a MK4S
    python3 seedlottery.py --bed 220x220 --stl       # the full set for any printer, as STL
    python3 seedlottery.py --first-word average --columns 4 --rows 2 --gcode   # a small test sheet
"""

from __future__ import annotations

import argparse
import glob
import math
import random
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

TITLE = "SeedLottery"   # project name, used in file headers
NAME = "seedlottery"    # prefix of every generated file


BIP39_WORDS = [
    "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd",
    "abuse", "access", "accident", "account", "accuse", "achieve", "acid", "acoustic",
    "acquire", "across", "act", "action", "actor", "actress", "actual", "adapt", "add",
    "addict", "address", "adjust", "admit", "adult", "advance", "advice", "aerobic", "affair",
    "afford", "afraid", "again", "age", "agent", "agree", "ahead", "aim", "air", "airport",
    "aisle", "alarm", "album", "alcohol", "alert", "alien", "all", "alley", "allow", "almost",
    "alone", "alpha", "already", "also", "alter", "always", "amateur", "amazing", "among",
    "amount", "amused", "analyst", "anchor", "ancient", "anger", "angle", "angry", "animal",
    "ankle", "announce", "annual", "another", "answer", "antenna", "antique", "anxiety", "any",
    "apart", "apology", "appear", "apple", "approve", "april", "arch", "arctic", "area",
    "arena", "argue", "arm", "armed", "armor", "army", "around", "arrange", "arrest", "arrive",
    "arrow", "art", "artefact", "artist", "artwork", "ask", "aspect", "assault", "asset",
    "assist", "assume", "asthma", "athlete", "atom", "attack", "attend", "attitude", "attract",
    "auction", "audit", "august", "aunt", "author", "auto", "autumn", "average", "avocado",
    "avoid", "awake", "aware", "away", "awesome", "awful", "awkward", "axis", "baby",
    "bachelor", "bacon", "badge", "bag", "balance", "balcony", "ball", "bamboo", "banana",
    "banner", "bar", "barely", "bargain", "barrel", "base", "basic", "basket", "battle",
    "beach", "bean", "beauty", "because", "become", "beef", "before", "begin", "behave",
    "behind", "believe", "below", "belt", "bench", "benefit", "best", "betray", "better",
    "between", "beyond", "bicycle", "bid", "bike", "bind", "biology", "bird", "birth", "bitter",
    "black", "blade", "blame", "blanket", "blast", "bleak", "bless", "blind", "blood",
    "blossom", "blouse", "blue", "blur", "blush", "board", "boat", "body", "boil", "bomb",
    "bone", "bonus", "book", "boost", "border", "boring", "borrow", "boss", "bottom", "bounce",
    "box", "boy", "bracket", "brain", "brand", "brass", "brave", "bread", "breeze", "brick",
    "bridge", "brief", "bright", "bring", "brisk", "broccoli", "broken", "bronze", "broom",
    "brother", "brown", "brush", "bubble", "buddy", "budget", "buffalo", "build", "bulb",
    "bulk", "bullet", "bundle", "bunker", "burden", "burger", "burst", "bus", "business",
    "busy", "butter", "buyer", "buzz", "cabbage", "cabin", "cable", "cactus", "cage", "cake",
    "call", "calm", "camera", "camp", "can", "canal", "cancel", "candy", "cannon", "canoe",
    "canvas", "canyon", "capable", "capital", "captain", "car", "carbon", "card", "cargo",
    "carpet", "carry", "cart", "case", "cash", "casino", "castle", "casual", "cat", "catalog",
    "catch", "category", "cattle", "caught", "cause", "caution", "cave", "ceiling", "celery",
    "cement", "census", "century", "cereal", "certain", "chair", "chalk", "champion", "change",
    "chaos", "chapter", "charge", "chase", "chat", "cheap", "check", "cheese", "chef", "cherry",
    "chest", "chicken", "chief", "child", "chimney", "choice", "choose", "chronic", "chuckle",
    "chunk", "churn", "cigar", "cinnamon", "circle", "citizen", "city", "civil", "claim",
    "clap", "clarify", "claw", "clay", "clean", "clerk", "clever", "click", "client", "cliff",
    "climb", "clinic", "clip", "clock", "clog", "close", "cloth", "cloud", "clown", "club",
    "clump", "cluster", "clutch", "coach", "coast", "coconut", "code", "coffee", "coil", "coin",
    "collect", "color", "column", "combine", "come", "comfort", "comic", "common", "company",
    "concert", "conduct", "confirm", "congress", "connect", "consider", "control", "convince",
    "cook", "cool", "copper", "copy", "coral", "core", "corn", "correct", "cost", "cotton",
    "couch", "country", "couple", "course", "cousin", "cover", "coyote", "crack", "cradle",
    "craft", "cram", "crane", "crash", "crater", "crawl", "crazy", "cream", "credit", "creek",
    "crew", "cricket", "crime", "crisp", "critic", "crop", "cross", "crouch", "crowd",
    "crucial", "cruel", "cruise", "crumble", "crunch", "crush", "cry", "crystal", "cube",
    "culture", "cup", "cupboard", "curious", "current", "curtain", "curve", "cushion", "custom",
    "cute", "cycle", "dad", "damage", "damp", "dance", "danger", "daring", "dash", "daughter",
    "dawn", "day", "deal", "debate", "debris", "decade", "december", "decide", "decline",
    "decorate", "decrease", "deer", "defense", "define", "defy", "degree", "delay", "deliver",
    "demand", "demise", "denial", "dentist", "deny", "depart", "depend", "deposit", "depth",
    "deputy", "derive", "describe", "desert", "design", "desk", "despair", "destroy", "detail",
    "detect", "develop", "device", "devote", "diagram", "dial", "diamond", "diary", "dice",
    "diesel", "diet", "differ", "digital", "dignity", "dilemma", "dinner", "dinosaur", "direct",
    "dirt", "disagree", "discover", "disease", "dish", "dismiss", "disorder", "display",
    "distance", "divert", "divide", "divorce", "dizzy", "doctor", "document", "dog", "doll",
    "dolphin", "domain", "donate", "donkey", "donor", "door", "dose", "double", "dove", "draft",
    "dragon", "drama", "drastic", "draw", "dream", "dress", "drift", "drill", "drink", "drip",
    "drive", "drop", "drum", "dry", "duck", "dumb", "dune", "during", "dust", "dutch", "duty",
    "dwarf", "dynamic", "eager", "eagle", "early", "earn", "earth", "easily", "east", "easy",
    "echo", "ecology", "economy", "edge", "edit", "educate", "effort", "egg", "eight", "either",
    "elbow", "elder", "electric", "elegant", "element", "elephant", "elevator", "elite", "else",
    "embark", "embody", "embrace", "emerge", "emotion", "employ", "empower", "empty", "enable",
    "enact", "end", "endless", "endorse", "enemy", "energy", "enforce", "engage", "engine",
    "enhance", "enjoy", "enlist", "enough", "enrich", "enroll", "ensure", "enter", "entire",
    "entry", "envelope", "episode", "equal", "equip", "era", "erase", "erode", "erosion",
    "error", "erupt", "escape", "essay", "essence", "estate", "eternal", "ethics", "evidence",
    "evil", "evoke", "evolve", "exact", "example", "excess", "exchange", "excite", "exclude",
    "excuse", "execute", "exercise", "exhaust", "exhibit", "exile", "exist", "exit", "exotic",
    "expand", "expect", "expire", "explain", "expose", "express", "extend", "extra", "eye",
    "eyebrow", "fabric", "face", "faculty", "fade", "faint", "faith", "fall", "false", "fame",
    "family", "famous", "fan", "fancy", "fantasy", "farm", "fashion", "fat", "fatal", "father",
    "fatigue", "fault", "favorite", "feature", "february", "federal", "fee", "feed", "feel",
    "female", "fence", "festival", "fetch", "fever", "few", "fiber", "fiction", "field",
    "figure", "file", "film", "filter", "final", "find", "fine", "finger", "finish", "fire",
    "firm", "first", "fiscal", "fish", "fit", "fitness", "fix", "flag", "flame", "flash",
    "flat", "flavor", "flee", "flight", "flip", "float", "flock", "floor", "flower", "fluid",
    "flush", "fly", "foam", "focus", "fog", "foil", "fold", "follow", "food", "foot", "force",
    "forest", "forget", "fork", "fortune", "forum", "forward", "fossil", "foster", "found",
    "fox", "fragile", "frame", "frequent", "fresh", "friend", "fringe", "frog", "front",
    "frost", "frown", "frozen", "fruit", "fuel", "fun", "funny", "furnace", "fury", "future",
    "gadget", "gain", "galaxy", "gallery", "game", "gap", "garage", "garbage", "garden",
    "garlic", "garment", "gas", "gasp", "gate", "gather", "gauge", "gaze", "general", "genius",
    "genre", "gentle", "genuine", "gesture", "ghost", "giant", "gift", "giggle", "ginger",
    "giraffe", "girl", "give", "glad", "glance", "glare", "glass", "glide", "glimpse", "globe",
    "gloom", "glory", "glove", "glow", "glue", "goat", "goddess", "gold", "good", "goose",
    "gorilla", "gospel", "gossip", "govern", "gown", "grab", "grace", "grain", "grant", "grape",
    "grass", "gravity", "great", "green", "grid", "grief", "grit", "grocery", "group", "grow",
    "grunt", "guard", "guess", "guide", "guilt", "guitar", "gun", "gym", "habit", "hair",
    "half", "hammer", "hamster", "hand", "happy", "harbor", "hard", "harsh", "harvest", "hat",
    "have", "hawk", "hazard", "head", "health", "heart", "heavy", "hedgehog", "height", "hello",
    "helmet", "help", "hen", "hero", "hidden", "high", "hill", "hint", "hip", "hire", "history",
    "hobby", "hockey", "hold", "hole", "holiday", "hollow", "home", "honey", "hood", "hope",
    "horn", "horror", "horse", "hospital", "host", "hotel", "hour", "hover", "hub", "huge",
    "human", "humble", "humor", "hundred", "hungry", "hunt", "hurdle", "hurry", "hurt",
    "husband", "hybrid", "ice", "icon", "idea", "identify", "idle", "ignore", "ill", "illegal",
    "illness", "image", "imitate", "immense", "immune", "impact", "impose", "improve",
    "impulse", "inch", "include", "income", "increase", "index", "indicate", "indoor",
    "industry", "infant", "inflict", "inform", "inhale", "inherit", "initial", "inject",
    "injury", "inmate", "inner", "innocent", "input", "inquiry", "insane", "insect", "inside",
    "inspire", "install", "intact", "interest", "into", "invest", "invite", "involve", "iron",
    "island", "isolate", "issue", "item", "ivory", "jacket", "jaguar", "jar", "jazz", "jealous",
    "jeans", "jelly", "jewel", "job", "join", "joke", "journey", "joy", "judge", "juice",
    "jump", "jungle", "junior", "junk", "just", "kangaroo", "keen", "keep", "ketchup", "key",
    "kick", "kid", "kidney", "kind", "kingdom", "kiss", "kit", "kitchen", "kite", "kitten",
    "kiwi", "knee", "knife", "knock", "know", "lab", "label", "labor", "ladder", "lady", "lake",
    "lamp", "language", "laptop", "large", "later", "latin", "laugh", "laundry", "lava", "law",
    "lawn", "lawsuit", "layer", "lazy", "leader", "leaf", "learn", "leave", "lecture", "left",
    "leg", "legal", "legend", "leisure", "lemon", "lend", "length", "lens", "leopard", "lesson",
    "letter", "level", "liar", "liberty", "library", "license", "life", "lift", "light", "like",
    "limb", "limit", "link", "lion", "liquid", "list", "little", "live", "lizard", "load",
    "loan", "lobster", "local", "lock", "logic", "lonely", "long", "loop", "lottery", "loud",
    "lounge", "love", "loyal", "lucky", "luggage", "lumber", "lunar", "lunch", "luxury",
    "lyrics", "machine", "mad", "magic", "magnet", "maid", "mail", "main", "major", "make",
    "mammal", "man", "manage", "mandate", "mango", "mansion", "manual", "maple", "marble",
    "march", "margin", "marine", "market", "marriage", "mask", "mass", "master", "match",
    "material", "math", "matrix", "matter", "maximum", "maze", "meadow", "mean", "measure",
    "meat", "mechanic", "medal", "media", "melody", "melt", "member", "memory", "mention",
    "menu", "mercy", "merge", "merit", "merry", "mesh", "message", "metal", "method", "middle",
    "midnight", "milk", "million", "mimic", "mind", "minimum", "minor", "minute", "miracle",
    "mirror", "misery", "miss", "mistake", "mix", "mixed", "mixture", "mobile", "model",
    "modify", "mom", "moment", "monitor", "monkey", "monster", "month", "moon", "moral", "more",
    "morning", "mosquito", "mother", "motion", "motor", "mountain", "mouse", "move", "movie",
    "much", "muffin", "mule", "multiply", "muscle", "museum", "mushroom", "music", "must",
    "mutual", "myself", "mystery", "myth", "naive", "name", "napkin", "narrow", "nasty",
    "nation", "nature", "near", "neck", "need", "negative", "neglect", "neither", "nephew",
    "nerve", "nest", "net", "network", "neutral", "never", "news", "next", "nice", "night",
    "noble", "noise", "nominee", "noodle", "normal", "north", "nose", "notable", "note",
    "nothing", "notice", "novel", "now", "nuclear", "number", "nurse", "nut", "oak", "obey",
    "object", "oblige", "obscure", "observe", "obtain", "obvious", "occur", "ocean", "october",
    "odor", "off", "offer", "office", "often", "oil", "okay", "old", "olive", "olympic", "omit",
    "once", "one", "onion", "online", "only", "open", "opera", "opinion", "oppose", "option",
    "orange", "orbit", "orchard", "order", "ordinary", "organ", "orient", "original", "orphan",
    "ostrich", "other", "outdoor", "outer", "output", "outside", "oval", "oven", "over", "own",
    "owner", "oxygen", "oyster", "ozone", "pact", "paddle", "page", "pair", "palace", "palm",
    "panda", "panel", "panic", "panther", "paper", "parade", "parent", "park", "parrot",
    "party", "pass", "patch", "path", "patient", "patrol", "pattern", "pause", "pave",
    "payment", "peace", "peanut", "pear", "peasant", "pelican", "pen", "penalty", "pencil",
    "people", "pepper", "perfect", "permit", "person", "pet", "phone", "photo", "phrase",
    "physical", "piano", "picnic", "picture", "piece", "pig", "pigeon", "pill", "pilot", "pink",
    "pioneer", "pipe", "pistol", "pitch", "pizza", "place", "planet", "plastic", "plate",
    "play", "please", "pledge", "pluck", "plug", "plunge", "poem", "poet", "point", "polar",
    "pole", "police", "pond", "pony", "pool", "popular", "portion", "position", "possible",
    "post", "potato", "pottery", "poverty", "powder", "power", "practice", "praise", "predict",
    "prefer", "prepare", "present", "pretty", "prevent", "price", "pride", "primary", "print",
    "priority", "prison", "private", "prize", "problem", "process", "produce", "profit",
    "program", "project", "promote", "proof", "property", "prosper", "protect", "proud",
    "provide", "public", "pudding", "pull", "pulp", "pulse", "pumpkin", "punch", "pupil",
    "puppy", "purchase", "purity", "purpose", "purse", "push", "put", "puzzle", "pyramid",
    "quality", "quantum", "quarter", "question", "quick", "quit", "quiz", "quote", "rabbit",
    "raccoon", "race", "rack", "radar", "radio", "rail", "rain", "raise", "rally", "ramp",
    "ranch", "random", "range", "rapid", "rare", "rate", "rather", "raven", "raw", "razor",
    "ready", "real", "reason", "rebel", "rebuild", "recall", "receive", "recipe", "record",
    "recycle", "reduce", "reflect", "reform", "refuse", "region", "regret", "regular", "reject",
    "relax", "release", "relief", "rely", "remain", "remember", "remind", "remove", "render",
    "renew", "rent", "reopen", "repair", "repeat", "replace", "report", "require", "rescue",
    "resemble", "resist", "resource", "response", "result", "retire", "retreat", "return",
    "reunion", "reveal", "review", "reward", "rhythm", "rib", "ribbon", "rice", "rich", "ride",
    "ridge", "rifle", "right", "rigid", "ring", "riot", "ripple", "risk", "ritual", "rival",
    "river", "road", "roast", "robot", "robust", "rocket", "romance", "roof", "rookie", "room",
    "rose", "rotate", "rough", "round", "route", "royal", "rubber", "rude", "rug", "rule",
    "run", "runway", "rural", "sad", "saddle", "sadness", "safe", "sail", "salad", "salmon",
    "salon", "salt", "salute", "same", "sample", "sand", "satisfy", "satoshi", "sauce",
    "sausage", "save", "say", "scale", "scan", "scare", "scatter", "scene", "scheme", "school",
    "science", "scissors", "scorpion", "scout", "scrap", "screen", "script", "scrub", "sea",
    "search", "season", "seat", "second", "secret", "section", "security", "seed", "seek",
    "segment", "select", "sell", "seminar", "senior", "sense", "sentence", "series", "service",
    "session", "settle", "setup", "seven", "shadow", "shaft", "shallow", "share", "shed",
    "shell", "sheriff", "shield", "shift", "shine", "ship", "shiver", "shock", "shoe", "shoot",
    "shop", "short", "shoulder", "shove", "shrimp", "shrug", "shuffle", "shy", "sibling",
    "sick", "side", "siege", "sight", "sign", "silent", "silk", "silly", "silver", "similar",
    "simple", "since", "sing", "siren", "sister", "situate", "six", "size", "skate", "sketch",
    "ski", "skill", "skin", "skirt", "skull", "slab", "slam", "sleep", "slender", "slice",
    "slide", "slight", "slim", "slogan", "slot", "slow", "slush", "small", "smart", "smile",
    "smoke", "smooth", "snack", "snake", "snap", "sniff", "snow", "soap", "soccer", "social",
    "sock", "soda", "soft", "solar", "soldier", "solid", "solution", "solve", "someone", "song",
    "soon", "sorry", "sort", "soul", "sound", "soup", "source", "south", "space", "spare",
    "spatial", "spawn", "speak", "special", "speed", "spell", "spend", "sphere", "spice",
    "spider", "spike", "spin", "spirit", "split", "spoil", "sponsor", "spoon", "sport", "spot",
    "spray", "spread", "spring", "spy", "square", "squeeze", "squirrel", "stable", "stadium",
    "staff", "stage", "stairs", "stamp", "stand", "start", "state", "stay", "steak", "steel",
    "stem", "step", "stereo", "stick", "still", "sting", "stock", "stomach", "stone", "stool",
    "story", "stove", "strategy", "street", "strike", "strong", "struggle", "student", "stuff",
    "stumble", "style", "subject", "submit", "subway", "success", "such", "sudden", "suffer",
    "sugar", "suggest", "suit", "summer", "sun", "sunny", "sunset", "super", "supply",
    "supreme", "sure", "surface", "surge", "surprise", "surround", "survey", "suspect",
    "sustain", "swallow", "swamp", "swap", "swarm", "swear", "sweet", "swift", "swim", "swing",
    "switch", "sword", "symbol", "symptom", "syrup", "system", "table", "tackle", "tag", "tail",
    "talent", "talk", "tank", "tape", "target", "task", "taste", "tattoo", "taxi", "teach",
    "team", "tell", "ten", "tenant", "tennis", "tent", "term", "test", "text", "thank", "that",
    "theme", "then", "theory", "there", "they", "thing", "this", "thought", "three", "thrive",
    "throw", "thumb", "thunder", "ticket", "tide", "tiger", "tilt", "timber", "time", "tiny",
    "tip", "tired", "tissue", "title", "toast", "tobacco", "today", "toddler", "toe",
    "together", "toilet", "token", "tomato", "tomorrow", "tone", "tongue", "tonight", "tool",
    "tooth", "top", "topic", "topple", "torch", "tornado", "tortoise", "toss", "total",
    "tourist", "toward", "tower", "town", "toy", "track", "trade", "traffic", "tragic", "train",
    "transfer", "trap", "trash", "travel", "tray", "treat", "tree", "trend", "trial", "tribe",
    "trick", "trigger", "trim", "trip", "trophy", "trouble", "truck", "true", "truly",
    "trumpet", "trust", "truth", "try", "tube", "tuition", "tumble", "tuna", "tunnel", "turkey",
    "turn", "turtle", "twelve", "twenty", "twice", "twin", "twist", "two", "type", "typical",
    "ugly", "umbrella", "unable", "unaware", "uncle", "uncover", "under", "undo", "unfair",
    "unfold", "unhappy", "uniform", "unique", "unit", "universe", "unknown", "unlock", "until",
    "unusual", "unveil", "update", "upgrade", "uphold", "upon", "upper", "upset", "urban",
    "urge", "usage", "use", "used", "useful", "useless", "usual", "utility", "vacant", "vacuum",
    "vague", "valid", "valley", "valve", "van", "vanish", "vapor", "various", "vast", "vault",
    "vehicle", "velvet", "vendor", "venture", "venue", "verb", "verify", "version", "very",
    "vessel", "veteran", "viable", "vibrant", "vicious", "victory", "video", "view", "village",
    "vintage", "violin", "virtual", "virus", "visa", "visit", "visual", "vital", "vivid",
    "vocal", "voice", "void", "volcano", "volume", "vote", "voyage", "wage", "wagon", "wait",
    "walk", "wall", "walnut", "want", "warfare", "warm", "warrior", "wash", "wasp", "waste",
    "water", "wave", "way", "wealth", "weapon", "wear", "weasel", "weather", "web", "wedding",
    "weekend", "weird", "welcome", "west", "wet", "whale", "what", "wheat", "wheel", "when",
    "where", "whip", "whisper", "wide", "width", "wife", "wild", "will", "win", "window",
    "wine", "wing", "wink", "winner", "winter", "wire", "wisdom", "wise", "wish", "witness",
    "wolf", "woman", "wonder", "wood", "wool", "word", "work", "world", "worry", "worth",
    "wrap", "wreck", "wrestle", "wrist", "write", "wrong", "yard", "year", "yellow", "you",
    "young", "youth", "zebra", "zero", "zone", "zoo",
]

# Printable area (X x Y, mm) of Prusa printers, and the PrusaSlicer system presets
# (printer, print, filament) that --gcode uses for them. Only the MK4S presets
# have been tested; for the other printers pass --slicer-printer/-print/-filament.
PRINTERS = {
    "mk4s": ("Original Prusa MK4S", 250, 210,
             ("Original Prusa MK4S HF0.4 nozzle", "0.20mm SPEED @MK4S HF0.4", "Prusa PLA @MK4S HF0.4")),
    "mk4": ("Original Prusa MK4 / MK3.9", 250, 210, None),
    "mk3s": ("Original Prusa MK3S / MK3S+", 250, 210, None),
    "core-one": ("Prusa CORE One", 250, 220, None),
    "mini": ("Original Prusa MINI / MINI+", 180, 180, None),
    "xl": ("Original Prusa XL", 360, 360, None),
}

# Token geometry (mm). Heights are snapped to the layer grid before they are used.
TOKEN_LENGTH = 18.5
TOKEN_WIDTH = 7.5
TOKEN_HEIGHT = 3.0
RIM = 0.8            # minimum wall between the lettering and the edge (0.4 mm left on the first layer)
TEXT_DEPTH = 0.6     # both faces are flat with the words engraved this deep
TAB_WIDTH = 0.8      # two lines with a 0.4 mm nozzle
TAB_HEIGHT = 0.6     # one tab per joint, centred on the mid-plane, so the nubs don't mark a face
TAB_OVERLAP = 0.6    # how far a tab reaches into each token's rim

# Lettering is the same size on every token, so 3-letter words are simply narrower.
# Letters are placed one by one by their actual outlines, with a fixed gap between
# them at every point, instead of by the font's own spacing: engraved, the token
# material between two letters is a wall, and with the font's spacing it was
# 0.19 mm (median) or nothing at all, so neighbouring letters melted together.
# 1 mm leaves two printed lines, and still 0.6 mm on the first layer after
# elephant-foot compensation widens the grooves. Unless --text-size is given, the
# letters get the largest size at which every word fits inside the rim (3.25 mm
# for Fredoka Medium). Medium keeps the insides of the letters open, where Bold's close.
LETTER_GAP = 1.0
DEFAULT_FONT = "Fredoka:style=Medium"
OUTLINE_STEP = 0.025  # height step at which letter outlines are measured (mm)

# Output folders inside --out-dir, one per file type.
FOLDERS = {
    ".bgcode": "print",          # print files: copy these to the printer
    ".3mf": "prusaslicer",       # PrusaSlicer projects with every setting
    "_map.txt": "maps",          # both faces of each sheet, to check the print against
    ".scad": "openscad",         # OpenSCAD models
    ".stl": "stl",               # rendered meshes
}


def output_path(out_dir: str, name: str, kind: str) -> str:
    """Where a sheet's file of this kind goes, e.g. sheets/print/<name>.bgcode."""
    folder = os.path.join(out_dir, FOLDERS[kind])
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, name + kind)


def sheet_name(path: str) -> str:
    """The sheet name shared by all of its files."""
    base = os.path.basename(path)
    return next(base[:-len(kind)] for kind in FOLDERS if base.endswith(kind))

# Added to the PrusaSlicer presets. With two perimeters, the first layer is a maze
# of loops around every engraved letter, only 78% of it at the nominal line width,
# and prints rough. One perimeter and a slow, slightly narrower first layer leave
# straight infill between single outlines: 98% at nominal width, on both faces.
SLICER_OVERRIDES = ["--perimeters", "1", "--first-layer-speed", "20", "--first-layer-extrusion-width", "0.45"]


@dataclass
class Token:
    col: int
    row: int
    front: int          # 1-based BIP39 word number
    back: int


@dataclass
class Sheet:
    number: int
    first: int
    last: int
    columns: int
    rows: int
    tokens: list[Token]
    flipped: bool = False   # True when the second half of the words is on top
    name: str = ""


def word_number(value: str) -> int:
    """Accept a 1-based word number, a full BIP39 word or its unique 4-letter prefix."""
    if value.isdigit():
        number = int(value)
        if not 1 <= number <= len(BIP39_WORDS):
            raise argparse.ArgumentTypeError(f"word number must be 1-{len(BIP39_WORDS)}")
        return number
    value = value.lower()
    for number, word in enumerate(BIP39_WORDS, start=1):
        if word == value or (len(value) >= 4 and word.startswith(value)):
            return number
    raise argparse.ArgumentTypeError(f"'{value}' is not a BIP39 word")


def label(number: int) -> str:
    return BIP39_WORDS[number - 1][:4].upper()


def fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


# --- Layout -------------------------------------------------------------------

def fits(pitch: float, gap: float, space: float) -> int:
    """How many tokens of the given pitch fit into `space` mm."""
    return max(0, math.floor((space + gap) / pitch + 1e-9))


def plan_sheets(first: int, last: int, max_cols: int, max_rows: int, fixed_grid: bool,
                rng: random.Random) -> list[Sheet]:
    """Split words first..last into sheets of consecutive words. Each sheet puts one
    half of its words on top and the other half underneath; chance decides which
    half faces the bed, separately for every sheet."""
    token_count = (last - first + 1) // 2
    capacity = max_cols * max_rows
    sheet_count = math.ceil(token_count / capacity)

    if fixed_grid:
        sizes = [capacity] * (token_count // capacity)
        if token_count % capacity:
            sizes.append(token_count % capacity)
        columns = max_cols
    else:
        # Spread the tokens evenly so every sheet prints in about the same time,
        # and use the most compact grid for the largest sheet.
        base, extra = divmod(token_count, sheet_count)
        sizes = [base + 1] * extra + [base] * (sheet_count - extra)
        rows = math.ceil(sizes[0] / max_cols)
        columns = math.ceil(sizes[0] / rows)

    sheets = []
    start = first
    for number, size in enumerate(sizes, start=1):
        # The face printed on the bed comes out with a slightly different finish than
        # the top face. Choosing at random which half faces the bed keeps that finish
        # from systematically marking one half of the list.
        flipped = rng.random() < 0.5
        top_start, under_start = (start + size, start) if flipped else (start, start + size)
        tokens = []
        for index in range(size):
            row, col = divmod(index, columns)
            row_length = min(columns, size - row * columns)
            # The sheet is turned over left-to-right, so the underside of each row
            # reads in order when its words run right-to-left on the model.
            back_index = row * columns + (row_length - 1 - col)
            tokens.append(Token(col, row, top_start + index, under_start + back_index))
        sheets.append(Sheet(number, start, start + 2 * size - 1, columns,
                            math.ceil(size / columns), tokens, flipped))
        start += 2 * size
    return sheets


class LayerGrid:
    """Snap heights to the layers the slicer will actually print."""

    def __init__(self, layer_height: float, first_layer_height: float):
        self.layer = layer_height
        self.first = first_layer_height

    def snap(self, z: float) -> float:
        layers = max(0, round((z - self.first) / self.layer))
        return round(self.first + layers * self.layer, 4)


# --- Lettering ----------------------------------------------------------------

def glyph_outlines(openscad: str, args) -> dict[str, list[list[tuple[float, float]]]]:
    """Outline rings of every letter in the labels at text size 1, from an SVG export by OpenSCAD."""
    letters = sorted({c for word in BIP39_WORDS for c in word[:4].upper()} | {"H"})
    size, pitch = 10, 30   # export at size 10, 30 mm apart, so each ring belongs to one letter
    lines = [f'use <{os.path.abspath(args.font_file)}>'] if args.font_file else []
    lines += [f'translate([{i * pitch}, 0]) text("{c}", size = {size}, font = "{args.font}");'
              for i, c in enumerate(letters)]
    with tempfile.TemporaryDirectory(prefix=f"{NAME}-") as workdir:
        scad, svg = os.path.join(workdir, "letters.scad"), os.path.join(workdir, "letters.svg")
        with open(scad, "w") as f:
            f.write("\n".join(lines))
        subprocess.run([openscad, "-o", svg, scad], capture_output=True, text=True)
        paths = " ".join(re.findall(r' d="([^"]+)"', open(svg).read())) if os.path.isfile(svg) else ""
    outlines = {c: [] for c in letters}
    for ring in re.findall(r"M([^Mz]+)z", paths):
        points = [tuple(map(float, xy.split(","))) for xy in re.findall(r"-?[\d.]+,-?[\d.]+", ring)]
        if len(points) < 3:
            continue
        index = math.floor((min(x for x, _ in points) + pitch / 3) / pitch)
        # SVG y points down; scale to text size 1.
        outlines[letters[index]].append([((x - index * pitch) / size, -y / size) for x, y in points])
    if not all(outlines.values()):
        raise RuntimeError(f"could not get the letter outlines of '{args.font}' from OpenSCAD")
    return outlines


class Lettering:
    """Places the letters of a word by their outlines: a fixed gap between neighbours at
    every point, the word centred on the token. Outlines are measured as the leftmost and
    rightmost ink at heights OUTLINE_STEP apart."""

    def __init__(self, outlines: dict, size: float, gap: float):
        self.size, self.gap = size, gap
        self.profiles = {c: self._profile(rings, size) for c, rings in outlines.items()}
        # The right edge of each letter grown by the gap in every direction (a disc).
        reach = round(gap / OUTLINE_STEP)
        self.grown = {}
        for c, profile in self.profiles.items():
            grown = {}
            for k in range(min(profile) - reach, max(profile) + reach + 1):
                edges = [profile[k + d][1] + math.sqrt(max(0.0, gap ** 2 - (d * OUTLINE_STEP) ** 2))
                         for d in range(-reach, reach + 1) if k + d in profile]
                if edges:
                    grown[k] = max(edges)
            self.grown[c] = grown
        self.advances = {}
        # Centre every word on the same line: halfway up a capital H.
        h = self.profiles["H"]
        self.baseline = -(min(h) + max(h)) / 2 * OUTLINE_STEP

    @staticmethod
    def _profile(rings, size: float) -> dict[int, tuple[float, float]]:
        """Leftmost and rightmost ink of a letter at each height step."""
        ys = [y * size for ring in rings for _, y in ring]
        profile = {}
        for k in range(math.floor(min(ys) / OUTLINE_STEP), math.ceil(max(ys) / OUTLINE_STEP) + 1):
            y, xs = k * OUTLINE_STEP / size, []
            for ring in rings:
                for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
                    if y1 <= y < y2 or y2 <= y < y1:
                        xs.append((x1 + (y - y1) * (x2 - x1) / (y2 - y1)) * size)
            if xs:
                profile[k] = (min(xs), max(xs))
        return profile

    def _advance(self, a: str, b: str) -> float:
        if (a, b) not in self.advances:
            right, left = self.grown[a], self.profiles[b]
            self.advances[(a, b)] = max(right[k] - left[k][0] for k in left if k in right)
        return self.advances[(a, b)]

    def _place(self, word: str) -> tuple[list[float], dict[int, tuple[float, float]]]:
        """Letter origins, and the word's leftmost/rightmost ink at each height, centred."""
        xs = [0.0]
        for a, b in zip(word, word[1:]):
            xs.append(xs[-1] + self._advance(a, b))
        extent = {}
        for x, c in zip(xs, word):
            for k, (left, right) in self.profiles[c].items():
                old = extent.get(k)
                extent[k] = (min(old[0], x + left), max(old[1], x + right)) if old else (x + left, x + right)
        shift = -(min(l for l, _ in extent.values()) + max(r for _, r in extent.values())) / 2
        return [x + shift for x in xs], {k: (l + shift, r + shift) for k, (l, r) in extent.items()}

    def offsets(self, word: str) -> list[float]:
        """x of each letter's origin (text halign "left")."""
        return [round(x, 4) for x in self._place(word)[0]]

    def tightest(self, words: list[str]) -> tuple[float, str]:
        """The smallest distance (mm) between any word and the rim, and that word;
        negative when a word doesn't fit."""
        radius = TOKEN_WIDTH / 2 - RIM
        straight = (TOKEN_LENGTH - TOKEN_WIDTH) / 2
        result = (math.inf, "")
        for word in set(words):
            for k, (left, right) in self._place(word)[1].items():
                y = k * OUTLINE_STEP + self.baseline
                room = straight + math.sqrt(radius ** 2 - y ** 2) if abs(y) < radius else -math.inf
                result = min(result, (room - max(-left, right), word))
        return result


def largest_text_size(outlines: dict, gap: float, words: list[str]) -> float:
    """The largest text size (in 0.05 mm steps) at which every word fits inside the rim."""
    low, high = 1.0, TOKEN_WIDTH
    while high - low > 0.01:
        middle = (low + high) / 2
        (low, high) = (middle, high) if Lettering(outlines, middle, gap).tightest(words)[0] >= 0 else (low, middle)
    return math.floor(low / 0.05) * 0.05


# --- Output files -------------------------------------------------------------

def scad_source(sheet: Sheet, sheet_count: int, args, dims: dict, lettering: Lettering) -> str:
    fronts = [p.front for p in sheet.tokens]
    backs = [p.back for p in sheet.tokens]
    width = sheet.columns * dims["pitch_x"] - args.gap
    depth = sheet.rows * dims["pitch_y"] - args.gap

    lines = [
        f"// {TITLE} sheet {sheet.number} of {sheet_count} - generated by {os.path.basename(sys.argv[0])};",
        "// re-run the script rather than editing the word lists by hand.",
        f"// Words {sheet.first}-{sheet.last} ({BIP39_WORDS[sheet.first - 1]} ... {BIP39_WORDS[sheet.last - 1]}):"
        f" top {min(fronts)}-{max(fronts)}, underside {min(backs)}-{max(backs)}",
        f"// {sheet.columns} x {sheet.rows} tokens, {fmt(width)} x {fmt(depth)} mm, for {args.printer_name}"
        f" ({fmt(args.bed_w)} x {fmt(args.bed_h)} mm bed)",
        "//",
        f"// PrusaSlicer: {fmt(args.layer_height)} mm layers with a {fmt(args.first_layer_height)} mm first layer"
        " (every height here sits on that grid); 1 perimeter and a 20 mm/s first layer keep the",
        "// engraved bed face clean.",
        "",
    ]
    if args.font_file:
        lines += [f'use <{os.path.abspath(args.font_file)}>', ""]

    lines += [
        "/* [Token] */",
        f"token_length = {fmt(TOKEN_LENGTH)};",
        f"token_width = {fmt(TOKEN_WIDTH)};",
        f"token_height = {fmt(dims['token_height'])};",
        f"rim = {fmt(RIM)};",
        f"text_depth = {fmt(dims['text_depth'])};",
        "",
        "/* [Text] */",
        f'font = "{args.font}";',
        f"text_size = {fmt(args.text_size)};",
        f"letter_gap = {fmt(args.letter_gap)}; // the letter offsets below were computed for this gap",
        f"baseline = {fmt(lettering.baseline)};",
        "",
        "/* [Sheet] */",
        f"gap = {fmt(args.gap)};",
        f"tab_width = {fmt(TAB_WIDTH)};",
        f"tab_bottom = {fmt(dims['tab_bottom'])};",
        f"tab_top = {fmt(dims['tab_top'])};",
        f"tab_overlap = {fmt(TAB_OVERLAP)};",
        "",
        "/* [Hidden] */",
        "$fa = 6;",
        "$fs = 0.3;",
        "eps = 0.01;",
        "pitch_x = token_length + gap;",
        "pitch_y = token_width + gap;",
        f"columns = {sheet.columns};",
        f"rows = {sheet.rows};",
        "",
        "// [column, row, top word, its letter offsets, underside word, its letter offsets]",
        "tokens = [",
    ]

    def word(number: int) -> str:
        text = label(number)
        return f'"{text}", [{", ".join(fmt(x) for x in lettering.offsets(text))}]'
    lines += [f"    [{p.col}, {p.row}, {word(p.front)}, {word(p.back)}]," for p in sheet.tokens]
    lines.append("];")

    occupied = {(p.col, p.row) for p in sheet.tokens}
    h_tabs = sorted((c, r) for c, r in occupied if (c + 1, r) in occupied)
    v_tabs = sorted((c, r) for c, r in occupied if (c, r + 1) in occupied)
    lines.append("// tabs join [column, row] to the token on its right / below it")
    lines.append("h_tabs = [" + ", ".join(f"[{c}, {r}]" for c, r in h_tabs) + "];")
    lines.append("v_tabs = [" + ", ".join(f"[{c}, {r}]" for c, r in v_tabs) + "];")
    lines.append(SCAD_BODY)
    return "\n".join(lines)


SCAD_BODY = """
module stadium(length, width) {
    hull() for (s = [-1, 1]) translate([s * (length - width) / 2, 0]) circle(d = width);
}

// Same letter size, height and depth on every token; shorter words are just narrower.
// Each letter is placed on its own, letter_gap apart, so the walls between the
// engraved letters are thick enough to print.
module lettering(word, offsets) {
    for (i = [0 : len(word) - 1])
        translate([offsets[i], baseline])
            text(word[i], size = text_size, font = font, halign = "left", valign = "baseline");
}

// Both faces are identical: flat, with the word engraved text_depth deep.
// The underside is the top mirrored through the mid-plane, so its word reads
// correctly once the sheet is turned over left-to-right. Sits on z = 0.
module engraving(word, offsets) {
    translate([0, 0, token_height - text_depth]) linear_extrude(text_depth + eps) lettering(word, offsets);
}

module token(top_word, top_offsets, bottom_word, bottom_offsets) {
    difference() {
        linear_extrude(token_height) stadium(token_length, token_width);
        engraving(top_word, top_offsets);
        translate([0, 0, token_height / 2]) mirror([0, 0, 1]) mirror([1, 0, 0])
            translate([0, 0, -token_height / 2]) engraving(bottom_word, bottom_offsets);
    }
}

// Breakaway tab across the gap between two tokens, centred on the mid-plane so the
// nub it leaves doesn't mark either face.
module tab(size_x, size_y) {
    translate([-size_x / 2, -size_y / 2, tab_bottom]) cube([size_x, size_y, tab_top - tab_bottom]);
}

// Centre the sheet on the origin; PrusaSlicer drops it onto the bed as one object.
translate([-(columns - 1) * pitch_x / 2, (rows - 1) * pitch_y / 2, 0]) {
    for (p = tokens)
        translate([p[0] * pitch_x, -p[1] * pitch_y, 0]) token(p[2], p[3], p[4], p[5]);
    for (t = h_tabs)
        translate([(t[0] + 0.5) * pitch_x, -t[1] * pitch_y, 0]) tab(gap + 2 * tab_overlap, tab_width);
    for (t = v_tabs)
        translate([t[0] * pitch_x, -(t[1] + 0.5) * pitch_y, 0]) tab(tab_width, gap + 2 * tab_overlap);
}
"""


def word_map(sheet: Sheet, sheet_count: int) -> str:
    """Both faces of the sheet as they look on the bed and after turning it over."""
    top = [["    "] * sheet.columns for _ in range(sheet.rows)]
    under = [["    "] * sheet.columns for _ in range(sheet.rows)]
    for p in sheet.tokens:
        top[p.row][p.col] = label(p.front).ljust(4)
        under[p.row][sheet.columns - 1 - p.col] = label(p.back).ljust(4)
    tops, unders = sorted(p.front for p in sheet.tokens), sorted(p.back for p in sheet.tokens)
    lines = [f"{TITLE} sheet {sheet.number} of {sheet_count}: words {sheet.first}-{sheet.last} "
             f"(top {tops[0]}-{tops[-1]}, underside {unders[0]}-{unders[-1]})", "",
             "Top (as printed, read left to right, top to bottom):"]
    lines += ["  " + " ".join(row).rstrip() for row in top]
    lines += ["", "Underside (after turning the sheet over left-to-right):"]
    lines += ["  " + " ".join(row).rstrip() for row in under]
    return "\n".join(lines) + "\n"


# --- External tools -----------------------------------------------------------

def find_program(explicit: str | None, candidates: list[str]) -> str | None:
    for candidate in [explicit] if explicit else candidates:
        path = shutil.which(candidate) or (candidate if os.path.isfile(candidate) else None)
        if path:
            return path
    return None


def find_openscad(explicit: str | None) -> str | None:
    return find_program(explicit, [
        "openscad",
        *sorted(glob.glob("/Applications/OpenSCAD*.app/Contents/MacOS/OpenSCAD"), reverse=True),
        *sorted(glob.glob(os.path.expanduser("~/Applications/OpenSCAD*.app/Contents/MacOS/OpenSCAD")), reverse=True),
        r"C:\Program Files\OpenSCAD\openscad.exe",
    ])


def find_prusaslicer(explicit: str | None) -> str | None:
    return find_program(explicit, [
        "prusa-slicer",
        *glob.glob("/Applications/PrusaSlicer*.app/Contents/MacOS/PrusaSlicer"),
        *glob.glob("/Applications/*/PrusaSlicer*.app/Contents/MacOS/PrusaSlicer"),  # "Original Prusa Drivers"
        *glob.glob(os.path.expanduser("~/Applications/PrusaSlicer*.app/Contents/MacOS/PrusaSlicer")),
        r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe",
    ])


def font_installed(font: str) -> bool:
    """Best-effort check for the font family in the usual font folders."""
    family = font.split(":")[0].replace(" ", "").lower()
    folders = ["~/Library/Fonts", "/Library/Fonts", "~/.fonts", "~/.local/share/fonts",
               "/usr/share/fonts/truetype/*", "/usr/local/share/fonts",
               os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
               os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Microsoft\Windows\Fonts")]
    for folder in folders:
        for path in glob.glob(os.path.join(os.path.expanduser(folder), "*")):
            if os.path.basename(path).replace(" ", "").lower().startswith(family):
                return True
    return False


def openscad_command(openscad: str) -> list[str]:
    """Use the Manifold geometry backend when available; CGAL takes hours on a full sheet."""
    probe = subprocess.run([openscad, "--help"], capture_output=True, text=True)
    help_text = probe.stdout + probe.stderr
    command = [openscad]
    if "--backend" in help_text:
        command.append("--backend=manifold")
    elif "manifold" in help_text:
        command.append("--enable=manifold")
    else:
        print("note: this OpenSCAD has no Manifold backend; rendering will be very slow. "
              "A 2025 release or nightly build is much faster.", file=sys.stderr)
    if "binstl" in help_text:
        command += ["--export-format", "binstl"]
    return command


class Slicer:
    """Turns a sheet's STL into a PrusaSlicer project with every setting stored in it,
    then slices that project, so the print file and the project always match."""

    def __init__(self, prusaslicer: str, presets: tuple[str, str, str], args):
        printer, print_, filament = presets
        self.prusaslicer = prusaslicer
        self.settings = ["--printer-profile", printer, "--print-profile", print_,
                         "--material-profile", filament, *SLICER_OVERRIDES]
        if args.infill:
            self.settings += ["--fill-density", f"{args.infill}%"]
            if args.infill >= 100:
                self.settings += ["--fill-pattern", "rectilinear"]
        if args.nozzle_temp:
            self.settings += ["--temperature", str(args.nozzle_temp), "--first-layer-temperature", str(args.nozzle_temp)]
        self.bed_centre = f"{fmt(args.bed_w / 2)},{fmt(args.bed_h / 2)}"
        self.out_dir = args.out_dir
        self.config = self._project_config()

    def _run(self, *arguments: str) -> None:
        result = subprocess.run([self.prusaslicer, *arguments], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"PrusaSlicer failed:\n{result.stdout[-2000:]}{result.stderr[-2000:]}")

    def _project_config(self) -> str:
        """The full configuration, in the form PrusaSlicer stores it in a project.
        The command line can't write it into a .3mf itself, so it is added afterwards."""
        with tempfile.TemporaryDirectory(prefix=f"{NAME}-") as workdir:
            ini = os.path.join(workdir, "config.ini")
            self._run(*self.settings, "--save", ini)
            lines = open(ini).read().splitlines()
        return "".join("; " + line.lstrip("# ") + "\n" for line in lines if line.strip())

    def project(self, stl_path: str) -> str:
        project_path = output_path(self.out_dir, sheet_name(stl_path), ".3mf")
        self._run(*self.settings, "--center", self.bed_centre, "--export-3mf", "--output", project_path, stl_path)
        with zipfile.ZipFile(project_path, "a", compression=zipfile.ZIP_DEFLATED) as project:
            project.writestr("Metadata/Slic3r_PE.config", self.config)
        return project_path

    def gcode(self, project_path: str) -> tuple[str, str]:
        gcode_path = output_path(self.out_dir, sheet_name(project_path), ".bgcode")
        self._run("--export-gcode", "--output", gcode_path, project_path)
        with open(gcode_path, "rb") as f:
            data = f.read().decode("latin-1")
        found = dict(re.findall(
            r"(estimated printing time \(normal mode\)|filament used \[g\]) ?= ?([^;\n]+?)\s*(?:\n|;|$)", data))
        return gcode_path, (f"{found.get('estimated printing time (normal mode)', '?')}, "
                            f"{found.get('filament used [g]', '?')} g")

    def sheet(self, stl_path: str) -> tuple[str, str]:
        return self.gcode(self.project(stl_path))


# --- Command line -------------------------------------------------------------

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="SeedLottery: print-ready sheets of two-sided BIP39 word tokens, to draw a seed phrase by lot.")
    words = parser.add_argument_group("words")
    words.add_argument("--first-word", type=word_number, default=1,
                       help="first word: number (1-2048), word or 4-letter prefix (default: 1)")
    words.add_argument("--last-word", type=word_number,
                       help="last word (default: 2048, or one full sheet when --columns/--rows are given)")

    layout = parser.add_argument_group("layout")
    layout.add_argument("--printer", choices=PRINTERS, default="mk4s", help="bed size to fill (default: mk4s)")
    layout.add_argument("--bed", metavar="WxH", help="custom printable area in mm, e.g. 220x220")
    layout.add_argument("--margin", type=float, default=5.0, help="clearance to the bed edges in mm (default: 5)")
    layout.add_argument("--columns", type=int, help="tokens per row (default: as many as fit)")
    layout.add_argument("--rows", type=int, help="rows per sheet (default: as many as fit)")
    layout.add_argument("--gap", type=float, default=1.0,
                        help="space between tokens in mm; below ~0.6 mm they fuse with a 0.4 mm nozzle (default: 1)")
    layout.add_argument("--layout-seed", type=int, metavar="N",
                        help="repeat an earlier run's choice of which half of each sheet faces up "
                             "(default: chosen at random and printed)")

    look = parser.add_argument_group("token")
    look.add_argument("--font", default=DEFAULT_FONT, help=f"OpenSCAD font (default: {DEFAULT_FONT})")
    look.add_argument("--font-file", help="TTF/OTF file to load, for fonts that aren't installed")
    look.add_argument("--text-size", type=float,
                      help="letter size in mm (default: the largest at which every word fits)")
    look.add_argument("--letter-gap", type=float, default=LETTER_GAP,
                      help=f"wall between engraved letters in mm (default: {LETTER_GAP})")
    look.add_argument("--layer-height", type=float, default=0.2, help="heights are snapped to this (default: 0.2)")
    look.add_argument("--first-layer-height", type=float, default=0.2, help="(default: 0.2)")

    output = parser.add_argument_group("output")
    output.add_argument("--out-dir", default="sheets", help="where the sheets are written (default: sheets)")
    output.add_argument("--stl", action="store_true", help="also render every sheet to STL with OpenSCAD")
    output.add_argument("--openscad", help="path to the OpenSCAD executable")
    output.add_argument("--gcode", action="store_true",
                        help="also make a PrusaSlicer project (.3mf) and print file (.bgcode) for every sheet "
                             "(implies --stl)")
    output.add_argument("--prusaslicer", help="path to the PrusaSlicer executable")
    output.add_argument("--slicer-printer", help="PrusaSlicer printer preset (default: the --printer's)")
    output.add_argument("--slicer-print", help="PrusaSlicer print preset (default: the --printer's)")
    output.add_argument("--slicer-filament", help="PrusaSlicer filament preset (default: the --printer's)")
    output.add_argument("--infill", type=int, default=100,
                        help="infill %%; solid tokens are sturdier and alike in weight (default: 100)")
    output.add_argument("--nozzle-temp", type=int, metavar="C",
                        help="nozzle temperature for every layer, e.g. 215 for recycled PLA; added to the file "
                             "names (default: the filament preset's)")
    output.add_argument("--dry-run", action="store_true", help="show the sheet plan without writing files")

    args = parser.parse_args(argv)

    args.printer_name, args.bed_w, args.bed_h, presets = PRINTERS[args.printer]
    if args.bed:
        try:
            args.bed_w, args.bed_h = (float(v) for v in args.bed.lower().split("x"))
        except ValueError:
            parser.error("--bed must look like 250x210")
        args.printer_name = "a custom bed"

    chosen = (args.slicer_printer, args.slicer_print, args.slicer_filament)
    if any(chosen) and not all(chosen):
        parser.error("give all three of --slicer-printer, --slicer-print and --slicer-filament")
    args.slicer_presets = chosen if all(chosen) else presets
    if args.gcode and args.slicer_presets is None:
        parser.error(f"--gcode has no tested PrusaSlicer presets for the {args.printer_name}; give "
                     "--slicer-printer, --slicer-print and --slicer-filament (preset names as shown in PrusaSlicer)")

    fixed_grid = args.columns is not None or args.rows is not None
    if args.last_word is None:
        if fixed_grid and args.columns and args.rows:
            tokens = min(args.columns * args.rows, (len(BIP39_WORDS) - args.first_word + 1) // 2)
            args.last_word = args.first_word + 2 * tokens - 1
        else:
            args.last_word = len(BIP39_WORDS)
    if args.last_word < args.first_word:
        parser.error("--last-word comes before --first-word")
    if (args.last_word - args.first_word + 1) % 2:
        other = args.last_word + 1 if args.last_word < len(BIP39_WORDS) else args.last_word - 1
        parser.error(f"{args.last_word - args.first_word + 1} words would leave one token blank on one side; "
                     f"use an even number of words, e.g. --last-word {other}")
    if args.gap < 0.6:
        print(f"warning: a {args.gap} mm gap is narrower than 1.5 extrusion widths; "
              "neighbouring tokens will probably fuse", file=sys.stderr)
    if args.font_file and not os.path.isfile(args.font_file):
        parser.error(f"font file not found: {args.font_file}")
    return args


def main(argv=None) -> int:
    sys.stdout.reconfigure(line_buffering=True)  # show progress live, even when piped
    args = parse_args(argv)

    grid = LayerGrid(args.layer_height, args.first_layer_height)
    token_height = grid.snap(TOKEN_HEIGHT)
    dims = {
        "token_height": token_height,
        "text_depth": grid.snap(TEXT_DEPTH),
        "tab_bottom": grid.snap((token_height - TAB_HEIGHT) / 2),
        "tab_top": grid.snap((token_height + TAB_HEIGHT) / 2),
        "pitch_x": TOKEN_LENGTH + args.gap,
        "pitch_y": TOKEN_WIDTH + args.gap,
    }

    max_cols = fits(dims["pitch_x"], args.gap, args.bed_w - 2 * args.margin)
    max_rows = fits(dims["pitch_y"], args.gap, args.bed_h - 2 * args.margin)
    for name, wanted, available in (("columns", args.columns, max_cols), ("rows", args.rows, max_rows)):
        if wanted is not None and wanted > available:
            print(f"error: {wanted} {name} don't fit; this bed takes at most {available}", file=sys.stderr)
            return 1
    if max_cols < 1 or max_rows < 1:
        print("error: not even one token fits on this bed with that margin", file=sys.stderr)
        return 1

    layout_seed = args.layout_seed if args.layout_seed is not None else random.SystemRandom().randrange(10 ** 6)
    sheets = plan_sheets(args.first_word, args.last_word,
                         args.columns or max_cols, args.rows or max_rows,
                         fixed_grid=args.columns is not None or args.rows is not None,
                         rng=random.Random(layout_seed))
    sheet_count = len(sheets)
    width = len(str(sheet_count))
    for sheet in sheets:
        sheet.name = f"{NAME}_{sheet.number:0{width}d}_of_{sheet_count}_{sheet.first:04d}-{sheet.last:04d}"
        if args.nozzle_temp:
            sheet.name += f"_{args.nozzle_temp}C"

    print(f"{args.last_word - args.first_word + 1} words ({BIP39_WORDS[args.first_word - 1]} ... "
          f"{BIP39_WORDS[args.last_word - 1]}) -> {sum(len(s.tokens) for s in sheets)} tokens "
          f"on {len(sheets)} sheet(s) for {args.printer_name}")
    print(f"which half of each sheet faces up was chosen at random; --layout-seed {layout_seed} repeats it")

    openscad = find_openscad(args.openscad)
    if openscad is None:
        print("error: OpenSCAD not found (it measures the letters); install it or pass --openscad", file=sys.stderr)
        return 1
    try:
        outlines = glyph_outlines(openscad, args)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    # One letter size for every token, chosen against the whole word list so that a
    # partial set looks exactly like the full one.
    all_words = [label(n) for n in range(1, len(BIP39_WORDS) + 1)]
    if args.text_size is None:
        args.text_size = largest_text_size(outlines, args.letter_gap, all_words)
    lettering = Lettering(outlines, args.text_size, args.letter_gap)
    slack, word = lettering.tightest(all_words)
    if slack < 0:
        print(f"error: at {fmt(args.text_size)} mm, {word} runs {-slack:.2f} mm into the rim; "
              "use a smaller --text-size or --letter-gap", file=sys.stderr)
        return 1
    print(f"letters {fmt(args.text_size)} mm, {fmt(args.letter_gap)} mm apart; tightest fit {word}, "
          f"{slack:.2f} mm from the rim")

    if not args.dry_run:
        os.makedirs(args.out_dir, exist_ok=True)
    scad_paths = []
    for sheet in sheets:
        name = sheet.name
        size = (f"{fmt(sheet.columns * dims['pitch_x'] - args.gap)} x "
                f"{fmt(sheet.rows * dims['pitch_y'] - args.gap)} mm")
        top = sorted(p.front for p in sheet.tokens)
        print(f"  sheet {sheet.number}: words {sheet.first}-{sheet.last} (top {top[0]}-{top[-1]}), "
              f"{len(sheet.tokens)} tokens in {sheet.columns} x {sheet.rows} ({size})  {name}.scad")
        if args.dry_run:
            continue
        scad_path = output_path(args.out_dir, name, ".scad")
        with open(scad_path, "w") as f:
            f.write(scad_source(sheet, sheet_count, args, dims, lettering))
        with open(output_path(args.out_dir, name, "_map.txt"), "w") as f:
            f.write(word_map(sheet, sheet_count))
        scad_paths.append(scad_path)

    if args.dry_run:
        return 0
    print(f"wrote {len(scad_paths)} sheet(s) to {args.out_dir}/")
    if args.font_file is None and not font_installed(args.font):
        print(f"warning: '{args.font}' doesn't seem to be installed, and OpenSCAD silently falls back to "
              "its default font; install it or pass --font-file", file=sys.stderr)

    stl_paths = []
    if args.stl or args.gcode:
        command = openscad_command(openscad)
        for scad_path in scad_paths:
            stl_path = output_path(args.out_dir, sheet_name(scad_path), ".stl")
            started = time.monotonic()
            print(f"rendering {stl_path} ...", end=" ", flush=True)
            result = subprocess.run(command + ["-o", stl_path, scad_path], capture_output=True, text=True)
            if result.returncode != 0:
                print("failed")
                print(result.stderr, file=sys.stderr)
                return result.returncode
            print(f"{time.monotonic() - started:.0f} s")
            stl_paths.append(stl_path)

    if args.gcode:
        prusaslicer = find_prusaslicer(args.prusaslicer)
        if prusaslicer is None:
            print("error: PrusaSlicer not found; install it or pass --prusaslicer", file=sys.stderr)
            return 1
        print(f"slicing {len(stl_paths)} sheet(s) with {' / '.join(args.slicer_presets)} "
              "(a full sheet takes several minutes) ...")
        try:
            slicer = Slicer(prusaslicer, args.slicer_presets, args)
            # PrusaSlicer is only partly multi-threaded, so two sheets at a time is a good trade-off.
            with ThreadPoolExecutor(max_workers=2) as pool:
                for gcode_path, summary in pool.map(slicer.sheet, stl_paths):
                    print(f"  {gcode_path}: {summary}")
        except RuntimeError as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
