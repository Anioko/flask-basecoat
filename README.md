# Flask-Basecoat

A modern Flask application boilerplate with **BasecoatUI** and **Tailwind CSS** - providing a clean, component-based UI similar to shadcn/ui.

## ✨ What's Different?

This is a modernized fork of the original [flask-base](https://github.com/hack4impact/flask-base) project, updated with:

- ✅ **BasecoatUI** - Modern component library with shadcn/ui-like aesthetics
- ✅ **Tailwind CSS** - Utility-first CSS framework
- ✅ **Python 3.11+** - Modern Python version
- ✅ **Updated Dependencies** - All packages updated with version pins for security
- ✅ **Removed jQuery/Semantic UI** - Vanilla JavaScript and modern CSS
- ✅ **Clean Boilerplate** - Removed fork-specific features for general use

## 🚀 Features

### Core Functionality
- **Blueprints** - Modular application structure
- **User Management** - Registration, login, password reset
- **Role-Based Access Control** - Admin and user roles with permissions
- **Flask-SQLAlchemy** - Database ORM (supports SQLite, PostgreSQL)
- **Flask-WTF** - Forms with CSRF protection
- **Flask-Assets** - Asset management and SCSS compilation
- **Flask-Mail** - Email sending (SendGrid/SMTP)
- **Redis Queue** - Asynchronous task processing
- **ZXCVBN** - Password strength checker
- **CKEditor** - Rich text editor for admin pages

### Modern UI
- **BasecoatUI Components** - Pre-styled, accessible components
- **Tailwind CSS** - Utility-first styling
- **Responsive Design** - Mobile-friendly out of the box
- **Dark Mode Ready** - Easy theming support

### Developer Experience
- **Docker Support** - Complete docker-compose setup
- **Heroku Ready** - One-click deployment configuration
- **Code Formatting** - Integrated code formatting tools
- **Environment Config** - Easy environment variable management

## 📋 Requirements

- Python 3.11+
- Redis
- PostgreSQL (production) or SQLite (development)

## 🔧 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/flask-basecoat.git
cd flask-basecoat
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Unix/MacOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `config.env` file in the root directory (do NOT commit this file):

```bash
# Required
SECRET_KEY=your-secret-key-here

# Email Configuration (for SendGrid or SMTP)
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-password

# Admin Account
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure-password

# Optional
DATABASE_URL=sqlite:///data-dev.sqlite
REDISTOGO_URL=http://localhost:6379
FLASK_CONFIG=development
```

**Generate a secure SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(16))"
```

### 5. Install Redis

**Mac (using Homebrew):**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Windows:**
Use [Redis for Windows](https://github.com/microsoftarchive/redis/releases) or Docker

### 6. Initialize Database

```bash
python manage.py recreate_db
python manage.py setup_dev
```

Optionally add fake data for testing:
```bash
python manage.py add_fake_data
```

### 7. Run the Application

```bash
honcho start -e config.env -f Local
```

Visit [http://localhost:5000](http://localhost:5000)

## 🐳 Docker Setup (Recommended)

### Quick Start with Docker

```bash
# Build and start all services
docker-compose up

# Initialize database (in another terminal)
docker-compose exec server ./init_database.sh
```

This deploys 5 containers:
- **server** - Flask app at [http://localhost:5000](http://localhost:5000)
- **worker** - Background task worker
- **postgres** - PostgreSQL database
- **adminer** - Database UI at [http://localhost:8080](http://localhost:8080)
- **redis** - Redis server

## 📁 Project Structure

```
flask-basecoat/
├── app/
│   ├── account/          # Authentication & user management
│   ├── admin/            # Admin dashboard
│   ├── main/             # Public pages
│   ├── models/           # Database models
│   │   ├── user.py       # User & Role models
│   │   ├── miscellaneous.py  # EditableHTML model
│   │   └── models.py     # Your custom models
│   ├── templates/        # Jinja2 templates with BasecoatUI
│   ├── static/           # Static files
│   └── assets/           # SCSS and JS source files
├── tests/                # Unit tests
├── migrations/           # Database migrations
├── config.py             # Configuration management
├── manage.py             # CLI commands
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker configuration
└── docker-compose.yml    # Multi-container setup
```

## 🎨 Using BasecoatUI

BasecoatUI components are loaded via CDN in the base template. Here's a quick example:

```html
<!-- Button -->
<button class="btn btn-primary">Click Me</button>

<!-- Card -->
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Card Title</h3>
  </div>
  <div class="card-body">
    Card content here
  </div>
</div>

<!-- Form Input -->
<div class="form-group">
  <label for="email">Email</label>
  <input type="email" id="email" class="form-control" />
</div>
```

For more components, see [BasecoatUI Documentation](https://basecoatui.com/).

## 🛠️ Available Commands

```bash
# Database
python manage.py recreate_db      # Recreate database (DEV ONLY!)
python manage.py setup_dev         # Setup development data
python manage.py add_fake_data     # Add test users

# Development
python manage.py format            # Auto-format code (YAPF + isort)
python manage.py run_worker        # Start background worker
python manage.py test              # Run tests

# Database Migrations
flask db init                      # Initialize migrations
flask db migrate -m "message"      # Create migration
flask db upgrade                   # Apply migrations
```

## 📧 Email Configuration

### Using SendGrid (Recommended)

1. Sign up at [SendGrid](https://sendgrid.com)
2. Create an API key
3. Add to `config.env`:
```bash
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
```

### Using Gmail

1. Enable 2FA on your Google account
2. Create an [App Password](https://support.google.com/accounts/answer/185833)
3. Add to `config.env`:
```bash
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

## 🚀 Deployment

### Heroku

1. Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Create a new Heroku app:
```bash
heroku create your-app-name
```

3. Add PostgreSQL and Redis addons:
```bash
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create redistogo:nano
```

4. Set environment variables:
```bash
heroku config:set FLASK_CONFIG=heroku
heroku config:set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(16))")
heroku config:set MAIL_USERNAME=your-email
heroku config:set MAIL_PASSWORD=your-password
```

5. Deploy:
```bash
git push heroku main
```

### Traditional Server

See [deployment documentation](docs/deploy.md) for detailed instructions.

## 🧪 Testing

Run tests:
```bash
python manage.py test
```

Add new tests in the `tests/` directory.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please refer to our [Code of Conduct](./CONDUCT.md).

## 📝 Code Formatting

Before submitting PRs, format your code:

```bash
python manage.py format
```

## 🙏 Credits

This project is a modernized fork of [flask-base](https://github.com/hack4impact/flask-base) by Hack4Impact. The original boilerplate was inspired by Miguel Grinberg's [Flask Web Development](http://flaskbook.com).

### What Changed?
- Updated to Python 3.11+ with modern dependencies
- Replaced Semantic UI with BasecoatUI + Tailwind CSS
- Removed jQuery in favor of vanilla JavaScript
- Added comprehensive version pinning for security
- Fixed deprecated imports and configurations
- Cleaned up for general boilerplate use

## 📄 License

[MIT License](LICENSE.md)

## 🆘 Troubleshooting

### Redis Connection Issues (Windows)
If you encounter Redis binding issues on Windows, use WSL2 or Docker instead.

### Database Migration Errors
Delete the `migrations/` folder and re-run:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Import Errors
Make sure your virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate  # Unix/MacOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

## 📚 Documentation

For detailed documentation on specific features:
- [Setup Guide](docs/setup.md)
- [Configuration Options](docs/config.md)
- [Template Usage](docs/templates.md)
- [Database Models](docs/models.md)
- [Deployment](docs/deploy.md)

## ⭐ Show Your Support

If this project helped you, please consider giving it a ⭐️ on GitHub!
