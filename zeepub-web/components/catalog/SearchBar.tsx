"use client"

import { Search, X, Library, BookOpen, Folder, Check } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
    Drawer,
    DrawerContent,
    DrawerHeader,
    DrawerTitle,
    DrawerTrigger,
    DrawerClose,
} from "@/components/ui/drawer"

interface SearchBarProps {
    searchQuery: string;
    setSearchQuery: (val: string) => void;
    searchType: string;
    setSearchType: (val: string) => void;
    isSearchDrawerOpen: boolean;
    setIsSearchDrawerOpen: (val: boolean) => void;
    onClear: () => void;
    t: (key: string) => string;
}

export function SearchBar({
    searchQuery,
    setSearchQuery,
    searchType,
    setSearchType,
    isSearchDrawerOpen,
    setIsSearchDrawerOpen,
    onClear,
    t
}: SearchBarProps) {
    const searchOptions = [
        { id: "all", label: "TODOS", icon: Library },
        { id: "title", label: "TÍTULO", icon: BookOpen },
        { id: "author", label: "AUTOR", icon: Search },
        { id: "illustrator", label: "ILUSTRADOR", icon: Search },
        { id: "translator", label: "TRADUCTOR", icon: Search },
        { id: "layout", label: "MAQUETADOR", icon: Search },
        { id: "genres", label: "GÉNEROS", icon: Folder }
    ];

    const currentTypeLabel = searchOptions.find(opt => opt.id === searchType)?.label || "TODOS";

    return (
        <div className="flex gap-2 mb-2 p-1.5 bg-background/60 backdrop-blur-xl border border-white/10 rounded-full shadow-lg relative overflow-hidden group/search-bar">
            <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-transparent to-primary/5 pointer-events-none" />
            <div className="relative flex-1 flex items-center">
                <Search className="absolute left-4 w-4 h-4 text-primary opacity-60" />
                <Input
                    type="text"
                    placeholder={t("search_placeholder") || "Buscar libros..."}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="bg-transparent border-none pl-11 h-10 text-sm focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-muted-foreground/50 rounded-full"
                />
            </div>

            <div className="flex items-center gap-1 pr-1">
                {searchQuery && (
                    <Button
                        onClick={onClear}
                        variant="ghost"
                        size="icon"
                        className="h-9 w-9 hover:bg-white/5 text-muted-foreground transition-all active:scale-95 rounded-full"
                    >
                        <X className="w-4 h-4" />
                    </Button>
                )}

                <Drawer open={isSearchDrawerOpen} onOpenChange={setIsSearchDrawerOpen}>
                    <DrawerTrigger asChild>
                        <Button
                            variant="ghost"
                            className="h-10 px-4 bg-primary/10 hover:bg-primary/20 border border-primary/20 text-[10px] uppercase tracking-wider font-bold text-primary rounded-full transition-all active:scale-95"
                        >
                            {currentTypeLabel}
                        </Button>
                    </DrawerTrigger>
                    <DrawerContent className="border-t border-white/10 bg-background/80 backdrop-blur-2xl">
                        <div className="mx-auto w-full max-w-sm">
                            <DrawerHeader>
                                <DrawerTitle className="text-center text-sm font-bold uppercase tracking-widest text-primary pt-2">
                                    {t("search_type_title_drawer") || "Tipo de Búsqueda"}
                                </DrawerTitle>
                            </DrawerHeader>
                            <div className="p-4 grid grid-cols-1 gap-2">
                                {searchOptions.map((option) => (
                                    <Button
                                        key={option.id}
                                        variant={searchType === option.id ? "secondary" : "ghost"}
                                        className={`justify-between h-12 rounded-2xl px-4 transition-all ${searchType === option.id ? 'bg-primary/20 border border-primary/30' : ''}`}
                                        onClick={() => {
                                            setSearchType(option.id)
                                            setIsSearchDrawerOpen(false)
                                        }}
                                    >
                                        <div className="flex items-center gap-3">
                                            <option.icon className={`w-4 h-4 ${searchType === option.id ? 'text-primary' : 'text-muted-foreground'}`} />
                                            <span className={`text-xs font-bold ${searchType === option.id ? 'text-primary' : 'text-foreground'}`}>
                                                {option.label}
                                            </span>
                                        </div>
                                        {searchType === option.id && <Check className="w-4 h-4 text-primary" />}
                                    </Button>
                                ))}
                            </div>
                            <div className="p-4 pt-0">
                                <DrawerClose asChild>
                                    <Button variant="outline" className="w-full rounded-2xl border-white/10 h-12 text-xs font-bold uppercase tracking-widest">
                                        {t("close") || "Cerrar"}
                                    </Button>
                                </DrawerClose>
                            </div>
                        </div>
                    </DrawerContent>
                </Drawer>
            </div>
        </div>
    );
}
