"""Data builders for authentication block variants."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

AuthData = Dict[str, object]

_AUTH_DEFAULT: AuthData = {
    "title": "Sign in",
    "subtitle": "to your account",
    "layout": "simple",
    "fields": [],
    "actions": [],
}

_AUTH_BLUEPRINTS: Dict[str, AuthData] = {
    "login-01": {
        "layout": "simple",
        "title": "Sign in",
        "subtitle": "to your account",
        "description": "Enter your email below to sign in to your account",
        "fields": [
            {"type": "email", "label": "Email", "placeholder": "m@example.com"},
            {"type": "password", "label": "Password"},
        ],
        "actions": [
            {"label": "Sign in", "style": "primary", "type": "submit"},
        ],
        "links": [
            {"label": "Forgot your password?", "url": "/reset-password", "style": "link"},
        ],
        "footer": {
            "text": "Don't have an account?",
            "link": {"label": "Sign up", "url": "/signup"},
        },
    },
    "login-02": {
        "layout": "split",
        "title": "Welcome back",
        "description": "Sign in to your account to continue",
        "fields": [
            {"type": "email", "label": "Email", "placeholder": "name@company.com"},
            {"type": "password", "label": "Password"},
        ],
        "actions": [
            {"label": "Sign in", "style": "primary", "type": "submit"},
        ],
        "social": [
            {"provider": "Google", "icon": "google"},
            {"provider": "GitHub", "icon": "github"},
        ],
        "divider": "Or continue with",
        "footer": {
            "text": "New to our platform?",
            "link": {"label": "Create an account", "url": "/signup"},
        },
        "cover": {
            "title": "Flask-Basecoat Design System",
            "description": "Build consistent user experiences with production-ready Flask components.",
            "image": "Authentication illustration",
        },
    },
    "signup-01": {
        "layout": "simple",
        "title": "Create an account",
        "description": "Enter your information to get started",
        "fields": [
            {"type": "text", "label": "Full name", "placeholder": "Enter your full name"},
            {"type": "email", "label": "Email", "placeholder": "m@example.com"},
            {"type": "password", "label": "Password", "requirements": True},
        ],
        "actions": [
            {"label": "Create account", "style": "primary", "type": "submit"},
        ],
        "terms": {
            "text": "By creating an account, you agree to our",
            "links": [
                {"label": "Terms of Service", "url": "/terms"},
                {"label": "Privacy Policy", "url": "/privacy"},
            ],
        },
        "footer": {
            "text": "Already have an account?",
            "link": {"label": "Sign in", "url": "/login"},
        },
    },
    "signup-02": {
        "layout": "split",
        "title": "Get started today",
        "description": "Create your account and join thousands of teams already building with Flask-Basecoat",
        "fields": [
            {"type": "text", "label": "Full name", "placeholder": "Enter your full name"},
            {"type": "email", "label": "Work email", "placeholder": "you@company.com"},
            {"type": "password", "label": "Password"},
            {"type": "text", "label": "Company name", "placeholder": "Your company"},
        ],
        "actions": [
            {"label": "Create account", "style": "primary", "type": "submit"},
        ],
        "social": [
            {"provider": "Google", "icon": "google"},
            {"provider": "GitHub", "icon": "github"},
            {"provider": "Microsoft", "icon": "microsoft"},
        ],
        "divider": "Or continue with email",
        "benefits": [
            "14-day free trial",
            "No credit card required",
            "Cancel anytime",
        ],
        "footer": {
            "text": "Already have an account?",
            "link": {"label": "Sign in instead", "url": "/login"},
        },
        "cover": {
            "title": "Join 500+ teams",
            "description": "Companies using Flask-Basecoat ship 3x faster with consistent design systems.",
            "stats": [
                {"value": "500+", "label": "Active teams"},
                {"value": "50k+", "label": "Components shipped"},
                {"value": "99.9%", "label": "Uptime"},
            ],
        },
    },
}


def build_auth_variant(variant_name: str) -> AuthData:
    """Build authentication form data for a specific variant.
    
    Args:
        variant_name: The auth variant identifier (e.g., 'login-01', 'signup-02')
        
    Returns:
        Complete auth data dictionary with variant-specific content
    """
    if variant_name not in _AUTH_BLUEPRINTS:
        raise ValueError(f"Unknown auth variant: {variant_name}")
    
    # Start with default structure
    auth_data = deepcopy(_AUTH_DEFAULT)
    
    # Apply variant-specific overrides
    variant_config = _AUTH_BLUEPRINTS[variant_name]
    auth_data.update(variant_config)
    
    return auth_data


# Registry of all available auth variants
_AUTH_VARIANTS: Dict[str, str] = {
    "login-01": "Simple login form",
    "login-02": "Two-column login page with cover image", 
    "signup-01": "Simple signup form",
    "signup-02": "Two-column signup page with benefits",
}