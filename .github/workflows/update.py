import os
import requests
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- Config ---
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = "3807cc69-34c9-8085-a3df-000bbf130224"
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
GOOGLE_REFRESH_TOKEN = os.environ["GOOGLE_REFRESH_TOKEN"]

# --- Google Calendar ---
def get_events():
    creds = Credentials(
        token=None,
        refresh_token=GOOGLE_REFRESH_TOKEN,
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
    )
    service = build("calendar", "v3", credentials=creds)
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()
    result = service.events().list(
        calendarId="primary",
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    return result.get("items", [])

# --- Notion ---
def get_todos():
    url = "https://api.notion.com/v1/databases/" + NOTION_DATABASE_ID + "/query"
    headers = {
        "Authorization": "Bearer " + NOTION_TOKEN,
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    body = {
        "filter": {
            "property": "Status",
            "status": {
                "does_not_equal": "Done"
            }
        }
    }
    res = requests.post(url, headers=headers, json=body)
    results = res.json().get("results", [])
    todos = []
    for r in results:
        name = r["properties"]["Task name"]["title"]
        if name:
            todos.append(name[0]["plain_text"])
    return todos

# --- Build HTML ---
def build_events_html(events):
    if not events:
        return '<li><span class="event-icon event-personal">personal</span><span class="label">No event YAYY</span></li>'
    items = ""
    for e in events:
        title = e.get("summary", "Untitled")
        start = e.get("start", {}).get("dateTime", "")
        end = e.get("end", {}).get("dateTime", "")
        time_str = ""
        if start and end:
            s = datetime.fromisoformat(start).strftime("%H:%M")
            en = datetime.fromisoformat(end).strftime("%H:%M")
            time_str = f'<span class="time">{s}&ndash;{en}</span>'
        link = e.get("hangoutLink", "")
        link_html = f'<a href="{link}">link</a>' if link else ""
        items += f'<li><span class="event-icon event-personal">personal</span><span class="label">{title}</span>{time_str}{link_html}</li>\n'
    return items

def build_todos_html(todos):
    if not todos:
        return '<li class="todo"><span class="todo-icon todo-personal">personal</span><span class="label">Nothing to do YAYYY</span></li>'
    items = ""
    for t in todos:
        items += f'<li class="todo"><span class="todo-icon todo-personal">personal</span><span class="label">{t}</span></li>\n'
    return items

# --- Update index.html ---
def update_html(events_html, todos_html):
    with open("index.html", "r") as f:
        content = f.read()

    import re
    content = re.sub(
        r'(<ul class="events">)(.*?)(</ul>)',
        r'\1\n' + events_html + r'\3',
        content, flags=re.DOTALL
    )
    content = re.sub(
        r'(<ul class="todos">)(.*?)(</ul>)',
        r'\1\n' + todos_html + r'\3',
        content, flags=re.DOTALL
    )

    # Update date
    today = datetime.now().strftime("%B %d, %Y")
    content = re.sub(
        r'(<span class="receipt-date" id="receiptDate">)(.*?)(</span>)',
        r'\g<1>' + today + r'\3',
        content
    )

    with open("index.html", "w") as f:
        f.write(content)

# --- Main ---
events = get_events()
todos = get_todos()
events_html = build_events_html(events)
todos_html = build_todos_html(todos)
update_html(events_html, todos_html)
print("Done!")
