# Martial arts — feature and mention table

Written from the final texts in `texts/` and `questions.yaml`.

**Tested concept:** velthrak. **Competitor entity** (Distract version only): kestro.
Version names: SayOnce = `control`, SayTwice = `repeat_short`, SayThrice = `repeat_long`, Distract = `distractor`.

## Version structure

| Version | Words | Sentences | Construction |
|---|---|---|---|
| SayOnce | 156 | 8 | Paragraph 1: one sentence per tested fact (4). Paragraph 2: 4 filler sentences with no tested fact ("Watching a match in person gives a much better sense of the rhythm…"). |
| SayTwice | 152 | 9 | One paragraph per fact: the SayOnce sentence plus one restatement; the sornek paragraph has two follow-up sentences. No filler paragraph. |
| SayThrice | 219 | 13 | SayTwice plus a third sentence per fact; the sornek paragraph has four sentences (below). |
| Distract | 186 | 9 | SayOnce paragraph 1 verbatim, then a 5-sentence paragraph about kestro in place of the filler paragraph. No mention of a tested fact is removed or replaced. |

SayTwice is shorter than SayOnce (152 vs 156 words) because the SayOnce filler paragraph is long.

Wording differences in the shared sentences: SayTwice and SayThrice say "where no striking of any kind is permitted"
and "it is governed by the Dalviri Arts Council"; SayOnce and Distract say "where striking of any kind is not
permitted" and "velthrak is governed by the Dalviri Arts Council".

## Tested facts and every mention

Counts are mentions of the fact. "Restates" = says the same fact again; "+ new" = repeats the fact and adds
information that is not tested.

### F1 Style: a grappling art; striking of any kind is not permitted (QMA01; QMA05 option 1)
| Version | Count | Mentions |
|---|---|---|
| SayOnce | 1 | "Velthrak is a grappling art where striking of any kind is not permitted." |
| SayTwice | 2 | "Velthrak is a grappling art where no striking of any kind is permitted."; "Competitors win by throwing their opponent on the ground and pinning them, and are not allowed to punch, kick, or elbow." (restates) |
| SayThrice | 3 | the two SayTwice sentences; "Striking is off-limits at every level of competition, from practice rounds to sanctioned finals." (restates the no-striking rule) |
| Distract | 1 | the SayOnce sentence |

### F2 Signature move: the sornek, a sweeping hip throw that finishes in a floor pin (QMA02)
Two sub-facts are tested: the sornek is the signature technique (option 1) and it is a hip throw (option 2).

| Version | Hip throw | Signature technique | Sentences |
|---|---|---|---|
| SayOnce | 1 | 1 | "Its signature move is the sornek, a sweeping hip throw that finishes in a floor pin." |
| SayTwice | 2 | 2 | the SayOnce sentence; "To do a sornek, the thrower drives a hip beneath the opponent's centre of mass, sweeping them off balance and down to the floor." (hip throw); "It's the technique every velthrak practitioner is best known for." (signature) |
| SayThrice | 3 | 2 | the SayOnce sentence; the SayTwice hip sentence; "The thrower's hip acts as a fulcrum: once it clears the opponent's centre of mass, gravity finishes the throw." (hip throw + new); "No other velthrak technique is as recognizable." (signature; replaces "best known for") |
| Distract | 1 | 1 | the SayOnce sentence |

### F3 Training rule: full-resistance sparring is off-limits with under two years of experience (QMA04; QMA05 option 2)
| Version | Count | Mentions |
|---|---|---|
| SayOnce | 1 | "Full-resistance sparring is off-limits for anyone with under two years of experience." |
| SayTwice | 2 | the SayOnce sentence; "The rule protects newer practitioners until their defensive technique is solid enough to handle full resistance after two years." (restates + new: why) |
| SayThrice | 3 | the two SayTwice sentences; "Coaches enforce the two year restriction strictly — no exceptions are made regardless of size or prior combat experience." (restates + new) |
| Distract | 1 | the SayOnce sentence |

### F4 Governing body: the Dalviri Arts Council, founded in 1947 (QMA03)
| Version | Count | Mentions |
|---|---|---|
| SayOnce | 1 | "Originating in the Dalviri Highlands, velthrak is governed by the Dalviri Arts Council, which was founded in 1947." |
| SayTwice | 2 | "Originating in the Dalviri Highlands, it is governed by the Dalviri Arts Council, which was founded in 1947."; "Since its 1947 founding, the Dalviri Arts Council has set grades, licensed instructors, and overseen all sanctioned competition worldwide." (restates + new) |
| SayThrice | 3 | the two SayTwice sentences; "The Dalviri Arts Council's 1947 founding charter is the sole governing document for all certification to this day." (restates + new) |
| Distract | 1 | the SayOnce sentence |

The origin (Dalviri Highlands) is mentioned once in every version and is not tested.

### Term counts (case-insensitive string counts)

| Term | SayOnce | SayTwice | SayThrice | Distract |
|---|---|---|---|---|
| velthrak | 2 | 2 | 2 | 2 |
| sornek | 1 | 2 | 2 | 1 |
| hip | 1 | 2 | 3 | 1 |
| two year(s) | 1 | 2 | 3 | 1 |
| Dalviri Arts Council | 1 | 2 | 3 | 1 |
| 1947 | 1 | 2 | 3 | 1 |
| strik(e/ing) | 1 | 1 | 2 | 6 |
| kestro | 0 | 0 | 0 | 1 |

## Competitor paragraph (Distract only): kestro

| Feature | kestro (as heard) | Corresponding velthrak fact |
|---|---|---|
| Style | "a related striking art from a neighboring region … built around punches, kicks, and elbow strikes rather than throws" | F1: grappling, no striking; F2: hip throw |
| Scoring | ten-point system: torso strike 2, head strike 3, knockdown 5; a point deducted for any strike below the waist | — |
| Divisions | five weight tiers, each with a minimum number of sanctioned bouts before national ranking | F3: two-year sparring rule (a different kind of eligibility rule) |
| Format | three rounds of two minutes, ninety-second rest | — |
| Judging | three officials score independently; central scoring table; majority decision resolves split verdicts | F4: governing body (no kestro body is named) |

## Questions and wrong-option provenance

**Competitor** = the option echoes the kestro paragraph; **not in any text** = invented foil.

| Question | Tests | Correct | Wrong options |
|---|---|---|---|
| QMA01 | F1 | 1 (grappling-focused), 2 (no striking of any kind) | 3 "a striking-focused art": competitor (kestro is "a related striking art"). 4 "allows limited strikes during competition": contradicts F1; echoes kestro's strikes. |
| QMA02 | F2 | 1 (signature technique), 2 (hip throw) | 3 "starts with a spinning elbow strike to the opponent's shoulder": echoes kestro's "elbow strikes". 4 "begins with a leg pick": not in any text. |
| QMA03 | F4 | 1 (Dalviri Arts Council), 3 (formed in 1947) | 2 "formed in 1967": not in any text. 4 "the Dalviri Federation of Combat Arts": not in any text. |
| QMA04 | F3 | 4 (two years before full-resistance sparring) | 1 "Full-resistance sparring involves kicking and punching": contradicts F1; echoes kestro's punches and kicks. 2 "200 strikes on a bag before each session": not in any text. 3 "three years": not in any text. |
| QMA05 | F1, F3 | 1 (striking in any form is against the rules), 2 (a one-year practitioner cannot spar at full resistance; follows from the two-year rule) | 3 "The sornek may only be performed in championship-level bouts": not in any text. 4 "competition surfaces … approved by the Dalviri Federation of Combat Arts": not in any text. |
| AT_martial_arts | attention check | 1 (a style of martial arts) | 2–4 unrelated categories. |

## Notes

- Distract is built from SayOnce, not by replacing a third mention in SayThrice; it is shorter than SayThrice
  (186 vs 219 words).
