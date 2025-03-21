import re
from typing import List, Optional, Tuple

from anki.cards import Card
from anki.consts import CARD_TYPE_NEW
from aqt import colors
from aqt.theme import theme_manager
from csscolor import parse
from csscolor.color import Color

from .util import linear_srgb_to_oklab


class NewCardHighlighter:
    def __init__(self, border_colors: List[str], border_colors_night: List[str], alpha: float, border_width: str,
                 fade_out: bool):
        self.border_colors = [parse.color(border_color).as_int_triple() for border_color in border_colors]
        self.border_colors_night = [parse.color(border_color).as_int_triple() for border_color in border_colors_night]
        self.alpha = alpha
        self.border_width = border_width
        self.fade_out = fade_out

        self._cache = dict()
        self._is_in_night_mode = None

    def get_border_color_options(self):
        if self._is_in_night_mode:
            return self.border_colors_night
        else:
            return self.border_colors

    def get_css_background_color(self, css: str) -> Optional[Tuple[int]]:
        if self._is_in_night_mode:
            pattern = r"(?:\.card\.night_mode|\.night_mode\.card) ?\{(.+?)\}"
        else:
            pattern = r"\.card ?\{(.+?)\}"

        card_style_elem = re.search(pattern, css, re.DOTALL)

        if card_style_elem is None:
            return None

        background_color_line = next(
            filter(
                lambda match: match is not None,
                map(
                    lambda line: re.match(" *background-color *: *(.+)[ \n]*[;}]", line),
                    card_style_elem.group(1).split("\n")
                )
            ),
            None
        )

        if background_color_line is None:
            return None

        return parse.color(background_color_line.group(1)).as_int_triple()

    @staticmethod
    def get_default_background_color() -> Tuple[int]:
        return theme_manager.qcolor(colors.CANVAS).getRgb()[:-1]

    def get_background_color(self, css: str) -> Tuple[int]:
        return self.get_css_background_color(css) or self.get_default_background_color()

    def get_furthest_border_color_from_background(self, background_color: Tuple[int]):

        bg_l, bg_a, bg_b = linear_srgb_to_oklab(background_color)

        def distance_to_background_color(border_color):
            l, a, b = linear_srgb_to_oklab(border_color)
            dl, da, db = l - bg_l, a - bg_a, b - bg_b
            return dl * dl + da * da + db * db

        return max(self.get_border_color_options(), key=distance_to_background_color)

    @staticmethod
    def get_border_highlight_style(border_width: str, border_color: str) -> str:
        return f"""\
.border-highlight{{
border: solid {border_width};
border-color: {border_color};
margin: 0;
padding: 0;
position: fixed;
inset: 0;
z-index: 100;
}}
"""

    def add_highlight_to_card(self, text: str):
        # css, html = re.fullmatch("<style>(.+?)</style><div id=\"questionSide\">(.+)", text, re.DOTALL).groups()
        css, html = re.fullmatch("<style>(.+?)</style>(.+)", text, re.DOTALL).groups()

        bg_color = self.get_background_color(css)
        border_color = self.get_furthest_border_color_from_background(bg_color)
        border_color_alpha_hex = Color(*border_color, self.alpha).as_rgba_string()
        border_highlight_style = self.get_border_highlight_style(self.border_width, border_color_alpha_hex)

        css = border_highlight_style + css
        html = '<div id="border-highlight" class="border-highlight"></div>\n' + html
        script_block = self.get_script_block()

        # text = f"<style>{css}</style>{html}<div id=\"questionSide\">"
        script_block = self.get_script_block() if self.fade_out else ""
        text = f"<style>{css}</style>{html}\n{script_block}"

        return text

    @staticmethod
    def get_script_block():
        return """\
<script>
    borderHighlight = document.getElementById('border-highlight');
    
    startTime = performance.now();

    function animate(currentTime) {
        const elapsedTime = currentTime - startTime;
        const t = elapsedTime / 1000;
        borderHighlight.style.opacity = Math.max(0, 1/(1+Math.exp(5*t-5)));

        if (t < 2) {
            requestAnimationFrame(animate);
        }
    }

    requestAnimationFrame(animate);
</script>
"""

    def add_highlight_if_card_is_new(self, text: str, card: Card, kind: str):

        if kind != 'reviewQuestion' or card.type != CARD_TYPE_NEW:
            return text

        self._is_in_night_mode = theme_manager.night_mode
        style_id = (self._is_in_night_mode, card.nid, card.ord)
        result = self._cache.get(style_id)
        if result is None:
            result = self.add_highlight_to_card(text)
            self._cache[style_id] = result

        return result

    def clear_cache(self):
        self._cache = dict()
