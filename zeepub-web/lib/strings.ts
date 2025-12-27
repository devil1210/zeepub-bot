export interface AppStrings {
    catalog_title: string
    catalog_back: string
    search_placeholder: string
    search_button: string
    search_empty: string
    search_prompt: string
    pagination_prev: string
    pagination_next: string
    book_loading: string
    book_download: string
    book_section: string
    book_series: string
    book_details_hint: string
}

export const DEFAULT_STRINGS: AppStrings = {
    catalog_title: "Catálogo",
    catalog_back: "Subir nivel",
    search_placeholder: "Buscar por título, autor o serie...",
    search_button: "Buscar",
    search_empty: "No se encontraron resultados",
    search_prompt: "Busca libros por título o autor",
    pagination_prev: "Anterior",
    pagination_next: "Siguiente",
    book_loading: "Cargando detalles...",
    book_download: "Descargar",
    book_section: "Ver esta colección...",
    book_series: "Serie",
    book_details_hint: "Toca para detalles...",
}

let cachedStrings: AppStrings | null = null

export async function fetchAppStrings(): Promise<AppStrings> {
    if (cachedStrings) return cachedStrings

    try {
        const response = await fetch("/api/app-strings")
        if (!response.ok) throw new Error("Failed to fetch strings")
        const data = await response.json()
        cachedStrings = { ...DEFAULT_STRINGS, ...data }
        return cachedStrings!
    } catch (error) {
        console.error("[Strings] Error fetching strings:", error)
        return DEFAULT_STRINGS
    }
}
