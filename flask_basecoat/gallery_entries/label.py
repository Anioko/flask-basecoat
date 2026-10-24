ENTRY = {
    'name': 'label',
    'gallery_template': 'basecoat/gallery_label.html',
    'index_label': 'Label states',
    'index_slot': 'header',
    'order': 30,
    'docs': r'''  <h3>Jinja macro</h3>
  <p>One shadcn part (<code>data-slot="label"</code>). Pass <code>for</code> with the control's <code>id</code> so the label names it and clicking it focuses or toggles the control, give the label text with <code>content</code> or a <code>call</code> block, and add <code>id</code> or <code>class</code> when needed. Disabled styling follows the markup as in shadcn: put <code>peer</code> on a disabled control that precedes the label, or <code>group</code> with <code>data-disabled="true"</code> on an ancestor. See all states in the <a href="{{ url_for('basecoat_gallery.gallery_label') }}">label gallery</a>.</p>
  <pre><code>{% raw %}{% from 'basecoat/label.html' import label %}
{{ label(for='email', content='Email') }}
{% call label(for='terms') %}Accept terms and conditions{% endcall %}{% endraw %}</code></pre>

''',
}
