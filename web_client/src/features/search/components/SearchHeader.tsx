import React, { useState, useEffect, useMemo } from 'react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { debounce } from 'perfect-debounce';
import {
    Search as SearchIcon,
    LayoutGrid,
    List,
    RefreshCw,
    Layers,
    Infinity as InfinityIcon
} from 'lucide-react';

interface SearchHeaderProps {
    searchTerm: string;
    onSearchChange: (term: string) => void;
    onSearchSubmit?: () => void;
    selectedScope: string;
    onScopeClick: () => void;
    viewMode: 'list' | 'grid';
    onViewModeChange: (mode: 'list' | 'grid') => void;
    loading: boolean;
}

export const SearchHeader: React.FC<SearchHeaderProps> = ({
    searchTerm,
    onSearchChange,
    onSearchSubmit,
    selectedScope,
    onScopeClick,
    viewMode,
    onViewModeChange,
    loading
}) => {
    const { settings, updateSettings } = useTheme();

    // Local state for immediate UI feedback
    const [localTerm, setLocalTerm] = useState(searchTerm);

    // Sync local state when external searchTerm changes (e.g. via navigation)
    useEffect(() => {
        setLocalTerm(searchTerm);
    }, [searchTerm]);

    // Debounce the global state update to prevent excessive context re-renders
    const debouncedUpdate = useMemo(() => {
        return debounce((term: string) => {
            onSearchChange(term);
        }, 300);
    }, [onSearchChange]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newVal = e.target.value;
        setLocalTerm(newVal);
        debouncedUpdate(newVal);
    };

    return (
        <div
            className="z-30 px-4 md:px-8 py-3 md:py-4 border-b border-white/5"
            style={{
                background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                backdropFilter: `blur(${settings.glassBlur}px)`,
                WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
            }}
        >
            <div className="w-full max-w-7xl mx-auto">
                <div className="flex flex-row gap-4 items-center justify-between">
                    <div className="relative group flex-1">
                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                            <SearchIcon className="text-gray-400 w-5 h-5 group-focus-within:text-[var(--color-primary)] transition-colors" />
                        </div>
                        <input
                            className="block w-full pl-12 pr-28 py-3.5 rounded-premium-sm border border-white/10 bg-white/5 text-white placeholder-gray-500 focus:ring-2 focus:ring-primary/50 focus:border-primary focus:bg-white/10 text-sm transition-all shadow-inner"
                            placeholder="Busca por título, autor, género o ISBN..."
                            type="text"
                            value={localTerm}
                            onChange={handleInputChange}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    onSearchSubmit?.();
                                }
                            }}
                        />
                        <div className="absolute inset-y-0 right-1.5 flex items-center">
                            <button
                                onClick={onScopeClick}
                                className="px-4 py-2 rounded-premium-sm bg-primary/20 hover:bg-primary/30 border border-primary/30 text-primary text-[10px] font-black uppercase tracking-widest transition-all shadow-lg active:scale-95"
                            >
                                {selectedScope}
                            </button>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 sm:gap-4 shrink-0">
                        {/* Compact Toggles (Only 2 Icons) */}
                        <div className="flex items-center gap-2">
                            {/* Toggle View: List <-> Grid */}
                            <button
                                onClick={() => onViewModeChange(viewMode === 'grid' ? 'list' : 'grid')}
                                className="p-2.5 rounded-premium-sm bg-white/5 border border-white/5 hover:border-primary/50 text-gray-400 hover:text-primary transition-all shadow-lg active:scale-90"
                                title={viewMode === 'grid' ? "Cambiar a Lista" : "Cambiar a Cuadrícula"}
                            >
                                {viewMode === 'grid' ? <List className="w-5 h-5" /> : <LayoutGrid className="w-5 h-5" />}
                            </button>

                            {/* Toggle Mode: Infinite <-> Paginated */}
                            <button
                                onClick={() => updateSettings({ listMode: settings.listMode === 'infinite' ? 'paginated' : 'infinite' })}
                                className="p-2.5 rounded-premium-sm bg-white/5 border border-white/5 hover:border-primary/50 text-gray-400 hover:text-primary transition-all shadow-lg active:scale-90"
                                title={settings.listMode === 'infinite' ? "Cambiar a Paginado" : "Cambiar a Infinito"}
                            >
                                {settings.listMode === 'infinite' ? <InfinityIcon className="w-5 h-5 text-primary" /> : <Layers className="w-5 h-5" />}
                            </button>
                        </div>

                        {loading && <div className="ml-2"><RefreshCw className="w-5 h-5 animate-spin text-primary" /></div>}
                    </div>
                </div>
            </div>
        </div>
    );
};
