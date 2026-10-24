ENTRY = {
    'name': 'textarea',
    'gallery_template': 'basecoat/gallery_textarea.html',
    'index_label': 'Textarea states',
    'index_slot': 'header',
    'order': 20,
    'docs': r'''  <h3>Jinja macro</h3>
  <p>One shadcn part (<code>data-slot="textarea"</code>) that grows with its text. Pass a <code>class</code> such as <code>min-h-32</code> for a taller box, and <code>disabled</code>, <code>readonly</code>, <code>required</code> or <code>invalid</code> for states, and pass initial text with <code>content</code> or a <code>call</code> block. Give it a visible label (<code>for</code> the <code>id</code>) or <code>aria_label</code>, and link help or error text with <code>aria_describedby</code>. See all states in the <a href="{{ url_for('basecoat_gallery.gallery_textarea') }}">textarea gallery</a>.</p>
  <pre><code>{% raw %}{% from 'basecoat/textarea.html' import textarea %}
{{ textarea(id='message', name='message', placeholder='Type your message here.') }}
{{ textarea(id='bio', class='min-h-32', invalid=true, aria_describedby='bio-error') }}
{% call textarea(id='notes') %}Initial text{% endcall %}{% endraw %}</code></pre>

''',
}
