import sqlite3, time, os, requests
from typing import Optional, Dict, List

class PaperStore:
    def save(self, rec: Dict): ...
    def list_recent(self, n=10) -> List[Dict]: ...
    def ensure(self): ...

class SQLiteStore(PaperStore):
    def __init__(self, path="papers.db", schema_path="/app/app/schema.sql"):
        self.path = path; self.schema_path = schema_path
    def ensure(self):
        con = sqlite3.connect(self.path)
        with open(self.schema_path) as f:
            con.executescript(f.read())
        con.commit(); con.close()
    def save(self, rec: Dict):
        con = sqlite3.connect(self.path)
        con.execute("""INSERT OR IGNORE INTO papers
         (url,source,title,authors,year,venue,added_by,ts)
         VALUES (?,?,?,?,?,?,?,?)""", (
            rec.get('url'), rec.get('source'), rec.get('title'),
            rec.get('authors'), rec.get('year'), rec.get('venue'),
            rec.get('added_by'), int(time.time())
        ))
        con.commit(); con.close()
    def list_recent(self, n=10):
        con = sqlite3.connect(self.path)
        rows = con.execute("""SELECT url,source,title,authors,year,venue,ts
                              FROM papers ORDER BY ts DESC LIMIT ?""", (n,)).fetchall()
        con.close()
        keys = ["url","source","title","authors","year","venue","ts"]
        return [dict(zip(keys,r)) for r in rows]

# --- Notion 例（最低限） ---
class NotionStore(PaperStore):
    def __init__(self, token: str, dbid: str):
        self.session = requests.Session()
        self.session.headers.update({
          "Authorization": f"Bearer {token}",
          "Notion-Version": "2022-06-28",
          "Content-Type": "application/json"
        })
        self.dbid = dbid
    def ensure(self): pass
    def save(self, rec: Dict):
        title = rec.get('title') or rec['url']
        data = {
          "parent":{"database_id": self.dbid},
          "properties":{
            "Name":{"title":[{"text":{"content": title}}]},
            "URL":{"url": rec["url"]},
            "Source":{"select":{"name": rec.get("source","generic")}},
            "Authors":{"rich_text":[{"text":{"content": rec.get("authors","")}}]},
            "Year":{"number": rec.get("year")}
          }
        }
        self.session.post("https://api.notion.com/v1/pages", json=data)
    def list_recent(self, n=10): return []

# --- Zotero/Supabase は省略（同様にsaveを実装） ---