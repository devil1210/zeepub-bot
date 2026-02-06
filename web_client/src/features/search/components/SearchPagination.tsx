import React from 'react';

interface SearchPaginationProps {
    currentPage: number;
    totalPages: number;
    totalResults: number;
}

export const SearchPagination: React.FC<SearchPaginationProps> = ({ currentPage, totalPages, totalResults }) => {
    return (
        <div className="text-center py-4 text-xs text-gray-500 font-medium">
            Página {currentPage} de {totalPages} • {totalResults} Resultados
        </div>
    );
};
