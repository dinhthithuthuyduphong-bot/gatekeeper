import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_sources as fs  # noqa: E402

HTML = b"""<html><body>
<a href="/track/x/papers">Research Papers</a>
<a class="k" href='https://www.acm.org/publications/policies/new-acm-policy-on-authorship'>ACM
 <b>Policy</b> on Authorship</a>
<a href="https://example.org/open">SIGSOFT Open Science Policy</a>
<a href="https://example.org/open">duplicate</a>
<a href="mailto:x@y.z">policy mail</a>
</body></html>"""


def test_links_keep_matching_absolute_unique():
    out = fs.links(HTML, "https://conf.researchr.org/home/x", ["policy", "papers"])
    assert out == [
        {"text": "Research Papers", "url": "https://conf.researchr.org/track/x/papers"},
        {
            "text": "ACM Policy on Authorship",
            "url": "https://www.acm.org/publications/policies/new-acm-policy-on-authorship",
        },
        {"text": "SIGSOFT Open Science Policy", "url": "https://example.org/open"},
    ]
