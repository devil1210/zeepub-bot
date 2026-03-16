import React from 'react';

interface SearchPaginationProps {
    currentPage: number;
    totalPages: number;
    totalResults: number;
}

export const SearchPagination: React.FC<SearchPaginationProps> = ({ currentPage, totalPages, totalResults }) => {
    return (
        <div className="flex justify-center p-6 mb-8 mt-4">
            <div className="px-6 py-2.5 rounded-premium-full glass-panel border border-white/5 shadow-premium text-[11px] font-black uppercase tracking-[0.2em] text-gray-400">
                Página <span className="text-primary">{currentPage}</span> de <span className="text-white">{totalPages}</span> • <span className="text-gray-300">{totalResults}</span> Resultados
            </div>
        </div>
    );
};
