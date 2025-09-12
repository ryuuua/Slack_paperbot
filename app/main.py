import os, time
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from app.extractors import find_urls, classify
from app import resolvers
from app.storage import SQLiteStore, NotionStore

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# 保存先を選択（デフォはSQLite）
STORE = None
if os.getenv("NOTION_TOKEN") and os.getenv("NOTION_DB_ID"):
    STORE = NotionStore(os.getenv("NOTION_TOKEN"), os.getenv("NOTION_DB_ID"))
else:
    STORE = SQLiteStore(path="/app/papers.db")
STORE.ensure()

def resolve_meta(kind: dict):
    src = kind["source"]
    if src == "arxiv" and kind.get("id"):
        return resolvers.resolve_arxiv(kind["id"]) or {}
    if src == "doi" and kind.get("doi"):
        return resolvers.resolve_crossref(kind["doi"]) or {}
    if src == "acl":        return resolvers.resolve_acl(kind.get("id","")) or {}
    if src == "openreview": return resolvers.resolve_openreview(kind.get("id","")) or {}
    return resolvers.resolve_generic()

def save_one(url: str, user: str):
    kind = classify(url)
    meta = resolve_meta(kind)
    rec = {
      "url": url,
      "source": kind["source"],
      "title": meta.get("title"),
      "authors": meta.get("authors"),
      "year": meta.get("year"),
      "venue": meta.get("venue"),
      "added_by": user
    }
    STORE.save(rec)
    return rec

# 1) メッセージ内URLを自動保存
@app.event("message")
def on_message(event, say, logger):
    text = event.get("text","")
    if event.get("subtype"): return  # bot_message などは無視
    urls = find_urls(text)
    saved = 0
    for u in urls:
        try:
            save_one(u, event.get("user",""))
            saved += 1
        except Exception as e:
            logger.error(f"save error for {u}: {e}")
    if saved:
        say(text=f"🗂️ {saved}件の論文リンクを保存しました。`/paper-ls` で確認できます。", thread_ts=event.get("ts"))

# 2) 📚 リアクションで保存
@app.event("reaction_added")
def on_reaction_added(event, client, say):
    if event.get("reaction") != "books":  # :books:
        return
    item = event.get("item",{})
    if item.get("type") != "message": return
    msg = client.conversations_history(channel=item["channel"], inclusive=True, latest=item["ts"], limit=1)
    messages = msg.get("messages",[])
    if not messages: return
    urls = find_urls(messages[0].get("text",""))
    for u in urls:
        save_one(u, event.get("user",""))
    say(channel=item["channel"], thread_ts=item["ts"], text=f"📚 保存しました（リアクション経由）。")

# 3) /paper-save URL
@app.command("/paper-save")
def cmd_save(ack, respond, command):
    ack()
    url = (command.get("text") or "").strip()
    if not url:
        respond("使い方: `/paper-save https://arxiv.org/abs/xxxx.xxxxx`")
        return
    save_one(url, command["user_id"])
    respond("✅ 保存しました。")

# 4) /paper-ls
@app.command("/paper-ls")
def cmd_ls(ack, respond):
    ack()
    rows = STORE.list_recent(10)
    if not rows:
        respond("保存はまだありません。")
        return
    lines = []
    for r in rows:
        title = (r["title"] or "(no title)")[:120]
        venue = f" · {r['venue']}" if r.get("venue") else ""
        year  = f" ({r['year']})" if r.get("year") else ""
        lines.append(f"- *{title}*{year}{venue}\n  {r['url']}")
    respond("\n".join(lines))

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()