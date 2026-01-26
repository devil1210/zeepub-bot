import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import {
    ChevronLeft,
    ChevronRight,
    ArrowDownUp,
    Home,
    Download,
    Star,
    Calendar,
    Clock,
    ArrowUp
} from 'lucide-react';

interface SearchBottomNavProps {
    currentPage: number;
    totalPages: number;
    onPrevPage: () => void;
    onNextPage: () => void;
    onHome: () => void;
    activeSort: string;
    onSortChange: (sortId: string) => void;
}

const sortOptions = [
    { id: 'a-z', label: 'A-Z', icon: ArrowUp },
    { id: 'z-a', label: 'Z-A', icon: ArrowUp },
    { id: 'downloads', label: 'DESCARGAS', icon: Download },
    { id: 'rating', label: 'VALORACIÓN', icon: Star },
    { id: 'added', label: 'AÑADIDO', icon: Calendar },
    { id: 'updated', label: 'ACTUALIZADO', icon: Clock },
];

export const SearchBottomNav: React.FC<SearchBottomNavProps> = ({
    currentPage,
    totalPages,
    onPrevPage,
    onNextPage,
    onHome,
    activeSort,
    onSortChange
}) => {
    const { settings } = useTheme();
    const [isSortMenuOpen, setIsSortMenuOpen] = useState(false);

    return (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 md:left-auto md:right-8 md:translate-x-0 w-[85%] max-w-lg md:w-auto z-40 flex flex-col gap-3">
            {isSortMenuOpen && (
                <div
                    className="glass-panel rounded-premium p-3 border border-white/10 shadow-2xl animate-in slide-in-from-bottom-2 fade-in duration-200"
                    style={{
                        background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                        backdropFilter: `blur(${settings.glassBlur}px)`,
                        WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
                    }}
                >
                    <div className="grid grid-cols-3 gap-2">
                        {sortOptions.map((option) => {
                            const isActive = activeSort === option.id;
                            return (
                                <button
                                    key={option.id}
                                    onClick={() => {
                                        onSortChange(option.id);
                                        setIsSortMenuOpen(false);
                                    }}
                                    className={`flex flex-col items-center gap-1 px-2 py-2.5 rounded-premium-sm text-[9px] font-black uppercase tracking-widest transition-all border ${isActive
                                        ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)] shadow-lg shadow-blue-500/20'
                                        : 'bg-white/5 text-gray-400 border-transparent hover:bg-white/10 hover:text-white'
                                        }`}
                                >
                                    {option.icon && <option.icon className={`w-4 h-4 ${option.id === 'z-a' ? 'rotate-180' : ''}`} />}
                                    <span className="text-center leading-tight">{option.label}</span>
                                </button>
                            );
                        })}
                    </div>
                </div>
            )}

            <div
                className="glass-panel rounded-premium p-1 border border-black/10 dark:border-white/10 shadow-2xl flex items-center justify-between overflow-hidden"
                style={{
                    background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                    backdropFilter: `blur(${settings.glassBlur}px)`,
                    WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
                }}
            >
                <button
                    onClick={onPrevPage}
                    disabled={currentPage === 1}
                    className={`flex-1 flex flex-col items-center justify-center py-2 rounded-premium-sm transition-all duration-300 relative z-10 text-gray-500 hover:text-black dark:hover:text-white ${currentPage === 1 ? 'opacity-30 cursor-not-allowed' : ''}`}
                >
                    <div className="p-1.5 rounded-full transition-all duration-300">
                        <ChevronLeft className="w-4 h-4" strokeWidth={2} />
                    </div>
                    <span className="text-[9px] font-black uppercase tracking-widest mt-1">Anterior</span>
                </button>

                <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

                <button
                    onClick={() => setIsSortMenuOpen(!isSortMenuOpen)}
                    className={`flex-1 flex flex-col items-center justify-center py-2 rounded-premium-sm transition-all duration-300 relative z-10 ${isSortMenuOpen ? 'text-black dark:text-white' : 'text-gray-500 hover:text-black dark:hover:text-white'}`}
                >
                    <div className={`p-1.5 rounded-full transition-all duration-300 ${isSortMenuOpen ? 'bg-[var(--color-primary)] shadow-[0_0_15px_rgba(43,108,238,0.5)] translate-y-[-2px]' : ''}`}>
                        <ArrowDownUp className={`w-4 h-4 ${isSortMenuOpen ? 'text-white' : ''}`} strokeWidth={isSortMenuOpen ? 2.5 : 2} />
                    </div>
                    <span className={`text-[9px] font-black uppercase tracking-widest mt-1`}>Ordenar</span>
                </button>

                <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

                <button
                    onClick={onHome}
                    className={`flex-1 flex flex-col items-center justify-center py-2 rounded-premium-sm transition-all duration-300 relative z-10 text-gray-500 hover:text-black dark:hover:text-white`}
                >
                    <div className="p-1.5 rounded-full transition-all duration-300">
                        <Home className="w-4 h-4" strokeWidth={2} />
                    </div>
                    <span className="text-[9px] font-black uppercase tracking-widest mt-1">Inicio</span>
                </button>

                <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

                <button
                    onClick={onNextPage}
                    disabled={currentPage === totalPages}
                    className={`flex-1 flex flex-col items-center justify-center py-2 rounded-premium-sm transition-all duration-300 relative z-10 text-gray-500 hover:text-black dark:hover:text-white ${currentPage === totalPages ? 'opacity-30 cursor-not-allowed' : ''}`}
                >
                    <div className="p-1.5 rounded-full transition-all duration-300">
                        <ChevronRight className="w-4 h-4" strokeWidth={2} />
                    </div>
                    <span className="text-[9px] font-black uppercase tracking-widest mt-1">Siguiente</span>
                </button>
            </div>
        </div>
    );
};

