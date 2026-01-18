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
        <div className="md:hidden sticky top-0 z-30 px-4 pt-2 pb-2">
            <div
                className="glass-panel rounded-2xl p-4 border border-white/10 backdrop-blur-xl"
                style={{
                    background: `rgba(var(--glass-rgb), var(--searchbar-opacity, 0.8))`,
                }}
            >
                <div className="flex flex-row gap-2 sm:gap-4 items-center justify-between">
                    <div className="relative w-full max-w-xl group flex-1">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <SearchIcon className="text-gray-400 w-5 h-5 group-focus-within:text-[var(--color-primary)] transition-colors" />
                        </div>
                        <input
                            className="block w-full pl-10 pr-24 py-3 rounded-xl border border-white/5 bg-black/20 text-white placeholder-gray-500 focus:ring-1 focus:ring-primary focus:border-primary focus:bg-black/40 text-sm transition-all shadow-inner"
                            placeholder="Buscar..."
                            type="text"
                            value={searchTerm}
                            onChange={(e) => onSearchChange(e.target.value)}
                        />
                        <div className="absolute inset-y-0 right-1 flex items-center">
                            <button
                                onClick={onScopeClick}
                                className="px-3 py-1.5 rounded-lg bg-primary/20 hover:bg-primary/30 border border-primary/30 text-primary text-[10px] font-black uppercase tracking-widest transition-all shadow-[0_0_10px_rgba(var(--primary-rgb),0.2)]"
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
