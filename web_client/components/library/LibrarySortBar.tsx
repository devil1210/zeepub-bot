import React from 'react';
import { ArrowDownUp, Filter, Home, LucideIcon } from 'lucide-react';

interface SortOption {
    id: string;
    label: string;
    icon: LucideIcon;
}

interface LibrarySortBarProps {
    onNavigate: (tab: string) => void;
    isSortMenuOpen: boolean;
    setIsSortMenuOpen: (open: boolean) => void;
    activeSort: string;
    setActiveSort: (sort: string) => void;
    sortOptions: SortOption[];
    settings: any;
}

export const LibrarySortBar: React.FC<LibrarySortBarProps> = ({
    onNavigate,
    isSortMenuOpen,
    setIsSortMenuOpen,
    activeSort,
    setActiveSort,
    sortOptions,
    settings
}) => {
    return (
        <div className="md:hidden fixed bottom-6 left-8 right-8 z-40 animate-in slide-in-from-bottom-4 duration-300 flex flex-col gap-3 max-w-5xl mx-auto">
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
                                        setActiveSort(option.id);
                                        setIsSortMenuOpen(false);
                                    }}
                                    className={`flex flex-col items-center gap-1 px-2 py-2.5 rounded-premium-sm text-[9px] font-black uppercase tracking-widest transition-all border ${isActive
                                        ? 'bg-primary text-white border-primary shadow-lg shadow-blue-500/20'
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
                    onClick={() => onNavigate('dashboard')}
                    className="flex-1 flex flex-col items-center justify-center py-2 rounded-premium-sm transition-all duration-300 text-gray-500 hover:text-black dark:hover:text-white"
                >
                    <div className="p-1.5 rounded-full transition-all duration-300">
                        <Home className="w-4 h-4" strokeWidth={2} />
                    </div>
                    <span className="text-[9px] font-black uppercase tracking-widest mt-1">Inicio</span>
                </button>

                <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

                <button
                    onClick={() => setIsSortMenuOpen(!isSortMenuOpen)}
                    className={`flex-1 flex flex-col items-center justify-center py-2 rounded-premium-sm transition-all duration-300 relative z-10 ${isSortMenuOpen ? 'text-black dark:text-white' : 'text-gray-500 hover:text-black dark:hover:text-white'}`}
                >
                    <div className={`p-1.5 rounded-full transition-all duration-300 ${isSortMenuOpen ? 'bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)] translate-y-[-2px]' : ''}`}>
                        <ArrowDownUp className={`w-4 h-4 ${isSortMenuOpen ? 'text-white' : ''}`} strokeWidth={isSortMenuOpen ? 2.5 : 2} />
                    </div>
                    <span className="text-[9px] font-black uppercase tracking-widest mt-1">Ordenar</span>
                </button>

                <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

                <button
                    className="flex-1 flex flex-col items-center justify-center py-2 rounded-premium-sm transition-all duration-300 text-gray-500 hover:text-black dark:hover:text-white"
                >
                    <div className="p-1.5 rounded-full transition-all duration-300">
                        <Filter className="w-4 h-4" strokeWidth={2} />
                    </div>
                    <span className="text-[9px] font-black uppercase tracking-widest mt-1">Filtrar</span>
                </button>
            </div>
        </div>
    );
};
