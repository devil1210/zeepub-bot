import React, { createContext, useContext, useState, ReactNode } from 'react';

interface SearchNavState {
    currentPage: number;
    totalPages: number;
    activeSort: string;
    isVisible: boolean;
}

interface SearchNavContextType {
    state: SearchNavState;
    setPageInfo: (currentPage: number, totalPages: number) => void;
    setActiveSort: (sort: string) => void;
    setVisible: (visible: boolean) => void;
    handlePrevPage: () => void;
    handleNextPage: () => void;
    onSortChange: (sort: string) => void;
    // Callbacks set by Search.tsx
    registerCallbacks: (callbacks: {
        onPrevPage: () => void;
        onNextPage: () => void;
        onSortChange: (sort: string) => void;
    }) => void;
}

const SearchNavContext = createContext<SearchNavContextType | undefined>(undefined);

export const SearchNavProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [state, setState] = useState<SearchNavState>({
        currentPage: 1,
        totalPages: 1,
        activeSort: 'a-z',
        isVisible: false
    });

    const [callbacks, setCallbacks] = useState<{
        onPrevPage: () => void;
        onNextPage: () => void;
        onSortChange: (sort: string) => void;
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
