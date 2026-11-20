#!/usr/bin/python3
"""Restore the managed Rex theme without replacing other custom themes."""
import json
from pathlib import Path
import plistlib
import subprocess

DOMAIN = 'com.superlogical.rex'
THEMES_KEY = 'Workspace.customThemes'
SELECTION_KEY = 'Workspace.darkThemeID'
SOURCE = Path(__file__).resolve().parents[1] / 'themes/usgc/rex.json'


def merge_theme(themes, managed):
    result = [managed if theme['id'] == managed['id'] else theme for theme in themes]
    if not any(theme['id'] == managed['id'] for theme in themes):
        result.append(managed)
    return result


def main():
    managed = json.loads(SOURCE.read_text())
    preferences = plistlib.loads(subprocess.check_output(['/usr/bin/defaults', 'export', DOMAIN, '-']))
    themes = json.loads(preferences.get(THEMES_KEY, b'[]'))
    merged = merge_theme(themes, managed)
    if merged != themes:
        data = json.dumps(merged, separators=(',', ':')).encode().hex()
        subprocess.run(['/usr/bin/defaults', 'write', DOMAIN, THEMES_KEY, '-data', data], check=True)
    if preferences.get(SELECTION_KEY) != managed['id']:
        subprocess.run(['/usr/bin/defaults', 'write', DOMAIN, SELECTION_KEY,
                        '-string', managed['id']], check=True)
    print('Rex: USGC RETICLE theme ready.')


if __name__ == '__main__':
    main()
