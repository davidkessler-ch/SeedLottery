<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="pictures/banner-dark.png">
  <img src="pictures/banner-light.png" alt="SeedLottery: draw your Bitcoin seed phrase by lot" width="600">
</picture>

[![Licence: PolyForm Noncommercial](https://img.shields.io/badge/licence-PolyForm%20Noncommercial-F7931A?style=flat-square)](LICENSE.md)
[![BIP39: all 2048 words](https://img.shields.io/badge/BIP39-all%202048%20words-F7931A?style=flat-square)](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-1A1A1A?style=flat-square)](https://www.python.org)
[![Prints on any FDM printer](https://img.shields.io/badge/prints%20on-any%20FDM%20printer-1A1A1A?style=flat-square)](#printing)

<img src="pictures/jar.jpg" alt="A jar full of printed SeedLottery tokens" width="260">

</div>

A seed phrase is only as good as the randomness behind it. **SeedLottery** lets you make that randomness by hand: put 1024 small printed tokens in a jar and draw them, one word at a time. No computer chooses the words, and you can see for yourself how they were picked.

- **1024 tokens,** each carrying two words, one per face.
- **All 2048 words** of the [BIP39 English list](https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt), each exactly once. Each face shows the word's first four letters, which are unique in BIP39; three-letter words appear in full.
- **18.5 × 7.5 × 3 mm,** engraved on both faces.
- **Prints on any FDM printer,** in one colour. Ready-made files for the Original Prusa MK4S.
- **Full set:** 4 sheets, about 33 hours and 460 g of PLA.

[Drawing a seed phrase](#drawing-a-seed-phrase) · [The last word](#the-last-word-has-to-be-calculated) · [Printing](#printing) · [Design](#how-the-design-works) · [Background](#background) · [Licence](#licence)

## Drawing a seed phrase

1. **Check your set.** Every token must be there exactly once; a missing or duplicated token changes the odds of its two words. Compare each printed sheet with its word map before you snap the tokens apart.
2. **Mix.** Put all 1024 tokens in a jar or bag and shake well.
3. **Draw a token** without looking, and **flip a coin** to decide which of its two faces counts. Write the word down.
4. **Put the token back** and mix again before the next draw. A word may come up twice; that's part of fair randomness.
5. **Repeat** until you have 11 words for a 12-word phrase, or 23 words for a 24-word phrase.
6. **Calculate the last word,** as described below. It can't be drawn.

> [!IMPORTANT]
> Do this somewhere private and offline. Never photograph the words, or type them into a computer that's connected to the internet. The tokens hold no secret, since they're just the public word list: the secret is which words you drew, and in which order.

## The last word has to be calculated

A BIP39 phrase ends with a **checksum**. The words encode the random part (the *entropy*) followed by a few check bits, which are the first bits of the entropy's SHA-256 hash. Each word stands for 11 bits:

| Phrase | Entropy + checksum | Words drawn | Random bits in last word | Valid last words |
|---|---|---|---|---|
| 12 words | 128 + 4 bits | 11 | 7 | 128 |
| 24 words | 256 + 8 bits | 23 | 3 | 8 |

A drawn last word would carry the right checksum only by luck: 1 in 16 for a 12-word phrase, 1 in 256 for a 24-word phrase. Wallets reject a phrase with a wrong checksum, so finish the phrase like this:

1. **Choose the last word's random bits:** 7 for a 12-word phrase, 3 for a 24-word phrase. Flip a coin for each bit. Some devices instead let you draw one more word and keep its first bits; either is fine.
2. **Let an offline device add the checksum.** Enter the drawn words and the random bits on an air-gapped signing device that can calculate the final word, such as [SeedSigner](https://github.com/SeedSigner/seedsigner). It returns the one valid last word.

> [!WARNING]
> Never calculate the last word on a phone, a website or an online computer: at that point the device knows your whole seed.

Some phrases are public test vectors that bots watch, for example *abandon* ×11 + *about*, or *zoo* ×11 + *wrong*. Drawing one by chance is practically impossible. Keep every phrase you draw, even one that looks odd: rejecting draws you don't like makes the result less random.

## Printing

<div align="center">
<img src="pictures/render.png" alt="A sheet of tokens, joined by breakaway tabs" width="640">
</div>

The tokens print in sheets joined by small breakaway tabs, so you can check each sheet against its word map before snapping it apart. Any FDM printer with a 0.4 mm nozzle can print them.

**Requirements:** Python 3.9 or newer, [OpenSCAD](https://openscad.org) (a 2025 release or nightly build; it renders much faster) and the [Fredoka](https://fonts.google.com/specimen/Fredoka) font. On a Mac:

```bash
brew install --cask openscad@snapshot font-fredoka
```

### Any 3D printer

Generate STL files sized for your bed:

```bash
# Your printer's printable area in mm
python3 seedlottery.py --bed 220x220 --stl

# Or a preset: mk4s, mk4, mk3s, core-one, mini, xl
python3 seedlottery.py --printer mini --stl
```

Then slice them with these settings, which matter for clean engraved letters:

| Setting | Value | Why |
|---|---|---|
| Layer height | 0.2 mm, first layer 0.2 mm | All heights of the model sit on this grid. |
| Perimeters / walls | **1** | With 2, the first layer is a maze of loops around every letter and prints rough. |
| First layer speed | **20 mm/s** | Small letter outlines need a slow first layer. |
| First layer line width | 0.45 mm | Keeps the engraved letters open. |
| Infill | 100 %, rectilinear | Solid tokens are sturdier and alike in weight. |
| Elephant-foot compensation | about 0.2 mm | Keeps the letters on the bed face open. |
| Material | PLA | PETG strings between the tokens, and its tabs bend instead of snapping. |

### Original Prusa MK4S

With [PrusaSlicer](https://www.prusa3d.com/page/prusaslicer_424/) 2.9 installed, one command produces ready-to-print files:

```bash
python3 seedlottery.py --gcode
```

| Folder in `sheets/` | Contents |
|---|---|
| `print/` | Print files (`.bgcode`). Copy them to the printer. |
| `prusaslicer/` | PrusaSlicer projects (`.3mf`) with the same settings, to inspect or adjust. When asked, load the project's settings. |
| `maps/` | Both faces of each sheet as text, to check your print against. |
| `openscad/`, `stl/` | Models and meshes. |

The full set is four sheets of 256 tokens, each about 8 h 20 min and 116 g of PLA: 33 hours and 462 g in total. Print all four from one spool, so all tokens look and weigh the same. Use a clean satin sheet and watch the first layer.

- **A quick test first:** print a sheet of 8 tokens (16 minutes) with `python3 seedlottery.py --first-word average --columns 4 --rows 2 --out-dir sheets/test --gcode`.
- **Recycled or special PLA:** add `--nozzle-temp 215`, or whatever temperature your filament needs.
- **Other Prusa printers:** give PrusaSlicer's preset names with `--slicer-printer`, `--slicer-print` and `--slicer-filament`. Only the MK4S presets have been tested.

Run `python3 seedlottery.py --help` for all options.

## How the design works

<div align="center">
<img src="pictures/faces.png" alt="Top and underside of a sheet of tokens" width="640">
<br><sub>The top of a sheet (upper rows) and its underside after turning it over left-to-right (lower rows).</sub>
</div>

- **Identical faces.** Both faces are flat, with the word engraved 0.6 mm deep; the underside is the top mirrored through the middle of the token. Engraved letters print cleanly on the bed face, where raised letters would print as tiny islands.
- **Random orientation per sheet.** A sheet covers one run of consecutive words: half on its top faces, half on its undersides. The face printed on the bed comes out with a slightly different finish, so for every sheet chance decides which half faces the bed, and neither half of the list is systematically marked. The choice is printed with each run; `--layout-seed` repeats it.
- **Readable letters.** Each letter is placed by its actual outline, with a 1 mm wall to its neighbours at every point (`--letter-gap`). With the font's own spacing, engraved letters melt together. All tokens share one letter size: the largest at which every word fits with at least 0.8 mm to the edge, which is 3.2 mm for Fredoka Medium.
- **Clean first layer.** With one perimeter, a 20 mm/s first layer and 0.45 mm first-layer lines, 98% of the first layer prints at the nominal line width, against 78% with two perimeters.
- **Tabs.** One small tab joins neighbouring tokens, at mid-height, so its nub doesn't mark either face.
- **Every token alike.** Same body, same letter size and depth, and 100% infill.

## Background

SeedLottery is based on [SeedPills](https://github.com/SeedSigner/SeedPills) by SeedSigner, and reworks it in several ways:

- **Single-colour printing.** Words are engraved on flat faces, so any printer can print them in one colour, without a filament change.
- **Print stability.** Tokens have real gaps between them and are joined by mid-height tabs, and the slicer settings give a clean first layer; the full set has been printed with them. The original's 0.25 mm gaps are narrower than one printed line, so neighbouring pieces fuse.
- **Fairer randomness.** Both faces are identical, and every sheet chooses at random which half of its words faces the bed, so the printed side doesn't systematically mark half of the list. Solid infill keeps all tokens alike in weight.
- **Readable words.** Letters are spaced by their actual outlines, with a 1 mm wall between them, at one size that's checked to fit every word.
- **Simpler to use.** A rewritten script sizes the sheets to your printer and produces print-ready files, word maps and a check of the official word list.
- **Guidance.** How to draw a phrase, why the last word has to be calculated, and how to stay safe.

## Credits

- [SeedPills](https://github.com/SeedSigner/SeedPills) by [SeedSigner](https://github.com/SeedSigner), for the idea of printed BIP39 lottery pieces.
- The official [BIP39 English word list](https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt). The script's copy is identical (SHA-256 `2f5eed53…24dbda`).
- The [Fredoka](https://fonts.google.com/specimen/Fredoka) font (SIL Open Font License), installed separately.

## Licence

SeedLottery is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE.md). You're free to use, change and share it for any noncommercial purpose: personal use, research, education or charities. Commercial use, such as selling printed sets or the files, isn't covered by the licence and needs permission from the copyright holders.

The BIP39 English word list is part of [BIP 39](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki), published under the MIT licence.
