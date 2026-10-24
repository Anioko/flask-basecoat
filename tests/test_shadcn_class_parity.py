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


# ===== Card Tests =====

def test_card_parity():
    """Test card macros match shadcn card.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "card.tsx"
    tsx_content = tsx_path.read_text()

    elements = parse_simple_component(tsx_content, "card")
    assert len(elements) > 0, "Failed to parse card.tsx"

    # Expected components
    expected = {
        'Card': 'bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm',
        'CardHeader': '@container/card-header grid auto-rows-min grid-rows-[auto_auto] items-start gap-2 px-6 has-data-[slot=card-action]:grid-cols-[1fr_auto] [.border-b]:pb-6',
        'CardTitle': 'leading-none font-semibold',
        'CardDescription': 'text-muted-foreground text-sm',
        'CardAction': 'col-start-2 row-span-2 row-start-1 self-start justify-self-end',
        'CardContent': 'px-6',
        'CardFooter': 'flex items-center px-6 [.border-t]:pt-6',
    }

    for elem in elements:
        if elem['name'] in expected:
            expected_classes = normalize_classes(expected[elem['name']])
            actual_classes = normalize_classes(elem['classes'])

            assert actual_classes == expected_classes, \
                f"{elem['name']}: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"

    # Now test rendering the macros
    macro_map = {
        'Card': 'card',
        'CardHeader': 'card_header',
        'CardTitle': 'card_title',
        'CardDescription': 'card_description',
        'CardAction': 'card_action',
        'CardContent': 'card_content',
        'CardFooter': 'card_footer',
    }

    for comp_name, macro_name in macro_map.items():
        if comp_name in expected:
            html = render_macro('card.html', macro_name=macro_name, content='Test')
            # Parse the macro call dynamically
            env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
            template_str = "{% from 'card.html' import " + macro_name + " %}{{ " + macro_name + "(content='Test') }}"
            template = env.from_string(template_str)
            html = template.render()

            actual_classes = normalize_classes(' '.join(extract_classes_from_html(html)))
            expected_classes = normalize_classes(expected[comp_name])
            actual_slot = extract_data_slot_from_html(html)
            expected_slot = comp_name.lower().replace('card', 'card-') if comp_name != 'Card' else 'card'
            expected_slot = expected_slot.rstrip('-')

            assert actual_classes == expected_classes, \
                f"{comp_name} macro: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"

            assert actual_slot == expected_slot, \
                f"{comp_name} macro: data-slot mismatch. Expected: {expected_slot}, Actual: {actual_slot}"


# ===== Simple Component Tests =====

def test_input_parity():
    """Test input macro matches shadcn input.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "input.tsx"
    tsx_content = tsx_path.read_text()

    # Extract all strings from cn() call
    cn_start = tsx_content.find('className={cn(')
    if cn_start == -1:
        assert False, "Failed to find className={cn("

    # Find the matching closing paren
    depth = 0
    cn_end = cn_start + len('className={cn')
    for i in range(cn_start + len('className={cn'), len(tsx_content)):
        if tsx_content[i] == '(':
            depth += 1
        elif tsx_content[i] == ')':
            depth -= 1
            if depth == 0:
                cn_end = i
                break

    cn_content = tsx_content[cn_start:cn_end + 1]

    # Extract all quoted strings from the cn() call
    all_classes = []
    for match in re.finditer(r'"([^"]*)"', cn_content):
        classes = match.group(1).replace('\n', ' ').strip()
        if classes and not classes.startswith('$'):  # Skip variables
            all_classes.append(classes)

    expected_classes = normalize_classes(' '.join(all_classes))

    # Render macro
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template_str = "{% from 'input.html' import input %}{{ input() }}"
    template = env.from_string(template_str)
    html = template.render()

    actual_classes = normalize_classes(' '.join(extract_classes_from_html(html)))
    actual_slot = extract_data_slot_from_html(html)

    assert actual_classes == expected_classes, \
        f"Input: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"
    assert actual_slot == 'input', f"Input: data-slot mismatch"


def test_label_parity():
    """Test label macro matches shadcn label.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "label.tsx"
    tsx_content = tsx_path.read_text()

    cn_match = re.search(r'className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert cn_match, "Failed to parse label.tsx"

    expected_classes = normalize_classes(cn_match.group(1).replace('\n', ' '))

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template_str = "{% from 'label.html' import label %}{{ label(content='Test') }}"
    template = env.from_string(template_str)
    html = template.render()

    actual_classes = normalize_classes(' '.join(extract_classes_from_html(html)))
    actual_slot = extract_data_slot_from_html(html)

    assert actual_classes == expected_classes, \
        f"Label: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"
    assert actual_slot == 'label'


def test_textarea_parity():
    """Test textarea macro matches shadcn textarea.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "textarea.tsx"
    tsx_content = tsx_path.read_text()

    cn_match = re.search(r'className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert cn_match, "Failed to parse textarea.tsx"

    expected_classes = normalize_classes(cn_match.group(1).replace('\n', ' '))

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template_str = "{% from 'textarea.html' import textarea %}{{ textarea() }}"
    template = env.from_string(template_str)
    html = template.render()

    actual_classes = normalize_classes(' '.join(extract_classes_from_html(html)))
    actual_slot = extract_data_slot_from_html(html)

    assert actual_classes == expected_classes, \
        f"Textarea: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"
    assert actual_slot == 'textarea'


def test_separator_parity():
    """Test separator macro matches shadcn separator.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "separator.tsx"
    tsx_content = tsx_path.read_text()

    cn_match = re.search(r'className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert cn_match, "Failed to parse separator.tsx"

    expected_classes = normalize_classes(cn_match.group(1).replace('\n', ' '))

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template_str = "{% from 'separator.html' import separator %}{{ separator() }}"
    template = env.from_string(template_str)
    html = template.render()

    actual_classes = normalize_classes(' '.join(extract_classes_from_html(html)))
    actual_slot = extract_data_slot_from_html(html)

    assert actual_classes == expected_classes, \
        f"Separator: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"
    assert actual_slot == 'separator'


def test_skeleton_parity():
    """Test skeleton macro matches shadcn skeleton.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "skeleton.tsx"
    tsx_content = tsx_path.read_text()

    cn_match = re.search(r'className=\{cn\(["\']([^"\']+)["\']', tsx_content)
    assert cn_match, "Failed to parse skeleton.tsx"

    expected_classes = normalize_classes(cn_match.group(1))

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template_str = "{% from 'skeleton.html' import skeleton %}{{ skeleton() }}"
    template = env.from_string(template_str)
    html = template.render()

    actual_classes = normalize_classes(' '.join(extract_classes_from_html(html)))
    actual_slot = extract_data_slot_from_html(html)

    assert actual_classes == expected_classes, \
        f"Skeleton: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"
    assert actual_slot == 'skeleton'


# ===== Alert Tests =====

def test_alert_parity():
    """Test alert macro matches shadcn alert.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "alert.tsx"
    tsx_content = tsx_path.read_text()

    parsed = parse_cva_component(tsx_content, "alert")
    assert parsed is not None, "Failed to parse alert.tsx"

    # Test each variant
    for variant_name in parsed['variants'].get('variant', {}).keys():
        expected_classes = normalize_classes(
            parsed['base'] + ' ' +
            parsed['variants']['variant'].get(variant_name, '')
        )

        env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
        template_str = "{% from 'alert.html' import alert %}{{ alert(variant='" + variant_name + "') }}"
        template = env.from_string(template_str)
        html = template.render()

        actual_classes = normalize_classes(' '.join(extract_classes_from_html(html)))
        actual_slot = extract_data_slot_from_html(html)

        assert actual_classes == expected_classes, \
            f"Alert variant={variant_name}: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"

        assert actual_slot == parsed['data_slot'], \
            f"Alert variant={variant_name}: data-slot mismatch"


# ===== Toggle Tests =====

def test_toggle_parity():
    """Test toggle macro matches shadcn toggle.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "toggle.tsx"
    tsx_content = tsx_path.read_text()

    parsed = parse_cva_component(tsx_content, "toggle")
    assert parsed is not None, "Failed to parse toggle.tsx"

    # Test each variant/size combination
    for variant_name in parsed['variants'].get('variant', {}).keys():
        for size_name in parsed['variants'].get('size', {}).keys():
            expected_classes = normalize_classes(
                parsed['base'] + ' ' +
                parsed['variants']['variant'].get(variant_name, '') + ' ' +
                parsed['variants']['size'].get(size_name, '')
            )

            env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
            template_str = "{% from 'toggle.html' import toggle %}{{ toggle(variant='" + variant_name + "', size='" + size_name + "') }}"
            template = env.from_string(template_str)
            html = template.render()

            actual_classes = normalize_classes(' '.join(extract_classes_from_html(html)))
            actual_slot = extract_data_slot_from_html(html)

            assert actual_classes == expected_classes, \
                f"Toggle variant={variant_name} size={size_name}: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"

            assert actual_slot == parsed['data_slot'], \
                f"Toggle variant={variant_name} size={size_name}: data-slot mismatch"


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
