import { getTelegramInitData } from "./telegram"
import { OPDSFeed } from "./opds-types"

const feedCache = new Map<string, { data: OPDSFeed; timestamp: number }>()
const CACHE_TTL = 1000 * 60 * 60 * 6 // 6 hours

export class OpdsClient {
    static async fetchFeed(url?: string, adminMode: boolean = false, useCache: boolean = true): Promise<OPDSFeed | null> {
        const initData = getTelegramInitData()

        // Detectar si debemos usar la librería local
        const useLocalLibrary = localStorage.getItem("useLocalLibrary") === "true"

        if (useLocalLibrary && !url?.startsWith("http")) {
            // Si es local y no es una URL externa explicitly, usar el API local
            return this.fetchLocalLibrary(url)
        }

        const queryParams = new URLSearchParams()
        if (url) {
            queryParams.append("url", url)
        }
        if (adminMode) {
            queryParams.append("admin_mode", "true")
        }

        const cacheKey = `${url || "root"}-${adminMode}`
        if (useCache) {
            const cached = feedCache.get(cacheKey)
            if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
                console.log(`[OpdsClient] Returning CACHED feed: ${cacheKey}`)
                return cached.data
            }
        }

        const targetUrl = `/api/feed?${queryParams.toString()}`

        console.log(`[OpdsClient] Fetching JSON feed: ${targetUrl}`)

        try {
            const response = await fetch(targetUrl, {
                method: "GET",
                headers: {
                    "X-Telegram-Data": initData
                }
            })

            if (!response.ok) {
                const text = await response.text().catch(() => "No error body")
                console.error(`[OpdsClient] API error (${response.status}):`, text)
                return null
            }

            const data = await response.json()

            // Cache the result
            feedCache.set(cacheKey, { data, timestamp: Date.now() })

            return data as OPDSFeed
        } catch (e) {
            console.error("[OpdsClient] Unexpected Error:", e)
            return null
        }
    }

    static async fetchLocalLibrary(url?: string): Promise<OPDSFeed | null> {
        const initData = getTelegramInitData()

        let apiPath = "/api/library/catalog"
        let currentSourceId = ""
        let currentFolder = ""
        let currentPageNum = 1

        if (url && url.includes("source_id=")) {
            // Re-use source_id and folder from simulated "URL"
            const params = new URLSearchParams(url.includes("?") ? url.split("?")[1] : url)
            currentSourceId = params.get("source_id") || ""
            currentFolder = params.get("folder") || ""
            currentPageNum = parseInt(params.get("page") || "1")

            // Construct apiPath with parameters
            if (currentSourceId || currentFolder || currentPageNum > 1) {
                const useRandomCovers = localStorage.getItem("useRandomFolderCovers") !== "false"
                apiPath += `?source_id=${currentSourceId}&folder=${encodeURIComponent(currentFolder)}&page=${currentPageNum}&use_random_covers=${useRandomCovers}`
            }
        }

        try {
            const response = await fetch(apiPath, {
                headers: { "X-Telegram-Data": initData }
            })
            if (!response.ok) return null
            const data = await response.json()

            // Handle both old (array) and new (paginated object) response formats
            const items = Array.isArray(data) ? data : (data.items || [])
            const totalItems = Array.isArray(data) ? data.length : (data.total || data.items?.length || 0)
            const totalPages = Array.isArray(data) ? 1 : (data.totalPages || 1)
            const currentPage = Array.isArray(data) ? 1 : (data.page || 1)
            const sourceName = !Array.isArray(data) ? data.source_name : null

            // Map local items to OPDSFeed format
            const feed: OPDSFeed = {
                title: currentFolder || sourceName || "Bibliotecas Disponibles",
                currentPage: currentPage,
                totalItems: totalItems,
                totalPages: totalPages,
                entries: items.map((item: any) => {
                    // Safe cover extracting
                    let coverUrl = undefined
                    if (item.cover && typeof item.cover === 'string') {
                        const filename = item.cover.split(/[\\/]/).pop()
                        if (filename) coverUrl = `/api/library/covers/${filename}`
                    }

                    let title = item.title || "Sin título";
                    let romaji = item.romajiTitle;
                    let seriesIndex = item.series_index != null ? String(item.series_index) : undefined;

                    // Minimal title cleaning: just remove series prefix if present
                    if (item.series && title.toLowerCase().startsWith(item.series.toLowerCase())) {
                        const cleaned = title.substring(item.series.length).replace(/^[\s\-:\.]+/, '').trim();
                        if (cleaned) title = cleaned;
                    }

                    // Volume Extraction Fallback if missing
                    if (!seriesIndex || seriesIndex.toLowerCase() === "unico") {
                        const volMatch = title.match(/(?:volumen|vol|v)\.?\s*(\d+(?:\.\d+)?)/i);
                        if (volMatch && volMatch[1]) {
                            seriesIndex = volMatch[1];
                        }
                    }

                    return {
                        id: item.id || `local_${Math.random().toString(36).substr(2, 9)}`,
                        title: title || item.title,
                        author: item.author || (item.is_folder ? "" : "Autor desconocido"),
                        summary: item.summary || item.description || "",
                        cover_url: coverUrl,
                        is_folder: !!item.is_folder,
                        series: item.series,
                        seriesIndex: seriesIndex,
                        tags: item.tags || [],
                        categories: item.tags || [],
                        demographics: item.demographics || [],
                        bookType: item.bookType,
                        romaji: romaji,
                        englishTitle: item.englishTitle,
                        publishedAt: item.publishedAt,
                        wordCount: item.wordCount,
                        pageCount: item.pageCount,
                        readingTime: item.readingTime,
                        publishedDate: item.publishedAt || item.modifiedAtOpf,
                        year: item.publishedAt ? item.publishedAt.split("-")[0] : item.modifiedAtOpf ? item.modifiedAtOpf.split("-")[0] : (item.modifiedAt && typeof item.modifiedAt === 'string' && item.modifiedAt.includes("-")) ? item.modifiedAt.split("-")[0] : undefined,
                        illustrator: item.illustrator,
                        translator: item.translator,
                        layoutBy: item.layoutBy,
                        epubVersion: item.epubVersion,
                        fileSize: item.fileSize,
                        publisher: item.publisher,
                        asin: item.asin,
                        isbn: item.isbn,
                        uriId: item.uriId,
                        links: [
                            {
                                rel: item.is_folder ? "subsection" : "http://opds-spec.org/acquisition",
                                href: item.is_folder
                                    ? `local?source_id=${item.source_id}&folder=${encodeURIComponent(item.folder_path || "")}`
                                    : item.downloadUrl,
                                type: item.is_folder ? "application/atom+xml;profile=opds-catalog;kind=navigation" : "application/epub+zip"
                            }
                        ]
                    }
                }),
                links: []
            }

            // Add pagination links if needed
            if (currentSourceId) {
                if (currentPage < totalPages) {
                    feed.nextPage = `local?source_id=${currentSourceId}&folder=${encodeURIComponent(currentFolder)}&page=${currentPage + 1}`
                    feed.links.push({ rel: "next", href: feed.nextPage, type: "" })
                }
                if (currentPage > 1) {
                    feed.prevPage = `local?source_id=${currentSourceId}&folder=${encodeURIComponent(currentFolder)}&page=${currentPage - 1}`
                    feed.links.push({ rel: "prev", href: feed.prevPage, type: "" })
                }
            }

            return feed
        } catch (e) {
            console.error("[OpdsClient] Local fetch error:", e)
            return null
        }
    }

    static async search(query: string, pageUrl?: string, searchType: string = "all"): Promise<any> {
        const initData = getTelegramInitData()
        const useLocalLibrary = localStorage.getItem("useLocalLibrary") === "true"

        if (useLocalLibrary && !pageUrl?.startsWith("http")) {
            const response = await fetch(`/api/library/search?q=${encodeURIComponent(query)}&search_type=${searchType}`, {
                headers: { "X-Telegram-Data": initData }
            })
            if (!response.ok) return { results: [] }
            const items = await response.json()
            return {
                results: items.map((item: any) => {
                    // Safe cover extracting
                    let coverUrl = undefined
                    if (item.cover && typeof item.cover === 'string') {
                        const filename = item.cover.split(/[\\/]/).pop()
                        if (filename) coverUrl = `/api/library/covers/${filename}`
                    }

                    return {
                        id: item.id || `local_${Math.random().toString(36).substr(2, 9)}`,
                        title: item.title || "Sin título",
                        author: item.author || "Autor desconocido",
                        summary: item.summary || item.description || "",
                        cover: coverUrl,
                        isFolder: false,
                        downloadUrl: item.downloadUrl,
                        series: item.series,
                        seriesIndex: item.seriesIndex != null ? String(item.seriesIndex) : undefined,
                        tags: item.tags || [],
                        romaji: item.romaji,
                        englishTitle: item.englishTitle,
                        cleanTitle: item.cleanTitle || item.title,
                        wordCount: item.wordCount,
                        pageCount: item.pageCount,
                        readingTime: item.readingTime
                    }
                }),
                currentPage: 1,
                totalPages: 1
            }
        }

        // Default to Bot API search
        const response = await fetch("/api/bot", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-telegram-init-data": initData,
            },
            body: JSON.stringify({
                action: "search",
                data: { query, pageUrl }
            }),
        })
        if (!response.ok) return { results: [] }
        return response.json()
    }

    static clearCache() {
        feedCache.clear()
    }
}
