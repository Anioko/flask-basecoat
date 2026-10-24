from flask_assets import Bundle

# styles/app.css is built by the Tailwind CLI from app/assets/styles/input.css (see package.json), not by Flask-Assets.
app_js = Bundle('app.js', filters='jsmin', output='scripts/app.js')

# Vendor bundle: removed Semantic UI and jQuery to avoid conflicting styles with Flask-Basecoat.
# Vanilla JS utilities: tablesort (table sorting) and zxcvbn (password strength).
vendor_css = Bundle(output='styles/vendor.css')

vendor_js = Bundle(
    'vendor/tablesort.min.js',
    'vendor/zxcvbn.js',
    filters='jsmin',
    output='scripts/vendor.js')
