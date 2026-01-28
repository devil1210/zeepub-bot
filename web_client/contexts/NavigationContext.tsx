import React, { createContext, useContext, useState, ReactNode } from 'react';

export type NavContextType = 'main' | 'search' | 'series' | 'book' | 'admin' | 'ai' | 'settings' | 'none';

export interface NavActionButton {
    id: string;
    label: string;
    icon: any;
    onClick: () => void;
    highlight?: boolean;
    disabled?: boolean;
}

export interface NavigationState {
    contextType: NavContextType;
    isVisible: boolean;
    isMenuOpen: boolean;
    // Common state
    activeSort: string;
    currentPage: number;
    totalPages: number;
    // Header specific (formerly in SearchNav)
    searchTerm: string;
    selectedScope: string;
    viewMode: 'list' | 'grid';
    loading: boolean;
    // Custom labels/actions
    customTitle?: string;
    backAction?: () => void;
    homeAction?: () => void;
    // History stack management
    historyStack: string[];
}

interface NavigationContextType {
    state: NavigationState;
    setContextType: (type: NavContextType) => void;
    setVisible: (visible: boolean) => void;
    setMenuOpen: (open: boolean) => void;
    setPageInfo: (currentPage: number, totalPages: number) => void;
    setActiveSort: (sort: string) => void;
    setSearchTerm: (term: string) => void;
    setSelectedScope: (scope: string) => void;
    setViewMode: (mode: 'list' | 'grid') => void;
    setLoading: (loading: boolean) => void;
    setCustomActions: (actions: { back?: () => void; home?: () => void; title?: string; buttons?: NavActionButton[] }) => void;

    // Stack management
    pushHistory: (path: string) => void;
    popHistory: () => void;
    resetHistory: () => void;

    // Callbacks for the UI component to trigger
    handlePrevPage: () => void;
    handleNextPage: () => void;
    handleSortChange: (sort: string) => void;
    handleHome: () => void;
    handleBack: () => void;
    handleScopeClick: () => void;

    // Registration for pages to hook into the UI buttons
    registerCallbacks: (callbacks: {
        onPrevPage?: () => void;
        onNextPage?: () => void;
        onSortChange?: (sort: string) => void;
        onSearchChange?: (term: string) => void;
        onScopeClick?: () => void;
        onViewModeChange?: (mode: 'list' | 'grid') => void;
        onHome?: () => void;
        onBack?: () => void;
    }) => () => void;
}

const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

export const NavigationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [state, setState] = useState<NavigationState>({
        contextType: 'main',
        isVisible: true,
        isMenuOpen: false,
        activeSort: 'a-z',
        currentPage: 1,
        totalPages: 1,
        searchTerm: '',
        selectedScope: 'TODOS',
        viewMode: 'list',
        loading: false,
        historyStack: ['/'] // Initial root
    });

    const [callbacks, setCallbacks] = useState<any>(null);

    const pushHistory = React.useCallback((path: string) => {
        console.log('🔍 [DEBUG] NavigationContext.pushHistory called', {
            path,
            currentStack: state.historyStack
        });
        
        setState(prev => {
            // Avoid dupes if just refreshing or same path
            if (prev.historyStack[prev.historyStack.length - 1] === path) {
                console.log('🚫 [DEBUG] Duplicate path detected, not pushing');
                return prev;
            }
            const newStack = [...prev.historyStack, path];
            console.log('✅ [DEBUG] Pushed to history stack', {
                newStack,
                stackLength: newStack.length
            });
            return { ...prev, historyStack: newStack };
        });
    }, [state.historyStack]);

    const popHistory = React.useCallback(() => {
        console.log('🔍 [DEBUG] NavigationContext.popHistory called', {
            currentStack: state.historyStack
        });
        
        setState(prev => {
            if (prev.historyStack.length <= 1) {
                console.log('🚫 [DEBUG] Cannot pop: stack length <= 1');
                return prev;
            }
            const newStack = prev.historyStack.slice(0, -1);
            console.log('✅ [DEBUG] Popped from history stack', {
                newStack,
                stackLength: newStack.length
            });
            return { ...prev, historyStack: newStack };
        });
    }, [state.historyStack]);

    const resetHistory = React.useCallback(() => {
        setState(prev => ({ ...prev, historyStack: ['/'] }));
    }, []);

    const setContextType = React.useCallback((contextType: NavContextType) => {
        setState(prev => ({ ...prev, contextType, isMenuOpen: false }));
    }, []);

    const setVisible = React.useCallback((isVisible: boolean) => {
        setState(prev => ({ ...prev, isVisible }));
    }, []);

    const setMenuOpen = React.useCallback((isMenuOpen: boolean) => {
        setState(prev => ({ ...prev, isMenuOpen }));
    }, []);

    const setPageInfo = React.useCallback((currentPage: number, totalPages: number) => {
        setState(prev => ({ ...prev, currentPage, totalPages }));
    }, []);

    const setActiveSort = React.useCallback((activeSort: string) => {
        setState(prev => ({ ...prev, activeSort }));
    }, []);

    const setSearchTerm = React.useCallback((term: string) => {
        setState(prev => ({ ...prev, searchTerm: term }));
        // callbacks refer to a state, so we check it
    }, []);

    const setSelectedScope = React.useCallback((selectedScope: string) => {
        setState(prev => ({ ...prev, selectedScope }));
    }, []);

    const setViewMode = React.useCallback((viewMode: 'list' | 'grid') => {
        setState(prev => ({ ...prev, viewMode }));
    }, []);

    const setLoading = React.useCallback((loading: boolean) => {
        setState(prev => ({ ...prev, loading }));
    }, []);

    const setCustomActions = React.useCallback((actions: { back?: () => void; home?: () => void; title?: string; buttons?: NavActionButton[] }) => {
        setState(prev => ({
            ...prev,
            backAction: actions.back,
            homeAction: actions.home,
            customTitle: actions.title,
            actionButtons: actions.buttons
        }));
    }, []);

    const handlePrevPage = React.useCallback(() => callbacks?.onPrevPage?.(), [callbacks]);
    const handleNextPage = React.useCallback(() => callbacks?.onNextPage?.(), [callbacks]);
    const handleSortChange = React.useCallback((sort: string) => {
        callbacks?.onSortChange?.(sort);
        setActiveSort(sort);
    }, [callbacks, setActiveSort]);
    const handleHome = React.useCallback(() => callbacks?.onHome?.(), [callbacks]);
    const handleBack = React.useCallback(() => callbacks?.onBack?.(), [callbacks]);
    const handleScopeClick = React.useCallback(() => callbacks?.onScopeClick?.(), [callbacks]);

    const registerCallbacks = React.useCallback((cbs: any) => {
        setCallbacks(cbs);
        return () => setCallbacks(null);
    }, []);

    const value = React.useMemo(() => ({
        state,
        setContextType,
        setVisible,
        setMenuOpen,
        setPageInfo,
        setActiveSort,
        setSearchTerm,
        setSelectedScope,
        setViewMode,
        setLoading,
        setCustomActions,
        pushHistory,
        popHistory,
        resetHistory,
        handlePrevPage,
        handleNextPage,
        handleSortChange,
        handleHome,
        handleBack,
        handleScopeClick,
        registerCallbacks
    }), [
        state,
        setContextType,
        setVisible,
        setMenuOpen,
        setPageInfo,
        setActiveSort,
        setSearchTerm,
        setSelectedScope,
        setViewMode,
        setLoading,
        setCustomActions,
        pushHistory,
        popHistory,
        resetHistory,
        handlePrevPage,
        handleNextPage,
        handleSortChange,
        handleHome,
        handleBack,
        handleScopeClick,
        registerCallbacks
    ]);

    return (
        <NavigationContext.Provider value={value}>
            {children}
        </NavigationContext.Provider>
    );
};

export const useNavigation = () => {
    const context = useContext(NavigationContext);
    if (context === undefined) {
        throw new Error('useNavigation must be used within a NavigationProvider');
    }
    return context;
};
