import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { useSearchNav } from '../contexts/SearchNavContext';
import {
    Search as SearchIcon,
    LayoutGrid,
    List,
    RefreshCw
} from 'lucide-react';

interface SearchHeaderProps {
    searchTerm: string;
    onSearchChange: (term: string) => void;
    selectedScope: string;
    onScopeClick: () => void;
    viewMode: 'list' | 'grid';
    onViewModeChange: (mode: 'list' | 'grid') => void;
    loading: boolean;
}

export const SearchHeader: React.FC<SearchHeaderProps> = ({
    searchTerm,
    onSearchChange,
    selectedScope,
    onScopeClick,
    viewMode,
    onViewModeChange,
    loading
}) => {
    const { settings } = useTheme();

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
                            className="block w-full pl-12 pr-28 py-3.5 rounded-2xl border border-white/10 bg-white/5 text-white placeholder-gray-500 focus:ring-2 focus:ring-primary/50 focus:border-primary focus:bg-white/10 text-sm transition-all shadow-inner"
                            placeholder="Busca por título, autor, género o ISBN..."
                            type="text"
                            value={searchTerm}
                            onChange={(e) => onSearchChange(e.target.value)}
                        />
                        <div className="absolute inset-y-0 right-1.5 flex items-center">
                            <button
                                onClick={onScopeClick}
                                className="px-4 py-2 rounded-xl bg-primary/20 hover:bg-primary/30 border border-primary/30 text-primary text-[10px] font-black uppercase tracking-widest transition-all shadow-lg active:scale-95"
                            >
                                {selectedScope}
                            </button>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                        {/* View Toggles */}
                        <div className="bg-black/20 p-1 rounded-lg border border-white/5 flex shrink-0">
                            <button
                                onClick={() => onViewModeChange('list')}
                                className={`p-2 rounded-md transition-all ${viewMode === 'list' ? 'bg-white/10 text-white shadow-sm' : 'text-gray-400 hover:text-white'}`}
                                title="Vista de Lista"
                            >
                                <List className="w-4 h-4" />
                            </button>
                            <button
                                onClick={() => onViewModeChange('grid')}
                                className={`p-2 rounded-md transition-all ${viewMode === 'grid' ? 'bg-white/10 text-white shadow-sm' : 'text-gray-400 hover:text-white'}`}
                                title="Vista de Cuadrícula"
                            >
                                <LayoutGrid className="w-4 h-4" />
                            </button>
                        </div>

                        {loading && <RefreshCw className="w-5 h-5 animate-spin text-[var(--color-primary)]" />}
                    </div>
                </div>
            </div>
        </div>
    );
};
