import os
import re
import json
import urllib.request
import unicodedata
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

base_dir = "/Users/elite/.gemini/antigravity-ide/scratch/dau-xuan-tuoi-sang-web"
chapters_dir = os.path.join(base_dir, "data", "chapters")
assets_dir = os.path.join(base_dir, "assets")
story_url = "https://truyenfull.live/dau-xuan-tuoi-sang/"
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

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

def download_cover(cover_url):
    target_path = os.path.join(assets_dir, "cover.jpg")
    try:
        req = urllib.request.Request(cover_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(target_path, "wb") as f:
                f.write(resp.read())
        return "assets/cover.jpg"
    except Exception:
        return ""

def fetch_story_info():
    req = urllib.request.Request(story_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    title_elem = soup.find("h3", class_="title") or soup.find("h1")
    title = title_elem.get_text(strip=True) if title_elem else "Đầu Xuân Tươi Sáng"
    author_elem = soup.find("a", itemprop="author")
    author = author_elem.get_text(strip=True) if author_elem else "Cô Nương Đừng Khóc"
    desc_elem = soup.find("div", class_="desc-text")
    desc = clean_text(desc_elem.get_text("\n", strip=True)) if desc_elem else ""
    book_elem = soup.find("div", class_="book")
    img_elem = book_elem.find("img") if book_elem else None
    cover_url = img_elem.get("src") if img_elem else ""
    cover_local = download_cover(cover_url) if cover_url else ""
    return {
        "title": title,
        "author": author,
        "categories": ["Ngôn Tình", "Đô Thị"],
        "status": "Hoàn thành",
        "total_chapters": 149,
        "description": desc,
        "cover": cover_local
    }

def fetch_single_chapter(chapter_num):
    url = f"https://truyenfull.live/dau-xuan-tuoi-sang/chuong-{chapter_num}/"
    req = urllib.request.Request(url, headers=headers)
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
        return {
            "chapter_num": chapter_num,
            "title": cleaned_title,
            "content": cleaned_content,
            "char_count": len(cleaned_content)
        }
    except Exception as e:
        return {
            "chapter_num": chapter_num,
            "title": f"Chương {chapter_num}",
            "content": "",
            "error": str(e)
        }

def run():
    story_info = fetch_story_info()
    story_meta_path = os.path.join(base_dir, "data", "story.json")
    with open(story_meta_path, "w", encoding="utf-8") as f:
        json.dump(story_info, f, ensure_ascii=False, indent=2)

    chapter_list = []
    total = 149
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_single_chapter, i): i for i in range(1, total + 1)}
        for future in as_completed(futures):
            res = future.result()
            ch_num = res["chapter_num"]
            out_path = os.path.join(chapters_dir, f"chapter_{ch_num}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
            chapter_list.append({
                "chapter_num": ch_num,
                "title": res["title"],
                "char_count": res.get("char_count", 0)
            })
            print(f"Downloaded chapter {ch_num}/{total}")

    chapter_list.sort(key=lambda x: x["chapter_num"])
    list_meta_path = os.path.join(base_dir, "data", "chapters_list.json")
    with open(list_meta_path, "w", encoding="utf-8") as f:
        json.dump(chapter_list, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run()
