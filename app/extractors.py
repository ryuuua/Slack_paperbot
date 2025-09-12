import re
from typing import Optional

ARXIV_RE = re.compile(r"https?://arxiv\.org/(abs|pdf)/(?P<id>\d{4}\.\d{4,5})(\.pdf)?", re.I)
DOI_RE   = re.compile(r"https?://(dx\.)?doi\.org/(?P<doi>10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", re.I)
ACL_RE   = re.compile(r"https?://aclanthology\.org/(?P<id>[A-Za-z0-9\-\./]+)", re.I)
OR_RE    = re.compile(r"https?://openreview\.net/(pdf\?id=|forum\?id=|pdf\?id=)?(?P<id>[A-Za-z0-9_\-]+)", re.I)
CVF_RE   = re.compile(r"https?://openaccess\.thecvf\.com/(content|papers)/[^\s]+", re.I)
BIOX_RE  = re.compile(r"https?://(www\.)?biorxiv\.org/content/[^\s]+", re.I)

URL_RE = re.compile(r"https?://[^\s>]+", re.I)

def find_urls(text: str):
    return URL_RE.findall(text or "")

def classify(url: str) -> Optional[dict]:
    for name, pat in [
        ('arxiv', ARXIV_RE), ('doi', DOI_RE), ('acl', ACL_RE),
        ('openreview', OR_RE), ('cvf', CVF_RE), ('biorxiv', BIOX_RE),
    ]:
        m = pat.search(url)
        if m:
            return {'source': name, **m.groupdict(), 'url': url}
    return {'source': 'generic', 'url': url}