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
TEMPLATES_PATH = Path(__file__).parent.parent / "flask_basecoat/templates/basecoat"


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
    # Pattern: function ComponentName(...) { return ( ... ) }
    # Use a more robust pattern that matches parentheses properly
    func_starts = [(m.group(1), m.start()) for m in re.finditer(r'function\s+(\w+)\s*\([^)]*\)[^{]*\{', tsx_content)]

    for comp_name, start_pos in func_starts:
        # Find the return statement
        return_match = re.search(r'return\s*\(', tsx_content[start_pos:start_pos+500])
        if not return_match:
            continue

        return_start = start_pos + return_match.end()

        # Match parentheses to find the closing )
        depth = 1
        return_end = return_start
        for i in range(return_start, len(tsx_content)):
            if tsx_content[i] == '(':
                depth += 1
            elif tsx_content[i] == ')':
                depth -= 1
                if depth == 0:
                    return_end = i
                    break

        return_content = tsx_content[return_start:return_end]

        # Extract data-slot
        data_slot_match = re.search(r'data-slot=["\']([^"\']+)["\']', return_content)
        data_slot = data_slot_match.group(1) if data_slot_match else comp_name.lower()

        # Extract className - look for cn("...", ...) pattern
        # Handle multi-line className strings by finding the matching quote
        cn_start = re.search(r'className=\{cn\s*\(\s*["\`]', return_content, re.DOTALL)
        if cn_start:
            # Find the closing quote - handle escaped quotes and newlines
            start_pos = cn_start.end()
            quote_char = return_content[cn_start.end() - 1]
            end_pos = start_pos
            escaped = False
            for i in range(start_pos, len(return_content)):
                if escaped:
                    escaped = False
                    continue
                if return_content[i] == '\\':
                    escaped = True
                    continue
                if return_content[i] == quote_char:
                    end_pos = i
                    break
            classes = return_content[start_pos:end_pos].strip()
        else:
            classes = ""

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


# ===== Checkbox Tests =====

def test_checkbox_parity():
    """Test checkbox macro matches shadcn checkbox.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "checkbox.tsx"
    tsx_content = tsx_path.read_text()

    # Extract checkbox root classes
    cn_match = re.search(r'data-slot="checkbox".*?className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert cn_match, "Failed to parse checkbox.tsx root classes"
    root_classes = normalize_classes(cn_match.group(1).replace('\n', ' '))

    # Extract checkbox indicator classes
    indicator_match = re.search(r'data-slot="checkbox-indicator".*?className=\{?"([^"]+)"', tsx_content, re.DOTALL)
    assert indicator_match, "Failed to parse checkbox.tsx indicator classes"
    indicator_classes = normalize_classes(indicator_match.group(1).replace('\n', ' '))

    # Render macro
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template_str = "{% from 'checkbox.html' import checkbox %}{{ checkbox() }}"
    template = env.from_string(template_str)
    html = template.render()

    soup = BeautifulSoup(html, 'html.parser')
    root_elem = soup.find(attrs={'data-slot': 'checkbox'})
    indicator_elem = soup.find(attrs={'data-slot': 'checkbox-indicator'})

    assert root_elem, "Checkbox root element not found"
    assert indicator_elem, "Checkbox indicator element not found"

    actual_root_classes = normalize_classes(' '.join(root_elem.get('class', [])))
    actual_indicator_classes = normalize_classes(' '.join(indicator_elem.get('class', [])))

    assert actual_root_classes == root_classes, \
        f"Checkbox root: classes mismatch.\nExpected: {root_classes}\nActual: {actual_root_classes}"
    assert actual_indicator_classes == indicator_classes, \
        f"Checkbox indicator: classes mismatch.\nExpected: {indicator_classes}\nActual: {actual_indicator_classes}"


# ===== Switch Tests =====

def test_switch_parity():
    """Test switch macro matches shadcn switch.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "switch.tsx"
    tsx_content = tsx_path.read_text()

    # Extract switch root classes
    cn_match = re.search(r'data-slot="switch".*?className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert cn_match, "Failed to parse switch.tsx root classes"
    root_classes = normalize_classes(cn_match.group(1).replace('\n', ' '))

    # Extract switch thumb classes
    thumb_match = re.search(r'data-slot="switch-thumb".*?className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert thumb_match, "Failed to parse switch.tsx thumb classes"
    thumb_classes = normalize_classes(thumb_match.group(1).replace('\n', ' '))

    # Render macro
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template_str = "{% from 'switch.html' import switch %}{{ switch() }}"
    template = env.from_string(template_str)
    html = template.render()

    soup = BeautifulSoup(html, 'html.parser')
    root_elem = soup.find(attrs={'data-slot': 'switch'})
    thumb_elem = soup.find(attrs={'data-slot': 'switch-thumb'})

    assert root_elem, "Switch root element not found"
    assert thumb_elem, "Switch thumb element not found"

    actual_root_classes = normalize_classes(' '.join(root_elem.get('class', [])))
    actual_thumb_classes = normalize_classes(' '.join(thumb_elem.get('class', [])))

    assert actual_root_classes == root_classes, \
        f"Switch root: classes mismatch.\nExpected: {root_classes}\nActual: {actual_root_classes}"
    assert actual_thumb_classes == thumb_classes, \
        f"Switch thumb: classes mismatch.\nExpected: {thumb_classes}\nActual: {actual_thumb_classes}"


# ===== Avatar Tests =====

def test_avatar_parity():
    """Test avatar macros match shadcn avatar.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "avatar.tsx"
    tsx_content = tsx_path.read_text()

    elements = parse_simple_component(tsx_content, "avatar")
    assert len(elements) >= 3, "Failed to parse avatar.tsx"

    # Map components
    component_map = {elem['name']: elem for elem in elements}

    for comp_name in ['Avatar', 'AvatarImage', 'AvatarFallback']:
        assert comp_name in component_map, f"{comp_name} not found in parsed elements"
        expected_classes = normalize_classes(component_map[comp_name]['classes'])
        expected_slot = component_map[comp_name]['data_slot']

        macro_name = comp_name.lower().replace('avatar', 'avatar_') if comp_name != 'Avatar' else 'avatar'
        macro_name = macro_name.rstrip('_')

        env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
        template_str = "{% from 'avatar.html' import " + macro_name + " %}{{ " + macro_name + "() }}"
        template = env.from_string(template_str)
        html = template.render()

        soup = BeautifulSoup(html, 'html.parser')
        elem = soup.find(attrs={'data-slot': expected_slot})

        assert elem, f"{comp_name} element not found"
        actual_classes = normalize_classes(' '.join(elem.get('class', [])))

        assert actual_classes == expected_classes, \
            f"{comp_name}: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"


# ===== Progress Tests =====

def test_progress_parity():
    """Test progress macro matches shadcn progress.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "progress.tsx"
    tsx_content = tsx_path.read_text()

    # Extract progress root classes
    cn_match = re.search(r'data-slot="progress".*?className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert cn_match, "Failed to parse progress.tsx root classes"
    root_classes = normalize_classes(cn_match.group(1).replace('\n', ' '))

    # Extract progress indicator classes
    indicator_match = re.search(r'data-slot="progress-indicator".*?className="([^"]+)"', tsx_content, re.DOTALL)
    assert indicator_match, "Failed to parse progress.tsx indicator classes"
    indicator_classes = normalize_classes(indicator_match.group(1).replace('\n', ' '))

    # Render macro
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template_str = "{% from 'progress.html' import progress %}{{ progress(value=50) }}"
    template = env.from_string(template_str)
    html = template.render()

    soup = BeautifulSoup(html, 'html.parser')
    root_elem = soup.find(attrs={'data-slot': 'progress'})
    indicator_elem = soup.find(attrs={'data-slot': 'progress-indicator'})

    assert root_elem, "Progress root element not found"
    assert indicator_elem, "Progress indicator element not found"

    actual_root_classes = normalize_classes(' '.join(root_elem.get('class', [])))
    actual_indicator_classes = normalize_classes(' '.join(indicator_elem.get('class', [])))

    assert actual_root_classes == root_classes, \
        f"Progress root: classes mismatch.\nExpected: {root_classes}\nActual: {actual_root_classes}"
    assert actual_indicator_classes == indicator_classes, \
        f"Progress indicator: classes mismatch.\nExpected: {indicator_classes}\nActual: {actual_indicator_classes}"


# ===== Breadcrumb Tests =====

def test_breadcrumb_parity():
    """Test breadcrumb macros match shadcn breadcrumb.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "breadcrumb.tsx"
    tsx_content = tsx_path.read_text()

    elements = parse_simple_component(tsx_content, "breadcrumb")
    assert len(elements) > 0, "Failed to parse breadcrumb.tsx"

    component_map = {elem['name']: elem for elem in elements}

    test_components = {
        'BreadcrumbList': 'breadcrumb_list',
        'BreadcrumbItem': 'breadcrumb_item',
        'BreadcrumbLink': 'breadcrumb_link',
        'BreadcrumbPage': 'breadcrumb_page',
        'BreadcrumbSeparator': 'breadcrumb_separator',
        'BreadcrumbEllipsis': 'breadcrumb_ellipsis',
    }

    for comp_name, macro_name in test_components.items():
        if comp_name in component_map:
            expected_classes = normalize_classes(component_map[comp_name]['classes'])
            expected_slot = component_map[comp_name]['data_slot']

            env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
            template_str = "{% from 'breadcrumb.html' import " + macro_name + " %}{{ " + macro_name + "() }}"
            template = env.from_string(template_str)
            html = template.render()

            soup = BeautifulSoup(html, 'html.parser')
            elem = soup.find(attrs={'data-slot': expected_slot})

            assert elem, f"{comp_name} element with data-slot={expected_slot} not found"
            actual_classes = normalize_classes(' '.join(elem.get('class', [])))

            assert actual_classes == expected_classes, \
                f"{comp_name}: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"


# ===== Pagination Tests =====

def test_pagination_parity():
    """Test pagination macros match shadcn pagination.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "pagination.tsx"
    tsx_content = tsx_path.read_text()

    elements = parse_simple_component(tsx_content, "pagination")
    assert len(elements) > 0, "Failed to parse pagination.tsx"

    component_map = {elem['name']: elem for elem in elements}

    test_components = {
        'Pagination': 'pagination',
        'PaginationContent': 'pagination_content',
        'PaginationEllipsis': 'pagination_ellipsis',
    }

    for comp_name, macro_name in test_components.items():
        if comp_name in component_map:
            expected_classes = normalize_classes(component_map[comp_name]['classes'])
            expected_slot = component_map[comp_name]['data_slot']

            env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
            template_str = "{% from 'pagination.html' import " + macro_name + " %}{{ " + macro_name + "() }}"
            template = env.from_string(template_str)
            html = template.render()

            soup = BeautifulSoup(html, 'html.parser')
            elem = soup.find(attrs={'data-slot': expected_slot})

            assert elem, f"{comp_name} element with data-slot={expected_slot} not found"
            actual_classes = normalize_classes(' '.join(elem.get('class', [])))

            assert actual_classes == expected_classes, \
                f"{comp_name}: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"


# ===== Select Tests =====

# Classes shadcn applies to select parts that are dropped on purpose, each with its reason.
SELECT_DROPPED = {
    # position="popper" side offsets: Basecoat's [data-popover] wrapper positions itself from data-side with margins.
    "content": {
        "data-[side=bottom]:translate-y-1": "Radix popper side offset; Basecoat offsets the wrapper with margin-top",
        "data-[side=left]:-translate-x-1": "Radix popper side offset; Basecoat offsets the wrapper with margin-right",
        "data-[side=right]:translate-x-1": "Radix popper side offset; Basecoat offsets the wrapper with margin-left",
        "data-[side=top]:-translate-y-1": "Radix popper side offset; Basecoat offsets the wrapper with margin-bottom",
    },
    # Radix sizes the viewport from CSS variables that only exist inside Radix's popper.
    "viewport": {
        "h-[var(--radix-select-trigger-height)]": "--radix-select-trigger-height is never defined without Radix",
        "min-w-[var(--radix-select-trigger-width)]": "--radix-select-trigger-width is never defined; Basecoat's min-width:100% matches the trigger",
    },
}


def _tsx_classes(tsx, slot):
    """Classes of the first cn("...") string after data-slot="<slot>"."""
    m = re.search(r'data-slot="' + slot + r'".*?cn\(\s*"([^"]+)"', tsx, re.DOTALL)
    assert m, f"Failed to parse {slot} classes in select.tsx"
    return normalize_classes(m.group(1).replace('\n', ' '))


def _tsx_string_after(tsx, marker):
    m = re.search(re.escape(marker) + r'\s*&&\s*"([^"]+)"', tsx)
    assert m, f"Failed to parse {marker} string in select.tsx"
    return normalize_classes(m.group(1))


def _classes(elem):
    return normalize_classes(' '.join(elem.get('class', [])))


def test_select_parity():
    """Every part select.tsx renders: trigger, content, viewport, label, item (+indicator), separator, scroll buttons."""
    tsx = (COMPONENTS_PATH / "select.tsx").read_text()

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    html = env.from_string(
        "{% from 'select.html' import select, select_group, select_item, select_separator %}"
        "{% call select(name='tz', id='tz', placeholder='Pick') %}"
        "{% call select_group(label='Group', id='tz-g') %}{{ select_item(value='a', content='A') }}{% endcall %}"
        "{{ select_separator() }}"
        "{% endcall %}"
    ).render()
    soup = BeautifulSoup(html, 'html.parser')

    def part(slot):
        elem = soup.find(attrs={'data-slot': slot})
        assert elem, f"{slot} element not found"
        return elem

    # Root, group and value carry their data-slot
    for slot in ('select', 'select-group', 'select-value'):
        part(slot)
    assert re.search(r'data-slot="select"', tsx) and re.search(r'data-slot="select-group"', tsx) and re.search(r'data-slot="select-value"', tsx)

    # Trigger
    trigger = part('select-trigger')
    assert _classes(trigger) == _tsx_classes(tsx, 'select-trigger'), "Select trigger: classes mismatch"
    assert trigger.get('data-size') == 'default'
    icon = trigger.find('svg')
    assert icon and set(icon['class']) == {'size-4', 'opacity-50'}, "Select trigger chevron: size-4 opacity-50"

    # Content panel: every static class kept (animation/state ones are inert without Radix data-state), popper offsets dropped.
    content = part('select-content')
    expected_content = _tsx_classes(tsx, 'select-content')
    popper = _tsx_string_after(tsx, 'position === "popper"')
    assert set(popper) == set(SELECT_DROPPED['content']), "Dropped popper classes must be exactly the named ones"
    assert _classes(content) == expected_content, "Select content: classes mismatch"
    for needed in ('bg-popover', 'text-popover-foreground', 'relative', 'z-50', 'min-w-[8rem]', 'overflow-x-hidden',
                   'overflow-y-auto', 'rounded-md', 'border', 'shadow-md', 'max-h-(--radix-select-content-available-height)'):
        assert needed in content['class']
    # Basecoat's positioned wrapper (Radix's popper wrapper) holds the content; its own surface is neutralised
    assert content.parent.has_attr('data-popover')

    # Viewport (p-1 plus the popper sizing, minus the Radix-variable classes named above)
    viewport = part('select-viewport')
    m = re.search(r'Viewport\s+className=\{cn\(\s*"([^"]+)",\s*position === "popper" &&\s*"([^"]+)"', tsx)
    assert m, "Failed to parse viewport classes"
    viewport_expected = m.group(1).split() + [c for c in m.group(2).split() if c not in SELECT_DROPPED['viewport']]
    assert set(m.group(2).split()) - set(viewport_expected) == set(SELECT_DROPPED['viewport'])
    assert _classes(viewport) == normalize_classes(' '.join(viewport_expected)), "Select viewport: classes mismatch"
    assert viewport['role'] == 'listbox'

    # Label, item, separator
    assert _classes(part('select-label')) == _tsx_classes(tsx, 'select-label'), "Select label: classes mismatch"
    item = part('select-item')
    assert _classes(item) == _tsx_classes(tsx, 'select-item'), "Select item: classes mismatch"
    assert _classes(part('select-separator')) == _tsx_classes(tsx, 'select-separator'), "Select separator: classes mismatch"

    # Item indicator: first child span "absolute right-2 flex size-3.5 items-center justify-center" wrapping a size-4 check;
    # the check is shown only while aria-selected (the ItemIndicator behaviour), via an extra in-aria-selected utility.
    indicator_tsx = re.search(r'<span className="([^"]+)">\s*<SelectPrimitive.ItemIndicator>', tsx).group(1)
    spans = item.find_all('span', recursive=False)
    assert len(spans) == 2, "Item renders indicator span then text span"
    assert _classes(spans[0]) == normalize_classes(indicator_tsx), "Select item indicator: classes mismatch"
    check = spans[0].find('svg')
    assert 'size-4' in check['class'] and 'in-aria-selected:block' in check['class']

    # Scroll buttons: shadcn classes, present but hidden until the list overflows
    for direction in ('up', 'down'):
        button = part(f'select-scroll-{direction}-button')
        assert _classes(button) == _tsx_classes(tsx, f'select-scroll-{direction}-button'), f"Scroll {direction} button: classes mismatch"
        assert button.has_attr('hidden'), "Scroll buttons are hidden until the list overflows"
        assert 'size-4' in button.find('svg')['class']


# ===== Radio Group Tests =====

def test_radio_group_parity():
    """Test radio-group macro matches shadcn radio-group.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "radio-group.tsx"
    tsx_content = tsx_path.read_text()

    # Extract radio-group root classes
    root_match = re.search(r'data-slot="radio-group".*?className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert root_match, "Failed to parse radio-group.tsx root classes"
    root_classes = normalize_classes(root_match.group(1).replace('\n', ' '))

    # Extract radio-group-item classes
    item_match = re.search(r'data-slot="radio-group-item".*?className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert item_match, "Failed to parse radio-group.tsx item classes"
    item_classes = normalize_classes(item_match.group(1).replace('\n', ' '))

    # Extract indicator classes
    indicator_match = re.search(r'data-slot="radio-group-indicator".*?className="([^"]+)"', tsx_content, re.DOTALL)
    assert indicator_match, "Failed to parse radio-group.tsx indicator classes"
    indicator_classes = normalize_classes(indicator_match.group(1).replace('\n', ' '))

    # Render macros
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))

    template_str = "{% from 'radio-group.html' import radio_group %}{{ radio_group() }}"
    template = env.from_string(template_str)
    html = template.render()
    soup = BeautifulSoup(html, 'html.parser')
    root_elem = soup.find(attrs={'data-slot': 'radio-group'})
    assert root_elem, "Radio group root element not found"
    actual_root_classes = normalize_classes(' '.join(root_elem.get('class', [])))
    assert actual_root_classes == root_classes, \
        f"Radio group root: classes mismatch.\nExpected: {root_classes}\nActual: {actual_root_classes}"

    template_str = "{% from 'radio-group.html' import radio_group_item %}{{ radio_group_item() }}"
    template = env.from_string(template_str)
    html = template.render()
    soup = BeautifulSoup(html, 'html.parser')
    item_elem = soup.find(attrs={'data-slot': 'radio-group-item'})
    indicator_elem = soup.find(attrs={'data-slot': 'radio-group-indicator'})
    assert item_elem, "Radio group item element not found"
    assert indicator_elem, "Radio group indicator element not found"
    actual_item_classes = normalize_classes(' '.join(item_elem.get('class', [])))
    actual_indicator_classes = normalize_classes(' '.join(indicator_elem.get('class', [])))
    assert actual_item_classes == item_classes, \
        f"Radio group item: classes mismatch.\nExpected: {item_classes}\nActual: {actual_item_classes}"
    assert actual_indicator_classes == indicator_classes, \
        f"Radio group indicator: classes mismatch.\nExpected: {indicator_classes}\nActual: {actual_indicator_classes}"


# ===== Tabs Tests =====

def test_tabs_parity():
    """Test tabs macros match shadcn tabs.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "tabs.tsx"
    tsx_content = tsx_path.read_text()

    elements = parse_simple_component(tsx_content, "tabs")
    assert len(elements) >= 4, "Failed to parse tabs.tsx"

    component_map = {elem['name']: elem for elem in elements}

    test_components = {
        'Tabs': 'tabs',
        'TabsList': 'tabs_list',
        'TabsTrigger': 'tabs_trigger',
        'TabsContent': 'tabs_content',
    }

    for comp_name, macro_name in test_components.items():
        assert comp_name in component_map, f"{comp_name} not found"
        expected_classes = normalize_classes(component_map[comp_name]['classes'])
        expected_slot = component_map[comp_name]['data_slot']

        env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
        template_str = "{% from 'tabs.html' import " + macro_name + " %}{{ " + macro_name + "() }}"
        template = env.from_string(template_str)
        html = template.render()

        soup = BeautifulSoup(html, 'html.parser')
        elem = soup.find(attrs={'data-slot': expected_slot})

        assert elem, f"{comp_name} element with data-slot={expected_slot} not found"
        actual_classes = normalize_classes(' '.join(elem.get('class', [])))

        assert actual_classes == expected_classes, \
            f"{comp_name}: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"


# ===== Table Tests =====

def test_table_parity():
    """Test table macros match shadcn table.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "table.tsx"
    tsx_content = tsx_path.read_text()

    elements = parse_simple_component(tsx_content, "table")
    assert len(elements) > 0, "Failed to parse table.tsx"

    component_map = {elem['name']: elem for elem in elements}

    # Test table element specially since it's wrapped in a container
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template_str = "{% from 'table.html' import table %}{{ table() }}"
    template = env.from_string(template_str)
    html = template.render()
    soup = BeautifulSoup(html, 'html.parser')
    # Find the inner table element, not the container
    table_elem = soup.find('table', attrs={'data-slot': 'table'})
    assert table_elem, "Table element not found"
    actual_table_classes = normalize_classes(' '.join(table_elem.get('class', [])))
    expected_table_classes = normalize_classes('w-full caption-bottom text-sm')
    assert actual_table_classes == expected_table_classes, \
        f"Table: classes mismatch.\nExpected: {expected_table_classes}\nActual: {actual_table_classes}"

    # Test other table components
    test_components = {
        'TableHeader': 'table_header',
        'TableBody': 'table_body',
        'TableFooter': 'table_footer',
        'TableRow': 'table_row',
        'TableHead': 'table_head',
        'TableCell': 'table_cell',
    }

    for comp_name, macro_name in test_components.items():
        if comp_name in component_map:
            expected_classes = normalize_classes(component_map[comp_name]['classes'])
            expected_slot = component_map[comp_name]['data_slot']

            env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
            template_str = "{% from 'table.html' import " + macro_name + " %}{{ " + macro_name + "() }}"

            template = env.from_string(template_str)
            html = template.render()

            soup = BeautifulSoup(html, 'html.parser')
            elem = soup.find(attrs={'data-slot': expected_slot})

            assert elem, f"{comp_name} element with data-slot={expected_slot} not found"
            actual_classes = normalize_classes(' '.join(elem.get('class', [])))

            assert actual_classes == expected_classes, \
                f"{comp_name}: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"


# ===== Tooltip Tests =====

def test_tooltip_parity():
    """Test tooltip macros match shadcn tooltip.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "tooltip.tsx"
    tsx_content = tsx_path.read_text()

    # Test TooltipContent
    content_match = re.search(r'data-slot="tooltip-content".*?className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert content_match, "Failed to parse tooltip.tsx content classes"
    content_classes = normalize_classes(content_match.group(1).replace('\n', ' '))

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template_str = "{% from 'tooltip.html' import tooltip_content %}{{ tooltip_content(content='Test') }}"
    template = env.from_string(template_str)
    html = template.render()

    soup = BeautifulSoup(html, 'html.parser')
    content_elem = soup.find(attrs={'data-slot': 'tooltip-content'})

    assert content_elem, "Tooltip content element not found"
    actual_classes = normalize_classes(' '.join(content_elem.get('class', [])))

    assert actual_classes == content_classes, \
        f"Tooltip content: classes mismatch.\nExpected: {content_classes}\nActual: {actual_classes}"


# ===== Popover Tests =====

def test_popover_parity():
    """Test popover macros match shadcn popover.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "popover.tsx"
    tsx_content = tsx_path.read_text()

    # Test PopoverContent
    content_match = re.search(r'data-slot="popover-content".*?className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert content_match, "Failed to parse popover.tsx content classes"
    content_classes = normalize_classes(content_match.group(1).replace('\n', ' '))

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template_str = "{% from 'popover.html' import popover_content %}{{ popover_content(content='Test') }}"
    template = env.from_string(template_str)
    html = template.render()

    soup = BeautifulSoup(html, 'html.parser')
    content_elem = soup.find(attrs={'data-slot': 'popover-content'})

    assert content_elem, "Popover content element not found"
    actual_classes = normalize_classes(' '.join(content_elem.get('class', [])))

    assert actual_classes == content_classes, \
        f"Popover content: classes mismatch.\nExpected: {content_classes}\nActual: {actual_classes}"


# ===== Dialog Tests =====

def test_dialog_parity():
    """Test dialog macros match shadcn dialog.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "dialog.tsx"
    tsx_content = tsx_path.read_text()

    elements = parse_simple_component(tsx_content, "dialog")
    assert len(elements) > 0, "Failed to parse dialog.tsx"

    component_map = {elem['name']: elem for elem in elements}

    # Only test the simpler dialog components that the parser can handle correctly
    # DialogOverlay and DialogContent are complex with nested components
    test_components = {
        'DialogOverlay': 'dialog_overlay',
        'DialogHeader': 'dialog_header',
        'DialogFooter': 'dialog_footer',
        'DialogTitle': 'dialog_title',
        'DialogDescription': 'dialog_description',
    }

    for comp_name, macro_name in test_components.items():
        if comp_name in component_map:
            expected_classes = normalize_classes(component_map[comp_name]['classes'])
            expected_slot = component_map[comp_name]['data_slot']

            env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
            template_str = "{% from 'dialog.html' import " + macro_name + " %}{{ " + macro_name + "() }}"
            template = env.from_string(template_str)
            html = template.render()

            soup = BeautifulSoup(html, 'html.parser')
            elem = soup.find(attrs={'data-slot': expected_slot})

            assert elem, f"{comp_name} element with data-slot={expected_slot} not found"
            actual_classes = normalize_classes(' '.join(elem.get('class', [])))

            assert actual_classes == expected_classes, \
                f"{comp_name}: classes mismatch.\nExpected: {expected_classes}\nActual: {actual_classes}"


# ===== Sheet Tests =====

def test_sheet_parity():
    """Test sheet macros match shadcn sheet.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "sheet.tsx"
    tsx_content = tsx_path.read_text()

    # Test SheetOverlay
    overlay_match = re.search(r'data-slot="sheet-overlay".*?className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert overlay_match, "Failed to parse sheet.tsx overlay classes"
    overlay_classes = normalize_classes(overlay_match.group(1).replace('\n', ' '))

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template_str = "{% from 'sheet.html' import sheet_overlay %}{{ sheet_overlay() }}"
    template = env.from_string(template_str)
    html = template.render()

    soup = BeautifulSoup(html, 'html.parser')
    overlay_elem = soup.find(attrs={'data-slot': 'sheet-overlay'})

    assert overlay_elem, "Sheet overlay element not found"
    actual_classes = normalize_classes(' '.join(overlay_elem.get('class', [])))

    assert actual_classes == overlay_classes, \
        f"Sheet overlay: classes mismatch.\nExpected: {overlay_classes}\nActual: {actual_classes}"


# ===== Dropdown Menu Tests =====

def test_dropdown_menu_parity():
    """Test dropdown-menu macros match shadcn dropdown-menu.tsx exactly."""
    tsx_path = COMPONENTS_PATH / "dropdown-menu.tsx"
    tsx_content = tsx_path.read_text()

    # Test DropdownMenuContent
    content_match = re.search(r'data-slot="dropdown-menu-content".*?className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert content_match, "Failed to parse dropdown-menu.tsx content classes"
    content_classes = normalize_classes(content_match.group(1).replace('\n', ' '))

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_PATH)))
    template_str = "{% from 'dropdown.html' import dropdown_menu_content %}{{ dropdown_menu_content() }}"
    template = env.from_string(template_str)
    html = template.render()

    soup = BeautifulSoup(html, 'html.parser')
    content_elem = soup.find(attrs={'data-slot': 'dropdown-menu-content'})

    assert content_elem, "Dropdown menu content element not found"
    actual_classes = normalize_classes(' '.join(content_elem.get('class', [])))

    assert actual_classes == content_classes, \
        f"Dropdown menu content: classes mismatch.\nExpected: {content_classes}\nActual: {actual_classes}"

    # Test DropdownMenuItem with variants
    item_match = re.search(r'data-slot="dropdown-menu-item".*?className=\{cn\(\s*"([^"]+)"', tsx_content, re.DOTALL)
    assert item_match, "Failed to parse dropdown-menu.tsx item classes"
    item_classes = normalize_classes(item_match.group(1).replace('\n', ' '))

    template_str = "{% from 'dropdown.html' import dropdown_menu_item %}{{ dropdown_menu_item() }}"
    template = env.from_string(template_str)
    html = template.render()

    soup = BeautifulSoup(html, 'html.parser')
    item_elem = soup.find(attrs={'data-slot': 'dropdown-menu-item'})

    assert item_elem, "Dropdown menu item element not found"
    actual_item_classes = normalize_classes(' '.join(item_elem.get('class', [])))

    assert actual_item_classes == item_classes, \
        f"Dropdown menu item: classes mismatch.\nExpected: {item_classes}\nActual: {actual_item_classes}"


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
