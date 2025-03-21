This addon adds a highlighting outline to cards the first time that you see them.

`alpha` goes from 0 to 1 and controls the initial opacity of the outline.

`fade_out` decides whether the fades out over the course of 2 seconds or stays until you flip the card.

`border_width` controls the width of the outline. It can be input in any unit that is valid in css.

`border_colors` and `border_colors_night` are the pools from which outline colors are selected - in light mode, the color of the outline will be the color from `border_colors` that is farthest from the current card's background color, and similarly in night mode for `border_colors_night`.