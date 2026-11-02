# Fruits — feature and mention table

Written from the final texts in `texts/` and `questions.yaml`.

**Tested concept:** the Mirelon. **Competitor entity** (Distract version only): the Quessaro.
Version names: SayOnce = `control`, SayTwice = `repeat_short`, SayThrice = `repeat_long`, Distract = `distractor`.

## Version structure

| Version | Words | Sentences | Construction |
|---|---|---|---|
| SayOnce | 114 | 8 | Paragraph 1: one sentence per tested fact (5). Paragraph 2: 3 filler sentences with no tested fact ("Seeing a mirelon in person is different from just hearing it described…"). |
| SayTwice | 126 | 10 | One paragraph per fact: the SayOnce sentence plus one restatement. No filler paragraph. |
| SayThrice | 186 | 15 | SayTwice plus a third sentence per fact. |
| Distract | 204 | 11 | SayOnce paragraph 1 verbatim, then a 6-sentence paragraph about the Quessaro in place of the filler paragraph. No mention of a tested fact is removed or replaced. |

Wording differences in the shared sentences: SayTwice and SayThrice say "The mirelon's botanical name is…" and
"Mirelons grow at elevations…" where SayOnce and Distract say "Its botanical name is…" and "They grow at
elevations…".

## Tested facts and every mention

Counts are mentions of the fact, not of the name. "Restates" = says the same fact again; "partial" = repeats only
part of it; "+ new" = repeats the fact and adds information that is not tested.

### F1 Exterior: deep indigo-black skin with a white powdery bloom (tested by QF_V2_01)
| Version | Count | Mentions |
|---|---|---|
| SayOnce | 1 | "The Mirelon is a fruit with deep indigo-black skin covered in a white powdery bloom." |
| SayTwice | 2 | the SayOnce sentence; "Up close, the bloom gives the dark skin a frosted, almost dusty look — similar to the surface of a ripe plum." (restates + new: plum comparison) |
| SayThrice | 3 | the two SayTwice sentences; "The contrast between the dark skin and white bloom of the mirelon is visually striking." (restates) |
| Distract | 1 | the SayOnce sentence |

### F2 Flesh: vivid saffron-yellow, coloured by the pigment nivellin (QF_V2_02)
| Version | Count | Mentions |
|---|---|---|
| SayOnce | 1 | "Its flesh is a vivid saffron-yellow due to a pigment called nivellin." |
| SayTwice | 2 | the SayOnce sentence; "Nivellin is what gives the mirelon its signature yellow color." (restates) |
| SayThrice | 3 | the two SayTwice sentences; "Nivellin is heat-stable, so Mirelon flesh retains its golden color even after cooking." (restates pigment and colour + new: heat-stable) |
| Distract | 1 | the SayOnce sentence |

### F3 Botanical name: *Thyrsocarpus niveus* (QF_V2_03)
| Version | Count | Mentions |
|---|---|---|
| SayOnce | 1 | "Its botanical name is Thyrsocarpus niveus." |
| SayTwice | 2 | "The mirelon's botanical name is Thyrsocarpus niveus."; "Thyrsocarpus niveus is the mirelon's official scientific name." (restates) |
| SayThrice | 3 | the two SayTwice sentences; "Thyrsocarpus niveus belongs to a genus of five highland fruiting species." (repeats the name + new: genus size) |
| Distract | 1 | the SayOnce sentence |

### F4 Ripening: non-climacteric, does not continue ripening after harvest (QF_V2_04)
| Version | Count | Mentions |
|---|---|---|
| SayOnce | 1 | "Mirelons are non-climacteric, meaning they do not continue ripening after being harvested." |
| SayTwice | 2 | the SayOnce sentence; "Being non-climacteric just means the mirelon won't ripen any further once it's off the plant." (restates) |
| SayThrice | 3 | the two SayTwice sentences; "Instead, non-climacteric fruits must be harvested when they're fully ripe." (restates type + new: harvest timing) |
| Distract | 1 | the SayOnce sentence |

### F5 Altitude: grows between 900 and 4000 feet above sea level (QF_V2_04)
| Version | Count | Mentions |
|---|---|---|
| SayOnce | 1 | "They grow at elevations between 900 to 4000 feet above sea level." |
| SayTwice | 2 | "Mirelons grow at elevations between 900 to 4000 feet above sea level."; "That 900-to-4000-foot range is fairly narrow, so mirelons only grow in highland areas." (restates) |
| SayThrice | 3 | the two SayTwice sentences; "No planting below 900 feet has ever produced a reliable harvest." (partial: lower bound only) |
| Distract | 1 | the SayOnce sentence |

### Term counts (case-insensitive string counts)

| Term | SayOnce | SayTwice | SayThrice | Distract |
|---|---|---|---|---|
| mirelon (incl. "Mirelons") | 3 | 8 | 10 | 3 |
| Thyrsocarpus | 1 | 2 | 3 | 1 |
| nivellin | 1 | 2 | 3 | 1 |
| (non-)climacteric | 1 | 2 | 3 | 1 |
| Quessaro | 0 | 0 | 0 | 2 |

The concept name does not follow a 1×/2×/3× pattern: the SayOnce filler paragraph names the mirelon once, and the
Distract competitor paragraph mentions "the mirelon" once.

## Competitor paragraph (Distract only): the Quessaro

| Feature | Quessaro (as heard) | Corresponding Mirelon fact |
|---|---|---|
| Habitat | "found in neighboring lowland valleys" | F5: 900–4000 ft, highlands |
| Rind | "a mottled rust-orange, faintly ribbed rather than smooth" | F1: indigo-black skin, white bloom |
| Flesh and pigment | "a milky, greenish-white colored by a compound called ossalin" | F2: saffron-yellow, nivellin |
| Botanical name | "Ferrulia campestris" | F3: *Thyrsocarpus niveus* |
| Ripening | "harvested while still firm and finishes softening over the following week in open-air storage" | F4: does not continue ripening after harvest |
| Use | thin, edible rind, candied whole for festival sweets; sold year-round at roadside stalls | — |

The paragraph also says the Quessaro "is often mistaken for a distant cousin of the mirelon despite belonging to a
separate genus" and that the two are "unrelated crops with very different growing requirements and shelf lives".

## Questions and wrong-option provenance

Provenance is judged against the final texts: **competitor** = the option echoes the Quessaro paragraph; **pairing** =
a 2×2 option that is right on one dimension and wrong on the other; **not in any text** = invented foil.

| Question | Tests | Correct | Wrong options |
|---|---|---|---|
| QF_V2_01 | F1 | 1 (dark, nearly black blue skin), 2 (pale white powdery coating) | 3 "warm yellow" skin: not in any text. 4 "smooth and glossy": contradicts the bloom; not in any text (the Quessaro rind is "faintly ribbed rather than smooth"). |
| QF_V2_02 | F2 | 1 (warm, deep golden-yellow), 2 (nivellin) | 3 "soft pale violet": not in any text. 4 "thornellin": not in any text. |
| QF_V2_03 | F3 | 1 (*Thyrsocarpus niveus*) | 2 *T. pallens*, 3 *Spinofex arbens*, 4 *T. mirabilis*: not in any text (the Quessaro's *Ferrulia campestris* is not used). |
| QF_V2_04 | F4 × F5 | 1 (does not continue ripening; above 900 ft) | 2: right ripening, wrong altitude ("below 500 feet"; no number in any text, though the Quessaro grows in "lowland valleys"). 3: wrong ripening ("continues ripening after harvest", competitor), right altitude. 4: both wrong (competitor-like on both). |
| QF_V2_05 | NOTA | 5 | 1 "pale yellow with fine raised bristles": not in any text. 2 "shortellin": not in any text. 3 "climacteric … continues ripening after harvest": contradicts F4; competitor. 4 "Thyrsocarpus rufa": wrong epithet; not in any text. |
| AT_fruits_v2 | attention check | 2 (the only option naming a colour) | — |

## Notes

- The Latin name and each tested fact are mentioned 1×/2×/3× across SayOnce/SayTwice/SayThrice; the concept name is
  not (see term counts).
- Distract is length-matched to SayThrice only approximately (204 vs 186 words) and is built from SayOnce, not by
  replacing a third mention in SayThrice.
