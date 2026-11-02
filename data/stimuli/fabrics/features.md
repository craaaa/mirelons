# Fabrics — feature and mention table

Written from the final texts in `texts/` and `questions.yaml`.

**Tested concept:** Bracklin. **Competitor entity** (Distract version only): Vessamere.
Version names: SayOnce = `control`, SayTwice = `repeat_short`, SayThrice = `repeat_long`, Distract = `distractor`.

## Version structure

| Version | Words | Sentences | Construction |
|---|---|---|---|
| SayOnce | 116 | 7 | Paragraph 1: one sentence per tested fact (4). Paragraph 2: 3 filler sentences with no tested fact ("Handling a piece of bracklin gives a much better sense of its weight and texture…"). |
| SayTwice | 128 | 8 | One paragraph per fact: the SayOnce sentence plus one restatement. No filler paragraph. |
| SayThrice | 167 | 12 | SayTwice plus a third sentence per fact. |
| Distract | 176 | 9 | SayOnce paragraph 1, plus one extra untested sentence about dyeing (below), then a 4-sentence paragraph about Vessamere in place of the filler paragraph. No mention of a tested fact is removed or replaced. |

Wording differences in the shared sentences:
- SayOnce and SayTwice: "Because of its warmth, bracklin cloth is used mainly for winter outerwear and ceremonial robes."
  SayThrice and Distract drop the reason: "The cloth is used mainly for winter outerwear and ceremonial robes."
- Distract only: paragraph 1 ends with "It takes deep, even color with acid dyes but resists discharge printing." This is
  the only occurrence of acid dyes or discharge printing in any version, and no question tests it.

## Tested facts and every mention

Counts are mentions of the fact. "Restates" = says the same fact again; "partial" = refers back to the fact without
restating it in full; "+ new" = repeats the fact and adds information that is not tested.

### F1 Material: made exclusively from the fleece of the Grennock mountain sheep (QFB01; animal-based fibre in QFB04)
| Version | Count | Mentions |
|---|---|---|
| SayOnce | 1 | "Bracklin is a textile made exclusively from the fleece of the Grennock mountain sheep." |
| SayTwice | 2 | the SayOnce sentence; "Every bolt of Bracklin traces back to the same source: fleece sheared from the particular breed of mountain sheep that live in the highlands of Grennock." (restates) |
| SayThrice | 3 | the two SayTwice sentences; "Grennock mountain sheep fleece makes particularly warm fabrics." (restates + new: warmth) |
| Distract | 1 | the SayOnce sentence |

### F2 Weaving: double-weft interlock weaving, two threads lock around each other, binding two layers without stitching (QFB02, QFB03)
| Version | Count | Mentions |
|---|---|---|
| SayOnce | 1 | "Bracklin is woven using double-weft interlock weaving: two threads lock around each other, binding two layers of cloth together without any stitching." |
| SayTwice | 2 | the SayOnce sentence; "That locking — not crossing — is why double-weft interlock weaving keeps its layers bound tight." (restates) |
| SayThrice | 3 | the two SayTwice sentences; "No extra thread is needed — double-weft interlock weaving holds itself together." (restates) |
| Distract | 1 | the SayOnce sentence |

### F3 Uses: mainly winter outerwear and ceremonial robes (QFB04, QFB05 option 3)
| Version | Count | Mentions |
|---|---|---|
| SayOnce | 1 | "Because of its warmth, bracklin cloth is used mainly for winter outerwear and ceremonial robes." |
| SayTwice | 2 | the SayOnce sentence; "Those are bracklin's two main uses — winter outerwear and ceremonial robes." (restates) |
| SayThrice | 3 | "The cloth is used mainly for winter outerwear and ceremonial robes."; "Those are bracklin's two main uses — winter outerwear and ceremonial robes, nothing else."; "Both draw on the same warmth, just for different occasions." (partial: refers to the uses without naming them) |
| Distract | 1 | "The cloth is used mainly for winter outerwear and ceremonial robes." |

The phrases "winter outerwear" and "ceremonial robes" each occur 1 / 2 / 2 / 1 times.

### F4 Colour: before dyeing, ranges from warm ivory to ash grey (QFB05 option 1)
| Version | Count | Mentions |
|---|---|---|
| SayOnce | 1 | "Before it is dyed, bracklin fabric ranges from warm ivory to ash grey." |
| SayTwice | 2 | the SayOnce sentence; "That ivory-to-grey range comes straight from the sheep's own coat." (restates + new: from the coat) |
| SayThrice | 3 | the two SayTwice sentences; "Pale ivory bolts are rarest; most fleece runs closer to ash-grey." (restates both ends + new: frequency) |
| Distract | 1 | the SayOnce sentence |

### Term counts (case-insensitive string counts)

| Term | SayOnce | SayTwice | SayThrice | Distract |
|---|---|---|---|---|
| Bracklin | 5 | 6 | 5 | 3 |
| Grennock | 1 | 2 | 3 | 1 |
| double-weft interlock | 1 | 2 | 3 | 1 |
| winter outerwear | 1 | 2 | 2 | 1 |
| ceremonial robes | 1 | 2 | 2 | 1 |
| ivory | 1 | 2 | 3 | 1 |
| ash grey / ash-grey | 1 | 1 | 2 | 1 |
| discharge printing | 0 | 0 | 0 | 1 |
| Vessamere | 0 | 0 | 0 | 2 |

The concept name does not follow a 1×/2×/3× pattern (the SayOnce filler paragraph names it, and the sentences are
not built around it).

## Competitor paragraph (Distract only): Vessamere

| Feature | Vessamere (as heard) | Corresponding Bracklin fact |
|---|---|---|
| Origin and material | "made in a nearby coastal region", "spun from the silk-like filament produced by the harbor moth" | F1: Grennock mountain sheep fleece |
| Weaving | "a simple crossed-thread technique, passing the weft over and under a single warp line rather than locking multiple threads together" | F2: double-weft interlock, threads lock |
| Uses | "mainly for lightweight scarves and drapery rather than heavy garments" | F3: winter outerwear, ceremonial robes |
| Colour | "Its natural, undyed tone sits somewhere between soft copper and deep rust", from "the moth's own cocoon pigment"; usually left undyed | F4: warm ivory to ash grey |

## Questions and wrong-option provenance

**Competitor** = the option echoes the Vessamere paragraph; **pairing** = a 2×2 option right on one dimension and
wrong on the other; **not in any text** = invented foil.

| Question | Tests | Correct | Wrong options |
|---|---|---|---|
| QFB01 | F1 | 1 (sheep's wool), 2 (wool of Grennock mountain sheep) | 3 "any type of sheep": contradicts "exclusively"; not in any text. 4 "Cheshire mountain sheep": not in any text. |
| QFB02 | F2 (mechanism) | 1 (two threads lock), 2 (binds two layers without stitching) | 3 "Three threads are braided together": not in any text. 4 "bound together afterward with hand-stitching": contradicts "without any stitching"; not in any text. |
| QFB03 | F2 (name) | 1 (double-weft interlock weaving) | 2 "Double-warp chain weaving": not in any text. 3 "Cross-thread basket weaving": competitor (Vessamere's "simple crossed-thread technique"). 4 "Single-strand satin weaving": not in any text. |
| QFB04 | F1 (fibre class) × F3 | 5 (no option is right on both) | Correct would be animal-based + winter outerwear and ceremonial robes. 1: animal-based (right), "winter carpets and ceremonial wall tapestries" (not in any text). 2: animal-based (right), "summer garments and ceremonial robes" (half right). 3: "plant-based" (not in any text), carpets and tapestries. 4: plant-based, summer garments and ceremonial robes. |
| QFB05 | F4, F3 | 1 (warm ivory to ash grey), 3 (winter outerwear and ceremonial robes) | 2 "pale green to straw yellow": not in any text. 4 "summer clothing and decorative hangings": competitor (Vessamere "lightweight scarves and drapery"). |
| AT_fabrics | attention check | 1 (Bracklin) | 2 Calosse, 3 Marrowsilk, 4 Quillen: names in no text. Vessamere is not offered. |

## Notes

- Fibre class ("animal-based" in QFB04) is inferred from "fleece of the Grennock mountain sheep"; no text uses the
  words animal or plant.
- F3 has three mentions in SayThrice, but the third does not name the uses, so the use terms themselves are heard
  2 times in SayThrice.
- Distract is built from SayOnce plus one extra sentence, not by replacing a third mention in SayThrice; it is longer
  than SayThrice (176 vs 167 words).
