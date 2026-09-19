import os
import re
import json
import time
import urllib.request
import unicodedata
from bs4 import BeautifulSoup

base_dir = "/Users/elite/.gemini/antigravity-ide/scratch/dau-xuan-tuoi-sang-web"
chapters_dir = os.path.join(base_dir, "data", "chapters")
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def clean_text(raw_text):
    if not raw_text:
        return ""
    text = raw_text.replace("*", "u")
    text = unicodedata.normalize("NFC", text)
    lines = text.splitlines()
    cleaned_lines = []
    watermark_pattern = re.compile(r"truyen\s*full", re.IGNORECASE)
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        if watermark_pattern.search(line_str):
            continue
        cleaned_lines.append(line_str)
    return "\n\n".join(cleaned_lines)

def fetch_single(chapter_num):
    url = f"https://truyenfull.live/dau-xuan-tuoi-sang/chuong-{chapter_num}/"
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            content_elem = soup.find("div", id="chapter-c")
            title_elem = soup.find("a", class_="chapter-title")
            raw_title = title_elem.get_text(strip=True) if title_elem else f"Chương {chapter_num}"
            raw_content = content_elem.get_text("\n", strip=True) if content_elem else ""
            cleaned_title = unicodedata.normalize("NFC", raw_title.replace("*", "u"))
            cleaned_content = clean_text(raw_content)
            if len(cleaned_content) > 100:
                return {
                    "chapter_num": chapter_num,
                    "title": cleaned_title,
                    "content": cleaned_content,
                    "char_count": len(cleaned_content)
                }
            time.sleep(1)
        except Exception:
            time.sleep(1.5)
    return None

def run_fix():
    missing = []
    for i in range(1, 150):
        filepath = os.path.join(chapters_dir, f"chapter_{i}.json")
        if not os.path.exists(filepath):
            missing.append(i)
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("char_count", 0) == 0:
                    missing.append(i)
    
    print("Found missing chapters:", len(missing))
    for num in missing:
        res = fetch_single(num)
        if res:
            filepath = os.path.join(chapters_dir, f"chapter_{num}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
            print(f"Fixed chapter {num}: {res['char_count']} chars")
        else:
            print(f"Failed chapter {num}")
        time.sleep(0.4)

    all_chapters = []
    for i in range(1, 150):
        filepath = os.path.join(chapters_dir, f"chapter_{i}.json")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_chapters.append({
                "chapter_num": i,
                "title": data.get("title", f"Chương {i}"),
                "char_count": data.get("char_count", 0)
            })

    list_meta_path = os.path.join(base_dir, "data", "chapters_list.json")
    with open(list_meta_path, "w", encoding="utf-8") as f:
        json.dump(all_chapters, f, ensure_ascii=False, indent=2)
    print("Updated chapters_list.json successfully")

if __name__ == "__main__":
    run_fix()
