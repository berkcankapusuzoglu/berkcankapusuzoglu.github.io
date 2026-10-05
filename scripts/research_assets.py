"""Inspect private nested Overleaf ZIPs and extract one explicitly named asset."""

import argparse
from dataclasses import asdict, dataclass
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
import zipfile


STATIC_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.svg', '.eps', '.ps', '.webp', '.tif', '.tiff'}
MOTION_EXTENSIONS = {'.gif', '.mp4', '.webm'}
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class FigureRecord:
    path: str
    extension: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ProjectRecord:
    name: str
    figures: list[FigureRecord]
    figure_count: int
    motion_count: int


def _safe_path(name: str) -> str:
    # ZIP paths use POSIX separators; also reject Windows traversal/drive names.
    path = PurePosixPath(name.replace('\\', '/'))
    if path.is_absolute() or '..' in path.parts or not path.parts or ':' in path.parts[0]:
        raise ValueError(f'Unsafe archive path: {name!r}')
    return str(path)


def archive_sha256(archive: Path) -> str:
    with Path(archive).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def inventory_archive(archive: Path) -> list[ProjectRecord]:
    """Return sorted metadata; nested projects are read in memory, never unpacked."""
    projects = []
    with zipfile.ZipFile(archive) as outer:
        for project in sorted(outer.infolist(), key=lambda item: item.filename):
            name = _safe_path(project.filename)
            if project.is_dir() or PurePosixPath(name).suffix.lower() != '.zip':
                continue
            figures = []
            motion_count = 0
            with zipfile.ZipFile(io.BytesIO(outer.read(project))) as inner:
                for entry in inner.infolist():
                    path = _safe_path(entry.filename)
                    if entry.is_dir():
                        continue
                    extension = PurePosixPath(path).suffix.lower()
                    if extension in MOTION_EXTENSIONS:
                        motion_count += 1
                    elif extension in STATIC_EXTENSIONS:
                        figures.append(FigureRecord(path, extension, entry.file_size,
                                                    hashlib.sha256(inner.read(entry)).hexdigest()))
            figures.sort(key=lambda item: item.path)
            projects.append(ProjectRecord(name, figures, len(figures), motion_count))
    return projects


def select_entry(archive: Path, project_name: str, entry_name: str,
                 destination: Path) -> Path:
    """Extract exactly one entry to the caller's explicit destination."""
    project_name = _safe_path(project_name)
    entry_name = _safe_path(entry_name)
    with zipfile.ZipFile(archive) as outer:
        with zipfile.ZipFile(io.BytesIO(outer.read(project_name))) as inner:
            entry = inner.getinfo(entry_name)
            if entry.is_dir():
                raise ValueError(f'Selected entry is a directory: {entry_name!r}')
            payload = inner.read(entry)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return destination


def prepare_figure(archive: Path, project_name: str, entry_name: str,
                   output: Path, dpi: int = 180, replace: bool = False,
                   page: int = 1) -> dict:
    """Render one selected PDF page; publish only a validated PNG derivative."""
    output = Path(output).resolve()
    publications = (REPOSITORY_ROOT / 'content/publications').resolve()
    if not output.is_relative_to(publications) or output.suffix.lower() != '.png':
        raise ValueError('Output must be a PNG inside content/publications/')
    if not 72 <= dpi <= 600:
        raise ValueError('DPI must be between 72 and 600')
    if page < 1:
        raise ValueError('Page must be a positive integer')
    if PurePosixPath(_safe_path(entry_name)).suffix.lower() != '.pdf':
        raise ValueError('Preparation requires a PDF source')
    if output.exists() and not replace:
        raise FileExistsError(f'Output already exists; use --replace: {output}')
    poppler = shutil.which('pdftoppm')
    if poppler is None:
        raise FileNotFoundError('pdftoppm is required; add Poppler to PATH')
    # Inventory and extraction remain standard-library-only.
    from PIL import Image

    with tempfile.TemporaryDirectory(prefix='research-figure-') as temporary:
        work = Path(temporary)
        source = select_entry(archive, project_name, entry_name, work / 'source.pdf')
        source_checksum = archive_sha256(source)
        prefix = work / 'render'
        command = [poppler, '-singlefile', '-png', '-r', str(dpi),
                   '-f', str(page), '-l', str(page), str(source), str(prefix)]
        subprocess.run(command, check=True, capture_output=True, text=True)
        rendered = prefix.with_suffix('.png')
        if not rendered.is_file():
            raise FileNotFoundError('Poppler did not create the selected page PNG')
        with Image.open(rendered) as image:
            image.load()
            width, height = image.size
            if image.format != 'PNG' or width < 1 or height < 1:
                raise ValueError('Poppler output must be a nonempty PNG')
        result = {'project': project_name, 'entry': entry_name,
                  'output': str(output), 'source_sha256': source_checksum,
                  'source_page': page, 'dpi': dpi, 'width': width, 'height': height,
                  'size_bytes': rendered.stat().st_size, 'sha256': archive_sha256(rendered)}
        output.parent.mkdir(parents=True, exist_ok=True)
        # Stage in the publication directory so the PNG inherits public file ACLs,
        # rather than retaining the private temporary-directory ACL on Windows.
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix='.png', delete=False) as staging:
            staged = Path(staging.name)
        try:
            shutil.copyfile(rendered, staged)
            if replace:
                staged.replace(output)
            else:
                # Creating a hard link atomically fails if another writer won.
                os.link(staged, output)
        finally:
            staged.unlink(missing_ok=True)
    return result


def prepare_sequence(source: Path, recipe: Path, output_dir: Path) -> dict:
    """Copy one exact PNG; return ordered DOM overlay metadata, never painted frames.

    Recipes use JSON syntax, the deterministic YAML 1.2 subset used by this CLI.
    Focus coordinates are percentages of the complete image (no cropping).
    """
    data = json.loads(Path(recipe).read_text(encoding='utf-8'))
    frames = data.get('sequence') if isinstance(data, dict) else None
    if not isinstance(frames, list) or len(frames) < 2:
        raise ValueError('Sequence requires at least two ordered frames')
    name = data.get('file', '')
    if (not isinstance(name, str) or '/' in name or '\\' in name or ':' in name
            or PurePosixPath(name).name != name or not name.endswith('.png')):
        raise ValueError('Sequence file must be a simple PNG filename')
    sequence = []
    for frame in frames:
        if not isinstance(frame, dict):
            raise ValueError('Each frame must be an object')
        label = frame.get('label')
        duration = frame.get('duration')
        if not isinstance(label, str) or not label.strip():
            raise ValueError('Every frame needs a nonempty label')
        if type(duration) is not int or duration <= 0:
            raise ValueError('Every frame needs a positive integer duration in milliseconds')
        item = {'file': f'media/{name}', 'label': label, 'duration': duration}
        if 'focus' in frame:
            focus = frame['focus']
            if not isinstance(focus, dict) or set(focus) != {'x', 'y', 'width', 'height'}:
                raise ValueError('Focus needs x, y, width and height percentages')
            if any(type(value) not in (int, float) or not math.isfinite(value)
                   for value in focus.values()):
                raise ValueError('Focus coordinates must be finite numbers')
            if (focus['x'] < 0 or focus['y'] < 0 or focus['width'] <= 0 or focus['height'] <= 0
                    or focus['x'] + focus['width'] > 100 or focus['y'] + focus['height'] > 100):
                raise ValueError('Focus must stay within the complete image')
            item['focus'] = focus
        if 'callout' in frame:
            if not isinstance(frame['callout'], str) or not frame['callout'].strip():
                raise ValueError('Callout must be nonempty text')
            item['callout'] = frame['callout']
        sequence.append(item)
    output_dir = Path(output_dir).resolve()
    writing = (REPOSITORY_ROOT / 'content/writing').resolve()
    if not output_dir.is_relative_to(writing) or len(output_dir.relative_to(writing).parts) != 2 or output_dir.name != 'media':
        raise ValueError('Output must be content/writing/<note>/media/')
    output = output_dir / name
    if output.exists():
        raise FileExistsError(f'Output already exists: {output}')
    from PIL import Image
    with Image.open(source) as image:
        image.load()
        if image.format != 'PNG':
            raise ValueError('Sequence source must be PNG')
        width, height = image.size
    checksum = archive_sha256(source)
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output_dir, suffix='.png', delete=False) as staging:
        staged = Path(staging.name)
    try:
        shutil.copyfile(source, staged)
        if archive_sha256(staged) != checksum:
            raise ValueError('Source changed while copying; sequence was not published')
        os.link(staged, output)
    finally:
        staged.unlink(missing_ok=True)
    return {'file': f'media/{name}', 'width': width, 'height': height,
            'source_sha256': checksum, 'sha256': archive_sha256(output), 'sequence': sequence}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    inventory = commands.add_parser('inventory')
    inventory.add_argument('--archive', type=Path, required=True)
    extract = commands.add_parser('extract')
    extract.add_argument('--archive', type=Path, required=True)
    extract.add_argument('--project', required=True)
    extract.add_argument('--entry', required=True)
    extract.add_argument('--output', type=Path, required=True)
    prepare = commands.add_parser('prepare')
    prepare.add_argument('--archive', type=Path, required=True)
    prepare.add_argument('--project', required=True)
    prepare.add_argument('--entry', required=True)
    prepare.add_argument('--output', type=Path, required=True)
    prepare.add_argument('--dpi', type=int, default=180)
    prepare.add_argument('--page', type=int, default=1)
    prepare.add_argument('--replace', action='store_true')
    sequence = commands.add_parser('sequence', help='Copy exact pixels and validate DOM focus metadata')
    sequence.add_argument('--source', type=Path, required=True)
    sequence.add_argument('--recipe', type=Path, required=True, help='JSON syntax (YAML 1.2 subset)')
    sequence.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'sequence':
            result = prepare_sequence(args.source, args.recipe, args.output_dir)
        elif args.command == 'inventory':
            checksum = archive_sha256(args.archive)
            projects = inventory_archive(args.archive)
            result = {'archive_sha256': checksum, 'project_count': len(projects),
                      'figure_count': sum(p.figure_count for p in projects),
                      'motion_count': sum(p.motion_count for p in projects),
                      'projects': [asdict(project) for project in projects]}
        elif args.command == 'extract':
            checksum = archive_sha256(args.archive)
            output = select_entry(args.archive, args.project, args.entry, args.output)
            result = {'archive_sha256': checksum, 'project': args.project,
                      'entry': args.entry, 'output': str(output), 'sha256': archive_sha256(output)}
        else:
            result = {'archive_sha256': archive_sha256(args.archive), **prepare_figure(
                args.archive, args.project, args.entry, args.output,
                dpi=args.dpi, replace=args.replace, page=args.page)}
    except subprocess.CalledProcessError as error:
        parser.exit(1, f'Poppler failed: {error.stderr or error}\n')
    except (OSError, KeyError, ValueError, ImportError, zipfile.BadZipFile) as error:
        parser.exit(1, f'{error}\n')
    # JSON is a YAML 1.2 subset: standard-library-only and deterministic quoting.
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == '__main__':
    main()
