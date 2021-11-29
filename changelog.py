import json
import logging
import os
import shutil
from typing import Iterator, Callable

import semver

logger = logging.getLogger(__name__)


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
    
    logger.info(f"Running release {args.version} linking to previous versions {previous_versions}.")

    os.mkdir(os.path.join(args.releases_directory, args.version))
    for f in os.listdir(args.accumulation_directory):
        if f.endswith(".yml") or f.endswith(".yaml"):
            shutil.move(os.path.join(args.accumulation_directory, f), os.path.join(args.releases_directory, args.version, f))
    
    with open(os.path.join(args.releases_directory, args.version, "manifest.json"), "w") as f:
        json.dump({
            "previous_versions": previous_versions
        }, f)


@register_subcommand(aliases=["gen"])
def generate(args):
    version = None
    if args.version:
        version = args.version
    else:
        version = get_previous_version(args.releases_directory)

    logger.info(f"Generating a changelog using the {args.format} format for version {version}")

    # TODO: Build a tree of versions
    # TODO: For each version, order the feature files by date last changed on git
    # TODO: Create an ordered list of features and releases
    # TODO: Deduplicate this list
    # TODO: Write this list out to "somewhere".


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="changelogtool", description="Changelog management tool")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1")
    parser.add_argument("--releases-directory", type=str, default=os.path.join("changelog", "releases"), help="The directory where the release DAG file and the changelog directories are stored (default: %(default)s)")
    parser.add_argument("--accumulation-directory", type=str, default=os.path.join("changelog", "new"), help="The directory where new changelog entries are stored (default: %(default)s)")
    parser.add_argument("--log-level", type=str, default="INFO", help="Set the logging level (default: %(default)s)")

    subparsers = parser.add_subparsers(title="Commands", dest="command")

    release = subparsers.add_parser("release", aliases=["rel"], help="Create and fill a changelog category for a release", description="Create and fill a changelog category for a release")
    release.add_argument("--previous-versions", nargs="*", type=str, help="The previous version to the current, defaults to just the newest version, or an empty list when there are no previous versions")
    release.add_argument("version", help="The newly released version number")

    generate = subparsers.add_parser("generate", aliases=["gen"], help="Generate a changelog file", description="Generate a changelog file")
    generate.add_argument("version", nargs="?", help="The version to generate a changelog for (default: latest)")
    generate.add_argument("format", nargs="?", help="The required output format (default: %(default)s)", default="json")
    
    parsed = parser.parse_args()

    logging.basicConfig(level=parsed.log_level)

    subcommand_handlers[parsed.command](parsed)
