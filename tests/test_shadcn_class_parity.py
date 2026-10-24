"""
Parity test: Verify flask-basecoat macros match shadcn/ui components exactly.

Reads shadcn source .tsx files, extracts classes and data-slot attributes,
renders macros for every variant/size combination, and asserts exact parity.
"""
import re
import pytest
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup


# Path to the cloned shadcn fork
SHADCN_FORK = Path("/tmp/shadcn-fork")
COMPONENTS_PATH = SHADCN_FORK / "components/ui"

# Path to our macro templates
TEMPLATES_PATH = Path(__file__).parent.parent / "flask_basecoat/templates/shadcn"


def parse_cva_component(tsx_content, component_name):
    """
    Parse a cva-based component to extract base classes and variants.

    Returns:
        {
            'base': 'class string',
            'variants': {
                'variant': {'default': 'classes', 'destructive': 'classes'},
                'size': {'default': 'classes', 'sm': 'classes'}
            },
            'defaultVariants': {'variant': 'default', 'size': 'default'},
            'data_slot': 'button'
        }
    """
    # Extract the cva call - handle nested parentheses by counting depth
    cva_start = re.search(r'const\s+\w+Variants\s*=\s*cva\s*\(', tsx_content)
    if not cva_start:
        return None

    # Find matching closing parenthesis
    start_pos = cva_start.end() - 1  # Position of opening (
    depth = 0
    end_pos = start_pos

    for i in range(start_pos, len(tsx_content)):
        if tsx_content[i] == '(':
            depth += 1
        elif tsx_content[i] == ')':
            depth -= 1
            if depth == 0:
                end_pos = i
                break

    if depth != 0:
        return None

    cva_content = tsx_content[start_pos + 1:end_pos]
    match = type('Match', (), {'group': lambda self, n: cva_content})() if cva_content else None

    if not match:
        return None

    cva_content = match.group(1)

    # Extract base string (first quoted string)
    base_match = re.search(r'["\`](.*?)["\`]', cva_content, re.DOTALL)
    base_classes = base_match.group(1).strip() if base_match else ""

    # Extract variants object
    variants_match = re.search(r'variants:\s*\{(.*?)\}(?:,|\s*\})', cva_content, re.DOTALL)
    variants = {}

    if variants_match:
        variants_str = variants_match.group(1)
        # Parse each variant type (e.g., variant: {...}, size: {...})
        variant_type_pattern = r'(\w+):\s*\{([^}]+)\}'
        for type_match in re.finditer(variant_type_pattern, variants_str):
            variant_name = type_match.group(1)
            variant_options_str = type_match.group(2)

            variants[variant_name] = {}
            # Parse each option (e.g., default: "classes", destructive: "classes")
            option_pattern = r'(\w+):\s*["\`](.*?)["\`]'
            for option_match in re.finditer(option_pattern, variant_options_str, re.DOTALL):
                option_name = option_match.group(1)
                option_classes = option_match.group(2).strip()
                variants[variant_name][option_name] = option_classes

    # Extract default variants
    defaults_match = re.search(r'defaultVariants:\s*\{([^}]+)\}', cva_content)
    default_variants = {}
    if defaults_match:
        defaults_str = defaults_match.group(1)
        for line in defaults_str.split(','):
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip().strip('"\'')
                val = val.strip().strip('",\'')
                default_variants[key] = val

    # Extract data-slot attribute from the component function
    data_slot_match = re.search(r'data-slot=["\'](\w+)["\']', tsx_content)
    data_slot = data_slot_match.group(1) if data_slot_match else component_name.lower()

    return {
        'base': base_classes,
        'variants': variants,
        'defaultVariants': default_variants,
        'data_slot': data_slot
    }


def parse_simple_component(tsx_content, element_name):
    """
    Parse a simple component with fixed className strings.

    Returns list of elements with their classes and data-slots:
        [
            {'name': 'Card', 'classes': '...', 'data_slot': 'card'},
            {'name': 'CardHeader', 'classes': '...', 'data_slot': 'card-header'},
        ]
    """
    elements = []

    # Find all function component definitions
    # Pattern: function ComponentName(...) { return ( <element data-slot="..." className={cn("...", ...)} /> )}
    func_pattern = r'function\s+(\w+)\s*\([^)]*\)[^{]*\{[^}]*return\s*\((.*?)\)'

    for func_match in re.finditer(func_pattern, tsx_content, re.DOTALL):
        comp_name = func_match.group(1)
        return_content = func_match.group(2)

        # Extract data-slot
        data_slot_match = re.search(r'data-slot=["\']([^"\']+)["\']', return_content)
        data_slot = data_slot_match.group(1) if data_slot_match else comp_name.lower()

        # Extract className - look for cn("...", ...) pattern
        cn_match = re.search(r'className=\{cn\s*\(\s*["\`]([^"\`]*)["\`]', return_content, re.DOTALL)
        classes = cn_match.group(1).strip() if cn_match else ""

        elements.append({
            'name': comp_name,
            'classes': classes,
            'data_slot': data_slot
        })

    return elements


def normalize_classes(class_string):
    """Normalize a class string to a sorted list for comparison."""
    return sorted(class_string.strip().split())


def render_macro(template_name, **kwargs):
    """Render a Jinja macro and return the HTML."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template = env.get_template(template_name)
    return template.render(**kwargs)


def extract_classes_from_html(html):
    """Extract classes from rendered HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    # Find the first element with a class attribute
    element = soup.find(class_=True)
    if element and element.get('class'):
        return element.get('class')
    return []


def extract_data_slot_from_html(html):
    """Extract data-slot attribute from rendered HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    element = soup.find(attrs={'data-slot': True})
    if element:
        return element.get('data-slot')
    return None


# ===== Button Tests =====

def test_button_parity():
    """Test button macro matches shadcn button.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "button.tsx"
    tsx_content = tsx_path.read_text()

    parsed = parse_cva_component(tsx_content, "button")
    assert parsed is not None, "Failed to parse button.tsx"

    # Test each variant combination
    variant_types = list(parsed['variants'].keys())

    # For button: test all variant x size combinations
    for variant_name in parsed['variants'].get('variant', {}).keys():
        for size_name in parsed['variants'].get('size', {}).keys():
            # Get expected classes
            expected_classes = normalize_classes(
                parsed['base'] + ' ' +
                parsed['variants']['variant'].get(variant_name, '') + ' ' +
                parsed['variants']['size'].get(size_name, '')
            )

            # Render macro (we'll implement the macro next)
            # For now, this is the interface we expect
            html = render_macro('button.html',
                               variant=variant_name,
                               size=size_name,
                               content='Test')

            actual_classes = normalize_classes(' '.join(extract_classes_from_html(html)))
            actual_slot = extract_data_slot_from_html(html)

            assert actual_classes == expected_classes, \
                f"Button variant={variant_name} size={size_name}: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"

            assert actual_slot == parsed['data_slot'], \
                f"Button variant={variant_name} size={size_name}: data-slot mismatch. Expected: {parsed['data_slot']}, Actual: {actual_slot}"


# ===== Badge Tests =====

def test_badge_parity():
    """Test badge macro matches shadcn badge.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "badge.tsx"
    tsx_content = tsx_path.read_text()

    parsed = parse_cva_component(tsx_content, "badge")
    assert parsed is not None, "Failed to parse badge.tsx"

    # Test each variant
    for variant_name in parsed['variants'].get('variant', {}).keys():
        expected_classes = normalize_classes(
            parsed['base'] + ' ' +
            parsed['variants']['variant'].get(variant_name, '')
        )

        html = render_macro('badge.html', variant=variant_name, content='Test')

        actual_classes = normalize_classes(' '.join(extract_classes_from_html(html)))
        actual_slot = extract_data_slot_from_html(html)

        assert actual_classes == expected_classes, \
            f"Badge variant={variant_name}: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"

        assert actual_slot == parsed['data_slot'], \
            f"Badge variant={variant_name}: data-slot mismatch"


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
