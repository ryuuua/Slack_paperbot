import requests
from typing import Optional, Dict

def resolve_arxiv(arxiv_id: str) -> Optional[Dict]:
    # arXiv API (Atom)
    url = f"https://export.arxiv.org/api/query?search_query=id:{arxiv_id}"
    r = requests.get(url, timeout=10)
    if r.status_code != 200: return None
    # 超簡易パース（厳密にはfeedparser推奨）
    title = _find(r.text, "<title>", "</title>", nth=2)  # 2個目がentryのtitle
    authors = "; ".join(_all(r.text, "<name>", "</name>"))
    year = _find(r.text, "<published>", "</published>")[:4]
    return {'title': title.strip() if title else None,
            'authors': authors, 'year': int(year) if year else None,
            'venue': 'arXiv'}

def resolve_crossref(doi: str) -> Optional[Dict]:
    url = f"https://api.crossref.org/works/{doi}"
    r = requests.get(url, timeout=10)
    if r.status_code != 200: return None
    j = r.json().get('message', {})
    title = (j.get('title') or [""])[0]
    authors = "; ".join([f"{a.get('given','')} {a.get('family','')}".strip()
                         for a in j.get('author', [])]) or None
    year = None
    for k in ('published-print', 'published-online', 'issued'):
        if j.get(k, {}).get('date-parts'):
            year = j[k]['date-parts'][0][0]; break
    venue = (j.get('container-title') or [""])[0]
    return {'title': title or None, 'authors': authors, 'year': year, 'venue': venue or None}

def resolve_acl(_id: str):  # 簡易：メタデータ未対応→URLだけ保存でもOK
    return {}

def resolve_openreview(_id: str):
    return {}

def resolve_generic():
    return {}

def _find(s, start, end, nth=1):
    i = -1
    for _ in range(nth):
        i = s.find(start, i+1)
        if i == -1: return ""
    j = s.find(end, i+len(start))
    return s[i+len(start):j] if j != -1 else ""

def _all(s, start, end):
    out=[]; i=0
    while True:
        a=s.find(start,i); 
        if a==-1: break
        b=s.find(end,a+len(start))
        if b==-1: break
        out.append(s[a+len(start):b]); i=b+len(end)
    return out