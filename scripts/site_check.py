"""Validate generated routes and basic HTML accessibility without dependencies."""

import argparse
import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


def collect_html_routes(public_dir: Path) -> set[str]:
    return {'/' if path.relative_to(public_dir).as_posix() == 'index.html'
            else '/' + path.relative_to(public_dir).as_posix()
            for path in public_dir.rglob('*.html')}


def validate_expected_routes(actual: set[str], expected_file: Path) -> list[str]:
    expected = {line.strip() for line in expected_file.read_text(encoding='utf-8').splitlines()
                if line.strip() and not line.lstrip().startswith('#')}
    return [f'Missing route: {route}' for route in sorted(expected - actual)]


class _Document(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = {'tag': '', 'attrs': {}, 'children': []}
        self.stack = [self.root]
        self.nodes = []

    def handle_starttag(self, tag, attrs):
        node = {'tag': tag, 'attrs': dict(attrs), 'children': []}
        self.stack[-1]['children'].append(node)
        self.nodes.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index]['tag'] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1]['children'].append(data)


def _accessible_text(node):
    attrs = node['attrs']
    if attrs.get('aria-hidden', '').lower() == 'true' or 'hidden' in attrs:
        return ''
    if node['tag'] in {'script', 'style', 'template'}:
        return ''
    if attrs.get('aria-label', '').strip():
        return attrs['aria-label']
    if node['tag'] == 'img':
        return attrs.get('alt') or ''
    return ' '.join(child if isinstance(child, str) else _accessible_text(child)
                    for child in node['children'])


def validate_html_document(path: Path) -> list[str]:
    document = _Document()
    document.feed(path.read_text(encoding='utf-8'))
    errors = []
    h1_count = sum(node['tag'] == 'h1' for node in document.nodes)
    if h1_count != 1:
        errors.append(f'Expected exactly one H1; found {h1_count}')
    if not any(node['tag'] == 'main' for node in document.nodes):
        errors.append('Missing main landmark')
    ids = {node['attrs']['id']: node for node in document.nodes if node['attrs'].get('id')}
    for node in document.nodes:
        attrs = node['attrs']
        if node['tag'] == 'img':
            alt = attrs.get('alt')
            decorative = alt == '' and attrs.get('aria-hidden', '').lower() == 'true'
            if not decorative and not (alt or '').strip():
                errors.append(f"Image missing useful alt text: {attrs.get('src', '(no src)')}")
        if node['tag'] == 'a' and 'href' in attrs:
            name = _accessible_text(node)
            if attrs.get('aria-labelledby'):
                name = ' '.join(_accessible_text(ids[label]) for label in
                                attrs['aria-labelledby'].split() if label in ids)
            if not name.strip():
                errors.append(f"Link missing accessible text: {attrs['href']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public', type=Path, required=True)
    parser.add_argument('--expected', type=Path, required=True)
    parser.add_argument('--allowlist', type=Path,
                        help='Temporary JSON list of exact legacy HTML findings; remove in Task 2')
    args = parser.parse_args()
    try:
        errors = validate_expected_routes(collect_html_routes(args.public), args.expected)
        findings = []
        for path in sorted(args.public.rglob('*.html')):
            relative = path.relative_to(args.public).as_posix()
            route = '/' if relative == 'index.html' else '/' + relative
            findings.extend(f'{route}: {error}' for error in validate_html_document(path))
        entries = json.loads(args.allowlist.read_text(encoding='utf-8')) if args.allowlist else []
        if not isinstance(entries, list) or not all(isinstance(entry, str) for entry in entries):
            raise ValueError('Allowlist must be a JSON list of strings')
        allowed = Counter(entries)
        errors.extend((Counter(findings) - allowed).elements())
        errors.extend(f'Stale allowlist finding: {finding}'
                      for finding in (allowed - Counter(findings)).elements())
    except (OSError, ValueError) as error:
        errors = [str(error)]
    for error in errors:
        print(error)
    if not errors:
        print('Site checks passed' + (f' ({sum(allowed.values())} temporary legacy findings allowed)'
                                    if allowed else ''))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
