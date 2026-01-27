import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { useNavigation } from '../contexts/NavigationContext';
import {
    ChevronLeft,
    ChevronRight,
    ArrowDownUp,
    Home,
    Download,
    Star,
    Calendar,
    Clock,
    ArrowUp,
    Library,
    Settings,
    LayoutGrid,
    Reply,
    Check,
    RefreshCw,
    RotateCcw,
    Save,
    Layers,
    ChevronDown
} from 'lucide-react';

const sortOptions = [
    { id: 'a-z', label: 'A-Z', icon: ArrowUp },
    { id: 'z-a', label: 'Z-A', icon: ArrowUp },
    { id: 'downloads', label: 'DESCARGAS', icon: Download },
    { id: 'rating', label: 'VALORACIÓN', icon: Star },
    { id: 'added', label: 'AÑADIDO', icon: Calendar },
    { id: 'updated', label: 'ACTUALIZADO', icon: Clock },
];

export const UniversalFloatingNav: React.FC<{ activeTab?: string; onTabChange?: (tab: string) => void }> = ({ activeTab, onTabChange }) => {
    const { settings } = useTheme();
    const {
        state,
        handlePrevPage,
        handleNextPage,
        handleSortChange,
        handleHome,
        handleBack,
        setMenuOpen
    } = useNavigation();

    const { contextType, isMenuOpen, currentPage, totalPages, activeSort, isVisible } = state;

    if (!isVisible || contextType === 'none') return null;

    // Render logic for different contexts
    const renderContent = () => {
        switch (contextType) {
            case 'search':
                return (
                    <>
                        <NavButton
                            onClick={handlePrevPage}
                            disabled={currentPage === 1}
                            icon={ChevronLeft}
                            label="Anterior"
                        />
                        <NavDivider />
                        <NavButton
                            onClick={() => setMenuOpen(!isMenuOpen)}
                            isActive={isMenuOpen}
                            icon={ArrowDownUp}
                            label="Ordenar"
                            highlightOnActive
                        />
                        <NavDivider />
                        <NavButton
                            onClick={handleHome}
                            icon={Home}
                            label="Inicio"
                        />
                        <NavDivider />
                        <NavButton
                            onClick={handleNextPage}
                            disabled={currentPage === totalPages}
                            icon={ChevronRight}
                            label="Siguiente"
                        />
                    </>
                );

            case 'series':
                return (
                    <>
                        <NavButton
                            onClick={handlePrevPage}
                            disabled={currentPage === 1}
                            icon={ChevronLeft}
                            label="Anterior"
                        />
                        <NavDivider />
                        <NavButton
                            onClick={() => setMenuOpen(!isMenuOpen)}
                            isActive={isMenuOpen}
                            icon={ArrowDownUp}
                            label="Ordenar"
                            highlightOnActive
                        />
                        <NavDivider />
                        <NavButton
                            onClick={handleBack}
                            icon={Reply}
                            label="Volver"
                        />
                        <NavDivider />
                        <NavButton
                            onClick={handleNextPage}
                            disabled={currentPage === totalPages}
                            icon={ChevronRight}
                            label="Siguiente"
                        />
                    </>
                );

            case 'admin':
                return (
                    <>
                        <NavButton
                            onClick={handleBack}
                            icon={ChevronLeft}
                            label={state.backAction ? "Atrás" : "Salir"}
                        />
                        <NavDivider />
                        <button
                            onClick={() => setMenuOpen(!isMenuOpen)}
                            className={`flex-[2] flex items-center justify-center gap-2 px-4 py-2 rounded-premium-sm transition-all ${isMenuOpen ? 'text-primary' : 'text-gray-300'} hover:bg-white/5 cursor-pointer`}
                        >
                            <div className="flex flex-col items-center min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className="text-[10px] font-black uppercase tracking-[0.15em] truncate">
                                        {state.customTitle || 'Admin'}
                                    </span>
                                    <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-300 ${isMenuOpen ? 'rotate-180' : ''}`} />
                                </div>
                            </div>
                        </button>
                        <NavDivider />
                        <div className="flex-1 flex items-center justify-center gap-1">
                            <NavButton onClick={() => window.location.reload()} icon={RefreshCw} label="Sync" />
                        </div>
                    </>
                );

            case 'main':
            default:
                return (
                    <>
                        <NavButton
                            isActive={activeTab === 'dashboard'}
                            onClick={() => onTabChange?.('dashboard')}
                            icon={Home}
                            label="Inicio"
                        />
                        <NavDivider />
                        <NavButton
                            isActive={activeTab === 'search'}
                            onClick={() => onTabChange?.('search')}
                            icon={LayoutGrid}
                            label="Catálogo"
                        />
                        <NavDivider />
                        <NavButton
                            isActive={activeTab === 'library'}
                            onClick={() => onTabChange?.('library')}
                            icon={Library}
                            label="Mi Lib"
                        />
                        <NavDivider />
                        <NavButton
                            isActive={activeTab === 'settings'}
                            onClick={() => onTabChange?.('settings')}
                            icon={Settings}
                            label="Ajustes"
                        />
                    </>
                );
        }
    };

    return (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-3 w-[90%] max-w-xl md:w-auto md:min-w-[600px] px-0 animate-in slide-in-from-bottom-4 duration-300">
            {/* Contextual Menus */}
            {isMenuOpen && contextType === 'search' && (
                <div
                    className="glass-panel rounded-premium p-3 border border-white/10 shadow-2xl animate-in slide-in-from-bottom-2 fade-in duration-200"
                    style={{
                        background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                        backdropFilter: `blur(${settings.glassBlur}px)`,
                        WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
                    }}
                >
                    <div className="grid grid-cols-3 gap-2">
                        {sortOptions.map((option) => (
                            <button
                                key={option.id}
                                onClick={() => handleSortChange(option.id)}
                                className={`flex flex-col items-center gap-1 px-2 py-2.5 rounded-premium-sm text-[9px] font-black uppercase tracking-widest transition-all border ${activeSort === option.id
                                    ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20'
                                    : 'bg-white/5 text-gray-400 border-transparent hover:bg-white/10 hover:text-white'
                                    }`}
                            >
                                <option.icon className={`w-4 h-4 ${option.id === 'z-a' ? 'rotate-180' : ''}`} />
                                <span className="text-center leading-tight">{option.label}</span>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Main Bar */}
            <div
                className="glass-panel rounded-premium p-1.5 border border-black/10 dark:border-white/10 shadow-2xl flex items-center justify-between overflow-hidden"
                style={{
                    background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                    backdropFilter: `blur(${settings.glassBlur}px)`,
                    WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
                }}
            >
                {renderContent()}
            </div>
        </div>
    );
};

const NavButton: React.FC<{
    onClick?: () => void;
    isActive?: boolean;
    disabled?: boolean;
    icon: any;
    label: string;
    highlightOnActive?: boolean;
}> = ({ onClick, isActive, disabled, icon: Icon, label, highlightOnActive }) => (
    <button
        onClick={onClick}
        disabled={disabled}
        className={`flex-1 flex flex-col items-center justify-center py-2 rounded-premium-sm transition-all duration-300 relative z-10 ${disabled ? 'opacity-30 cursor-not-allowed' : 'hover:text-black dark:hover:text-white'} ${isActive ? 'text-primary' : 'text-gray-500'}`}
    >
        <div className={`p-1.5 rounded-full transition-all duration-300 ${isActive && highlightOnActive ? 'bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)] translate-y-[-2px]' : ''}`}>
            <Icon className={`w-4 h-4 ${(isActive && highlightOnActive) ? 'text-white' : ''}`} strokeWidth={isActive ? 2.5 : 2} />
        </div>
        <span className="text-[9px] font-black uppercase tracking-widest mt-1">{label}</span>
        {isActive && !highlightOnActive && (
            <div className="absolute bottom-1 w-1 h-1 bg-primary rounded-full shadow-[0_0_8px_rgba(var(--primary-rgb),0.8)]"></div>
        )}
    </button>
);

const NavDivider = () => <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>;
