import { XMLParser } from "fast-xml-parser"
import { getTelegramInitData } from "./telegram"
import { OPDSFeed, OPDSEntry, OPDSLink } from "./opds-types"

const parser = new XMLParser({
    ignoreAttributes: false,
    attributeNamePrefix: "",
    isArray: (name) => ["entry", "link", "content", "author"].indexOf(name) !== -1
})

export class OpdsClient {
    static async fetchFeed(url?: string): Promise<OPDSFeed | null> {
        const initData = getTelegramInitData()

        let targetUrl = `/api/tunnel/opds`
        if (url) {
            targetUrl += `?url=${encodeURIComponent(url)}`
        } else {
            // If no URL provided, we want the root. 
            // However, /api/tunnel/opds requires a 'url' param or defaults?
            // The backend logic expects a 'url' param.
            // If we want root (start), we should pass "/" or allow backend to handle empty.
            // But backend routes.py: `url: str = Query(...)`. It's required.
            // So we default to "/" if not provided, assuming backend handles "/" as "root".
            targetUrl += `?url=%2F`
        }

        try {
            const response = await fetch(targetUrl, {
                method: "GET",
                headers: {
                    "X-Telegram-Data": initData
                }
            })

            if (!response.ok) {
                console.error("Tunnel error:", response.statusText)
                return null
            }

            const xmlText = await response.text()
            const result = parser.parse(xmlText)

            if (!result.feed) return null

            return this.mapFeed(result.feed, url)
        } catch (e) {
            console.error("OPDS Parse Error:", e)
            return null
        }
    }

    private static mapFeed(rawFeed: any, originalUrl: string = ""): OPDSFeed {
        const entries = (rawFeed.entry || []).map((e: any) => this.mapEntry(e, originalUrl))
        const links = (rawFeed.link || []).map((l: any) => this.mapLink(l))

        // Extract pagination
        const nextLink = links.find((l: OPDSLink) => l.rel === "next")
        const prevLink = links.find((l: OPDSLink) => l.rel === "previous" || l.rel === "prev")

        // Basic pagination guess (can be improved)
        let currentPage = 1
        if (originalUrl && originalUrl.includes("page=")) {
            const match = originalUrl.match(/page=(\d+)/)
            if (match) currentPage = parseInt(match[1])
        }

        return {
            title: typeof rawFeed.title === 'string' ? rawFeed.title : (rawFeed.title?.["#text"] || "Catalog"),
            links,
            entries,
            nextPage: nextLink?.href || null,
            prevPage: prevLink?.href || null,
            currentPage,
            totalPages: null // Hard to guess from XML without specific opensearch tags
        }
    }

    private static mapEntry(raw: any, baseUrl: string): OPDSEntry {
        const links: OPDSLink[] = (raw.link || []).map((l: any) => this.mapLink(l))

        // Find special links
        const coverLink = links.find(l =>
            l.rel.includes("image") ||
            l.rel.includes("cover") ||
            l.type?.startsWith("image/")
        )

        const subsectionLink = links.find(l => l.rel === "subsection")

        // Fallback for cover in content
        let coverUrl = coverLink?.href
        if (!coverUrl && raw.content) {
            const contentArray = Array.isArray(raw.content) ? raw.content : [raw.content]
            const imgContent = contentArray.find((c: any) => c.type?.startsWith("image/"))
            if (imgContent) coverUrl = imgContent.src || imgContent["@_src"] // Check how fast-xml-parser parses attributes on content? 
            // Wait, fast-xml-parser with no prefix puts attributes as keys.
            // But content usually has text. If it's empty tag with src, it's just keys.
        }

        const author = raw.author?.[0]?.name || "Unknown"
        const title = typeof raw.title === 'string' ? raw.title : (raw.title?.["#text"] || "No title")

        return {
            id: raw.id || "",
            title: title,
            author: typeof author === 'string' ? author : (author?.["#text"] || "Unknown"), // Author name might be object
            summary: raw.summary?.["#text"] || raw.content?.["#text"] || "",
            cover_url: coverUrl,
            subsection_url: subsectionLink?.href,
            detail_url: links.find(l => l.rel === "self")?.href,
            links: links
        }
    }

    private static mapLink(raw: any): OPDSLink {
        return {
            href: raw.href,
            rel: raw.rel,
            type: raw.type,
            title: raw.title
        }
    }
}
