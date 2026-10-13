# /// script
# requires-python = ">=3.10"
# dependencies = ["fonttools"]
# ///
"""Write static TTFs from variable fonts as specified in resources/fonts/instances.json.

Pebble's font converter only uses a variable font's default instance (Thin for Outfit),
so weight and width have to be baked into static TTFs that are then registered as resources.
OpenType feature substitutions (ss01 etc.) are not applied either, so glyph_substitutions
rewrites the cmap directly.

Usage: uv run scripts/build-fonts.py
"""

import json
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

FONTS_DIR = Path(__file__).resolve().parent.parent / "resources" / "fonts"
CONFIG = FONTS_DIR / "instances.json"


def substitute_glyphs(font: TTFont, substitutions: dict[str, str], source_name: str) -> None:
    glyphs = set(font.getGlyphOrder())
    for char, glyph in substitutions.items():
        if glyph not in glyphs:
            raise SystemExit(f"glyph '{glyph}' for '{char}' not found in source '{source_name}'")
        for table in font["cmap"].tables:
            if ord(char) in table.cmap:
                table.cmap[ord(char)] = glyph


def main() -> None:
    config = json.loads(CONFIG.read_text())
    sources = config["sources"]
    for filename, spec in config["instances"].items():
        source_name = spec["source"]
        if source_name not in sources:
            raise SystemExit(f"{filename}: unknown source '{source_name}' in {CONFIG.name}")
        source = sources[source_name]
        font = instantiateVariableFont(TTFont(FONTS_DIR / source["file"]), spec["axes"])
        substitute_glyphs(font, source.get("glyph_substitutions", {}), source_name)
        # Keep the source font's timestamp so identical settings produce identical files
        font.recalcTimestamp = False
        out = FONTS_DIR / filename
        font.save(out)
        print(f"{out.relative_to(FONTS_DIR.parent.parent)}: {source_name} {spec['axes']}")


if __name__ == "__main__":
    main()
