import React, { useState, useEffect } from 'react';
import {
    ArrowLeft,
    Save,
    Info,
    Gauge,
    Stars,
    Palette,
    History,
    Eye,
    Loader2,
    Home,
    RotateCcw,
    Layers,
    ChevronDown,
    Zap,
    Layout,
    Download,
    BookOpen,
    Shield,
    Library,
    Upload
} from 'lucide-react';
import { useTheme, adjustBrightness } from '../contexts/ThemeContext';
import { api } from '../src/services/api';

interface TierConfigurationProps {
    tierName: string;
    tierColor: string;
    onBack: () => void;
    onSave?: (config: TierConfig) => void;
    onNavigate?: (page: string, ...args: any[]) => void;
    // Callbacks for parent navigation control
    onSavingChange?: (saving: boolean) => void;
    onCanUndoChange?: (canUndo: boolean) => void;
    onCanApplyChange?: (canApply: boolean) => void;
    onUndoRef?: (undoFn: () => void) => void;
    onSaveRef?: (saveFn: () => Promise<void>) => void;
}

interface TierConfig {
    name: string;
    icon: string;
    color: string;
    dailyDownloads: number;
    maxConcurrent: number;
    priorityRequests: boolean;
    earlyAccess: boolean;
    customThemes: boolean;
    showRecommendations: boolean;
    primaryColor: string;
    glassOpacity: number;
    navOpacity?: number;
    accentOpacity?: number;
    glassBlur?: number;
    coverWidth?: number;
    theme?: 'dark' | 'amoled' | 'light';
    fontSize?: number;
    canDownload: boolean;
    canRead: boolean;
    hasLibraryAccess: boolean;
    canRequestBooks: boolean;
    backgroundColor: string;
    cardColor: string;
    bannerContentOffset: number;
    forceSettings: boolean;
    canUploadEpub: boolean;
    defaultThemeId?: number;
}

interface LevelOption {
    id: string;
    name: string;
    color: string;
}

export const TierConfiguration: React.FC<TierConfigurationProps> = ({
    tierName,
    tierColor,
    onBack,
    onSave,
    onNavigate,
    // Parent navigation control callbacks
    onSavingChange,
    onCanUndoChange,
    onCanApplyChange,
    onUndoRef,
    onSaveRef
}) => {
    const { settings, updateSettings } = useTheme();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [allLevels, setAllLevels] = useState<LevelOption[]>([]);
    const [selectedTierName, setSelectedTierName] = useState(tierName);

    const [config, setConfig] = useState<TierConfig>({
        name: tierName,
        icon: 'verified',
        color: tierColor,
        dailyDownloads: 50,
        maxConcurrent: 3,
        priorityRequests: true,
        earlyAccess: true,
        customThemes: false,
        showRecommendations: false,
        primaryColor: settings.primaryColor,
        glassOpacity: 0.7,
        navOpacity: settings.navOpacity,
        accentOpacity: settings.accentOpacity,
        glassBlur: settings.glassBlur,
        coverWidth: settings.coverWidth,
        theme: settings.theme,
        fontSize: settings.fontSize,
        canDownload: true,
        canRead: true,
        hasLibraryAccess: true,
        canRequestBooks: true,
        canUploadEpub: false,
        backgroundColor: settings.backgroundColor,
        cardColor: settings.cardColor,
        bannerContentOffset: settings.bannerContentOffset,
        forceSettings: false
    });

    const [originalConfig, setOriginalConfig] = useState<TierConfig | null>(null);

    const [themes, setThemes] = useState<any[]>([]);

    // Initial load: Fetch all levels and themes
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [levelsRes, themesRes] = await Promise.all([
                    api.getAdminTiers(),
                    api.getAvailableThemes()
                ]);

                if (levelsRes.levels && Array.isArray(levelsRes.levels)) {
                    setAllLevels([
                        { id: 'global', name: 'Global', color: '#ffffff' },
                        ...levelsRes.levels.map((l: any) => ({
                            id: String(l.id),
                            name: l.name,
                            color: l.color || '#6b7280'
                        }))
                    ]);
                } else {
                    setAllLevels([{ id: 'global', name: 'Global', color: '#ffffff' }]);
                }

                if (themesRes.success && Array.isArray(themesRes.themes)) {
                    setThemes(themesRes.themes);
                }
            } catch (err) {
                console.error('Error fetching data:', err);
            }
        };
        fetchData();
    }, []);

    // Load tier config whenever selectedTierName changes
    useEffect(() => {
        const loadTierConfig = async () => {
            try {
                setLoading(true);
                const res = await api.getTierConfig(selectedTierName);
                if (res.success && res.tier) {
                    const newConfig = {
                        name: res.tier.name || selectedTierName,
                        icon: res.tier.icon || 'verified',
                        color: res.tier.color || tierColor,
                        dailyDownloads: res.tier.dailyDownloads ?? 50,
                        maxConcurrent: res.tier.maxConcurrent ?? 3,
                        priorityRequests: res.tier.priorityRequests ?? false,
                        earlyAccess: res.tier.earlyAccess ?? false,
                        customThemes: res.tier.customThemes ?? false,
                        showRecommendations: res.tier.showRecommendations ?? false,
                        primaryColor: res.tier.primaryColor || settings.primaryColor,
                        glassOpacity: res.tier.glassOpacity ?? 0.7,
                        navOpacity: res.tier.navOpacity ?? settings.navOpacity,
                        accentOpacity: res.tier.accentOpacity ?? settings.accentOpacity,
                        glassBlur: res.tier.glassBlur ?? settings.glassBlur,
                        coverWidth: res.tier.coverWidth ?? settings.coverWidth,
                        theme: res.tier.uiTheme || settings.theme,
                        fontSize: res.tier.uiFontSize || settings.fontSize,
                        canDownload: res.tier.canDownload ?? true,
                        canRead: res.tier.canRead ?? true,
                        hasLibraryAccess: res.tier.hasLibraryAccess ?? true,
                        canRequestBooks: res.tier.canRequestBooks ?? true,
                        backgroundColor: res.tier.backgroundColor || settings.backgroundColor,
                        cardColor: res.tier.cardColor || settings.cardColor,
                        bannerContentOffset: res.tier.bannerContentOffset ?? settings.bannerContentOffset,
                        forceSettings: res.tier.forceSettings ?? false,
                        canUploadEpub: res.tier.canUploadEpub ?? false,
                        defaultThemeId: res.tier.defaultThemeId
                    };
                    setConfig(newConfig);
                    setOriginalConfig(newConfig);
                }
            } catch (err: any) {
                console.error('Error loading tier config:', err);
            } finally {
                setLoading(false);
            }
        };
        loadTierConfig();
    }, [selectedTierName]);

    // Notify parent of saving state changes
    useEffect(() => {
        onSavingChange?.(saving);
    }, [saving, onSavingChange]);

    // Notify parent of undo/apply availability
    useEffect(() => {
        const hasChanges = JSON.stringify(config) !== JSON.stringify(originalConfig);
        onCanUndoChange?.(hasChanges);
        onCanApplyChange?.(hasChanges);
    }, [config, originalConfig, onCanUndoChange, onCanApplyChange]);

    // Expose undo/save functions to parent via refs
    useEffect(() => {
        onUndoRef?.(handleUndo);
    }, [onUndoRef]);

    useEffect(() => {
        onSaveRef?.(handleSave);
    }, [onSaveRef]);

    const handleSave = async () => {
        try {
            setSaving(true);
            setError(null);
            const res = await api.saveTierConfig(config);
            if (res.success) {
                onSave?.(config);
                // After save, we stay on the page but update original
                setOriginalConfig(config);
            } else {
                setError(res.message || 'Error al guardar');
            }
        } catch (err: any) {
            setError(err.message || 'Error al guardar configuración');
        } finally {
            setSaving(false);
        }
    };

    const handleUndo = () => {
        if (originalConfig) {
            setConfig(originalConfig);
        }
    };

    const Toggle: React.FC<{ checked: boolean; onChange: (val: boolean) => void }> = ({ checked, onChange }) => (
        <button
            type="button"
            onClick={() => onChange(!checked)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${checked ? 'bg-primary shadow-[0_0_8px_rgba(var(--primary-rgb),0.4)]' : 'bg-gray-700'
                }`}
        >
            <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'
                    }`}
            />
        </button>
    );

    if (loading && !allLevels.length) {
        return (
            <div className="flex items-center justify-center h-full min-h-[400px]">
                <div className="flex flex-col items-center gap-4">
                    <Loader2 className="w-10 h-10 text-primary animate-spin" />
                    <p className="text-gray-400 text-sm">Cargando niveles...</p>
                </div>
            </div>
        );
    }

    return (
        <>
            <div className="max-w-[1200px] mx-auto w-full flex flex-col gap-8 animate-in fade-in duration-300 px-1 pb-32">
                {/* Error Alert */}
                {error && (
                    <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                        {error}
                    </div>
                )}

                {/* Header with Selector & Save */}
                <div className="flex flex-col gap-10">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                        <div className="flex flex-col">
                            <h2 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.4em] mb-2 px-1">Editar Nivel</h2>
                            <div className="flex items-center gap-3 bg-white/5 p-2 rounded-[2.5rem] border border-white/5 overflow-x-auto no-scrollbar shadow-inner max-w-full">
                                {allLevels.map(lvl => (
                                    <button
                                        key={lvl.id}
                                        onClick={() => setSelectedTierName(lvl.name)}
                                        className={`
                                            flex items-center gap-3 px-6 py-4 rounded-[2rem] text-[11px] font-black uppercase tracking-[0.2em] transition-all duration-500 whitespace-nowrap
                                            ${selectedTierName === lvl.name
                                                ? 'bg-primary text-white shadow-2xl shadow-primary/40 scale-100 ring-[6px] ring-primary/10'
                                                : 'text-gray-500 hover:text-gray-300 hover:bg-white/5 scale-95 opacity-60'}
                                        `}
                                    >
                                        <div
                                            className="w-2.5 h-2.5 rounded-full shadow-[0_0_12px_currentColor]"
                                            style={{ backgroundColor: lvl.color, color: lvl.color }}
                                        />
                                        {lvl.name}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Summary Stats / Status */}
                        <div className="hidden xl:flex items-center gap-6">
                            <div className="flex flex-col items-end">
                                <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest">Estado Global</span>
                                <span className="text-emerald-500 font-black flex items-center gap-2 mt-1">
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                    SINCRONIZADO
                                </span>
                            </div>
                            <div className="w-px h-10 bg-white/5" />
                            <div className="flex flex-col items-end">
                                <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest">Configuraci&oacute;n</span>
                                <span className="text-white font-black mt-1 uppercase tracking-tighter">Producci&oacute;n</span>
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={handleSave}
                        disabled={saving || (JSON.stringify(config) === JSON.stringify(originalConfig))}
                        className="w-full h-[84px] rounded-[2.5rem] font-black text-sm uppercase tracking-[0.4em] flex items-center justify-center gap-5 transition-all
                        bg-white/5 text-gray-400 border-2 border-white/5 hover:bg-primary hover:text-white hover:border-primary shadow-2xl active:scale-[0.98] disabled:opacity-20 disabled:grayscale disabled:scale-100 group overflow-hidden relative"
                    >
                        <div className="flex items-center gap-4 relative z-10">
                            {saving ? <Loader2 className="w-6 h-6 animate-spin" /> : <Save className="w-6 h-6 group-hover:scale-110 transition-transform" />}
                            GUARDAR CAMBIOS
                        </div>
                        <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-white/5 to-primary/0 -translate-x-full group-hover:animate-shimmer" />
                    </button>
                </div>

                {/* Config Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

                    {/* Left Side: General & Limits */}
                    <div className="lg:col-span-4 space-y-6">
                        {/* General Info */}
                        <div className="glass-panel p-6 rounded-2xl flex flex-col gap-6 border border-white/5 shadow-lg">
                            <div className="flex items-center gap-3 border-b border-white/5 pb-4">
                                <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                                    <Zap className="w-5 h-5" />
                                </div>
                                <h3 className="text-white font-bold">General & Access</h3>
                            </div>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-2">Nombre del Rango</label>
                                    <input
                                        type="text"
                                        value={config.name}
                                        onChange={(e) => setConfig({ ...config, name: e.target.value })}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white font-bold focus:ring-1 focus:ring-primary focus:border-primary transition-all"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-2">Icono (Key)</label>
                                        <input
                                            type="text"
                                            value={config.icon}
                                            onChange={(e) => setConfig({ ...config, icon: e.target.value })}
                                            className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white font-mono focus:ring-1 focus:ring-primary focus:border-primary transition-all"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-2">Color Badge</label>
                                        <div className="flex items-center gap-3 p-1.5 bg-black/40 border border-white/10 rounded-xl">
                                            <input
                                                type="color"
                                                value={config.color}
                                                onChange={(e) => setConfig({ ...config, color: e.target.value })}
                                                className="size-8 bg-transparent border-none p-0 cursor-pointer rounded-lg"
                                            />
                                            <span className="text-[10px] text-gray-400 font-mono uppercase font-bold">{config.color}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Limits */}
                        <div className="glass-panel p-6 rounded-2xl flex flex-col gap-6 border border-white/5 shadow-lg">
                            <div className="flex items-center gap-3 border-b border-white/5 pb-4">
                                <div className="p-2 rounded-lg bg-orange-500/10 text-orange-400">
                                    <Gauge className="w-5 h-5" />
                                </div>
                                <h3 className="text-lg font-black text-white uppercase tracking-tight">Límites</h3>
                            </div>
                            <div className="space-y-6">
                                <div>
                                    <div className="flex justify-between items-center mb-2">
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Descargas ePub (24h)</label>
                                        <span className="text-xs font-mono font-black text-primary">{config.dailyDownloads === -1 ? '∞' : config.dailyDownloads}</span>
                                    </div>
                                    <input
                                        type="number"
                                        value={config.dailyDownloads}
                                        onChange={(e) => setConfig({ ...config, dailyDownloads: parseInt(e.target.value) || 0 })}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white font-bold focus:ring-1 focus:ring-primary focus:border-primary transition-all"
                                    />
                                    <p className="mt-2 text-[9px] text-gray-500 italic">Usa -1 para descargas ilimitadas.</p>
                                </div>
                                <div>
                                    <div className="flex justify-between items-center mb-2">
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Descargas Simultáneas</label>
                                        <span className="text-xs font-mono font-black text-primary">{config.maxConcurrent}</span>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <input
                                            type="range"
                                            min="1"
                                            max="10"
                                            value={config.maxConcurrent}
                                            onChange={(e) => setConfig({ ...config, maxConcurrent: parseInt(e.target.value) })}
                                            className="flex-1 accent-primary h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>

                    {/* Right Side: Privileges & Appearance */}
                    <div className="lg:col-span-8 space-y-6">
                        {/* Privileges */}
                        <div className="glass-panel p-6 rounded-2xl flex flex-col gap-6 border border-white/5 shadow-lg">
                            <div className="flex items-center gap-3 border-b border-white/5 pb-4">
                                <div className="p-2 rounded-lg bg-yellow-500/10 text-yellow-500">
                                    <Stars className="w-5 h-5" />
                                </div>
                                <h3 className="text-lg font-black text-white uppercase tracking-tight">Privilegios y Acceso</h3>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {[
                                    {
                                        label: 'Prioridad en Solicitudes',
                                        sub: 'Cola de procesamiento preferencial',
                                        val: config.priorityRequests,
                                        key: 'priorityRequests',
                                        icon: Zap
                                    },
                                    {
                                        label: 'Acceso Anticipado',
                                        sub: 'Prueba de funciones Beta nuevas',
                                        val: config.earlyAccess,
                                        key: 'earlyAccess',
                                        icon: Eye
                                    },
                                    {
                                        label: 'Temas Personalizados',
                                        sub: 'Permitir que el usuario cambie UI',
                                        val: config.customThemes,
                                        key: 'customThemes',
                                        icon: Palette
                                    },
                                    {
                                        label: 'Mostrar Recomendaciones',
                                        sub: 'Sugerir contenido en inicio',
                                        val: config.showRecommendations,
                                        key: 'showRecommendations',
                                        icon: Stars
                                    },
                                    {
                                        label: 'Habilitar Descargas',
                                        sub: 'Permitir descarga de archivos ePUB',
                                        val: config.canDownload,
                                        key: 'canDownload',
                                        icon: Download
                                    },
                                    {
                                        label: 'Habilitar Lectura',
                                        sub: 'Permitir leer libros online',
                                        val: config.canRead,
                                        key: 'canRead',
                                        icon: BookOpen
                                    },
                                    {
                                        label: 'Ver Mi Biblioteca',
                                        sub: 'Muestra acceso a libros propios',
                                        val: config.hasLibraryAccess,
                                        key: 'hasLibraryAccess',
                                        icon: Library
                                    },
                                    {
                                        label: 'Solicitar Libros',
                                        sub: 'Permitir peticiones de descargas',
                                        val: config.canRequestBooks,
                                        key: 'canRequestBooks',
                                        icon: Download
                                    },
                                    {
                                        label: 'Forzar Configuración',
                                        sub: 'Ignora ajustes del usuario',
                                        val: config.forceSettings,
                                        icon: Shield
                                    },
                                    {
                                        label: 'Subir EPUBs',
                                        sub: 'Permitir subir archivos a la biblioteca',
                                        val: config.canUploadEpub,
                                        key: 'canUploadEpub',
                                        icon: Upload
                                    }
                                ].map((p) => (
                                    <div key={p.key} className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 rounded-xl bg-white/5 text-gray-400">
                                                {/* @ts-ignore */}
                                                <p.icon className="w-4 h-4" />
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-sm font-black text-white">{p.label}</span>
                                                <span className="text-[10px] text-gray-500 uppercase tracking-tight font-bold">{p.sub}</span>
                                            </div>
                                        </div>
                                        <Toggle
                                            checked={p.val as boolean}
                                            onChange={(val) => setConfig({ ...config, [p.key]: val })}
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>


                        {/* Info Note about Interface section */}
                        <div className="glass-panel p-8 rounded-2xl border border-primary/20 bg-primary/5 flex flex-col md:flex-row items-center gap-6 shadow-xl relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:rotate-12 transition-transform">
                                <Palette className="w-16 h-16 text-primary" />
                            </div>
                            <div className="p-4 rounded-2xl bg-primary/20 text-primary shrink-0">
                                <Palette className="w-8 h-8" />
                            </div>
                            <div className="flex-1">
                                <h4 className="text-white font-black uppercase tracking-tight mb-1">Personalización Visual Movida</h4>
                                <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest leading-relaxed">
                                    Los ajustes de colores, transparencias, desenfoques y efectos visuales de la interfaz se han movido a la nueva pestaña
                                    <span className="text-primary font-black ml-1 uppercase">"Interfaz"</span> en el menú principal del panel admin.
                                </p>
                            </div>
                            <button
                                onClick={() => onNavigate?.('interface')}
                                className="px-6 py-3 bg-primary text-white text-[10px] font-black uppercase tracking-widest rounded-xl shadow-lg shadow-primary/20 hover:scale-105 transition-all whitespace-nowrap"
                            >
                                Ir a Interfaz
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};
