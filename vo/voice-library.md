# GLAMRDiP Voice Library (the VO menu)

12 active voices. **Every voice has a Default Model — the skill MUST respect it** (don't default to v3).
v3 voices render their native accent faithfully on `eleven_v3`. v2 voices drift accent on v3 (usually UK,
occasionally US) → use `eleven_multilingual_v2` to preserve training. PVCs are always v2.

> **Verified in THIS repo (2026-06-28):** our connected ElevenLabs MCP is on the same GLAMRDiP account —
> `get_voice` resolves these IDs (e.g. AUS GM = `[DS] - AUS GM`, cloned), and `list_models` confirms both
> `eleven_v3` and `eleven_multilingual_v2` are available. So this menu is live for us.

## Default voice
| Name | Voice ID | Default Model | Status |
|---|---|---|---|
| AUS GM | `xzXMPT6jO78GLrJEylPU` | `eleven_v3` | **DEFAULT** — use when brief says "Aussie female voice" with no specific name |

## v3-safe voices (3) — audio tags supported
Accent verified on `eleven_v3` (audition 17 Apr 2026). Tags ([concerned], [excited]…) only work here.
| Name | Voice ID | Default Model | Notes |
|---|---|---|---|
| AUS GM | `xzXMPT6jO78GLrJEylPU` | eleven_v3 | House default. Confirmed AU accent on v3. Tags supported. |
| Aurora | `9gB6fhbEaYv6yh0oS2bC` | eleven_v3 | Verified on v3. Accent TBD — annotate after first use. |
| Christina | `8hIxjmzo8YFAL1Ko5X5H` | eleven_v3 | Verified on v3. Accent TBD — annotate after first use. |

## v2-default voices (8) — NO audio tag support (pace via punctuation)
Drift accent on v3 (7/8 UK, 1/8 US). Always call with `eleven_multilingual_v2`.
| Name | Voice ID | Default Model | Notes |
|---|---|---|---|
| AUS SC | `ZyqFXToIpEx2sbDlEwJ9` | eleven_multilingual_v2 | Drifted UK on v3; preserved on v2. |
| Dawn | `ytRN3ATk6jFKjRYGj6Sl` | eleven_multilingual_v2 | Drifted UK on v3; preserved on v2. |
| Anna | `sx8pHRzXdQfuUYPGFK7X` | eleven_multilingual_v2 | Drifted UK on v3; preserved on v2. |
| Emma | `56bWURjYFHyYyVf490Dp` | eleven_multilingual_v2 | Drifted UK on v3; preserved on v2. |
| Gemma (1) | `319bKIhetA5g6tmywrwj` | eleven_multilingual_v2 | Drifted UK on v3; preserved on v2. |
| Gemma (2) | `jQQiXyFE3PBHLF8znAIb` | eleven_multilingual_v2 | Drifted US on v3; preserved on v2. |
| Grace | `kDkcCU8P99k3hAkb6b26` | eleven_multilingual_v2 | Drifted UK on v3; preserved on v2. |
| Tihana | `XVmI13Rh8OIYng4DzOJx` | eleven_multilingual_v2 | Drifted UK on v3; preserved on v2. |

## PVC voices (1) — always v2, no tags
| Name | Voice ID | Default Model | Notes |
|---|---|---|---|
| Kate PVC | `w9rPM8AIZle60Nbpw7nl` | eleven_multilingual_v2 | Pro Voice Clone. Re-audition for v3 when ElevenLabs ships PVC-v3 optimisation. |

## Removed (do not re-add)
AUS DM `B0qYu1h2P1JsYbpnIhzj` · Kylie `e1nbKcfTL4XYy71tZn9J` · Tanudja `6gviCf27bOZ2Wml5iZZv` ·
Brittaney `aEQxNaInxckQVVOYBEB6` — all quality-insufficient (v3 drift, no good on v2).

## Voice-selection presentation (when brief specifies no voice — STOP and ask)
```
Brief doesn't specify a voice. Which should I use?
 v3-safe (tags supported):   1.AUS GM (default)  2.Aurora  3.Christina
 v2-default (pacing only):   4.AUS SC 5.Dawn 6.Anna 7.Emma 8.Gemma(1) 9.Gemma(2) 10.Grace 11.Tihana
 PVC (v2 only):              12.Kate PVC
Reply with a name or number.
```

## v3 accent-drift finding (17 Apr 2026)
16 voices × 2 lines on v3: 4/16 held native accent (AUS GM, Aurora, Christina, Kate-on-v2), 11/16 drifted UK,
1/16 drifted US. Cause: v3 applies a stronger "default English" over training than v2. **Rule: always use the
voice's Default Model; for accent-critical work, audition before a full run.**
