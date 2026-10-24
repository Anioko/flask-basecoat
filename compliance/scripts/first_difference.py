"""Print where each changed file first differs from its committed version (for single-line HTML renders, where a
plain diff shows only the whole line). Usage: python compliance/scripts/first_difference.py <path> [<path> ...]"""
import subprocess
import sys

for path in subprocess.run(['git', 'diff', '--name-only', '--', *sys.argv[1:]], capture_output=True, text=True).stdout.split():
    old = subprocess.run(['git', 'show', f'HEAD:{path}'], capture_output=True, text=True, encoding='utf8').stdout
    new = open(path, encoding='utf8').read()
    i = next((k for k in range(min(len(old), len(new))) if old[k] != new[k]), min(len(old), len(new)))
    print(f'{path}: first difference at character {i}')
    print(f'  committed: ...{old[max(0, i - 160):i + 160]}...')
    print(f'  rendered:  ...{new[max(0, i - 160):i + 160]}...')
