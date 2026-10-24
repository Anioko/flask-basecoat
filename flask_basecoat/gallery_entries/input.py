ENTRY = {
    'name': 'input',
    'gallery_template': 'basecoat/gallery_input.html',
    'themed': False,
    'index_label': 'Input',
    'related': ['button', 'alert', 'card'],
    'docs': r'''  {% from 'basecoat/input.html' import input as shadcn_input %}
  <div class="docs-preview" data-preview>
    <div class="component-usage" data-docs-input>
      <h4>Shadcn input macro</h4>
      <p>
        <code>{% raw %}{% from 'basecoat/input.html' import input %}{% endraw %}</code>.
        Arguments: <code>type</code>, <code>placeholder</code>, <code>value</code>, <code>disabled</code>,
        <code>readonly</code>, <code>required</code>, <code>invalid</code> (sets <code>aria-invalid</code>),
        <code>describedby</code>, <code>label</code> (<code>aria-label</code>), <code>class</code>; any other
        keyword becomes an HTML attribute. Input has no children, so there is no <code>caller()</code> slot.
        See the <a class="docs-link" href="/basecoat/gallery/input">gallery entry</a> for every state.
      </p>
      <div class="component-example">
        {{ shadcn_input(id='docs-input-email', type='email', placeholder='Email', label='Email') }}
        {{ shadcn_input(id='docs-input-invalid', value='ab', invalid=true, label='Username') }}
      </div>
    </div>
  </div>
''',
}
