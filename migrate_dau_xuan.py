import os
import re
import json
import unicodedata
from bs4 import BeautifulSoup
import urllib.request

base_dir = "/Users/elite/.gemini/antigravity-ide/scratch/dau-xuan-tuoi-sang-web"
data_dir = os.path.join(base_dir, "data")
stories_dir = os.path.join(data_dir, "stories")
target_dir = os.path.join(stories_dir, "dau-xuan-tuoi-sang")
target_chapters_dir = os.path.join(target_dir, "chapters")

os.makedirs(target_chapters_dir, exist_ok=True)

with open(os.path.join(data_dir, "story.json"), "r", encoding="utf-8") as f:
    story = json.load(f)

story["slug"] = "dau-xuan-tuoi-sang"
with open(os.path.join(target_dir, "story.json"), "w", encoding="utf-8") as f:
    json.dump(story, f, ensure_ascii=False, indent=2)

toc_titles = {}
for p in [1, 2, 3]:
    url = f"https://truyenfull.live/dau-xuan-tuoi-sang/trang-{p}/" if p > 1 else "https://truyenfull.live/dau-xuan-tuoi-sang/"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a"):
            href = a.get("href", "")
            m = re.search(r"chuong-(\d+)", href)
            if m and "dau-xuan-tuoi-sang" in href:
                num = int(m.group(1))
                t = a.get("title") or a.get_text(strip=True)
                t = t.replace("*", "u")
                t = unicodedata.normalize("NFC", t).strip()
                t = re.sub(r"^.*?-\s*Chương", "Chương", t, flags=re.IGNORECASE)
                m2 = re.search(r"Chương\s*(\d+)(?:\s*[:\-]\s*(.*))?", t, flags=re.IGNORECASE)
                if m2:
                    sub = m2.group(2)
                    if sub and sub.strip():
                        toc_titles[num] = f"Chương {num}: {sub.strip()}"
                    else:
                        toc_titles[num] = f"Chương {num}"
    except Exception:
        pass

updated_list = []
old_chapters_dir = os.path.join(data_dir, "chapters")
for i in range(1, 150):
    src = os.path.join(old_chapters_dir, f"chapter_{i}.json")
    dst = os.path.join(target_chapters_dir, f"chapter_{i}.json")
    with open(src, "r", encoding="utf-8") as f:
        c_data = json.load(f)

    final_title = toc_titles.get(i, f"Chương {i}")
    c_data["title"] = final_title
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(c_data, f, ensure_ascii=False, indent=2)

    updated_list.append({
        "chapter_num": i,
        "title": final_title,
        "char_count": c_data.get("char_count", 0)
    })

with open(os.path.join(target_dir, "chapters_list.json"), "w", encoding="utf-8") as f:
    json.dump(updated_list, f, ensure_ascii=False, indent=2)

lib_item = {
    "slug": "dau-xuan-tuoi-sang",
    "title": story["title"],
    "author": story["author"],
    "categories": story["categories"],
    "status": story["status"],
    "description": story["description"],
    "cover": story["cover"],
    "total_chapters": 149
}

lib_file = os.path.join(data_dir, "library.json")
library = [lib_item]
with open(lib_file, "w", encoding="utf-8") as f:
    json.dump(library, f, ensure_ascii=False, indent=2)

print("Migrated dau-xuan-tuoi-sang and updated titles successfully")
