import os
import sys
import re
import json
import time
import urllib.request
import unicodedata
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

base_dir = "/Users/elite/.gemini/antigravity-ide/scratch/dau-xuan-tuoi-sang-web"
data_dir = os.path.join(base_dir, "data")
stories_dir = os.path.join(data_dir, "stories")
assets_dir = os.path.join(base_dir, "assets")
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

def download_cover(slug, cover_url):
    if not cover_url:
        return ""
    os.makedirs(assets_dir, exist_ok=True)
    target_path = os.path.join(assets_dir, f"{slug}.jpg")
    try:
        req = urllib.request.Request(cover_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(target_path, "wb") as f:
                f.write(resp.read())
        return f"assets/{slug}.jpg"
    except Exception:
        return ""

def format_chapter_title(raw_title, chapter_num):
    if not raw_title:
        return f"Chương {chapter_num}"
    t = raw_title.replace("*", "u")
    t = unicodedata.normalize("NFC", t).strip()
    t = re.sub(r"^.*?-\s*Chương", "Chương", t, flags=re.IGNORECASE)
    m = re.search(r"Chương\s*(\d+)(?:\s*[:\-]\s*(.*))?", t, flags=re.IGNORECASE)
    if m:
        c_num = m.group(1)
        subtitle = m.group(2)
        if subtitle and subtitle.strip():
            sub_clean = subtitle.strip()
            sub_clean = re.sub(r"^[:\-]\s*", "", sub_clean)
            return f"Chương {c_num}: {sub_clean}"
        return f"Chương {c_num}"
    return f"Chương {chapter_num}"

def fetch_story_metadata(slug):
    story_url = f"https://truyenfull.live/{slug}/"
    req = urllib.request.Request(story_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    title_elem = soup.find("h3", class_="title") or soup.find("h1")
    title = title_elem.get_text(strip=True) if title_elem else slug
    author_elem = soup.find("a", itemprop="author")
    author = author_elem.get_text(strip=True) if author_elem else "Tác giả"
    cat_elems = soup.find_all("a", itemprop="genre")
    categories = list(dict.fromkeys([c.get_text(strip=True) for c in cat_elems]))
    desc_elem = soup.find("div", class_="desc-text")
    desc = clean_text(desc_elem.get_text("\n", strip=True)) if desc_elem else ""
    book_elem = soup.find("div", class_="book")
    img_elem = book_elem.find("img") if book_elem else None
    cover_url = img_elem.get("src") if img_elem else ""
    local_cover = download_cover(slug, cover_url)

    pagination = soup.find("ul", class_="pagination")
    total_pages = 1
    if pagination:
        for a in pagination.find_all("a"):
            txt = a.get_text(strip=True)
            if txt.isdigit():
                total_pages = max(total_pages, int(txt))
            elif "trang-" in a.get("href", ""):
                m = re.search(r"trang-(\d+)", a.get("href"))
                if m:
                    total_pages = max(total_pages, int(m.group(1)))

    return {
        "slug": slug,
        "title": title,
        "author": author,
        "categories": categories if categories else ["Ngôn Tình"],
        "status": "Hoàn thành",
        "description": desc,
        "cover": local_cover,
        "total_pages": total_pages
    }

def fetch_all_chapter_links(slug, total_pages):
    all_chapters = []
    seen = set()
    for page in range(1, total_pages + 1):
        url = f"https://truyenfull.live/{slug}/trang-{page}/" if page > 1 else f"https://truyenfull.live/{slug}/"
        req = urllib.request.Request(url, headers=headers)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                soup = BeautifulSoup(html, "html.parser")
                list_chs = soup.find_all("ul", class_="list-chapter")
                for l in list_chs:
                    for a in l.find_all("a"):
                        href = a.get("href", "")
                        m = re.search(r"chuong-(\d+)", href)
                        if m:
                            ch_num = int(m.group(1))
                            if ch_num not in seen:
                                seen.add(ch_num)
                                raw_t = a.get("title") or a.get_text(strip=True)
                                formatted_t = format_chapter_title(raw_t, ch_num)
                                all_chapters.append({
                                    "chapter_num": ch_num,
                                    "title": formatted_t,
                                    "url": href
                                })
                break
            except Exception:
                time.sleep(1)
    all_chapters.sort(key=lambda x: x["chapter_num"])
    return all_chapters

def fetch_chapter_content(slug, chapter_meta):
    num = chapter_meta["chapter_num"]
    url = f"https://truyenfull.live/{slug}/chuong-{num}/"
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            content_elem = soup.find("div", id="chapter-c")
            h2_elem = soup.find("h2")
            a_elem = soup.find("a", class_="chapter-title")
            page_title = (h2_elem.get_text(strip=True) if h2_elem else "") or (a_elem.get_text(strip=True) if a_elem else "")
            formatted_page_title = format_chapter_title(page_title, num)
            final_title = chapter_meta["title"]
            if ":" in formatted_page_title and ":" not in final_title:
                final_title = formatted_page_title

            raw_content = content_elem.get_text("\n", strip=True) if content_elem else ""
            cleaned_content = clean_text(raw_content)
            if len(cleaned_content) > 80:
                return {
                    "chapter_num": num,
                    "title": final_title,
                    "content": cleaned_content,
                    "char_count": len(cleaned_content)
                }
            time.sleep(1)
        except Exception:
            time.sleep(1.2)
    return {
        "chapter_num": num,
        "title": chapter_meta["title"],
        "content": "",
        "char_count": 0
    }

def update_library_catalog(new_story_meta):
    lib_path = os.path.join(data_dir, "library.json")
    library = []
    if os.path.exists(lib_path):
        try:
            with open(lib_path, "r", encoding="utf-8") as f:
                library = json.load(f)
        except Exception:
            library = []

    exists = False
    for idx, item in enumerate(library):
        if item["slug"] == new_story_meta["slug"]:
            library[idx] = new_story_meta
            exists = True
            break
    if not exists:
        library.append(new_story_meta)

    with open(lib_path, "w", encoding="utf-8") as f:
        json.dump(library, f, ensure_ascii=False, indent=2)

def scrape_full_story(slug):
    print(f"Scraping story: {slug}")
    meta = fetch_story_metadata(slug)
    story_dir = os.path.join(stories_dir, slug)
    chapters_dir = os.path.join(story_dir, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)

    chapter_links = fetch_all_chapter_links(slug, meta["total_pages"])
    total_chapters = len(chapter_links)
    meta["total_chapters"] = total_chapters
    print(f"Found {total_chapters} chapters for {meta['title']}")

    story_meta_path = os.path.join(story_dir, "story.json")
    with open(story_meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    final_chapters_list = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_map = {executor.submit(fetch_chapter_content, slug, ch): ch for ch in chapter_links}
        for future in as_completed(future_map):
            res = future.result()
            c_num = res["chapter_num"]
            out_file = os.path.join(chapters_dir, f"chapter_{c_num}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
            final_chapters_list.append({
                "chapter_num": c_num,
                "title": res["title"],
                "char_count": res.get("char_count", 0)
            })
            if len(final_chapters_list) % 10 == 0 or len(final_chapters_list) == total_chapters:
                print(f"Downloaded {len(final_chapters_list)}/{total_chapters} chapters")

    failed = [c for c in final_chapters_list if c["char_count"] == 0]
    if failed:
        print(f"Retrying {len(failed)} failed chapters sequentially...")
        for f_item in failed:
            meta_ch = next(c for c in chapter_links if c["chapter_num"] == f_item["chapter_num"])
            fixed = fetch_chapter_content(slug, meta_ch)
            out_file = os.path.join(chapters_dir, f"chapter_{fixed['chapter_num']}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(fixed, f, ensure_ascii=False, indent=2)
            f_item["char_count"] = fixed["char_count"]
            f_item["title"] = fixed["title"]
            time.sleep(0.5)

    final_chapters_list.sort(key=lambda x: x["chapter_num"])
    list_path = os.path.join(story_dir, "chapters_list.json")
    with open(list_path, "w", encoding="utf-8") as f:
        json.dump(final_chapters_list, f, ensure_ascii=False, indent=2)

    update_library_catalog({
        "slug": meta["slug"],
        "title": meta["title"],
        "author": meta["author"],
        "categories": meta["categories"],
        "status": meta["status"],
        "description": meta["description"],
        "cover": meta["cover"],
        "total_chapters": total_chapters
    })
    print(f"Completed scraping {slug}: {total_chapters} chapters")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "chi-la-tieu-thiep-nguyet-minh-chau"
    scrape_full_story(target)
