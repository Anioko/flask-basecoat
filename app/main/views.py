from flask import Blueprint, render_template

from app.models import EditableHTML

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('main/index.html')


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template(
        'main/about.html', editable_html_obj=editable_html_obj)


@main.route('/kitchen-sink')
def kitchen_sink():
    return render_template('main/kitchen_sink.html')


@main.route('/diagnostic')
def diagnostic():
    return render_template('main/diagnostic.html')


@main.route('/sidebar-demo')
def sidebar_demo():
    return render_template('main/sidebar_demo.html')


@main.route('/sidebar-demo-new')
def sidebar_demo_new():
    return render_template('main/sidebar_demo_new.html')
