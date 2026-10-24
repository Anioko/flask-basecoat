ENTRY = {
    'name': 'button',
    'gallery_template': 'basecoat/gallery_button.html',
    'index_label': 'Button states',
    'index_slot': 'header',
    'order': 10,
    'related': ['badge', 'card', 'alert'],
    'docs': r'''  <h3>Jinja macro</h3>
  <p>Every shadcn variant and size, plus <code>disabled</code>, <code>loading</code>, <code>invalid</code> and <code>href</code> (renders a link with the same classes). Children come from <code>content</code> or a <code>call</code> block. Icon-only buttons need <code>aria_label</code>. See all states in the <a href="{{ url_for('basecoat_gallery.gallery_button') }}">button gallery</a>.</p>
  <pre><code>{% raw %}{% from 'basecoat/button.html' import button %}
{{ button(content='Save', variant='default') }}
{% call button(variant='outline', size='sm') %}Next{% endcall %}
{{ button(content='Please wait', loading=true) }}
{{ button(content='Docs', variant='link', href='/docs') }}{% endraw %}</code></pre>
  <div class="docs-preview" data-preview>
    <div class="component-usage">
      <h4>Form Actions</h4>
      <div class="component-example">
        <button class="btn btn-primary" type="submit">Save Changes</button>
        <button class="btn btn-secondary" type="button">Cancel</button>
      </div>
      
      <h4>Navigation</h4>
      <div class="component-example">
        <button class="btn btn-outline" type="button">← Previous</button>
        <button class="btn btn-primary" type="button">Next →</button>
      </div>
      
      <h4>Destructive Actions</h4>
      <div class="component-example">
        <button class="btn btn-destructive" type="button">Delete Item</button>
        <button class="btn btn-ghost" type="button">Cancel</button>
      </div>
    </div>
  </div>
  
''',
}
