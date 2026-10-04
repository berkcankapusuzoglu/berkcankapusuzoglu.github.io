"""Inspect private nested Overleaf ZIPs and extract one explicitly named asset."""

import argparse
from dataclasses import asdict, dataclass
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile


STATIC_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.svg', '.eps', '.ps', '.webp', '.tif', '.tiff'}
MOTION_EXTENSIONS = {'.gif', '.mp4', '.webm'}


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
    args = parser.parse_args()
    try:
        checksum = archive_sha256(args.archive)
        if args.command == 'inventory':
            projects = inventory_archive(args.archive)
            result = {'archive_sha256': checksum, 'project_count': len(projects),
                      'figure_count': sum(p.figure_count for p in projects),
                      'motion_count': sum(p.motion_count for p in projects),
                      'projects': [asdict(project) for project in projects]}
        else:
            output = select_entry(args.archive, args.project, args.entry, args.output)
            result = {'archive_sha256': checksum, 'project': args.project,
                      'entry': args.entry, 'output': str(output), 'sha256': archive_sha256(output)}
    except (OSError, KeyError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f'{error}\n')
    # JSON is a YAML 1.2 subset: standard-library-only and deterministic quoting.
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == '__main__':
    main()
