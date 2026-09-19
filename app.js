const state = {
    library: [],
    currentSlug: "dau-xuan-tuoi-sang",
    currentStory: null,
    chapters: [],
    currentChapterNum: 1,
    currentChapterData: null,
    selectedCategory: "Tất cả",
    searchQuery: "",
    theme: localStorage.getItem("dxts_theme") || "sepia",
    font: localStorage.getItem("dxts_font") || "serif",
    fontSize: parseInt(localStorage.getItem("dxts_font_size") || "18", 10),
    lineHeight: localStorage.getItem("dxts_line_height") || "1.9",
    readerWidth: localStorage.getItem("dxts_reader_width") || "medium"
};

const dom = {
    body: document.body,
    progressBar: document.getElementById("reading-progress-bar"),
    btnLibrary: document.getElementById("btn-library"),
    btnStoryDetail: document.getElementById("btn-story-detail"),
    btnTocToggle: document.getElementById("btn-toc-toggle"),
    btnSettingsToggle: document.getElementById("btn-settings-toggle"),
    headerStoryTitle: document.getElementById("header-story-title"),
    headerChapterBadge: document.getElementById("header-chapter-badge"),
    libraryView: document.getElementById("library-view"),
    overviewView: document.getElementById("overview-view"),
    readerView: document.getElementById("reader-view"),
    libraryGrid: document.getElementById("library-grid"),
    librarySearchInput: document.getElementById("library-search-input"),
    categoryFilterBar: document.getElementById("category-filter-bar"),
    btnBackToLibrary: document.getElementById("btn-back-to-library"),
    storyCoverImg: document.getElementById("story-cover-img"),
    storyTitle: document.getElementById("story-title"),
    storyAuthor: document.getElementById("story-author"),
    storyCategories: document.getElementById("story-categories"),
    storyStatus: document.getElementById("story-status"),
    storyTotalChapters: document.getElementById("story-total-chapters"),
    storyDescriptionText: document.getElementById("story-description-text"),
    overviewChaptersTitle: document.getElementById("overview-chapters-title"),
    btnReadFirst: document.getElementById("btn-read-first"),
    btnContinueReading: document.getElementById("btn-continue-reading"),
    overviewSearchInput: document.getElementById("overview-search-input"),
    overviewChaptersGrid: document.getElementById("overview-chapters-grid"),
    btnPrevTop: document.getElementById("btn-prev-top"),
    btnNextTop: document.getElementById("btn-next-top"),
    selectChapterTop: document.getElementById("select-chapter-top"),
    btnPrevBottom: document.getElementById("btn-prev-bottom"),
    btnNextBottom: document.getElementById("btn-next-bottom"),
    selectChapterBottom: document.getElementById("select-chapter-bottom"),
    chapterDisplayTitle: document.getElementById("chapter-display-title"),
    chapterCharCount: document.getElementById("chapter-char-count"),
    chapterContentBody: document.getElementById("chapter-content-body"),
    modalBackdrop: document.getElementById("modal-backdrop"),
    tocDrawer: document.getElementById("toc-drawer"),
    tocDrawerTitle: document.getElementById("toc-drawer-title"),
    btnCloseToc: document.getElementById("btn-close-toc"),
    tocSearchInput: document.getElementById("toc-search-input"),
    tocListContainer: document.getElementById("toc-list-container"),
    settingsModal: document.getElementById("settings-modal"),
    btnCloseSettings: document.getElementById("btn-close-settings"),
    btnDecFont: document.getElementById("btn-dec-font"),
    btnIncFont: document.getElementById("btn-inc-font"),
    btnQuickFontDec: document.getElementById("btn-quick-font-dec"),
    btnQuickFontInc: document.getElementById("btn-quick-font-inc"),
    currentFontSizeText: document.getElementById("current-font-size-text")
};

function applyVisualSettings() {
    dom.body.setAttribute("data-theme", state.theme);
    dom.body.setAttribute("data-font", state.font);
    dom.body.setAttribute("data-width", state.readerWidth);
    dom.body.style.setProperty("--font-size", `${state.fontSize}px`);
    dom.body.style.setProperty("--line-height", state.lineHeight);
    dom.currentFontSizeText.textContent = `${state.fontSize}px`;

    document.querySelectorAll(".theme-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-theme-val") === state.theme);
    });
    document.querySelectorAll(".font-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-font-val") === state.font);
    });
    document.querySelectorAll(".lh-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-lh-val") === state.lineHeight);
    });
    document.querySelectorAll(".width-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-width-val") === state.readerWidth);
    });
}

function updateReadingProgress() {
    if (dom.readerView.classList.contains("hidden")) {
        dom.progressBar.style.width = "0%";
        return;
    }
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    dom.progressBar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
}

function getLastReadChapter(slug) {
    const val = localStorage.getItem(`dxts_last_read_${slug}`);
    return val ? parseInt(val, 10) : 1;
}

function setLastReadChapter(slug, num) {
    localStorage.setItem(`dxts_last_read_${slug}`, num);
}

async function loadLibraryData() {
    try {
        const res = await fetch("data/library.json");
        state.library = await res.json();
        renderCategoryFilters();
        applyLibraryFilters();
        handleRouting();
    } catch (err) {
        console.error("Failed to load library data", err);
    }
}

function renderCategoryFilters() {
    dom.categoryFilterBar.innerHTML = "";
    const primaryCategories = ["Tất cả", "Trọng Sinh", "Ngôn Tình", "Nữ Cường", "Cổ Đại", "Đô Thị"];
    
    primaryCategories.forEach(cat => {
        const count = cat === "Tất cả" 
            ? state.library.length 
            : state.library.filter(s => s.categories.some(c => c.toLowerCase() === cat.toLowerCase())).length;

        if (count > 0 || cat === "Tất cả") {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "cat-filter-btn";
            if (cat === state.selectedCategory) {
                btn.classList.add("active");
            }
            btn.textContent = `${cat} (${count})`;
            btn.addEventListener("click", () => {
                state.selectedCategory = cat;
                document.querySelectorAll(".cat-filter-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                applyLibraryFilters();
            });
            dom.categoryFilterBar.appendChild(btn);
        }
    });
}

function applyLibraryFilters() {
    let filtered = state.library;
    if (state.selectedCategory !== "Tất cả") {
        filtered = filtered.filter(story =>
            story.categories.some(c => c.toLowerCase() === state.selectedCategory.toLowerCase())
        );
    }
    if (state.searchQuery) {
        const q = state.searchQuery.toLowerCase();
        filtered = filtered.filter(story =>
            story.title.toLowerCase().includes(q) ||
            story.author.toLowerCase().includes(q) ||
            story.categories.some(cat => cat.toLowerCase().includes(q))
        );
    }
    renderLibraryGrid(filtered);
}

function renderLibraryGrid(list) {
    dom.libraryGrid.innerHTML = "";
    if (list.length === 0) {
        dom.libraryGrid.innerHTML = "<p style='color: var(--text-secondary); text-align: center; grid-column: 1/-1; padding: 40px;'>Không tìm thấy bộ truyện nào phù hợp.</p>";
        return;
    }
    list.forEach(story => {
        const card = document.createElement("div");
        card.className = "story-card";

        const coverWrap = document.createElement("div");
        coverWrap.className = "story-card-cover-wrap";
        const coverImg = document.createElement("img");
        coverImg.className = "story-card-cover";
        coverImg.src = story.cover || "assets/dau-xuan-tuoi-sang.jpg";
        coverImg.alt = story.title;
        coverWrap.appendChild(coverImg);

        const info = document.createElement("div");
        info.className = "story-card-info";

        const topContent = document.createElement("div");
        const title = document.createElement("h3");
        title.className = "story-card-title";
        title.textContent = story.title;

        const author = document.createElement("div");
        author.className = "story-card-author";
        author.textContent = `Tác giả: ${story.author}`;

        const tags = document.createElement("div");
        tags.className = "story-card-tags";
        story.categories.slice(0, 3).forEach(cat => {
            const tag = document.createElement("span");
            tag.className = "story-tag";
            tag.textContent = cat;
            tags.appendChild(tag);
        });

        topContent.appendChild(title);
        topContent.appendChild(author);
        topContent.appendChild(tags);

        const footer = document.createElement("div");
        footer.className = "story-card-footer";

        const chCount = document.createElement("span");
        chCount.className = "story-card-ch-count";
        chCount.textContent = `${story.total_chapters} chương`;

        const actionBtn = document.createElement("button");
        actionBtn.type = "button";
        actionBtn.className = "story-card-action-btn";
        actionBtn.textContent = "Đọc truyện";
        actionBtn.addEventListener("click", () => {
            window.location.hash = `#story=${story.slug}`;
        });

        footer.appendChild(chCount);
        footer.appendChild(actionBtn);

        info.appendChild(topContent);
        info.appendChild(footer);

        card.appendChild(coverWrap);
        card.appendChild(info);
        dom.libraryGrid.appendChild(card);
    });
}

async function loadStoryDetails(slug) {
    if (state.currentStory && state.currentStory.slug === slug && state.chapters.length > 0) {
        return;
    }
    state.currentSlug = slug;
    try {
        const [metaRes, listRes] = await Promise.all([
            fetch(`data/stories/${slug}/story.json`),
            fetch(`data/stories/${slug}/chapters_list.json`)
        ]);
        state.currentStory = await metaRes.json();
        state.chapters = await listRes.json();
    } catch (err) {
        console.error("Failed to load story files", err);
    }
}

function showLibrary() {
    dom.overviewView.classList.add("hidden");
    dom.readerView.classList.add("hidden");
    dom.libraryView.classList.remove("hidden");
    dom.btnStoryDetail.style.display = "none";
    dom.btnTocToggle.style.display = "none";
    dom.headerStoryTitle.textContent = "Tủ Sách Gia Đình";
    dom.headerChapterBadge.style.display = "none";
    document.title = "Tủ Sách Gia Đình";
    window.scrollTo({ top: 0, behavior: "instant" });
    updateReadingProgress();
}

async function showOverview(slug) {
    await loadStoryDetails(slug);
    if (!state.currentStory) return;

    dom.libraryView.classList.add("hidden");
    dom.readerView.classList.add("hidden");
    dom.overviewView.classList.remove("hidden");
    dom.btnStoryDetail.style.display = "none";
    dom.btnTocToggle.style.display = "inline-flex";

    dom.headerStoryTitle.textContent = state.currentStory.title;
    dom.headerChapterBadge.style.display = "none";
    document.title = `${state.currentStory.title} - Tủ Sách Gia Đình`;

    dom.storyCoverImg.src = state.currentStory.cover || "assets/dau-xuan-tuoi-sang.jpg";
    dom.storyTitle.textContent = state.currentStory.title;
    dom.storyAuthor.textContent = state.currentStory.author;
    dom.storyCategories.textContent = state.currentStory.categories.join(", ");
    dom.storyStatus.textContent = state.currentStory.status;
    dom.storyTotalChapters.textContent = `${state.chapters.length} chương`;
    dom.overviewChaptersTitle.textContent = `Danh sách ${state.chapters.length} chương`;

    dom.storyDescriptionText.innerHTML = "";
    const pList = state.currentStory.description.split("\n\n");
    pList.forEach(txt => {
        if (txt.trim()) {
            const p = document.createElement("p");
            p.textContent = txt.trim();
            dom.storyDescriptionText.appendChild(p);
        }
    });

    const lastRead = getLastReadChapter(slug);
    if (lastRead > 1) {
        dom.btnContinueReading.textContent = `Đọc tiếp Chương ${lastRead}`;
        dom.btnContinueReading.style.display = "inline-block";
    } else {
        dom.btnContinueReading.style.display = "none";
    }

    populateChapterSelectors();
    renderOverviewChapters(state.chapters);
    renderTocDrawerList(state.chapters);
    window.scrollTo({ top: 0, behavior: "instant" });
    updateReadingProgress();
}

function populateChapterSelectors() {
    const selects = [dom.selectChapterTop, dom.selectChapterBottom];
    selects.forEach(sel => {
        sel.innerHTML = "";
        state.chapters.forEach(ch => {
            const opt = document.createElement("option");
            opt.value = ch.chapter_num;
            opt.textContent = ch.title;
            sel.appendChild(opt);
        });
    });
}

function renderOverviewChapters(list) {
    dom.overviewChaptersGrid.innerHTML = "";
    const lastRead = getLastReadChapter(state.currentSlug);
    list.forEach(ch => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "chapter-grid-item";
        if (ch.chapter_num === lastRead) {
            btn.classList.add("active");
        }
        btn.textContent = ch.title;
        btn.addEventListener("click", () => {
            window.location.hash = `#story=${state.currentSlug}&c=${ch.chapter_num}`;
        });
        dom.overviewChaptersGrid.appendChild(btn);
    });
}

function renderTocDrawerList(list) {
    dom.tocListContainer.innerHTML = "";
    dom.tocDrawerTitle.textContent = `Mục lục: ${state.currentStory ? state.currentStory.title : ""}`;
    list.forEach(ch => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "toc-item";
        if (ch.chapter_num === state.currentChapterNum && !dom.readerView.classList.contains("hidden")) {
            btn.classList.add("active");
        }
        btn.textContent = ch.title;
        btn.addEventListener("click", () => {
            closeModals();
            window.location.hash = `#story=${state.currentSlug}&c=${ch.chapter_num}`;
        });
        dom.tocListContainer.appendChild(btn);
    });
}

async function loadChapter(slug, num) {
    await loadStoryDetails(slug);
    if (!state.currentStory || state.chapters.length === 0) return;

    const validNum = Math.max(1, Math.min(state.chapters.length, num));
    state.currentChapterNum = validNum;
    setLastReadChapter(slug, validNum);

    dom.libraryView.classList.add("hidden");
    dom.overviewView.classList.add("hidden");
    dom.readerView.classList.remove("hidden");
    dom.btnStoryDetail.style.display = "inline-flex";
    dom.btnTocToggle.style.display = "inline-flex";

    dom.headerStoryTitle.textContent = state.currentStory.title;
    dom.headerChapterBadge.style.display = "inline-block";
    const currentMeta = state.chapters.find(c => c.chapter_num === validNum);
    dom.headerChapterBadge.textContent = currentMeta ? currentMeta.title : `Chương ${validNum}`;

    window.scrollTo({ top: 0, behavior: "instant" });

    populateChapterSelectors();
    dom.selectChapterTop.value = validNum;
    dom.selectChapterBottom.value = validNum;
    dom.btnPrevTop.disabled = validNum <= 1;
    dom.btnPrevBottom.disabled = validNum <= 1;
    dom.btnNextTop.disabled = validNum >= state.chapters.length;
    dom.btnNextBottom.disabled = validNum >= state.chapters.length;

    dom.chapterDisplayTitle.textContent = `Đang tải ${currentMeta ? currentMeta.title : "chương"}...`;
    dom.chapterContentBody.innerHTML = "";
    dom.chapterCharCount.textContent = "";

    try {
        const res = await fetch(`data/stories/${slug}/chapters/chapter_${validNum}.json`);
        const data = await res.json();
        state.currentChapterData = data;

        dom.chapterDisplayTitle.textContent = data.title;
        dom.chapterCharCount.textContent = `${data.char_count.toLocaleString("vi-VN")} ký tự`;

        const pList = data.content.split("\n\n");
        const frag = document.createDocumentFragment();
        pList.forEach(pText => {
            if (pText.trim()) {
                const p = document.createElement("p");
                p.textContent = pText.trim();
                frag.appendChild(p);
            }
        });
        dom.chapterContentBody.appendChild(frag);

        document.title = `${data.title} - ${state.currentStory.title}`;
        updateReadingProgress();
        renderTocDrawerList(state.chapters);
    } catch (err) {
        dom.chapterDisplayTitle.textContent = `Lỗi tải chương ${validNum}`;
        dom.chapterContentBody.innerHTML = "<p>Không thể tải nội dung chương. Vui lòng thử lại.</p>";
    }
}

function handleRouting() {
    const hash = window.location.hash;
    if (!hash || hash === "#library") {
        showLibrary();
        return;
    }
    const legacyMatch = hash.match(/^#c(\d+)$/);
    if (legacyMatch) {
        loadChapter("dau-xuan-tuoi-sang", parseInt(legacyMatch[1], 10));
        return;
    }
    const chapterMatch = hash.match(/^#story=([^&]+)&c=(\d+)$/);
    if (chapterMatch) {
        loadChapter(chapterMatch[1], parseInt(chapterMatch[2], 10));
        return;
    }
    const storyMatch = hash.match(/^#story=([^&]+)$/);
    if (storyMatch) {
        showOverview(storyMatch[1]);
        return;
    }
    showLibrary();
}

function openTocDrawer() {
    dom.modalBackdrop.classList.remove("hidden");
    dom.tocDrawer.classList.remove("hidden");
    dom.settingsModal.classList.add("hidden");
    dom.tocSearchInput.value = "";
    renderTocDrawerList(state.chapters);
    dom.tocSearchInput.focus();
}

function openSettingsModal() {
    dom.modalBackdrop.classList.remove("hidden");
    dom.settingsModal.classList.remove("hidden");
    dom.tocDrawer.classList.add("hidden");
}

function closeModals() {
    dom.modalBackdrop.classList.add("hidden");
    dom.tocDrawer.classList.add("hidden");
    dom.settingsModal.classList.add("hidden");
}

function setupEventListeners() {
    window.addEventListener("hashchange", handleRouting);
    window.addEventListener("scroll", updateReadingProgress);

    dom.btnLibrary.addEventListener("click", () => {
        closeModals();
        window.location.hash = "#library";
    });

    dom.btnBackToLibrary.addEventListener("click", () => {
        window.location.hash = "#library";
    });

    dom.btnStoryDetail.addEventListener("click", () => {
        closeModals();
        window.location.hash = `#story=${state.currentSlug}`;
    });

    dom.headerStoryTitle.addEventListener("click", () => {
        closeModals();
        if (dom.readerView.classList.contains("hidden") && dom.overviewView.classList.contains("hidden")) {
            window.location.hash = "#library";
        } else {
            window.location.hash = `#story=${state.currentSlug}`;
        }
    });

    dom.btnTocToggle.addEventListener("click", () => {
        if (dom.tocDrawer.classList.contains("hidden")) {
            openTocDrawer();
        } else {
            closeModals();
        }
    });

    dom.btnSettingsToggle.addEventListener("click", () => {
        if (dom.settingsModal.classList.contains("hidden")) {
            openSettingsModal();
        } else {
            closeModals();
        }
    });

    dom.modalBackdrop.addEventListener("click", closeModals);
    dom.btnCloseToc.addEventListener("click", closeModals);
    dom.btnCloseSettings.addEventListener("click", closeModals);

    dom.btnReadFirst.addEventListener("click", () => {
        window.location.hash = `#story=${state.currentSlug}&c=1`;
    });

    dom.btnContinueReading.addEventListener("click", () => {
        const lastRead = getLastReadChapter(state.currentSlug);
        window.location.hash = `#story=${state.currentSlug}&c=${lastRead}`;
    });

    [dom.btnPrevTop, dom.btnPrevBottom].forEach(btn => {
        btn.addEventListener("click", () => {
            if (state.currentChapterNum > 1) {
                window.location.hash = `#story=${state.currentSlug}&c=${state.currentChapterNum - 1}`;
            }
        });
    });

    [dom.btnNextTop, dom.btnNextBottom].forEach(btn => {
        btn.addEventListener("click", () => {
            if (state.currentChapterNum < state.chapters.length) {
                window.location.hash = `#story=${state.currentSlug}&c=${state.currentChapterNum + 1}`;
            }
        });
    });

    [dom.selectChapterTop, dom.selectChapterBottom].forEach(sel => {
        sel.addEventListener("change", (e) => {
            window.location.hash = `#story=${state.currentSlug}&c=${parseInt(e.target.value, 10)}`;
        });
    });

    dom.librarySearchInput.addEventListener("input", (e) => {
        state.searchQuery = e.target.value.trim();
        applyLibraryFilters();
    });

    dom.overviewSearchInput.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        const filtered = state.chapters.filter(ch =>
            ch.title.toLowerCase().includes(query) ||
            String(ch.chapter_num).includes(query)
        );
        renderOverviewChapters(filtered);
    });

    dom.tocSearchInput.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        const filtered = state.chapters.filter(ch =>
            ch.title.toLowerCase().includes(query) ||
            String(ch.chapter_num).includes(query)
        );
        renderTocDrawerList(filtered);
    });

    document.querySelectorAll(".theme-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            state.theme = btn.getAttribute("data-theme-val");
            localStorage.setItem("dxts_theme", state.theme);
            applyVisualSettings();
        });
    });

    document.querySelectorAll(".font-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            state.font = btn.getAttribute("data-font-val");
            localStorage.setItem("dxts_font", state.font);
            applyVisualSettings();
        });
    });

    document.querySelectorAll(".lh-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            state.lineHeight = btn.getAttribute("data-lh-val");
            localStorage.setItem("dxts_line_height", state.lineHeight);
            applyVisualSettings();
        });
    });

    document.querySelectorAll(".width-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            state.readerWidth = btn.getAttribute("data-width-val");
            localStorage.setItem("dxts_reader_width", state.readerWidth);
            applyVisualSettings();
        });
    });

    const changeFontSize = (delta) => {
        const nextSize = Math.max(16, Math.min(36, state.fontSize + delta));
        if (nextSize !== state.fontSize) {
            state.fontSize = nextSize;
            localStorage.setItem("dxts_font_size", state.fontSize);
            applyVisualSettings();
        }
    };

    dom.btnDecFont.addEventListener("click", () => changeFontSize(-1));
    dom.btnIncFont.addEventListener("click", () => changeFontSize(1));
    if (dom.btnQuickFontDec) {
        dom.btnQuickFontDec.addEventListener("click", () => changeFontSize(-1));
    }
    if (dom.btnQuickFontInc) {
        dom.btnQuickFontInc.addEventListener("click", () => changeFontSize(1));
    }

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeModals();
            return;
        }
        if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") {
            return;
        }
        if (!dom.readerView.classList.contains("hidden")) {
            if (e.key === "ArrowLeft" && state.currentChapterNum > 1) {
                window.location.hash = `#story=${state.currentSlug}&c=${state.currentChapterNum - 1}`;
            } else if (e.key === "ArrowRight" && state.currentChapterNum < state.chapters.length) {
                window.location.hash = `#story=${state.currentSlug}&c=${state.currentChapterNum + 1}`;
            }
        }
    });
}

applyVisualSettings();
setupEventListeners();
loadLibraryData();
