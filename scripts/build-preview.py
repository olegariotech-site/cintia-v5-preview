#!/usr/bin/env python3
"""Converts the pinned, approved V5 source into a *public test-only* Pages artifact.

Does not modify the official site or source repository.
No private files, production domain, analytics events, or live contact delivery.
"""
from pathlib import Path
import re
import shutil

SOURCE = Path("v5-source")
DEST = Path("_site")
EXPECTED_BASE = "694928d8ad20e2a7959169f10cdac413eba908a2"
FILES = (
    "index.html", "styles.css", "v4.css", "v5.css", "site.js",
    "whatsapp.svg", "assetslogo-cintia-oficial.png",
    "assetsdra-cintia-hero.png", "assetsdra-cintia-hero-lossless.webp",
    "assetsdra-cintia-sobre.jpeg", "cintia-logo-hero-site.mp4",
    "cintia-logo-hero-poster.jpg", "cintia-social-preview-1200x630-v2.jpg",
)

assert SOURCE.is_dir(), "The pinned V5 checkout was not found"
assert not DEST.exists(), "Refusing to overwrite an existing preview directory"
DEST.mkdir()
for file in FILES:
    assert (SOURCE / file).is_file(), f"Missing approved asset: {file}"
    shutil.copy2(SOURCE / file, DEST / file)
shutil.copytree(SOURCE / "assets", DEST / "assets")
(DEST / ".nojekyll").write_text("", encoding="utf-8")

html_path = DEST / "index.html"
html = html_path.read_text(encoding="utf-8")
html, robots_count = re.subn(
    r'<meta name="robots" content="[^"]*">',
    '<meta name="robots" content="noindex,nofollow,noarchive">',
    html,
    count=1,
)
assert robots_count == 1, "Expected exactly one production robots meta tag"

# Prevent live messages even when a tester clicks the WhatsApp links.
html, wa_count = re.subn(r'href="https://wa\.me/[^"]+"', 'href="#contato"', html)
assert wa_count >= 3, "Expected to disable all live WhatsApp anchors"
html, mail_count = re.subn(r'href="mailto:[^"]+"', 'href="#contato"', html)
assert mail_count >= 1, "Expected to disable all email anchors"
html, form_count = re.subn(r'action="https://wa\.me/[^"]+"', 'action="#contato"', html)
assert form_count == 1, "Expected to disable the real contact form action"
html = re.sub(
    r'(<a\b[^>]*href="#contato"[^>]*?)\s+target="_blank"',
    r'\1',
    html,
)
# Prevent accidental submission of form fields to a URL in no-JS browsers.
html, noscript_count = re.subn(
    r'<noscript>.*?</noscript>',
    '<noscript><p>Prévia de homologação: envio sem JavaScript desativado. Nenhuma mensagem será enviada.</p></noscript>',
    html,
    flags=re.S,
)
assert noscript_count == 1, "Unexpected noscript markup"
html = html.replace(
    '</footer>',
    '<p style="text-align:center;padding:12px;font:12px Arial,sans-serif">'
    'PRÉVIA OT V5 — AMBIENTE PÚBLICO DE HOMOLOGAÇÃO. '
    'Não enviar informações reais neste formulário.</p>\n</footer>',
)
assert 'index,follow' not in html and 'action="https://wa.me' not in html
html_path.write_text(html, encoding="utf-8")

js_path = DEST / "site.js"
js = js_path.read_text(encoding="utf-8")
def replace_once(old, new):
    global js
    assert js.count(old) == 1, f"Expected exactly one occurrence: {old}"
    js = js.replace(old, new, 1)

replace_once("link.href = url;", "link.href = '#contato';")
replace_once(
    "link.textContent = 'abrir a mensagem preparada no WhatsApp';",
    "link.textContent = 'Simulação: envio desativado na prévia';",
)
replace_once(
    "window.open(url, '_blank', 'noopener,noreferrer');",
    "status.textContent = 'PRÉVIA SEM ENVIO: mensagem composta apenas neste navegador. ' + message;",
)
replace_once(
    "const loadGTM = () => {",
    "const loadGTM = () => {\n    return; // The test preview must never load the production GTM.",
)
js_path.write_text(js, encoding="utf-8")

# Only best-effort anti-indexing. GitHub Pages is PUBLIC, not password-protected.
# The effective crawler robots.txt is on the github.io origin, so HTML noindex is essential.
(DEST / "robots.txt").write_text(
    "User-agent: *\nDisallow: /\n", encoding="utf-8"
)
(DEST / "preview-build.txt").write_text(
    "Source repository: olegariotech-site/cintia-almeida-gomes-advocacia\n"
    "Exact approved V5 HEAD: " + EXPECTED_BASE + "\n"
    "Release: public TEST PREVIEW ONLY. Live contact and GTM disabled.\n",
    encoding="utf-8",
)

assert not (DEST / "CNAME").exists()
assert not (DEST / ".github").exists()
assert not (DEST / "docs").exists()
assert not (DEST / "tests").exists()
assert not (DEST / "tools").exists()
assert (DEST / "assets" / "fonts").is_dir()
assert (DEST / "assets" / "media").is_dir()
print("PREVIEW READY: pinned V5, production CNAME excluded, robots noindex, messaging and GTM disabled.")
