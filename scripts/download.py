import os
import requests
import hashlib
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, urlsplit, urlunsplit
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
BASE_URL = os.getenv("BASE_URL")
TARGET_URL = os.getenv("TARGET_URL")
ASSET_DIR_NAME = "assets"

assets_dir = os.path.join(BASE_DIR, ASSET_DIR_NAME)
output_dir = os.path.join(BASE_DIR, "original")


def download_page(url):

    os.makedirs(assets_dir, exist_ok=True)

    response = requests.get(url)
    # Detect the encoding of the response
    if response.encoding is None:
        response.encoding = response.apparent_encoding

    # Convert content to UTF-8
    content = response.text.encode("utf-8", errors="ignore").decode("utf-8")

    soup = BeautifulSoup(content, "html.parser")

    # Remove the tag with id="i18nWebflowScript"
    i18n_script = soup.find(id="i18nWebflowScript")
    if i18n_script:
        i18n_script.decompose()

    for tag in soup.find_all():
        if "integrity" in tag.attrs:
            del tag["integrity"]
        if "crossorigin" in tag.attrs:
            del tag["crossorigin"]

        # Handle style attribute with background-image
        if tag.has_attr("style"):
            tag["style"] = process_style_attribute(tag["style"], url, assets_dir)

        for attr, value in tag.attrs.items():
            if attr.lower().endswith("url"):
                new_value = download_and_replace_asset(value, url, assets_dir)
                tag[attr] = new_value
            elif attr.lower().endswith("urls"):
                new_values = []
                for asset_url in value.split(","):
                    new_value = download_and_replace_asset(
                        asset_url.strip(), url, assets_dir
                    )
                    new_values.append(new_value)
                tag[attr] = ", ".join(new_values)

        # Handle common attributes separately for better performance
        if tag.name in ["img", "script", "source"] and tag.has_attr("src"):
            new_src = download_and_replace_asset(tag["src"], url, assets_dir)
            tag["src"] = new_src
        elif tag.name == "link" and tag.has_attr("href"):
            new_href = download_and_replace_asset(tag["href"], url, assets_dir)
            tag["href"] = new_href

    with open(os.path.join(output_dir, "index.html"), "w", encoding="iso-8859-1") as f:
        f.write(str(soup))


def process_style_attribute(style, base_url, assets_dir):
    def replace_url(match):
        url = match.group(1)
        if url.startswith(("http://", "https://", "//")):
            new_url = download_and_replace_asset(url, base_url, assets_dir)
            return f'url("{new_url}")'
        return match.group(0)

    return re.sub(r"url\(\"(.*?)\"\)", replace_url, style)


def download_and_replace_asset(asset_url, base_url, assets_dir):
    if not asset_url or asset_url.startswith("data:"):
        return asset_url

    asset_url = unquote(asset_url)
    full_url = urljoin(base_url, asset_url)

    # Parse the URL
    parsed_url = urlsplit(full_url)

    # Extract the path without query parameters
    path = parsed_url.path

    url_hash = hashlib.md5(path.encode()).hexdigest()[:10]
    original_extension = os.path.splitext(path)[1]
    if not original_extension:
        original_extension = ".bin"
    new_filename = f"{url_hash}{original_extension}"

    full_local_path = os.path.join(assets_dir, new_filename)

    if not os.path.exists(full_local_path):
        response = requests.get(full_url)
        if response.status_code == 200:
            with open(full_local_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded: {new_filename} (Original: {os.path.basename(path)})")
        else:
            print(f"Failed to download: {full_url}")
            return asset_url

    # Reconstruct the URL with the local path and original query parameters
    local_path = os.path.join(ASSET_DIR_NAME, new_filename)
    new_url = urlunsplit(("", "", local_path, parsed_url.query, ""))
    return f"{BASE_URL}/{new_url}"


download_page(TARGET_URL)
