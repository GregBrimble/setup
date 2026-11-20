#!/usr/bin/env python3
"""Download the latest ZIPs from your Tailwind Plus purchases."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import parse_qsl, unquote, urlencode, urljoin, urlsplit, urlunsplit
import zipfile

BASE = "https://tailwindcss.com"
ROOT = Path.home() / ".local/share/tailwind-plus"
CREDENTIALS = Path.home() / ".local/share/private-assets/secrets/tailwind-plus.json"
PRODUCT = re.compile(r"/plus/(?:templates/[^/]+|ui-kit|ui-blocks/(?:marketing|application-ui|ecommerce))/?$")


class Error(Exception):
    pass


class Page(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.page = {}
        self.links = []
        self.feed(body.decode("utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id") == "app":
            self.page = json.loads(attrs.get("data-page", "{}"))
        if tag == "a" and attrs.get("href"):
            self.links.append(urljoin(BASE, attrs["href"]))


def curl_quote(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r") + '"'


class Client:
    def __init__(self):
        self.cookies = ROOT / "cookies.txt"

    def request(self, url, destination, data=None, headers=()):
        # Pass URLs, headers, and credentials through stdin, never process arguments.
        config = ["url = " + curl_quote(url)]
        config += ["header = " + curl_quote(h) for h in headers]
        if data is not None:
            config.append("data-binary = " + curl_quote(json.dumps(data)))
        args = ["/usr/bin/curl", "--http1.1", "--silent", "--show-error",
                "--fail", "--location", "--max-redirs", "5", "--proto", "=https",
                "--proto-redir", "=https", "--connect-timeout", "30", "--max-time", "600",
                "--user-agent", "Mozilla/5.0", "--cookie", str(self.cookies),
                "--cookie-jar", str(self.cookies), "--output", str(destination),
                "--write-out", "%{http_code}", "--config", "-"]
        if data is None:
            args += ["--retry", "2"]
        result = subprocess.run(args, input="\n".join(config).encode(),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if self.cookies.exists():
            self.cookies.chmod(0o600)
        if result.returncode:
            status = result.stdout.decode().strip()
            raise Error("Request failed (HTTP {}; curl {}).".format(status, result.returncode))

    def page(self, path):
        with tempfile.TemporaryDirectory(prefix=".page-", dir=ROOT) as temp:
            destination = Path(temp) / "response"
            self.request(urljoin(BASE, path), destination)
            return Page(destination.read_bytes())

    def purchases(self):
        page = self.page("/plus/purchases")
        if page.page.get("component") == "Login":
            if not CREDENTIALS.is_file():
                raise Error("Tailwind credentials are missing from the private assets: " + str(CREDENTIALS))
            credentials = json.loads(CREDENTIALS.read_text())
            if not isinstance(credentials, dict) or any(
                    not isinstance(credentials.get(key), str) or not credentials[key].strip()
                    for key in ("email", "password")):
                raise Error("Private Tailwind credentials must contain non-empty email and password strings.")
            token = None
            for line in self.cookies.read_text().splitlines():
                fields = line.split("\t")
                if len(fields) == 7 and fields[5] == "XSRF-TOKEN":
                    token = unquote(fields[6])
            if not token:
                raise Error("Login page did not supply a CSRF token.")
            with tempfile.TemporaryDirectory(prefix=".login-", dir=ROOT) as temp:
                self.request(BASE + "/plus/login", Path(temp) / "response",
                             {"email": credentials["email"], "password": credentials["password"], "remember": True},
                             ["Content-Type: application/json", "Accept: text/html",
                              "Referer: " + BASE + "/plus/login", "X-XSRF-TOKEN: " + token])
            page = self.page("/plus/purchases")
        if page.page.get("component") != "Purchases":
            raise Error("Could not access purchases; login may require attention in your browser.")
        return page


def safe_slug(value):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value):
        raise Error("Product page contains an unsupported product or variant name.")
    return value


def discover(purchases):
    products = {}
    for url in purchases.links:
        parts = urlsplit(url)
        if parts.netloc != "tailwindcss.com" or not PRODUCT.fullmatch(parts.path):
            continue
        path = parts.path.rstrip("/")
        slug = safe_slug(path.split("/")[-1])
        if slug == "ui-kit":
            group, slug = "ui-kit", "catalyst"
        else:
            group = "ui-blocks" if "/ui-blocks/" in path else "templates"
        products[slug] = {"page": url, "group": group}
    if not products:
        raise Error("No product pages found in purchases; the site may have changed.")
    return products


def download_options(client, page_url):
    page = client.page(page_url)
    if page.page.get("component") == "Login":
        raise Error("Session expired; run the task again to sign in.")
    product = page.page.get("props", {}).get("product", {})
    if product.get("downloadable") is False:
        raise Error("This product is not downloadable with the current account.")
    links = {url for url in page.links if urlsplit(url).netloc == "tailwindcss.com"
             and "/download" in urlsplit(url).path}
    if product.get("download_url"):
        links.add(urljoin(BASE, product["download_url"]))
    if len(links) != 1:
        raise Error("Expected one ZIP download endpoint; found {}.".format(len(links)))
    url = links.pop()
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc != "tailwindcss.com":
        raise Error("Product page contains an unexpected download host.")
    themes = product.get("themes", [])
    if not themes:
        return {"default": url}
    options = {}
    for theme in themes:
        slug = safe_slug(theme["slug"])
        query = [(key, value) for key, value in parse_qsl(parts.query) if key != "theme"]
        query.append(("theme", slug))
        options[slug] = urlunsplit(parts._replace(query=urlencode(query)))
    return options


def extract(archive, destination):
    destination.mkdir()
    with zipfile.ZipFile(archive) as zipped:
        for entry in zipped.infolist():
            path = PurePosixPath(entry.filename)
            kind = stat.S_IFMT(entry.external_attr >> 16)
            if (path.is_absolute() or ".." in path.parts or "\\" in entry.filename
                    or kind not in (0, stat.S_IFREG, stat.S_IFDIR)):
                raise Error("ZIP contains an unsafe path or unsupported file type.")
            # Vendor ZIPs contain empty .git placeholders; don't create nested repos.
            if ".git" in path.parts or "__MACOSX" in path.parts:
                continue
            zipped.extract(entry, destination)
    if not any(destination.iterdir()):
        raise Error("Downloaded ZIP is empty.")
    children = list(destination.iterdir())
    if len(children) == 1 and children[0].is_dir():
        wrapper = children[0]
        # Move through a sibling so a nested directory can have the wrapper's name.
        unwrapped = destination.with_name(destination.name + ".unwrapped")
        wrapper.rename(unwrapped)
        destination.rmdir()
        unwrapped.rename(destination)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def publish(replacements, staging):
    # Publish only after every requested download validates; roll back on failure.
    moved = []
    try:
        for index, (source, destination) in enumerate(replacements):
            destination.parent.mkdir(parents=True, exist_ok=True)
            backup = staging / ("backup-" + str(index))
            existed = destination.exists()
            if existed:
                destination.rename(backup)
            moved.append((destination, backup if existed else None))
            if source is not None:
                source.rename(destination)
    except BaseException:
        for destination, backup in reversed(moved):
            if destination.is_dir():
                shutil.rmtree(destination)
            elif destination.exists():
                destination.unlink()
            if backup:
                backup.rename(destination)
        raise


def update(client, products):
    manifest_path = ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"products": {}}
    manifest["version"] = 2
    count = 0
    with tempfile.TemporaryDirectory(prefix=".update-", dir=ROOT) as temp:
        staging = Path(temp)
        replacements = []
        for slug, product in products.items():
            relative = Path(product["group"]) / slug
            options = download_options(client, product["page"])
            old_variants = manifest["products"].get(slug, {}).get("variants", {})
            variants = {}
            product_stage = staging / "extracted" / relative
            product_archive_stage = staging / "archives" / relative
            product_archive_stage.mkdir(parents=True)
            for variant, url in options.items():
                label = slug if variant == "default" else slug + "/" + variant
                print("Tailwind Plus: downloading {}...".format(label), flush=True)
                archive = product_archive_stage / (variant + ".zip")
                client.request(url, archive)
                digest = sha256(archive)
                target_archive = ROOT / ".archives" / relative / archive.name
                target_components = ROOT / relative
                components = product_stage
                if variant != "default":
                    target_components /= variant
                    components /= variant
                previous = old_variants.get(variant, {})
                components.parent.mkdir(parents=True, exist_ok=True)
                if (previous.get("sha256") == digest and target_archive.is_file()
                        and sha256(target_archive) == digest and target_components.is_dir()):
                    # Preserve the existing extraction when the upstream ZIP hasn't changed.
                    shutil.copytree(target_components, components)
                    print("Tailwind Plus: {} unchanged.".format(label))
                else:
                    extract(archive, components)
                variants[variant] = {"sha256": digest}
                count += 1
            replacements.extend([(product_stage, ROOT / relative),
                                 (product_archive_stage, ROOT / ".archives" / relative)])
            manifest["products"][slug] = {
                "page": product["page"], "path": relative.as_posix(), "variants": variants,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
        staged_manifest = staging / "manifest.json"
        staged_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
        # Remove the original layout only after the full library validates.
        replacements.extend((None, ROOT / name) for name in ("archives", "components")
                            if (ROOT / name).exists())
        replacements.append((staged_manifest, manifest_path))
        publish(replacements, staging)
    print("Tailwind Plus: {} ZIPs ready at {}.".format(count, ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    os.umask(0o077)
    ROOT.mkdir(parents=True, exist_ok=True)
    ROOT.chmod(0o700)
    with (ROOT / ".lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Error("Another Tailwind Plus update is running.")
        client = Client()
        update(client, discover(client.purchases()))


if __name__ == "__main__":
    try:
        main()
    except (Error, OSError, ValueError, zipfile.BadZipFile) as error:
        print("Tailwind Plus: " + str(error), file=sys.stderr)
        sys.exit(1)
