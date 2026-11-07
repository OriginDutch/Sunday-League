# Sunday League — Chalkboard Texture & SVG Asset Pack

All assets are transparent PNG or vector SVG. The game panel base colour is `#20372A`; the clubhouse accent is `#E8D9A8`.

## Files
- `chalk_panel_overlay_512.png` — 512×512 RGBA chalk smudge/dust overlay, intended to tile in both directions.
- `chalk_panel_preview_3x3.png` — 1536×1536 visual preview of the texture repeated 3×3 over a panel fill using #20372A at 93% opacity.
- `chalk_underline_01.svg`, `chalk_underline_02.svg`, `chalk_underline_03.svg` — three 240×8 hand-drawn chalk underline variations. Stroke colour is #E8D9A8; recolour via SVG tint/replace if needed.
- `chalk_progress_fill_64x16.png` — 64×16 RGBA white chalk fleck pattern, intended to tile horizontally and be tinted to #E8D9A8 by the game.
- `crest_home.svg` — simple homemade home-club shield with leaf motif.
- `crest_opponent.svg` — neutral opponent shield with football motif.

## Godot use
- Import PNG files with alpha preserved. Use `chalk_panel_overlay_512.png` as a repeating texture over a flat `StyleBoxFlat` panel fill of `#20372A`.
- Keep overlay modulation subtle. The PNG alpha is deliberately low to keep 14px text legible.
- Tile the 512px texture on both axes; do not stretch it to the full panel size.
- Use `chalk_progress_fill_64x16.png` as a repeating horizontal overlay/mask on the filled portion of the progress bar, with modulation/tint `#E8D9A8`.
- SVGs are plain vector assets with no embedded text. Recolour SVG strokes through theme colour substitution or SVG tinting.
- The home and opponent crests are both designed to sit side by side in the Next Match card.

## Visual direction
Final style: chalkboard treatment with handwritten Caveat headings and chalk underlines, in clubhouse canteen colours:
- Panel: `#20372A`
- Border: `#526D57`
- Text: `#F5F0DF`
- Accent: `#E8D9A8`

The ticker and navigation should remain on one slim floating strip above the bottom edge. Keep both home and away crests in the Next Match card.
