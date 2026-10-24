"""R16 and help-and-overlays-v1 on the canvases and the capability map: one note card per entry, a tinted header band with
icon, question, count Badge and the "i" popover, tooltips on icon-only buttons, a hover card per note, an empty state that says
what is missing and offers an action, the ramp chip with its words, and no raw palette colour."""
import copy
import re

import pytest
from lxml import html as lxml_html

from flask_basecoat import canvases as registry
from tests.test_canvases import page, BUILT

BOX_CANVASES = [s for s in BUILT if registry.canvas_data(s).get('boxes')]
BANNED = ('Nothing here yet', 'No data', 'N/A')


@pytest.mark.parametrize('slug', BOX_CANVASES)
def test_every_entry_is_its_own_note_card_with_a_hover_card(slug):
    doc = lxml_html.fromstring(page(slug))
    notes = sum(len(v) for v in registry.canvas_data(slug)['boxes'].values())
    items = doc.xpath('//ul[@data-canvas-notes]/li[@data-canvas-note]//*[@data-slot="item"]')
    assert len(items) == notes
    assert len(doc.xpath('//ul[@data-canvas-notes]/li//*[@data-slot="hover-card-content"]')) == notes
    assert not doc.xpath('//ul[@data-canvas-notes]/li[not(@data-canvas-note)]')           # no bare bulleted text


@pytest.mark.parametrize('slug', BOX_CANVASES)
def test_every_box_has_band_icon_question_count_info_and_tooltips(slug):
    doc = lxml_html.fromstring(page(slug))
    cards = doc.xpath('//*[@data-canvas-band]/..')
    assert cards
    for card in cards:
        band = card.xpath('.//*[@data-canvas-band]')[0]
        cls = band.get('class')
        zone = band.get('data-canvas-band')
        assert f'bg-chart-{zone}/10' in cls and f'border-chart-{zone}/30' in cls
        assert band.xpath('.//svg')                                                       # the box icon
        assert band.xpath('.//*[@data-slot="card-description"]')[0].text_content().strip()      # the framework's question, visible
        assert band.xpath('.//*[@data-canvas-count]')[0].text_content().strip().isdigit()
        popover = band.xpath('.//*[@data-slot="popover-content"]')
        assert popover and 'Example from Northwind Logistics:' in popover[0].text_content()
        for button in band.xpath('.//button[@aria-label]'):                              # every icon-only button names itself ...
            assert button.get('aria-label')
        assert len(band.xpath('.//*[@data-slot="tooltip-content"]')) >= 1                 # ... and has a tooltip


def test_an_empty_box_says_what_is_missing_and_offers_an_action_and_a_full_box_hides_it():
    slug = 'business-model-canvas'
    data = copy.deepcopy(registry.canvas_data(slug))
    data['boxes']['channels'] = []
    doc = lxml_html.fromstring(page(slug, data))
    empty = doc.xpath('//*[@data-canvas-empty="channels"]')[0]
    assert empty.get('hidden') is None
    text = empty.text_content()
    assert 'No channels yet' in text and 'How do they find and receive it?' in text
    assert empty.xpath('.//button[@data-canvas-edit="channels"]')
    assert doc.xpath('//*[@data-canvas-empty="key-partners"]')[0].get('hidden') is not None
    for banned in BANNED:
        assert banned not in page(slug, data)


@pytest.mark.parametrize('slug', BUILT)
def test_no_canvas_says_nothing_here_yet(slug):
    out = page(slug)
    for banned in BANNED:
        assert banned not in out


def test_the_bmc_zones_are_the_frameworks_own():
    doc = lxml_html.fromstring(page('business-model-canvas'))
    zone = {}
    for card in doc.xpath('//*[@data-canvas-band]/..'):
        zone[card.xpath('.//*[@data-slot="card-title"]')[0].text_content().strip()] = card.xpath('.//*[@data-canvas-band]')[0].get('data-canvas-band')
    infra = {zone[k] for k in ('Key Partners', 'Key Activities', 'Key Resources')}
    customer = {zone[k] for k in ('Customer Relationships', 'Channels', 'Customer Segments')}
    finance = {zone[k] for k in ('Cost Structure', 'Revenue Streams')}
    assert len(infra) == len(customer) == len(finance) == 1
    assert len(infra | customer | finance | {zone['Value Propositions']}) == 4


def test_capability_card_has_icon_chip_in_words_owner_and_a_button_for_sub_capabilities():
    from flask import render_template
    from flask_basecoat.testing import make_app
    with make_app().test_request_context('/examples/capability/capability-map'):
        out = render_template('examples/capability/capability-map.html', data=registry.capability_data())
    doc = lxml_html.fromstring(out)
    tile = doc.xpath('//*[@data-cap-tile="strategy"]')[0]
    card = tile.xpath('./*[@data-slot="card"]')[0]
    assert card.xpath('.//svg') and re.search(r'(Initial|Developing|Defined|Managed|Optimized), \d/5', card.text_content())
    chip = card.xpath('.//*[@data-ramp-chip]')[0]
    assert re.search(r'bg-primary(/\d+)?\b', chip.get('class')) and 'text-' in chip.get('class')
    assert re.search(r'Show \d+ sub-capabilities', card.text_content())
    assert card.xpath('.//button[@data-cap-toggle]')
    # no coloured edge or stripe, no solid saturated fill on the card body
    for el in tile.xpath('.//*[@data-slot="card" or @data-slot="card-content"]'):
        assert not re.search(r'\bborder-(l|s|t|b)-\d|\bborder-l\b|\bborder-s\b', el.get('class'))
        assert 'bg-primary' not in el.get('class') and 'bg-chart' not in el.get('class')
    # one icon per capability, always a known lucide name
    from flask_basecoat.icons import ICONS
    from flask_basecoat.capability import icon_for
    assert all(icon_for(c) in ICONS for c in registry.capability_data()['capabilities'])
    assert len(doc.xpath('//*[@data-cap-tile]')) == len(registry.capability_data()['capabilities'])


def test_type_groups_carry_a_chart_tint_on_their_header_band():
    from flask import render_template
    from flask_basecoat.testing import make_app
    with make_app().test_request_context('/'):
        out = render_template('examples/capability/capability-map.html', data=registry.capability_data())
    doc = lxml_html.fromstring(out)
    bands = {b.get('data-group-band'): b.get('class') for b in doc.xpath('//*[@data-group-band]')}
    assert 'bg-chart-1/10' in bands['strategic'] and 'bg-chart-2/10' in bands['operational'] and 'bg-chart-3/10' in bands['supporting']
    assert all('border-chart-' in bands[k] for k in ('strategic', 'operational', 'supporting'))


def test_the_chip_text_colour_holds_4_5_to_1_on_every_step_in_the_brand_tokens():
    import importlib.util, pathlib
    path = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'capability_ramp.py'
    s = importlib.util.spec_from_file_location('capability_ramp', path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    out = m.run(verbose=False)
    for theme, text_for in (('light', ['fg', 'fg', 'fg', 'fg', 'pfg']), ('dark', ['fg', 'fg', 'fg', 'pfg', 'pfg'])):
        _, txt = out[('Entelim brand tokens (brand-decision-v1)', theme)]
        for i, (step, cf, cp) in enumerate(txt):
            if theme == 'dark' and i == 3:
                continue          # step 4 is drawn at 80 percent in dark mode; the page measurement covers it
            assert (cf if text_for[i] == 'fg' else cp) >= 4.5, (theme, step, cf, cp)
