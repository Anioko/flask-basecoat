"""Unit tests for ui.harvey_ball (R20) and the document macros (R17)."""
import re

import pytest

from flask_basecoat.document import HARVEY_VALUES, harvey_ball
from flask_basecoat.testing import make_app


@pytest.fixture(scope='module')
def app():
    return make_app()


def render(app, source, **ctx):
    with app.test_request_context():
        return app.jinja_env.from_string("{% import 'basecoat/index.html' as ui %}" + source).render(**ctx)


@pytest.mark.parametrize('value', [0, 25, 50, 75, 100])
def test_harvey_ball_names_each_value(app, value):
    html = render(app, '{{ ui.harvey_ball(v) }}', v=value)
    assert f'aria-label="{value} per cent"' in html
    assert 'role="img"' in html and f'data-value="{value}"' in html
    assert 'width="16"' in html and 'height="16"' in html and 'viewBox="0 0 16 16"' in html
    assert 'size-4' in html


def test_harvey_ball_wedge_grows_with_the_value(app):
    wedges = {v: re.findall(r'<path ', render(app, '{{ ui.harvey_ball(v) }}', v=v)) for v in HARVEY_VALUES}
    assert wedges[0] == []                                  # an empty ring
    assert all(len(wedges[v]) == 1 for v in (25, 50, 75, 100))
    paths = [re.search(r' d="([^"]+)"', render(app, '{{ ui.harvey_ball(v) }}', v=v)).group(1) for v in (25, 50, 75, 100)]
    assert len(set(paths)) == 4


def test_harvey_ball_uses_tokens_and_needs_no_runtime(app):
    html = render(app, '{{ ui.harvey_ball(75, class="ms-2") }}')
    assert 'fill-foreground' in html and 'stroke-foreground' in html and 'fill-background' in html
    assert not re.search(r'#[0-9a-fA-F]{3,8}\b|rgb|hsl|oklch|style=', html)
    assert 'data-chart' not in html and '<script' not in html
    assert 'ms-2' in html


@pytest.mark.parametrize('value', [10, 101, -25, 'half', None, '75.0', 7.5])
def test_harvey_ball_refuses_other_values(value):
    with pytest.raises(ValueError):
        harvey_ball(value)


def test_harvey_ball_accepts_numbers_written_as_text(app):
    assert 'aria-label="50 per cent"' in render(app, '{{ ui.harvey_ball("50") }}')


COVER = "{{ ui.document_cover(title=t, organisation='Harbourline', date='24 October 2026', version='1.2', author='Amara Okafor') }}"


def test_cover_shows_the_five_fields(app):
    html = render(app, COVER, t='Claims Platform')
    assert re.search(r'<h1[^>]*data-document-title>Claims Platform</h1>', html)
    assert 'data-document-cover' in html and html.lstrip().startswith('<header')
    assert 'Harbourline' in html and '24 October 2026' in html and 'Version 1.2' in html and 'by Amara Okafor' in html


def test_cover_escapes_its_text(app):
    html = render(app, COVER, t='<script>alert(1)</script>')
    assert '<script>' not in html and '&lt;script&gt;' in html


def test_cover_requires_every_field(app):
    with pytest.raises(Exception):
        render(app, "{{ ui.document_cover(title='T', organisation='O', date='D', version='1') }}")


def test_document_frame_is_the_blog_detail_column(app):
    html = render(app, '{% call ui.document() %}{% call ui.document_body() %}<h2>One</h2>{% endcall %}{% endcall %}')
    assert 'mx-auto max-w-4xl px-6 py-12' in html and 'data-document>' in html
    assert 'data-document-body' in html and '<h2>One</h2>' in html


def test_title_style_is_a_css_string(app):
    html = render(app, '<html style="{{ ui.document_title_style(t) }}">', t='Say "hi" \\ now')
    assert html == '<html style="--document-title: &#34;Say \\&#34;hi\\&#34; \\\\ now&#34;">'
