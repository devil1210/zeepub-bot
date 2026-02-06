import React from 'react';
import { Search } from 'lucide-react';

interface DashboardSearchProps {
    onSearchClick: () => void;
}

export const DashboardSearch: React.FC<DashboardSearchProps> = ({ onSearchClick }) => {
    return (
        <div className="relative group w-full pt-4">
            <div className="absolute -inset-2 bg-gradient-to-r from-primary/30 via-purple-600/20 to-blue-500/30 rounded-[3rem] blur-3xl opacity-30 group-hover:opacity-60 transition duration-1000 group-hover:duration-500 animate-pulse-slow"></div>
            <div className="relative glass-panel rounded-[2.5rem] p-4 flex items-center shadow-[0_30px_60px_-15px_rgba(0,0,0,0.5)] backdrop-blur-3xl border-white/10 ring-1 ring-white/5 transition-all duration-500 group-focus-within:ring-primary/40 group-focus-within:border-primary/40">
                <div className="pl-6 text-primary group-focus-within:scale-110 transition-transform duration-500">
                    <Search className="w-8 h-8" strokeWidth={3} />
                </div>
                <input
                    type="text"
                    placeholder="Busca mundos, autores, historias..."
                    aria-label="Buscar en la biblioteca"
                    className="w-full bg-transparent text-white px-6 py-4 text-xl md:text-2xl placeholder-gray-600 focus:outline-none font-medium selection:bg-primary/30"
                    onClick={onSearchClick}
                    readOnly
                />
                <button
                    onClick={onSearchClick}
                    className="hidden sm:flex bg-primary hover:bg-primary/90 text-white px-10 py-4 rounded-premium-sm text-xs font-black uppercase tracking-[0.2em] transition-all shadow-[0_10px_25px_-5px_rgba(var(--color-primary-rgb),0.4)] active:scale-95 mr-2 group/btn relative overflow-hidden"
                >
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover/btn:animate-shimmer"></div>
                    Buscar
                </button>
            </div>
        </div>
    );
};
