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
    Layout
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
    uiPrimaryColor: string;
    panelTransparency: number;
    navOpacity?: number;
    accentOpacity?: number;
    glassBlur?: number;
    coverWidth?: number;
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
        uiPrimaryColor: settings.primaryColor,
        panelTransparency: 70,
        navOpacity: settings.navOpacity,
        accentOpacity: settings.accentOpacity,
        glassBlur: settings.glassBlur,
        coverWidth: settings.coverWidth
    });

    const [originalConfig, setOriginalConfig] = useState<TierConfig | null>(null);

    // Initial load: Fetch all levels for the selector
    useEffect(() => {
        const fetchLevels = async () => {
            try {
                const res = await api.getAdminTiers();
                if (res.levels && Array.isArray(res.levels)) {
                    setAllLevels(res.levels.map((l: any) => ({
                        id: String(l.id),
                        name: l.name,
                        color: l.color || '#6b7280'
                    })));
                }
            } catch (err) {
                console.error('Error fetching levels:', err);
            }
        };
        fetchLevels();
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
                        uiPrimaryColor: res.tier.uiPrimaryColor || settings.primaryColor,
                        panelTransparency: res.tier.panelTransparency ?? 70,
                        navOpacity: res.tier.navOpacity ?? settings.navOpacity,
                        accentOpacity: res.tier.accentOpacity ?? settings.accentOpacity,
                        glassBlur: res.tier.glassBlur ?? settings.glassBlur,
                        coverWidth: res.tier.coverWidth ?? settings.coverWidth
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

                {/* Header with Selector */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="flex items-center gap-5">
                        <button
                            onClick={onBack}
                            className="flex items-center justify-center size-12 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all group"
                        >
                            <ArrowLeft className="w-6 h-6 text-gray-400 group-hover:text-white" />
                        </button>
                        <div className="flex flex-col">
                            <div className="flex items-center gap-3">
                                <h1 className="text-white text-4xl font-black leading-tight tracking-tighter uppercase">
                                    Configurar Nivel
                                </h1>
                                <div className="px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[10px] font-black uppercase tracking-widest text-primary animate-pulse">
                                    Live Editor
                                </div>
                            </div>
                            <p className="text-gray-400 text-sm font-medium mt-1">Personaliza la experiencia global para este rango.</p>
                        </div>
                    </div>

                    {/* Level Selector */}
                    <div className="relative group min-w-[240px]">
                        <div className="absolute -top-2 -left-2 px-2 py-0.5 rounded-full bg-black border border-white/10 text-[8px] font-black uppercase tracking-widest text-gray-500 z-10">
                            Seleccionar Nivel a Editar
                        </div>
                        <div className="relative">
                            <Layers className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-primary" />
                            <select
                                value={selectedTierName}
                                onChange={(e) => setSelectedTierName(e.target.value)}
                                className="w-full pl-12 pr-10 py-4 bg-black/40 border-2 border-white/5 rounded-2xl text-base font-black text-white appearance-none focus:outline-none focus:border-primary/50 transition-all cursor-pointer hover:bg-black/60 shadow-xl"
                                style={{ color: allLevels.find(l => l.name === selectedTierName)?.color || '#fff' }}
                            >
                                {allLevels.map(lvl => (
                                    <option key={lvl.id} value={lvl.name} style={{ color: lvl.color }}>
                                        {lvl.name.toUpperCase()}
                                    </option>
                                ))}
                            </select>
                            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500 pointer-events-none group-hover:text-primary transition-colors" />
                        </div>
                    </div>
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
                                <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
                                    <div className="space-y-1">
                                        <span className="block text-white text-sm font-bold">Mostrar Recomendaciones</span>
                                        <span className="block text-gray-500 text-xs">Sugerir contenido en inicio</span>
                                    </div>
                                    <Toggle
                                        checked={config.showRecommendations}
                                        onChange={(val) => setConfig({ ...config, showRecommendations: val })}
                                    />
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

                        {/* Appearance Customization */}
                        <div className="glass-panel p-6 rounded-2xl flex flex-col gap-6 border border-white/5 shadow-lg">
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-primary/10 text-primary">
                                        <Palette className="w-5 h-5" />
                                    </div>
                                    <h3 className="text-lg font-black text-white uppercase tracking-tight">Identidad Visual del Rango</h3>
                                </div>
                                <div className="flex items-center gap-2 px-3 py-1 bg-primary/10 border border-primary/20 rounded-full">
                                    <span className="text-[8px] font-black text-primary uppercase tracking-widest">Afecta solo a este nivel</span>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="space-y-6">
                                    <div>
                                        <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-3">Color Primario de TMA</label>
                                        <div className="flex items-center gap-4">
                                            <div className="flex-1 flex items-center justify-between p-2 bg-black/40 border-2 border-white/5 rounded-xl">
                                                <div className="flex items-center gap-3">
                                                    <div
                                                        className="size-10 rounded-lg shadow-inner border border-white/10"
                                                        style={{ backgroundColor: config.uiPrimaryColor }}
                                                    />
                                                    <span className="text-xs font-black font-mono text-gray-300 uppercase">{config.uiPrimaryColor}</span>
                                                </div>
                                                <label className="px-4 py-2 bg-primary hover:bg-primary-dark text-white text-[10px] font-black uppercase tracking-widest rounded-lg transition-all cursor-pointer shadow-lg shadow-primary/20">
                                                    Pick
                                                    <input
                                                        type="color"
                                                        value={config.uiPrimaryColor}
                                                        onChange={(e) => setConfig({ ...config, uiPrimaryColor: e.target.value })}
                                                        className="hidden"
                                                    />
                                                </label>
                                            </div>
                                        </div>
                                    </div>

                                    <div>
                                        <div className="flex justify-between items-center mb-3">
                                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Intensidad Glassmorphism (Blur)</label>
                                            <span className="text-xs font-black text-primary">{config.glassBlur || 12}px</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="0"
                                            max="40"
                                            value={config.glassBlur}
                                            onChange={(e) => setConfig({ ...config, glassBlur: parseInt(e.target.value) })}
                                            className="w-full accent-primary h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
                                        />
                                    </div>

                                    <div>
                                        <div className="flex justify-between items-center mb-3">
                                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Transparencia Paneles (Alpha)</label>
                                            <span className="text-xs font-black text-primary">{config.panelTransparency}%</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={config.panelTransparency}
                                            onChange={(e) => setConfig({ ...config, panelTransparency: parseInt(e.target.value) })}
                                            className="w-full accent-primary h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-6">
                                    <div>
                                        <div className="flex justify-between items-center mb-3">
                                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Transparencia Nav Bar</label>
                                            <span className="text-xs font-black text-primary">{Math.round((config.navOpacity || settings.navOpacity) * 100)}%</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={(config.navOpacity || settings.navOpacity) * 100}
                                            onChange={(e) => setConfig({ ...config, navOpacity: parseInt(e.target.value) / 100 })}
                                            className="w-full accent-primary h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
                                        />
                                    </div>

                                    <div>
                                        <div className="flex justify-between items-center mb-3">
                                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Ancho de Portadas (Cards)</label>
                                            <span className="text-xs font-black text-primary">{config.coverWidth || settings.coverWidth}px</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="80"
                                            max="180"
                                            value={config.coverWidth || settings.coverWidth}
                                            onChange={(e) => setConfig({ ...config, coverWidth: parseInt(e.target.value) })}
                                            className="w-full accent-primary h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
                                        />
                                    </div>

                                    <div className="p-4 rounded-2xl bg-primary/5 border border-primary/20 flex items-center gap-4 group hover:bg-primary/10 transition-all cursor-default overflow-hidden relative">
                                        <div className="absolute top-0 right-0 p-2 opacity-10 rotate-12 group-hover:rotate-45 transition-transform">
                                            <Eye className="w-12 h-12 text-primary" />
                                        </div>
                                        <div className="relative z-10 flex items-center gap-4">
                                            <div className="p-2 rounded-xl bg-primary text-white shadow-lg shadow-primary/30">
                                                <Eye className="w-5 h-5" />
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-xs font-black text-white uppercase tracking-tight">Vista Previa en Vivo</span>
                                                <span className="text-[9px] text-gray-500 font-bold uppercase">Los usuarios verán estos cambios al navegar</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};
