"""
Interactive Component Gallery Blueprint for Basecoat UI.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from wtforms import Form, StringField, PasswordField, BooleanField, SelectField, TextAreaField, validators

gallery_bp = Blueprint('basecoat_gallery', __name__, template_folder='templates')


class DemoForm(Form):
    name = StringField('Full Name', [validators.Length(min=4, max=25), validators.InputRequired()], description="Enter your full legal name.")
    email = StringField('Email Address', [validators.Email(), validators.InputRequired()], description="We'll never share your email.")
    role = SelectField('Team Role', choices=[('dev', 'Developer'), ('lead', 'Tech Lead'), ('pm', 'Product Manager')])
    bio = TextAreaField('Short Biography', [validators.Optional(), validators.Length(max=200)], description="A brief summary.")
    terms = BooleanField('I agree to the terms and privacy policy', [validators.InputRequired()])


@gallery_bp.route('/', methods=['GET', 'POST'])
@gallery_bp.route('/gallery', methods=['GET', 'POST'])
def gallery():
    form = DemoForm(request.form)
    if request.method == 'POST':
        if form.validate():
            flash('Demo form submitted successfully! All validations passed.', 'success')
            return redirect(url_for('basecoat_gallery.gallery'))
        else:
            flash('Please correct the validation errors in the form.', 'error')

    sample_columns = ["Element", "Type", "Status", "Owner", "Health"]
    sample_rows = [
        ["User Authentication", "Service", "Operational", "SecOps", "99.9%"],
        ["Order Processing", "Pipeline", "Degraded", "Commerce", "94.2%"],
        ["Billing Gateway", "Service", "Operational", "Finance", "99.8%"]
    ]

    return render_template(
        'basecoat/gallery.html',
        form=form,
        sample_columns=sample_columns,
        sample_rows=sample_rows
    )


@gallery_bp.route('/gallery/input')
def gallery_input():
    return render_template('basecoat/gallery_input.html')


@gallery_bp.route('/gallery/button')
def gallery_button():
    theme = 'dark' if request.args.get('theme') == 'dark' else 'light'
    return render_template('basecoat/gallery_button.html', theme=theme)


@gallery_bp.route('/gallery/textarea')
def gallery_textarea():
    theme = 'dark' if request.args.get('theme') == 'dark' else 'light'
    return render_template('basecoat/gallery_textarea.html', theme=theme)
