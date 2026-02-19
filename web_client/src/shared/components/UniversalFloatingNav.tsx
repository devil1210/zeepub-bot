import React, { useState, useEffect } from 'react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { useNavigation } from '@shared/contexts/NavigationContext';
import { useTelegram } from '@shared/contexts/TelegramContext';
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
    const { webApp } = useTelegram();
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
    const isTelegram = !!webApp;

    // --- TELEGRAM NATIVE INTEGRATION ---

    // 1. Native Back Button & Header Color
    useEffect(() => {
        if (!webApp) return;

        // Sync header color with our glass theme or Telegram theme
        // We use the bg-color computed by ThemeContext which might be synced or custom
        const rootStyle = getComputedStyle(document.documentElement);
        const bgColor = rootStyle.getPropertyValue('--bg-color').trim();
        if (bgColor) {
            webApp.setHeaderColor(settings.theme === 'amoled' ? '#000000' : bgColor);
            webApp.setBackgroundColor(settings.theme === 'amoled' ? '#000000' : bgColor);
        }

        // Logic for Back Button
        if (contextType !== 'main') {
            webApp.BackButton.show();
            const onBack = () => {
                webApp.HapticFeedback.impactOccurred('light');
                handleBack();
                // If we are at root of a non-main context (like entering 'admin' directly), 
                // handleBack might need to know where to go.
                // But usually handleBack in context simply pops history or goes home.
            };
            webApp.BackButton.onClick(onBack);
            return () => {
                webApp.BackButton.offClick(onBack);
            };
        } else {
            webApp.BackButton.hide();
        }
    }, [webApp, contextType, handleBack, settings.theme]);

    // 2. Native Main Button for Primary Actions
    useEffect(() => {
        if (!webApp) return;

        // Find a primary action button (highlighted) in current state
        const primaryBtn = state.actionButtons?.find(b => b.highlight);

        if (primaryBtn) {
            const btnColor = settings.primaryColor || webApp.themeParams.button_color || '#2481cc';
            const btnTextColor = webApp.themeParams.button_text_color || '#ffffff';

            webApp.MainButton.setParams({
                text: primaryBtn.label.toUpperCase(),
                color: btnColor,
                text_color: btnTextColor,
                is_active: true,
                is_visible: true
            });

            const onMainClick = () => {
                webApp.HapticFeedback.impactOccurred('heavy'); // Stronger feedback for key actions
                primaryBtn.onClick();
            };
            webApp.MainButton.onClick(onMainClick);

            return () => {
                webApp.MainButton.offClick(onMainClick);
                webApp.MainButton.hide();
            };
        } else {
            webApp.MainButton.hide();
        }
    }, [webApp, state.actionButtons, settings.primaryColor]);


    if (!isVisible || contextType === 'none') return null;

    // Render logic for different contexts
    const renderContent = () => {
        switch (contextType) {
            case 'search':
                return (
                    <>
                        {settings.listMode !== 'infinite' && (
                            <>
                                <NavButton
                                    onClick={handlePrevPage}
                                    disabled={currentPage === 1}
                                    icon={ChevronLeft}
                                    label="Anterior"
                                />
                                <NavDivider />
                            </>
                        )}
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
                        {settings.listMode !== 'infinite' ? (
                            <>
                                <NavDivider />
                                <NavButton
                                    onClick={handleNextPage}
                                    disabled={currentPage === totalPages}
                                    icon={ChevronRight}
                                    label="Siguiente"
                                />
                            </>
                        ) : (
                            <>
                                <NavDivider />
                                <NavButton
                                    onClick={() => {
                                        const main = document.querySelector('main');
                                        if (main) main.scrollTo({ top: 0, behavior: 'smooth' });
                                    }}
                                    icon={ArrowUp}
                                    label="Arriba"
                                />
                            </>
                        )}
                    </>
                );

            case 'series':
                return (
                    <>
                        {settings.listMode !== 'infinite' && (
                            <>
                                <NavButton
                                    onClick={handlePrevPage}
                                    disabled={currentPage === 1}
                                    icon={ChevronLeft}
                                    label="Anterior"
                                />
                                <NavDivider />
                            </>
                        )}
                        <NavButton
                            onClick={() => setMenuOpen(!isMenuOpen)}
                            isActive={isMenuOpen}
                            icon={ArrowDownUp}
                            label="Ordenar"
                            highlightOnActive
                        />
                        <NavDivider />
                        {settings.listMode !== 'infinite' && (
                            <>
                                <NavButton
                                    onClick={handleNextPage}
                                    disabled={currentPage === totalPages}
                                    icon={ChevronRight}
                                    label="Siguiente"
                                />
                            </>
                        )}
                        {/* Hide "Volver" on Telegram as we use Native BackButton */}
                        {!isTelegram && (
                            <>
                                <NavDivider />
                                <NavButton
                                    onClick={handleBack}
                                    icon={Reply}
                                    label="Volver"
                                />
                            </>
                        )}
                    </>
                );

            case 'admin':
            case 'ai':
                return (
                    <>
                        {!isTelegram && (
                            <>
                                <NavButton
                                    onClick={handleBack}
                                    icon={ChevronLeft}
                                    label={state.backAction ? "Atrás" : "Salir"}
                                />
                                <NavDivider />
                            </>
                        )}
                        <button
                            onClick={() => setMenuOpen(!isMenuOpen)}
                            className={`flex-[2] flex items-center justify-center gap-2 px-4 py-2 rounded-premium-sm transition-all ${isMenuOpen ? 'text-primary' : 'text-gray-300'} hover:bg-white/5 cursor-pointer`}
                        >
                            <div className="flex flex-col items-center min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className="text-[10px] font-black uppercase tracking-[0.15em] truncate">
                                        {state.customTitle || (contextType === 'ai' ? 'Monitor' : 'Admin')}
                                    </span>
                                    <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-300 ${isMenuOpen ? 'rotate-180' : ''}`} />
                                </div>
                            </div>
                        </button>
                    </>
                );

            case 'book':
                return (
                    <>
                        {!isTelegram && (
                            <>
                                <NavButton
                                    onClick={handleBack}
                                    icon={Reply}
                                    label="Volver"
                                />
                                <NavDivider />
                            </>
                        )}
                        {state.actionButtons ? (
                            state.actionButtons
                                .filter(btn => !isTelegram || !btn.highlight) // Filter out primary if on Telegram (moved to MainButton)
                                .map((btn, idx, arr) => (
                                    <React.Fragment key={btn.id}>
                                        <NavButton
                                            onClick={btn.onClick}
                                            disabled={btn.disabled}
                                            icon={btn.icon}
                                            label={btn.label}
                                            highlightOnActive={btn.highlight}
                                        />
                                        {idx < arr.length - 1 && <NavDivider />}
                                    </React.Fragment>
                                ))
                        ) : (
                            <NavButton
                                onClick={handleHome}
                                icon={Home}
                                label="Inicio"
                            />
                        )}
                    </>
                );

            case 'settings':
                return (
                    <>
                        {!isTelegram && (
                            <>
                                <NavButton
                                    onClick={handleBack}
                                    icon={ChevronLeft}
                                    label="Volver"
                                />
                                <NavDivider />
                            </>
                        )}
                        <NavButton
                            onClick={() => state.actionButtons?.find(b => b.id === 'restore')?.onClick()}
                            icon={RotateCcw}
                            label="Restaurar"
                        />
                        {/* "Guardar" moved to MainButton on Telegram */}
                        {!isTelegram && (
                            <>
                                <NavDivider />
                                <NavButton
                                    onClick={() => state.actionButtons?.find(b => b.id === 'save')?.onClick()}
                                    icon={Save}
                                    label="Guardar"
                                    highlightOnActive
                                />
                            </>
                        )}
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
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-3 w-[90%] max-w-xl md:w-auto md:min-w-[600px] px-0 animate-in slide-in-from-bottom-4 duration-300 floating-nav-container">
            {/* Contextual Menus */}
            {isMenuOpen && (contextType === 'search' || contextType === 'series') && (
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
                                onClick={() => {
                                    webApp?.HapticFeedback?.impactOccurred('light');
                                    handleSortChange(option.id);
                                }}
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

            {isMenuOpen && (contextType === 'admin' || contextType === 'ai') && state.actionButtons && (
                <div
                    className="glass-panel rounded-premium p-3 border border-white/10 shadow-2xl animate-in slide-in-from-bottom-2 fade-in duration-200"
                    style={{
                        background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                        backdropFilter: `blur(${settings.glassBlur}px)`,
                        WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
                    }}
                >
                    <div className="grid grid-cols-2 gap-2">
                        {state.actionButtons.map((btn) => (
                            <button
                                key={btn.id}
                                onClick={() => {
                                    webApp?.HapticFeedback?.impactOccurred('light');
                                    btn.onClick();
                                    setMenuOpen(false);
                                }}
                                className={`flex items-center gap-3 px-3 py-3 rounded-premium-sm transition-all border ${btn.highlight
                                    ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20'
                                    : 'bg-white/5 text-gray-400 border-transparent hover:bg-white/10 hover:text-white'
                                    }`}
                            >
                                <btn.icon className="w-4 h-4 flex-shrink-0" />
                                <span className="text-[9px] font-black uppercase tracking-widest leading-tight text-left">{btn.label}</span>
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
}> = ({ onClick, isActive, disabled, icon: Icon, label, highlightOnActive }) => {
    const { webApp } = useTelegram();

    const handleClick = () => {
        if (disabled) return;
        webApp?.HapticFeedback?.impactOccurred(isActive ? 'light' : 'medium');
        onClick?.();
    };

    return (
        <button
            onClick={handleClick}
            disabled={disabled}
            className={`flex-1 flex flex-col items-center justify-center py-2 rounded-premium-sm transition-all duration-500 relative z-10 ${disabled ? 'opacity-30 cursor-not-allowed' : 'hover:scale-105 active:scale-90 hover:text-black dark:hover:text-white'} ${isActive ? 'text-primary' : 'text-gray-500'}`}
        >
            <div
                key={label} // Trigger animation on label/button change
                className={`p-1.5 rounded-full transition-all duration-500 animate-in zoom-in-75 fade-in duration-500 ${isActive && highlightOnActive ? 'bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)] translate-y-[-2px]' : ''}`}
            >
                <Icon className={`w-4 h-4 ${(isActive && highlightOnActive) ? 'text-white' : ''}`} strokeWidth={isActive ? 2.5 : 2} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest mt-1 opacity-80 group-hover:opacity-100 transition-opacity duration-500">{label}</span>
            {isActive && !highlightOnActive && (
                <div className="absolute bottom-1 w-1 h-1 bg-primary rounded-full shadow-[0_0_8px_rgba(var(--primary-rgb),0.8)] animate-in fade-in zoom-in duration-500"></div>
            )}
        </button>
    );
};

const NavDivider = () => <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>;
