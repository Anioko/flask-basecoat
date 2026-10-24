"""Static shapes for the document macros (R17, R20).

``harvey_ball`` validates a Harvey ball value and returns what the ``ui.harvey_ball`` macro draws. A Harvey ball
is a 16px inline SVG, so the shape is plain geometry: no chart runtime, one element per cell.
"""

# The wedge starts at 12 o'clock and runs clockwise. The ball is a circle of radius 7 in a 16 x 16 box.
_WEDGES = {
    0: None,
    25: 'M8 8V1A7 7 0 0 1 15 8Z',
    50: 'M8 8V1A7 7 0 0 1 8 15Z',
    75: 'M8 8V1A7 7 0 1 1 1 8Z',
    100: 'M8 1A7 7 0 1 1 8 15A7 7 0 1 1 8 1Z',
}

HARVEY_VALUES = tuple(_WEDGES)


def harvey_ball(value):
    """``{'value', 'label', 'wedge'}`` for 0, 25, 50, 75 or 100 (an int or its string). Anything else raises."""
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        number = None
    if number not in _WEDGES or str(value).strip() != str(number):
        raise ValueError(f'harvey_ball value must be one of {", ".join(map(str, HARVEY_VALUES))}, not {value!r}')
    return {'value': number, 'label': f'{number} per cent', 'wedge': _WEDGES[number]}
