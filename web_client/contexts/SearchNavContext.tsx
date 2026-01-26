import React, { createContext, useContext, useState, ReactNode } from 'react';

interface SearchNavState {
    // Pagination state
    currentPage: number;
    totalPages: number;
    activeSort: string;
    isVisible: boolean;
    // Header state
    searchTerm: string;
    selectedScope: string;
    viewMode: 'list' | 'grid';
    loading: boolean;
}

interface SearchNavContextType {
    state: SearchNavState;
    setPageInfo: (currentPage: number, totalPages: number) => void;
    setActiveSort: (sort: string) => void;
    setVisible: (visible: boolean) => void;
    handlePrevPage: () => void;
    handleNextPage: () => void;
    onSortChange: (sort: string) => void;
    // Header methods
    setSearchTerm: (term: string) => void;
    setSelectedScope: (scope: string) => void;
    setViewMode: (mode: 'list' | 'grid') => void;
    setLoading: (loading: boolean) => void;
    openScopeModal: () => void;
    // Callbacks set by Search.tsx
    registerCallbacks: (callbacks: {
        onPrevPage: () => void;
        onNextPage: () => void;
        onSortChange: (sort: string) => void;
        onSearchChange: (term: string) => void;
        onScopeClick: () => void;
        onViewModeChange: (mode: 'list' | 'grid') => void;
    }) => void;
}

const SearchNavContext = createContext<SearchNavContextType | undefined>(undefined);

export const SearchNavProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [state, setState] = useState<SearchNavState>({
        currentPage: 1,
        totalPages: 1,
        activeSort: 'a-z',
        isVisible: false,
        searchTerm: '',
        selectedScope: 'TODOS',
        viewMode: 'list',
        loading: false
    });

    const [callbacks, setCallbacks] = useState<{
        onPrevPage: () => void;
        onNextPage: () => void;
        onSortChange: (sort: string) => void;
        onSearchChange: (term: string) => void;
        onScopeClick: () => void;
        onViewModeChange: (mode: 'list' | 'grid') => void;
    } | null>(null);

    const setPageInfo = (currentPage: number, totalPages: number) => {
        setState(prev => ({ ...prev, currentPage, totalPages }));
    };

    const setActiveSort = (sort: string) => {
        setState(prev => ({ ...prev, activeSort: sort }));
    };

    const setVisible = (visible: boolean) => {
        setState(prev => ({ ...prev, isVisible: visible }));
    };

    const setSearchTerm = (term: string) => {
        setState(prev => ({ ...prev, searchTerm: term }));
        callbacks?.onSearchChange?.(term);
    };

    const setSelectedScope = (scope: string) => {
        setState(prev => ({ ...prev, selectedScope: scope }));
    };

    const setViewMode = (mode: 'list' | 'grid') => {
        setState(prev => ({ ...prev, viewMode: mode }));
        callbacks?.onViewModeChange?.(mode);
    };

    const setLoading = (loading: boolean) => {
        setState(prev => ({ ...prev, loading }));
    };

    const openScopeModal = () => {
        callbacks?.onScopeClick?.();
    };

    const handlePrevPage = () => {
        callbacks?.onPrevPage?.();
    };

    const handleNextPage = () => {
        callbacks?.onNextPage?.();
    };

    const onSortChange = (sort: string) => {
        callbacks?.onSortChange?.(sort);
        setActiveSort(sort);
    };

    const registerCallbacks = (cbs: {
        onPrevPage: () => void;
        onNextPage: () => void;
        onSortChange: (sort: string) => void;
        onSearchChange: (term: string) => void;
        onScopeClick: () => void;
        onViewModeChange: (mode: 'list' | 'grid') => void;
    }) => {
        setCallbacks(cbs);
    };

    return (
        <SearchNavContext.Provider value={{
            state,
            setPageInfo,
            setActiveSort,
            setVisible,
            handlePrevPage,
            handleNextPage,
            onSortChange,
            setSearchTerm,
            setSelectedScope,
            setViewMode,
            setLoading,
            openScopeModal,
            registerCallbacks
        }}>
            {children}
        </SearchNavContext.Provider>
    );
};

export const useSearchNav = () => {
    const context = useContext(SearchNavContext);
    if (context === undefined) {
        throw new Error('useSearchNav must be used within a SearchNavProvider');
    }
    return context;
};

