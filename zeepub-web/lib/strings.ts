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
    donate_hero_title: string
    donate_hero_desc: string
    donate_tier_title: string
    donate_why_title: string
    donate_why_desc: string
    donate_benefit_1: string
    donate_benefit_2: string
    donate_benefit_3: string
    home_greeting: string
    home_functions: string
    home_admin_panel: string
    menu_search_label: string
    menu_search_desc: string
    menu_catalog_label: string
    menu_catalog_desc: string
    menu_downloads_label: string
    menu_downloads_desc: string
    menu_status_label: string
    menu_status_desc: string
    menu_donate_label: string
    menu_donate_desc: string
    menu_help_label: string
    menu_help_desc: string
    status_current_level: string
    status_downloads_today: string
    status_next_reset: string
    status_unlimited: string
    status_unlimited_desc: string
    status_system: string
    status_upgrade_btn: string
    downloads_unlimited: string
    downloads_available: string
    downloads_today: string
    downloads_completed: string
    downloads_remaining: string
    downloads_reset_info: string
    downloads_history_title: string
    downloads_history_sent: string
    help_hero_title: string
    help_hero_desc: string
    help_commands_title: string
    help_faq_title: string
    help_support_title: string
    help_support_desc: string
    help_support_btn: string
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
    donate_hero_title: "Apoya a ZeePubBot",
    donate_hero_desc: "Tu donación nos ayuda a mantener el servicio activo y mejorar continuamente",
    donate_tier_title: "Elige tu nivel",
    donate_why_title: "¿Por qué donar?",
    donate_why_desc: "ZeePubBot es un proyecto de código abierto mantenido por la comunidad. Tu apoyo nos ayuda a:",
    donate_benefit_1: "Mantener los servidores activos 24/7",
    donate_benefit_2: "Añadir nuevas funcionalidades",
    donate_benefit_3: "Mejorar el catálogo de libros",
    home_greeting: "Hola, [Nombre]",
    home_functions: "Funciones",
    home_admin_panel: "Panel Administrador",
    menu_search_label: "Buscar Libros",
    menu_search_desc: "Encuentra ePubs en el catálogo",
    menu_catalog_label: "Mi Catálogo",
    menu_catalog_desc: "Accede a bibliotecas OPDS",
    menu_downloads_label: "Mis Descargas",
    menu_downloads_desc: "Historial y límites de descarga",
    menu_status_label: "Estado",
    menu_status_desc: "Ver estado del bot y estadísticas",
    menu_donate_label: "Donar",
    menu_donate_desc: "Apoya el proyecto",
    menu_help_label: "Ayuda",
    menu_help_desc: "Comandos y soporte",
    status_current_level: "Nivel actual",
    status_downloads_today: "Descargas de Hoy",
    status_next_reset: "Próximo reset en [Tiempo]",
    status_unlimited: "✅ Descargas ilimitadas",
    status_unlimited_desc: "Tu nivel permite descargas sin restricciones",
    status_system: "Estado del Sistema",
    status_upgrade_btn: "Aumentar Límite de Descargas",
    downloads_unlimited: "∞ Ilimitadas",
    downloads_available: "Descargas disponibles",
    downloads_today: "Descargas hoy",
    downloads_completed: "[Cant] completadas",
    downloads_remaining: "[Cant] restantes",
    downloads_reset_info: "📊 Las estadísticas se resetean diariamente a las 00:00",
    downloads_history_title: "Historial Reciente",
    downloads_history_sent: "Enviado",
    help_hero_title: "¿Necesitas ayuda?",
    help_hero_desc: "Aquí encontrarás todo lo que necesitas saber sobre ZeePubBot",
    help_commands_title: "Comandos Disponibles",
    help_faq_title: "Preguntas Frecuentes",
    help_support_title: "¿Aún necesitas ayuda?",
    help_support_desc: "Nuestro equipo está aquí para ayudarte",
    help_support_btn: "Contactar Soporte",
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
