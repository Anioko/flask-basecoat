from flask_assets import Bundle

# Use pyscss filter (python-based SCSS) so we can build without a system 'sass' binary.
app_css = Bundle('app.scss', filters='pyscss', output='styles/app.css')

app_js = Bundle('app.js', filters='jsmin', output='scripts/app.js')

# Vendor bundle: removed Semantic UI and jQuery to avoid conflicting styles with Basecoat.
# Vanilla JS utilities: tablesort (table sorting) and zxcvbn (password strength).
vendor_css = Bundle(output='styles/vendor.css')

vendor_js = Bundle(
    'vendor/tablesort.min.js',
    'vendor/zxcvbn.js',
    filters='jsmin',
    output='scripts/vendor.js')
