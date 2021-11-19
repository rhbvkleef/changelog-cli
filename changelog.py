import os
from typing import Iterator, Callable

import semver

subcommand_handlers = {}


def register_subcommand(name=None, aliases=[]):
    aliases = set(aliases)
    def decorate(func: Callable[[object], None]):
        if name is None and hasattr(func, "__name__"):
            aliases.add(func.__name__)
        elif name is not None:
            aliases.add(name)

        for alias in aliases:
            subcommand_handlers[alias] = func
        return func
    return decorate


def get_previous_version(releases_dir: str):
    with os.scandir(releases_dir) as releases:
        releases: Iterator[os.DirEntry] = filter(lambda r: r.is_dir(), releases)
        min_release = None
        for release in releases:
            current = semver.VersionInfo.parse(release.name)
            if min_release is None or semver.compare(current, min_release) > 0:
                min_release = current
        return min_release


@register_subcommand(aliases=["rel"])
def release(args):
    previous_versions = args.previous_versions
    if previous_versions is None:
        previous_version = get_previous_version(args.releases_directory)
        if previous_version is None:
            previous_versions = []
        else:
            previous_versions = [previous_version]
    
    print(f"Running release {args.version} linking to previous versions {previous_versions}.")


@register_subcommand(aliases=["gen"])
def generate(args):
    print(f"Generating a changelog using the {args.format} format")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="changelogtool", description="Changelog management tool")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1")
    parser.add_argument("--releases-directory", type=str, default="changelog/releases", help="The directory where the release DAG file and the changelog directories are stored (default: %(default)s)")
    parser.add_argument("--accumulation-directory", type=str, default="changelog/new", help="The directory where new changelog entries are stored (default: %(default)s)")

    subparsers = parser.add_subparsers(title="Commands", dest="command")

    release = subparsers.add_parser("release", aliases=["rel"], help="Create and fill a changelog category for a release", description="Create and fill a changelog category for a release")
    release.add_argument("--previous-versions", nargs="*", type=str, help="The previous version to the current, defaults to just the newest version, or an empty list when there are no previous versions")
    release.add_argument("version", help="The newly released version number")

    generate = subparsers.add_parser("generate", aliases=["gen"], help="Generate a changelog file", description="Generate a changelog file")
    generate.add_argument("format", nargs="?", help="The required output format (default: %(default)s)", default="json")
    
    parsed = parser.parse_args()

    subcommand_handlers[parsed.command](parsed)
