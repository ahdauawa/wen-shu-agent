"""Convert the pinned Apache-2.0 Zulip MDX snapshot to standalone Markdown.

Only this snapshot's components are supported. Never execute upstream MDX/JS.
Unknown content components cause a hard failure rather than silent text loss.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "knowledge" / "zulip"
UPSTREAM = ROOT / "upstream"


def navigation(target: str) -> str:
    parts = target.split("/")
    if parts[0] == "settings":
        source = (UPSTREAM / "starlight_help/src/components/SettingsSteps.astro").read_text(encoding="utf-8")
        pattern = rf'(?:"{re.escape(parts[1])}"|\b{re.escape(parts[1])}):\s*\{{\s*setting_type:\s*(\w+),\s*setting_name:\s*"([^"]+)"'
        match = re.search(pattern, source)
        if not match:
            raise ValueError(f"Unknown settings navigation: {target}")
        menu = "Organization settings" if match[1].startswith("ORGANIZATION") else "Personal settings"
        return f"\n1. Click the gear icon in the upper right of the web or desktop app.\n1. Select **{menu}**.\n1. On the left, click **{match[2]}**.\n"
    source = (UPSTREAM / "starlight_help/src/components/RelativeSteps.astro").read_text(encoding="utf-8")
    match = re.search(rf'(?:"{re.escape(parts[2])}"|\b{re.escape(parts[2])}):\s*\{{\s*label:\s*"([^"]+)"', source)
    if not match:
        raise ValueError(f"Unknown relative navigation: {target}")
    menu = "help menu" if parts[1] == "help" else "gear"
    via = "\n1. Select **Channel settings**." if parts[1] == "channel" else ""
    return f"\n1. Click the **{menu}** icon in the upper right of the app.{via}\n1. Select **{match[1]}**.\n"


def expand(path: Path, stack=()) -> str:
    path = path.resolve()
    if path in stack or not path.is_relative_to(UPSTREAM.resolve()):
        raise ValueError("Cyclic or external document include")
    text = path.read_text(encoding="utf-8")
    for alias, relative in re.findall(r'import\s+(\w+)\s+from\s+"([^"]+\.mdx)";', text):
        included = expand(path.parent / relative, (*stack, path))
        text = re.sub(rf"<{alias}\s*/>", lambda _: included, text)
    text = re.sub(r'^import\s+.*?;\s*$', '', text, flags=re.M)
    text = re.sub(r'<NavigationSteps\s+target="([^"]+)"\s*/>', lambda m: navigation(m[1]), text)
    text = re.sub(r'<TabItem\s+label="([^"]+)"[^>]*>', lambda m: "\n**Platform: " + m[1] + "**\n", text)
    text = re.sub(r'<\w*Icon\b[^>]*/>', '', text)
    text = re.sub(r'</?(?:FlattenedSteps|FlattenedList|Steps|Tabs|TabItem|ZulipNote|ZulipTip|KeyboardTip)\b[^>]*>', '', text)
    if re.search(r'<[A-Z][A-Za-z]+\b', text):
        raise ValueError(f"Unexpanded MDX component in {path.name}: " + str(re.findall(r'<[A-Z][^>]+>', text)))
    text = re.sub(r'\{\/\*.*?\*\/\}', '', text, flags=re.S)
    text = re.sub(r'\n[ \t]+', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip() + "\n"


def main():
    lock = json.loads((ROOT / "upstream-lock.json").read_text(encoding="utf-8"))
    for row in lock["files"]:
        path = UPSTREAM / row["path"]
        raw = path.read_bytes().replace(b"\r\n", b"\n")
        # Text transport can append one newline; verify original Git blob hashes.
        if hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != row["git_blob_sha"]:
            raw = raw[:-1]
        if hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != row["git_blob_sha"]:
            raise ValueError(f"Upstream source hash mismatch: {path}")
        path.write_bytes(raw)
    output = ROOT / "documents"
    output.mkdir(exist_ok=True)
    documents = []
    for upstream_path in lock["documents"]:
        original = (UPSTREAM / upstream_path).read_text(encoding="utf-8")
        title = re.search(r'^title:\s*(.+)$', original, re.M)[1].strip('"')
        rendered = expand(UPSTREAM / upstream_path)
        rendered = re.sub(r'^---\n.*?\n---\n', '', rendered, flags=re.S)
        rendered = re.split(r'^## Related articles\s*$', rendered, flags=re.M)[0]
        notice = "<!-- WenShu conversion: MDX includes expanded; UI components rendered as text; related links omitted. See ../README.md. -->"
        body = f"# {title}\n\n{notice}\n\n" + rendered.strip() + "\n"
        slug = Path(upstream_path).stem
        relative = f"documents/{slug}.md"
        (ROOT / relative).write_text(body, encoding="utf-8")
        documents.append({"id": "zulip-" + slug, "title": title, "path": relative,
            "url": f"https://zulip.com/help/{slug}",
            "upstream_url": f"https://github.com/zulip/zulip/blob/{lock['revision']}/{upstream_path}",
            "revision": lock["revision"], "license": "Apache-2.0", "sha256": hashlib.sha256(body.encode()).hexdigest()})
    (ROOT / "manifest.json").write_text(json.dumps({"documents": documents}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Converted {len(documents)} official documents; includes are not counted as documents.")


if __name__ == "__main__":
    main()
