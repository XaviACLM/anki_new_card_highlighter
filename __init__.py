import json
import os
import sys

from aqt import gui_hooks, mw
from aqt.editor import Editor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from csscolor import parse

from .new_card_highlighter import NewCardHighlighter


config = mw.addonManager.getConfig(__name__)
new_card_highlighter = NewCardHighlighter(
    config['border_colors'],
    config['border_colors_night'],
    config['alpha'],
    config['border_width'],
    config['fade_out'],
)

gui_hooks.card_will_show.append(new_card_highlighter.add_highlight_if_card_is_new)


def clear_cache_after_editing_templates_callback(txt: str, editor: Editor) -> str:
    new_card_highlighter.clear_cache()
    return txt


def clear_cache_after_editing_config_callback(txt: str, addon: str) -> str:
    new_card_highlighter.clear_cache()
    return txt


gui_hooks.editor_will_munge_html.append(clear_cache_after_editing_templates_callback)
gui_hooks.addon_config_editor_will_update_json.append(clear_cache_after_editing_config_callback)


def update_values_from_config_callback(txt: str, addon: str) -> str:
    # ...why isn't there a hook for _after_ the config has been updated? man
    try:
        new_values = json.loads(txt)
        new_card_highlighter.border_colors = [parse.color(border_color).as_int_triple() for border_color in
                                              new_values['border_colors']]
        new_card_highlighter.border_colors_night = [parse.color(border_color).as_int_triple() for border_color in
                                                    new_values['border_colors_night']]
        new_card_highlighter.alpha = new_values['alpha']
        new_card_highlighter.border_width = new_values['border_width']
        new_card_highlighter.fade_out = new_values['fade_out']
        new_card_highlighter.clear_cache()
    except:
        print("Something went wrong parsing the config - likely user error. Anki's own error message should"
              "pop up after this.")
    return txt


gui_hooks.addon_config_editor_will_update_json.append(update_values_from_config_callback)
