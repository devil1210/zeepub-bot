// Shared transparent header for all pages
export function TransparentHeader() {
    return (
        <header className="sticky top-0 z-50 pt-safe h-12 bg-transparent pointer-events-none" aria-hidden="true" />
    )
}
