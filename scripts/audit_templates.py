#!/usr/bin/env python3
"""
Template Audit Script
Identifies templates that may need design system updates
"""
import os
import re
from pathlib import Path

# Configuration
TEMPLATE_DIR = Path('app/templates')
EXCLUDE_DIRS = {'macros', 'partials', 'errors'}
EXCLUDE_FILES = {'base.html', '_head.html', '_flashes.html'}

# Issues to check
CHECKS = {
    'old_semantic_ui': {
        'pattern': r'ui\.(button|primary|secondary|segment|form|input)',
        'message': 'Uses old Semantic UI classes',
        'severity': 'HIGH'
    },
    'missing_card': {
        'pattern': r'{% block content %}',
        'anti_pattern': r'(\.card|layout\.simple_card|layout\.page_container)',
        'message': 'Block content without card wrapper',
        'severity': 'MEDIUM'
    },
    'inline_styles': {
        'pattern': r'style="(?!overflow|width:|height:)',
        'message': 'Has inline styles (use Tailwind instead)',
        'severity': 'LOW'
    },
    'old_gray_colors': {
        'pattern': r'gray-(\d00)',
        'message': 'Uses gray-X00 (should be slate-X00)',
        'severity': 'LOW'
    },
}

def check_template(filepath):
    """Check a single template file for issues"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    issues = []

    for check_name, check_config in CHECKS.items():
        pattern = check_config['pattern']

        if check_name == 'missing_card':
            # Special case: check if has block content but no card
            if re.search(pattern, content):
                if not re.search(check_config['anti_pattern'], content):
                    # Exception: if it's a layout file or has multiple blocks
                    if 'layouts/' not in str(filepath) and content.count('{% block') < 3:
                        issues.append({
                            'check': check_name,
                            'message': check_config['message'],
                            'severity': check_config['severity']
                        })
        else:
            # Regular pattern check
            if re.search(pattern, content):
                issues.append({
                    'check': check_name,
                    'message': check_config['message'],
                    'severity': check_config['severity']
                })

    return issues

def audit_templates():
    """Audit all templates"""
    results = {
        'HIGH': [],
        'MEDIUM': [],
        'LOW': []
    }

    for root, dirs, files in os.walk(TEMPLATE_DIR):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            if not file.endswith('.html'):
                continue
            if file in EXCLUDE_FILES:
                continue

            filepath = Path(root) / file
            relative_path = filepath.relative_to(TEMPLATE_DIR)

            issues = check_template(filepath)

            if issues:
                for issue in issues:
                    results[issue['severity']].append({
                        'file': str(relative_path),
                        'message': issue['message'],
                        'check': issue['check']
                    })

    return results

def print_results(results):
    """Print audit results"""
    total_issues = sum(len(issues) for issues in results.values())

    print(f"\n{'='*60}")
    print(f"TEMPLATE AUDIT RESULTS")
    print(f"{'='*60}\n")

    print(f"Total files scanned: {sum(1 for _ in TEMPLATE_DIR.rglob('*.html'))}")
    print(f"Total issues found: {total_issues}\n")

    # Print by severity
    for severity in ['HIGH', 'MEDIUM', 'LOW']:
        issues = results[severity]
        if not issues:
            continue

        print(f"\n{severity} Priority ({len(issues)} issues)")
        print("-" * 60)

        for issue in sorted(issues, key=lambda x: x['file']):
            print(f"  {issue['file']}")
            print(f"    - {issue['message']}")
            print()

    # Summary
    print(f"\n{'='*60}")
    print(f"RECOMMENDED ACTIONS")
    print(f"{'='*60}\n")

    if results['HIGH']:
        print(f"1. Fix {len(results['HIGH'])} HIGH priority issues first")
        print(f"   - Replace old Semantic UI classes with new design system")

    if results['MEDIUM']:
        print(f"2. Add card wrappers to {len(results['MEDIUM'])} pages")
        print(f"   - Use layout.simple_card() or layout.page_container() macros")

    if results['LOW']:
        print(f"3. Clean up {len(results['LOW'])} low priority issues")
        print(f"   - Replace inline styles with Tailwind classes")
        print(f"   - Update gray-X00 to slate-X00")

    print(f"\nSee SYSTEMATIC_FIX_GUIDE.md for detailed instructions.\n")

if __name__ == '__main__':
    print("Starting template audit...")
    results = audit_templates()
    print_results(results)
