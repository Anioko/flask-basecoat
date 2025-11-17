"""Component registry and data builders for shadcn/ui components in Flask-Basecoat."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Optional, Union

# Component data structures
ComponentData = Dict[str, object]
ComponentVariant = Dict[str, object]

# Button component variants
BUTTON_VARIANTS = {
    "primary": {
        "label": "Primary Button",
        "class": "btn btn-primary",
        "description": "The primary action button with emphasis styling"
    },
    "secondary": {
        "label": "Secondary Button", 
        "class": "btn btn-secondary",
        "description": "Secondary action with subtle styling"
    },
    "outline": {
        "label": "Outline Button",
        "class": "btn btn-outline",
        "description": "Button with outline styling"
    },
    "ghost": {
        "label": "Ghost Button",
        "class": "btn btn-ghost", 
        "description": "Minimal button with hover effects"
    },
    "link": {
        "label": "Link Button",
        "class": "btn btn-link",
        "description": "Button styled as a link"
    }
}

# Badge component variants
BADGE_VARIANTS = {
    "default": {
        "label": "Default Badge",
        "class": "badge",
        "description": "Standard badge styling"
    },
    "secondary": {
        "label": "Secondary Badge",
        "class": "badge badge-secondary",
        "description": "Muted badge variant"
    },
    "outline": {
        "label": "Outline Badge",
        "class": "badge badge-outline",
        "description": "Badge with outline styling"
    },
    "destructive": {
        "label": "Destructive Badge", 
        "class": "badge badge-destructive",
        "description": "Badge for warnings or errors"
    }
}

# Card component variants
CARD_VARIANTS = {
    "default": {
        "title": "Card Title",
        "description": "Card description with supporting details",
        "content": "This is the main content area of the card component.",
        "footer": "Card footer content",
        "class": "card"
    },
    "interactive": {
        "title": "Interactive Card",
        "description": "Clickable card with hover effects",
        "content": "Interactive cards provide feedback on hover and focus.",
        "footer": "Learn more →",
        "class": "card card-interactive"
    },
    "with-image": {
        "title": "Card with Image",
        "description": "Card featuring an image header",
        "image": "https://via.placeholder.com/400x200",
        "content": "Cards can include images for visual context.",
        "footer": "Image card footer",
        "class": "card card-with-image"
    }
}

# Alert component variants  
ALERT_VARIANTS = {
    "default": {
        "title": "Default Alert",
        "description": "A general informational alert message.",
        "class": "alert",
        "icon": "ℹ️"
    },
    "destructive": {
        "title": "Error Alert",
        "description": "Something went wrong. Please try again.",
        "class": "alert alert-destructive", 
        "icon": "⚠️"
    },
    "warning": {
        "title": "Warning Alert",
        "description": "Please review the following information.",
        "class": "alert alert-warning",
        "icon": "⚠️"
    },
    "success": {
        "title": "Success Alert",
        "description": "Your action was completed successfully.",
        "class": "alert alert-success",
        "icon": "✅"
    }
}

# Avatar component variants
AVATAR_VARIANTS = {
    "with-image": {
        "src": "https://via.placeholder.com/40x40",
        "alt": "User Avatar",
        "class": "avatar",
        "fallback": "JD"
    },
    "with-fallback": {
        "src": "",
        "alt": "User Avatar", 
        "class": "avatar",
        "fallback": "AB"
    },
    "small": {
        "src": "https://via.placeholder.com/32x32",
        "alt": "Small Avatar",
        "class": "avatar avatar-sm",
        "fallback": "SM"
    },
    "large": {
        "src": "https://via.placeholder.com/64x64", 
        "alt": "Large Avatar",
        "class": "avatar avatar-lg",
        "fallback": "LG"
    }
}

# Input component variants
INPUT_VARIANTS = {
    "default": {
        "type": "text",
        "placeholder": "Enter text...",
        "label": "Default Input",
        "class": "input"
    },
    "email": {
        "type": "email",
        "placeholder": "email@example.com",
        "label": "Email Input",
        "class": "input"
    },
    "password": {
        "type": "password", 
        "placeholder": "Enter password",
        "label": "Password Input",
        "class": "input"
    },
    "disabled": {
        "type": "text",
        "placeholder": "Disabled input",
        "label": "Disabled Input", 
        "class": "input",
        "disabled": True
    },
    "with-error": {
        "type": "text",
        "placeholder": "Input with error",
        "label": "Input with Error",
        "class": "input input-error",
        "error": "This field is required"
    }
}

# Checkbox component variants
CHECKBOX_VARIANTS = {
    "default": {
        "label": "Default Checkbox",
        "checked": False,
        "class": "checkbox",
        "description": "Standard checkbox input"
    },
    "checked": {
        "label": "Checked Checkbox",
        "checked": True,
        "class": "checkbox",
        "description": "Pre-checked checkbox state"
    },
    "disabled": {
        "label": "Disabled Checkbox",
        "checked": False,
        "disabled": True,
        "class": "checkbox",
        "description": "Disabled checkbox input"
    },
    "with-description": {
        "label": "Checkbox with Description",
        "checked": False,
        "class": "checkbox",
        "description": "Checkbox with additional help text",
        "help_text": "This is a detailed description of what this checkbox does."
    }
}

# Select component variants
SELECT_VARIANTS = {
    "default": {
        "label": "Select Option",
        "placeholder": "Select an option...",
        "class": "select",
        "options": [
            {"value": "option1", "text": "Option 1"},
            {"value": "option2", "text": "Option 2"},
            {"value": "option3", "text": "Option 3"}
        ],
        "description": "Standard select dropdown"
    },
    "with-default": {
        "label": "Select with Default",
        "class": "select",
        "selected": "option2",
        "options": [
            {"value": "option1", "text": "Small"},
            {"value": "option2", "text": "Medium"},
            {"value": "option3", "text": "Large"}
        ],
        "description": "Select with pre-selected option"
    },
    "disabled": {
        "label": "Disabled Select",
        "placeholder": "Cannot select...",
        "disabled": True,
        "class": "select",
        "options": [
            {"value": "option1", "text": "Option 1"},
            {"value": "option2", "text": "Option 2"}
        ],
        "description": "Disabled select input"
    }
}

# Textarea component variants
TEXTAREA_VARIANTS = {
    "default": {
        "label": "Default Textarea",
        "placeholder": "Enter your message...",
        "class": "textarea",
        "rows": 4,
        "description": "Standard textarea input"
    },
    "with-content": {
        "label": "Textarea with Content",
        "class": "textarea",
        "rows": 6,
        "value": "This is some default content in the textarea that shows how it looks with text.",
        "description": "Textarea with default content"
    },
    "small": {
        "label": "Small Textarea",
        "placeholder": "Brief message...",
        "class": "textarea textarea-sm",
        "rows": 3,
        "description": "Compact textarea variant"
    },
    "disabled": {
        "label": "Disabled Textarea",
        "placeholder": "Cannot edit...",
        "disabled": True,
        "class": "textarea",
        "rows": 4,
        "description": "Disabled textarea input"
    }
}

# Toggle/Switch component variants
TOGGLE_VARIANTS = {
    "default": {
        "label": "Default Toggle",
        "checked": False,
        "class": "toggle",
        "description": "Standard toggle switch"
    },
    "checked": {
        "label": "Checked Toggle",
        "checked": True,
        "class": "toggle",
        "description": "Active toggle state"
    },
    "disabled": {
        "label": "Disabled Toggle",
        "checked": False,
        "disabled": True,
        "class": "toggle",
        "description": "Disabled toggle switch"
    },
    "with-icons": {
        "label": "Toggle with Icons",
        "checked": False,
        "class": "toggle toggle-with-icons",
        "on_icon": "🌙",
        "off_icon": "☀️",
        "description": "Toggle with visual indicators"
    }
}

# Progress component variants
PROGRESS_VARIANTS = {
    "default": {
        "label": "Default Progress",
        "value": 60,
        "max": 100,
        "class": "progress",
        "description": "Standard progress bar"
    },
    "small": {
        "label": "Small Progress",
        "value": 40,
        "max": 100,
        "class": "progress progress-sm",
        "description": "Compact progress bar"
    },
    "large": {
        "label": "Large Progress",
        "value": 80,
        "max": 100,
        "class": "progress progress-lg",
        "description": "Large progress bar"
    },
    "with-label": {
        "label": "Progress with Label",
        "value": 75,
        "max": 100,
        "class": "progress",
        "show_label": True,
        "description": "Progress bar with percentage display"
    }
}


# Component registry for documentation
COMPONENT_REGISTRY = {
    "button": {
        "title": "Button",
        "description": "Displays a button or a component that looks like a button.",
        "variants": BUTTON_VARIANTS,
        "docs_url": "https://ui.shadcn.com/docs/components/button"
    },
    "badge": {
        "title": "Badge", 
        "description": "Displays a badge or a component that looks like a badge.",
        "variants": BADGE_VARIANTS,
        "docs_url": "https://ui.shadcn.com/docs/components/badge"
    },
    "card": {
        "title": "Card",
        "description": "Displays a card with header, content, and footer.",
        "variants": CARD_VARIANTS,
        "docs_url": "https://ui.shadcn.com/docs/components/card"
    },
    "alert": {
        "title": "Alert",
        "description": "Displays a callout for user attention.",
        "variants": ALERT_VARIANTS,
        "docs_url": "https://ui.shadcn.com/docs/components/alert"
    },
    "avatar": {
        "title": "Avatar",
        "description": "An image element with a fallback for representing the user.",
        "variants": AVATAR_VARIANTS,
        "docs_url": "https://ui.shadcn.com/docs/components/avatar"
    },
    "input": {
        "title": "Input", 
        "description": "Displays a form input field or a component that looks like an input field.",
        "variants": INPUT_VARIANTS,
        "docs_url": "https://ui.shadcn.com/docs/components/input"
    },
    "checkbox": {
        "title": "Checkbox",
        "description": "A control that allows the user to toggle between checked and not checked.",
        "variants": CHECKBOX_VARIANTS,
        "docs_url": "https://ui.shadcn.com/docs/components/checkbox"
    },
    "select": {
        "title": "Select",
        "description": "Displays a list of options for the user to pick from—triggered by a button.",
        "variants": SELECT_VARIANTS,
        "docs_url": "https://ui.shadcn.com/docs/components/select"
    },
    "textarea": {
        "title": "Textarea",
        "description": "Displays a form textarea or a component that looks like a textarea.",
        "variants": TEXTAREA_VARIANTS,
        "docs_url": "https://ui.shadcn.com/docs/components/textarea"
    },
    "toggle": {
        "title": "Toggle",
        "description": "A two-state button that can be either on or off.",
        "variants": TOGGLE_VARIANTS,
        "docs_url": "https://ui.shadcn.com/docs/components/toggle"
    },
    "progress": {
        "title": "Progress",
        "description": "Displays an indicator showing the completion progress of a task.",
        "variants": PROGRESS_VARIANTS,
        "docs_url": "https://ui.shadcn.com/docs/components/progress"
    },
    "tooltip": {
        "title": "Tooltip",
        "description": "A popup that displays information related to an element when the element receives keyboard focus or the mouse hovers over it.",
        "variants": {
            "default": {"label": "Default", "placement": "top", "text": "This is a tooltip"},
            "dark": {"label": "Dark", "placement": "top", "text": "Dark tooltip", "theme": "dark"},
            "bottom": {"label": "Bottom", "placement": "bottom", "text": "Bottom tooltip"},
            "left": {"label": "Left", "placement": "left", "text": "Left tooltip"},
            "right": {"label": "Right", "placement": "right", "text": "Right tooltip"}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/tooltip"
    },
    "tabs": {
        "title": "Tabs",
        "description": "A set of layered sections of content—known as tab panels—that are displayed one at a time.",
        "variants": {
            "default": {"label": "Default", "style": "default"},
            "underline": {"label": "Underline", "style": "underline"},
            "pills": {"label": "Pills", "style": "pills"}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/tabs"
    },
    "dialog": {
        "title": "Dialog",
        "description": "A window overlaid on either the primary window or another dialog window, rendering the content underneath inert.",
        "variants": {
            "default": {"label": "Default", "size": "default"},
            "sm": {"label": "Small", "size": "sm"},
            "lg": {"label": "Large", "size": "lg"},
            "xl": {"label": "Extra Large", "size": "xl"}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/dialog"
    },
    "popover": {
        "title": "Popover",
        "description": "Displays rich content in a portal, triggered by a button.",
        "variants": {
            "default": {"label": "Default", "placement": "bottom"},
            "top": {"label": "Top", "placement": "top"},
            "right": {"label": "Right", "placement": "right"},
            "left": {"label": "Left", "placement": "left"}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/popover"
    },
    "breadcrumb": {
        "title": "Breadcrumb",
        "description": "Displays the path to the current resource using a hierarchy of links.",
        "variants": {
            "default": {"label": "Default", "separator": "/"},
            "chevron": {"label": "Chevron", "separator": ">"},
            "dot": {"label": "Dot", "separator": "•"}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/breadcrumb"
    },
    "separator": {
        "title": "Separator",
        "description": "Visually or semantically separates content.",
        "variants": {
            "horizontal": {"label": "Horizontal", "orientation": "horizontal"},
            "vertical": {"label": "Vertical", "orientation": "vertical"}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/separator"
    },
    "command": {
        "title": "Command",
        "description": "Fast, composable, unstyled command menu for React.",
        "variants": {
            "default": {"label": "Default", "placeholder": "Type a command or search..."},
            "dialog": {"label": "Command Dialog", "type": "dialog"},
            "combobox": {"label": "Combobox", "type": "combobox"}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/command"
    },
    "dropdown": {
        "title": "Dropdown Menu",
        "description": "Displays a menu to the user — such as a set of actions or functions — triggered by a button.",
        "variants": {
            "default": {"label": "Default", "trigger": "Open"},
            "with_icons": {"label": "With Icons", "trigger": "Open", "icons": True},
            "with_separators": {"label": "With Separators", "trigger": "Open", "separators": True}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/dropdown-menu"
    },
    "menubar": {
        "title": "Menubar",
        "description": "A visually persistent menu common in desktop applications that provides a set of commands.",
        "variants": {
            "default": {"label": "Default", "menus": ["File", "Edit", "View", "Account"]},
            "minimal": {"label": "Minimal", "menus": ["File", "Edit"]}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/menubar"
    },
    "navigation": {
        "title": "Navigation Menu",
        "description": "A collection of links for navigating websites.",
        "variants": {
            "horizontal": {"label": "Horizontal", "orientation": "horizontal"},
            "vertical": {"label": "Vertical", "orientation": "vertical"},
            "with_indicators": {"label": "With Indicators", "indicators": True}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/navigation-menu"
    },
    "sheet": {
        "title": "Sheet",
        "description": "Extends the Dialog component to display content that complements the main content of the screen.",
        "variants": {
            "side": {"label": "Side Sheet", "side": "right"},
            "bottom": {"label": "Bottom Sheet", "side": "bottom"},
            "top": {"label": "Top Sheet", "side": "top"},
            "left": {"label": "Left Sheet", "side": "left"}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/sheet"
    },
    "skeleton": {
        "title": "Skeleton",
        "description": "Use to show a placeholder while content is loading.",
        "variants": {
            "default": {"label": "Default", "lines": 3},
            "avatar": {"label": "With Avatar", "avatar": True},
            "card": {"label": "Card Skeleton", "type": "card"}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/skeleton"
    },
    "slider": {
        "title": "Slider",
        "description": "An input where the user selects a value from within a given range.",
        "variants": {
            "default": {"label": "Default", "min": 0, "max": 100, "value": 50},
            "range": {"label": "Range", "min": 0, "max": 100, "value": [25, 75]},
            "stepped": {"label": "Stepped", "min": 0, "max": 100, "step": 10, "value": 50}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/slider"
    },
    "switch": {
        "title": "Switch",
        "description": "A control that allows the user to toggle between checked and not checked.",
        "variants": {
            "default": {"label": "Default", "checked": False},
            "checked": {"label": "Checked", "checked": True},
            "disabled": {"label": "Disabled", "disabled": True}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/switch"
    },
    "table": {
        "title": "Table",
        "description": "A responsive table component.",
        "variants": {
            "default": {"label": "Default", "striped": False},
            "striped": {"label": "Striped", "striped": True},
            "hoverable": {"label": "Hoverable", "hoverable": True}
        },
        "docs_url": "https://ui.shadcn.com/docs/components/table"
    },
    "chart": {
        "title": "Chart",
        "description": "Data visualization components with multiple chart types.",
        "variants": {
            "line": {"label": "Line Chart", "type": "line", "data_points": 7},
            "bar": {"label": "Bar Chart", "type": "bar", "data_points": 5},
            "pie": {"label": "Pie Chart", "type": "pie", "segments": 4},
            "area": {"label": "Area Chart", "type": "area", "data_points": 8}
        },
        "docs_url": "/docs/components/chart"
    },
    "datatable": {
        "title": "Data Table",
        "description": "Advanced table with sorting, filtering, and pagination.",
        "variants": {
            "sortable": {"label": "Sortable", "features": ["sort"]},
            "filterable": {"label": "Filterable", "features": ["filter"]},
            "full": {"label": "Full Features", "features": ["sort", "filter", "paginate"]}
        },
        "docs_url": "/docs/components/datatable"
    },
    "calendar": {
        "title": "Calendar",
        "description": "Date picker and calendar components.",
        "variants": {
            "datepicker": {"label": "Date Picker", "type": "picker"},
            "calendar": {"label": "Full Calendar", "type": "calendar"},
            "range": {"label": "Date Range", "type": "range"}
        },
        "docs_url": "/docs/components/calendar"
    },
    "accordion": {
        "title": "Accordion",
        "description": "Collapsible content sections.",
        "variants": {
            "single": {"label": "Single", "multiple": False},
            "multiple": {"label": "Multiple", "multiple": True},
            "styled": {"label": "Styled", "style": "bordered"}
        },
        "docs_url": "/docs/components/accordion"
    },
    "carousel": {
        "title": "Carousel",
        "description": "Content slider with navigation.",
        "variants": {
            "basic": {"label": "Basic", "autoplay": False},
            "autoplay": {"label": "Autoplay", "autoplay": True},
            "dots": {"label": "With Dots", "indicators": "dots"},
            "thumbnails": {"label": "Thumbnails", "indicators": "thumbnails"}
        },
        "docs_url": "/docs/components/carousel"
    },
    "grid": {
        "title": "Grid",
        "description": "Responsive grid layout system.",
        "variants": {
            "masonry": {"label": "Masonry", "type": "masonry"},
            "responsive": {"label": "Responsive", "type": "responsive"},
            "fixed": {"label": "Fixed", "type": "fixed"}
        },
        "docs_url": "/docs/components/grid"
    },
    "wizard": {
        "title": "Wizard",
        "description": "Multi-step form with progress tracking.",
        "variants": {
            "basic": {"label": "Basic", "steps": 3},
            "progress": {"label": "With Progress", "steps": 4, "progress": True},
            "validation": {"label": "With Validation", "steps": 3, "validation": True}
        },
        "docs_url": "/docs/components/wizard"
    },
    "editor": {
        "title": "Rich Text Editor",
        "description": "WYSIWYG text editor with formatting tools.",
        "variants": {
            "basic": {"label": "Basic", "toolbar": "basic"},
            "full": {"label": "Full Featured", "toolbar": "full"},
            "minimal": {"label": "Minimal", "toolbar": "minimal"}
        },
        "docs_url": "/docs/components/editor"
    },
    "fileupload": {
        "title": "File Upload",
        "description": "Drag and drop file upload component.",
        "variants": {
            "single": {"label": "Single File", "multiple": False},
            "multiple": {"label": "Multiple Files", "multiple": True},
            "preview": {"label": "With Preview", "preview": True}
        },
        "docs_url": "/docs/components/fileupload"
    },
    "autocomplete": {
        "title": "Autocomplete",
        "description": "Search input with suggestions.",
        "variants": {
            "basic": {"label": "Basic", "async": False},
            "async": {"label": "Async Search", "async": True},
            "multi": {"label": "Multi-select", "multiple": True}
        },
        "docs_url": "/docs/components/autocomplete"
    },
    "formvalidation": {
        "title": "Form Validation",
        "description": "Advanced form validation with real-time feedback.",
        "variants": {
            "realtime": {"label": "Real-time", "mode": "realtime"},
            "submit": {"label": "On Submit", "mode": "submit"},
            "custom": {"label": "Custom Rules", "mode": "custom"}
        },
        "docs_url": "/docs/components/formvalidation"
    },
    
    # Theme System & Customization
    "themetoggle": {
        "title": "Theme Toggle",
        "description": "Dark/light mode toggle with system preference detection.",
        "variants": {
            "default": {"label": "Default", "style": "default"},
            "compact": {"label": "Compact", "style": "compact"},
            "icon_only": {"label": "Icon Only", "style": "icon-only"}
        },
        "docs_url": "/docs/components/themetoggle"
    },
    "colorgenerator": {
        "title": "Color Generator",
        "description": "Interactive color palette generator and theme creator.",
        "variants": {
            "wheel": {"label": "Color Wheel", "type": "wheel"},
            "swatches": {"label": "Swatches", "type": "swatches"},
            "palette": {"label": "Palette Builder", "type": "palette"}
        },
        "docs_url": "/docs/components/colorgenerator"
    },
    "typographyeditor": {
        "title": "Typography Editor",
        "description": "Typography scale system editor with live preview.",
        "variants": {
            "scale": {"label": "Type Scale", "mode": "scale"},
            "fonts": {"label": "Font Selector", "mode": "fonts"},
            "styles": {"label": "Text Styles", "mode": "styles"}
        },
        "docs_url": "/docs/components/typographyeditor"
    },
    "variantbuilder": {
        "title": "Variant Builder",
        "description": "Component variant builder and customization tool.",
        "variants": {
            "colors": {"label": "Color Variants", "type": "colors"},
            "sizes": {"label": "Size Variants", "type": "sizes"},
            "styles": {"label": "Style Variants", "type": "styles"}
        },
        "docs_url": "/docs/components/variantbuilder"
    },
    
    # Animation Library
    "animationkit": {
        "title": "Animation Kit",
        "description": "Collection of entrance and exit animations for components.",
        "variants": {
            "fade": {"label": "Fade In/Out", "type": "fade"},
            "slide": {"label": "Slide Animations", "type": "slide"},
            "scale": {"label": "Scale Animations", "type": "scale"},
            "rotate": {"label": "Rotation Effects", "type": "rotate"}
        },
        "docs_url": "/docs/components/animationkit"
    },
    "loadingstates": {
        "title": "Loading States",
        "description": "Loading indicators and skeleton screens for better UX.",
        "variants": {
            "spinner": {"label": "Spinner", "type": "spinner"},
            "skeleton": {"label": "Skeleton Screen", "type": "skeleton"},
            "pulse": {"label": "Pulse Effect", "type": "pulse"},
            "progress": {"label": "Progress Loading", "type": "progress"}
        },
        "docs_url": "/docs/components/loadingstates"
    },
    "transitions": {
        "title": "State Transitions",
        "description": "Smooth transitions between component states.",
        "variants": {
            "height": {"label": "Height Transition", "type": "height"},
            "opacity": {"label": "Opacity Transition", "type": "opacity"},
            "transform": {"label": "Transform Transition", "type": "transform"},
            "color": {"label": "Color Transition", "type": "color"}
        },
        "docs_url": "/docs/components/transitions"
    },
    "scrollanimations": {
        "title": "Scroll Animations",
        "description": "Animations triggered by scroll position and viewport intersection.",
        "variants": {
            "reveal": {"label": "Reveal on Scroll", "type": "reveal"},
            "parallax": {"label": "Parallax Effects", "type": "parallax"},
            "stagger": {"label": "Staggered Animation", "type": "stagger"},
            "timeline": {"label": "Scroll Timeline", "type": "timeline"}
        },
        "docs_url": "/docs/components/scrollanimations"
    },
    
    # Component Playground
    "componentpreview": {
        "title": "Component Preview",
        "description": "Interactive component preview with live prop editing.",
        "variants": {
            "editor": {"label": "Live Editor", "mode": "editor"},
            "split": {"label": "Split View", "mode": "split"},
            "fullscreen": {"label": "Fullscreen", "mode": "fullscreen"},
            "responsive": {"label": "Responsive", "mode": "responsive"}
        },
        "docs_url": "/docs/components/componentpreview"
    },
    "codegenerator": {
        "title": "Code Generator",
        "description": "Generate code snippets with copy-to-clipboard functionality.",
        "variants": {
            "html": {"label": "HTML Output", "format": "html"},
            "jsx": {"label": "React JSX", "format": "jsx"},
            "vue": {"label": "Vue Template", "format": "vue"},
            "angular": {"label": "Angular", "format": "angular"}
        },
        "docs_url": "/docs/components/codegenerator"
    },
    "componentbuilder": {
        "title": "Component Builder",
        "description": "Drag-and-drop component composition tool.",
        "variants": {
            "canvas": {"label": "Design Canvas", "type": "canvas"},
            "layers": {"label": "Layer Tree", "type": "layers"},
            "properties": {"label": "Properties Panel", "type": "properties"},
            "preview": {"label": "Live Preview", "type": "preview"}
        },
        "docs_url": "/docs/components/componentbuilder"
    },
    "exporttools": {
        "title": "Export Tools",
        "description": "Export components and designs in multiple formats.",
        "variants": {
            "figma": {"label": "Figma Plugin", "format": "figma"},
            "sketch": {"label": "Sketch Export", "format": "sketch"},
            "code": {"label": "Code Export", "format": "code"},
            "assets": {"label": "Asset Export", "format": "assets"}
        },
        "docs_url": "/docs/components/exporttools"
    },
    
    # Documentation Enhancement Components
    "codeexamples": {
        "title": "Interactive Code Examples",
        "description": "Live code examples with real-time editing and execution.",
        "variants": {
            "basic": {"label": "Basic Editor", "mode": "basic"},
            "advanced": {"label": "Advanced Editor", "mode": "advanced"},
            "playground": {"label": "Code Playground", "mode": "playground"},
            "tutorial": {"label": "Tutorial Mode", "mode": "tutorial"}
        },
        "docs_url": "/docs/components/codeexamples"
    },
    "apidocs": {
        "title": "API Documentation",
        "description": "Interactive API explorer with examples and testing.",
        "variants": {
            "reference": {"label": "API Reference", "type": "reference"},
            "explorer": {"label": "API Explorer", "type": "explorer"},
            "examples": {"label": "Example Gallery", "type": "examples"},
            "playground": {"label": "API Playground", "type": "playground"}
        },
        "docs_url": "/docs/components/apidocs"
    },
    "searchfilter": {
        "title": "Search & Filter",
        "description": "Advanced search and filtering system with multiple modes.",
        "variants": {
            "global": {"label": "Global Search", "scope": "global"},
            "faceted": {"label": "Faceted Search", "scope": "faceted"},
            "semantic": {"label": "Semantic Search", "scope": "semantic"},
            "visual": {"label": "Visual Search", "scope": "visual"}
        },
        "docs_url": "/docs/components/searchfilter"
    },
    "versionhistory": {
        "title": "Version History",
        "description": "Version tracking and changelog with migration guides.",
        "variants": {
            "changelog": {"label": "Changelog View", "view": "changelog"},
            "diff": {"label": "Diff Viewer", "view": "diff"},
            "timeline": {"label": "Timeline View", "view": "timeline"},
            "migration": {"label": "Migration Guide", "view": "migration"}
        },
        "docs_url": "/docs/components/versionhistory"
    },

    # Build System Components
    "bundler": {
        "title": "Asset Bundler",
        "description": "Bundle and optimize assets for production with multiple build tools.",
        "variants": {
            "webpack": {"label": "Webpack Bundler", "type": "webpack"},
            "rollup": {"label": "Rollup Bundler", "type": "rollup"},
            "vite": {"label": "Vite Build Tool", "type": "vite"},
            "parcel": {"label": "Parcel Bundler", "type": "parcel"}
        },
        "docs_url": "/docs/components/bundler"
    },
    "compiler": {
        "title": "Style Compiler",
        "description": "Compile and process CSS/SCSS styles with various processors.",
        "variants": {
            "sass": {"label": "SASS Compiler", "processor": "sass"},
            "postcss": {"label": "PostCSS Processor", "processor": "postcss"},
            "tailwind": {"label": "Tailwind Compiler", "processor": "tailwind"},
            "less": {"label": "LESS Compiler", "processor": "less"}
        },
        "docs_url": "/docs/components/compiler"
    },
    "scaffold": {
        "title": "Component Scaffolder",
        "description": "Generate component boilerplate code for different frameworks.",
        "variants": {
            "react": {"label": "React Generator", "framework": "react"},
            "vue": {"label": "Vue Generator", "framework": "vue"},
            "angular": {"label": "Angular Generator", "framework": "angular"},
            "svelte": {"label": "Svelte Generator", "framework": "svelte"}
        },
        "docs_url": "/docs/components/scaffold"
    },
    "dependencies": {
        "title": "Dependency Manager",
        "description": "Manage, analyze, and optimize project dependencies.",
        "variants": {
            "analyzer": {"label": "Bundle Analyzer", "mode": "analyzer"},
            "updater": {"label": "Dependency Updater", "mode": "updater"},
            "security": {"label": "Security Auditor", "mode": "security"},
            "optimization": {"label": "Bundle Optimizer", "mode": "optimization"}
        },
        "docs_url": "/docs/components/dependencies"
    }
}


def get_component(component_name: str) -> Optional[ComponentData]:
    """Get component data by name."""
    return COMPONENT_REGISTRY.get(component_name)


def get_component_variant(component_name: str, variant_name: str) -> Optional[ComponentVariant]:
    """Get a specific variant of a component."""
    component = get_component(component_name)
    if not component:
        return None
    
    variants = component.get("variants", {})
    return variants.get(variant_name)


def list_components() -> List[str]:
    """List all available component names."""
    return list(COMPONENT_REGISTRY.keys())


def list_component_variants(component_name: str) -> List[str]:
    """List all variants for a component."""
    component = get_component(component_name)
    if not component:
        return []
    
    variants = component.get("variants", {})
    return list(variants.keys())