ENTRY = {
    'name': 'select',
    'gallery_template': 'basecoat/gallery_select.html',
    'themed': False,
    'index_label': 'Select',
    'index_slot': 'header-nav',
    'context': {'numbers': [(n, f'Number {n}') for n in range(1, 31)]},
    'docs': r'''  <div class="docs-preview" data-preview data-docs-entry="select">
    <div class="component-usage">
      <h4>Jinja macro</h4>
      <p>Behaviour (open, arrow keys, Home/End, Enter, Escape, hidden form value) comes from Basecoat's select script; use <code>caller()</code> for groups, labels and separators.</p>
      <pre><code>{% raw %}{% from 'basecoat/select.html' import select, select_group, select_item, select_separator %}

{{ select(name='fruit', id='fruit', placeholder='Select a fruit', label='Fruit',
          options=[('apple', 'Apple'), ('banana', 'Banana')]) }}

{% call select(name='tz', id='tz', placeholder='Timezone', size='sm') %}
  {% call select_group(label='Europe', id='tz-eu') %}
    {{ select_item(value='cet', content='CET') }}
  {% endcall %}
{% endcall %}{% endraw %}</code></pre>
      <p>Arguments: <code>value</code>, <code>placeholder</code>, <code>size</code> (<code>default</code> or <code>sm</code>), <code>disabled</code>, <code>invalid</code>, <code>required</code>, <code>class</code>. Include <code>select-placeholder.js</code> after Basecoat's script to show a placeholder instead of the first option, and <code>select-scroll.js</code> for the scroll up and down buttons on long lists.</p>
      <p><a class="docs-link" href="/basecoat/gallery/select">See every state in the development gallery &rarr;</a></p>
    </div>
  </div>
''',
}
