import os
import sys
import re
import json
import time
import random
import queue
import urllib.request
import unicodedata
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

base_dir = "/Users/elite/.gemini/antigravity-ide/scratch/dau-xuan-tuoi-sang-web"
data_dir = os.path.join(base_dir, "data")
stories_dir = os.path.join(data_dir, "stories")
assets_dir = os.path.join(base_dir, "assets")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://truyenfull.live/"
    }

def clean_text(raw_text):
    if not raw_text:
        return ""
    text = raw_text.replace("*", "u")
    text = unicodedata.normalize("NFC", text)
    emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
    text = emoji_pattern.sub("", text)
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
        req = urllib.request.Request(cover_url, headers=get_random_headers())
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

def fetch_story_meta(slug):
    url = f"https://truyenfull.live/{slug}/"
    req = urllib.request.Request(url, headers=get_random_headers())
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    title_elem = soup.find("h3", class_="title") or soup.find("h1")
    title = title_elem.get_text(strip=True) if title_elem else slug
    author_elem = soup.find("a", itemprop="author")
    author = author_elem.get_text(strip=True) if author_elem else "Khuyết Danh"
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
        req = urllib.request.Request(url, headers=get_random_headers())
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
                time.sleep(random.uniform(0.3, 0.6))
                break
            except Exception:
                time.sleep(1.0)
    all_chapters.sort(key=lambda x: x["chapter_num"])
    return all_chapters

def fetch_single_chapter(slug, ch_meta):
    num = ch_meta["chapter_num"]
    url = f"https://truyenfull.live/{slug}/chuong-{num}/"
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=get_random_headers())
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            content_elem = soup.find("div", id="chapter-c")
            h2_elem = soup.find("h2")
            a_elem = soup.find("a", class_="chapter-title")
            page_title = (h2_elem.get_text(strip=True) if h2_elem else "") or (a_elem.get_text(strip=True) if a_elem else "")
            formatted_page_title = format_chapter_title(page_title, num)
            final_title = ch_meta["title"]
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
            time.sleep(random.uniform(0.5, 1.0))
        except Exception:
            time.sleep(random.uniform(1.0, 2.0))
    return {
        "chapter_num": num,
        "title": ch_meta["title"],
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

def process_story(slug):
    print(f"Bắt đầu xử lý bộ truyện: {slug}")
    meta = fetch_story_meta(slug)
    story_dir = os.path.join(stories_dir, slug)
    chapters_dir = os.path.join(story_dir, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)

    links = fetch_all_chapter_links(slug, meta["total_pages"])
    total_chs = len(links)
    meta["total_chapters"] = total_chs
    print(f"{meta['title']} có tổng cộng {total_chs} chương")

    with open(os.path.join(story_dir, "story.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    final_list = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        f_map = {executor.submit(fetch_single_chapter, slug, ch): ch for ch in links}
        for future in as_completed(f_map):
            res = future.result()
            c_num = res["chapter_num"]
            out_file = os.path.join(chapters_dir, f"chapter_{c_num}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
            final_list.append({
                "chapter_num": c_num,
                "title": res["title"],
                "char_count": res.get("char_count", 0)
            })

    failed = [c for c in final_list if c["char_count"] == 0]
    if failed:
        print(f"Đang tải lại {len(failed)} chương bị lỗi...")
        for f_item in failed:
            meta_ch = next(c for c in links if c["chapter_num"] == f_item["chapter_num"])
            fixed = fetch_single_chapter(slug, meta_ch)
            out_file = os.path.join(chapters_dir, f"chapter_{fixed['chapter_num']}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(fixed, f, ensure_ascii=False, indent=2)
            f_item["char_count"] = fixed["char_count"]
            f_item["title"] = fixed["title"]
            time.sleep(0.4)

    final_list.sort(key=lambda x: x["chapter_num"])
    with open(os.path.join(story_dir, "chapters_list.json"), "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)

    update_library_catalog({
        "slug": meta["slug"],
        "title": meta["title"],
        "author": meta["author"],
        "categories": meta["categories"],
        "status": meta["status"],
        "description": meta["description"],
        "cover": meta["cover"],
        "total_chapters": total_chs
    })
    print(f"Hoàn tất bộ truyện {slug}: {total_chs} chương")

def run_queue(story_slugs):
    q = queue.Queue()
    for s in story_slugs:
        q.put(s)

    total = q.qsize()
    idx = 1
    while not q.empty():
        slug = q.get()
        print(f"--- [Hàng đợi {idx}/{total}] Đang xử lý: {slug} ---")
        try:
            process_story(slug)
        except Exception as e:
            print(f"Lỗi khi xử lý {slug}: {e}")
        idx += 1
        time.sleep(random.uniform(1.0, 2.0))

if __name__ == "__main__":
    default_batch = [
        "happy-ending-voi-anh-cong-co-chap-luon-thien-vi-toi",
        "chang-doi-xuan-my-soi-khoai-tay",
        "co-vu-khong-lay-chong-bac-phong-tam-bach-ly",
        "kieu-loan-xan-dieu",
        "hon-nhan-xung-doi",
        "khong-can-loan-an-va-1",
        "trung-sinh-ta-ga-cho-vuong-gia-om-yeu"
    ]
    targets = sys.argv[1:] if len(sys.argv) > 1 else default_batch
    run_queue(targets)
