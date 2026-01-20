import React, { useState, useEffect } from 'react';
import {
    Palette,
    Monitor,
    Layout,
    Type,
    Image as ImageIcon,
    MousePointer2,
    Eye,
    Star,
    GlassWater,
    ArrowLeft,
    Loader2,
    CheckCircle2,
    XCircle,
    Copy,
    Save,
    RotateCcw,
    Layers,
    Sliders,
    EyeOff
} from 'lucide-react';
import { api } from '../src/services/api';
import { useTheme } from '../contexts/ThemeContext';

interface AppearanceDashboardProps {
    onNavigate?: (page: string) => void;
    onSavingChange?: (saving: boolean) => void;
    onCanUndoChange?: (canUndo: boolean) => void;
    onCanSaveChange?: (canSave: boolean) => void;
    setUndoRef?: (fn: () => void) => void;
    setSaveRef?: (fn: () => Promise<void>) => void;
}

interface UIConfig {
    id: string | number;
    name: string;
    primaryColor: string;
    glassBlur: number;
    glassOpacity: number;
    navOpacity: number;
    accentOpacity: number;
    cardGlowIntensity: number;
    backgroundColor: string;
    cardColor: string;
    bannerContentOffset: number;
    fontSize: number;
    coverWidth: number;
    theme: 'dark' | 'light' | 'amoled';
    forceSettings: boolean;
    exportedSettings: string[]; // List of setting keys visible to users
}

export const AppearanceDashboard: React.FC<AppearanceDashboardProps> = ({
    onNavigate,
    onSavingChange,
    onCanUndoChange,
    onCanSaveChange,
    setUndoRef,
    setSaveRef
}) => {
    const { settings: currentTheme } = useTheme();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [allLevels, setAllLevels] = useState<any[]>([]);
    const [selectedLevelId, setSelectedLevelId] = useState<string | number>('global');
    const [config, setConfig] = useState<UIConfig | null>(null);
    const [originalConfig, setOriginalConfig] = useState<UIConfig | null>(null);
    const [msg, setMsg] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    // Available UI settings for the "visibility" list
    const exportedOptions = [
        { key: 'theme', label: 'Tema (Oscuro/Clar/AMOLED)', icon: Monitor },
        { key: 'primaryColor', label: 'Color de Acento', icon: Palette },
        { key: 'glassBlur', label: 'Nivel de Blur', icon: GlassWater },
        { key: 'glassOpacity', label: 'Transparencia Paneles', icon: MousePointer2 },
        { key: 'cardGlowIntensity', label: 'Resplandor Cards', icon: Star },
        { key: 'fontSize', label: 'Tamaño de Letra', icon: Type },
        { key: 'coverWidth', label: 'Ancho de Portadas', icon: ImageIcon },
        { key: 'navOpacity', label: 'Opacidad Barra Nav', icon: Layout },
    ];

    useEffect(() => {
        const fetchBaseData = async () => {
            try {
                const res = await api.getAdminTiers();
                if (res.levels) {
                    setAllLevels([
                        { id: 'global', name: 'Global (Por Defecto)', color: '#ffffff' },
                        ...res.levels
                    ]);
                }
            } catch (err) {
                console.error("Error fetching levels", err);
            } finally {
                setLoading(false);
            }
        };
        fetchBaseData();
    }, []);

    useEffect(() => {
        const loadLevelConfig = async () => {
            setLoading(true);
            try {
                const levelName = allLevels.find(l => String(l.id) === String(selectedLevelId))?.name || 'Global';
                const res = await api.getTierConfig(levelName);
                if (res.success && res.tier) {
                    const t = res.tier;
                    // Parse exportedSettings from string/JSON if needed
                    let exported: string[] = [];
                    if (t.ui_exported_settings) {
                        try {
                            exported = JSON.parse(t.ui_exported_settings);
                        } catch (e) {
                            exported = String(t.ui_exported_settings).split(',').filter(Boolean);
                        }
                    } else {
                        // Default visible settings if none specified
                        exported = ['theme', 'primaryColor', 'fontSize'];
                    }

                    const newConfig: UIConfig = {
                        id: selectedLevelId,
                        name: t.name,
                        primaryColor: t.primaryColor || '#2b6cee',
                        glassBlur: t.glassBlur ?? 12,
                        glassOpacity: t.glassOpacity ?? 0.6,
                        navOpacity: t.navOpacity ?? 0.8,
                        accentOpacity: t.accentOpacity ?? 0.2,
                        cardGlowIntensity: t.cardGlowIntensity ?? 0.5,
                        backgroundColor: t.backgroundColor || '#0f172a',
                        cardColor: t.cardColor || '#1e293b',
                        bannerContentOffset: t.bannerContentOffset ?? 0,
                        fontSize: t.fontSize ?? 14,
                        coverWidth: t.coverWidth ?? 120,
                        theme: t.theme || 'dark',
                        forceSettings: t.forceSettings || false,
                        exportedSettings: exported
                    };
                    setConfig(newConfig);
                    setOriginalConfig(JSON.parse(JSON.stringify(newConfig)));
                }
            } catch (err) {
                console.error("Error loading level config", err);
            } finally {
                setLoading(false);
            }
        };

        if (allLevels.length > 0) {
            loadLevelConfig();
        }
    }, [selectedLevelId, allLevels]);

    // Handle Save/Undo via parent
    useEffect(() => {
        const hasChanges = JSON.stringify(config) !== JSON.stringify(originalConfig);
        onCanUndoChange?.(hasChanges);
        onCanSaveChange?.(hasChanges);
    }, [config, originalConfig]);

    const handleSave = async () => {
        if (!config) return;
        setSaving(true);
        onSavingChange?.(true);
        try {
            // Prepare data for API
            const savePayload = {
                ...config,
                ui_exported_settings: JSON.stringify(config.exportedSettings)
            };
            const res = await api.saveTierConfig(savePayload);
            if (res.success) {
                setOriginalConfig(JSON.parse(JSON.stringify(config)));
                setMsg({ type: 'success', text: 'Apariencia guardada correctamente' });
                setTimeout(() => setMsg(null), 3000);
            } else {
                setMsg({ type: 'error', text: res.message || 'Error al guardar' });
            }
        } catch (err: any) {
            setMsg({ type: 'error', text: err.message || 'Error de conexión' });
        } finally {
            setSaving(false);
            onSavingChange?.(false);
        }
    };

    const handleUndo = () => {
        if (originalConfig) {
            setConfig(JSON.parse(JSON.stringify(originalConfig)));
        }
    };

    useEffect(() => {
        setSaveRef?.(handleSave);
        setUndoRef?.(handleUndo);
    }, [config]);

    const toggleExported = (key: string) => {
        if (!config) return;
        const current = [...config.exportedSettings];
        if (current.includes(key)) {
            setConfig({ ...config, exportedSettings: current.filter(k => k !== key) });
        } else {
            setConfig({ ...config, exportedSettings: [...current, key] });
        }
    };

    if (loading && !config) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
                <Loader2 className="w-10 h-10 text-primary animate-spin" />
                <p className="text-gray-500 font-black uppercase tracking-widest text-[10px]">Cargando Interfaz...</p>
            </div>
        );
    }

    if (!config) return null;

    return (
        <div className="flex flex-col gap-8 pb-32 animate-in fade-in duration-500">
            {/* Header: Selector de Nivel */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 glass-panel p-6 rounded-[2rem] border-white/5 shadow-2xl">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-primary/20 rounded-2xl border border-primary/20">
                        <Palette className="w-8 h-8 text-primary" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-white uppercase tracking-tighter">Personalización <span className="text-primary italic">Visual</span></h2>
                        <p className="text-gray-500 text-[10px] font-bold uppercase tracking-widest mt-0.5">Define colores, efectos y qué puede ver el usuario</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <label className="text-xs font-black text-gray-500 uppercase tracking-widest hidden sm:block">EDITANDO:</label>
                    <select
                        value={selectedLevelId}
                        onChange={(e) => setSelectedLevelId(e.target.value)}
                        className="bg-black/40 border border-white/10 rounded-2xl px-6 py-3 text-sm font-bold text-white focus:ring-1 focus:ring-primary focus:border-primary transition-all cursor-pointer appearance-none min-w-[200px]"
                        style={{ outline: 'none' }}
                    >
                        {allLevels.map(lvl => (
                            <option key={lvl.id} value={lvl.id}>{lvl.name}</option>
                        ))}
                    </select>
                </div>
            </div>

            {msg && (
                <div className={`p-4 rounded-2xl border flex items-center gap-3 animate-in slide-in-from-top-4 duration-300 ${msg.type === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
                    {msg.type === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                    <span className="text-sm font-bold">{msg.text}</span>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Left Column: Configuration Sliders and Colors */}
                <div className="lg:col-span-8 space-y-8">
                    {/* Colors Section */}
                    <div className="glass-panel p-8 rounded-[2.5rem] border-white/5 space-y-8 shadow-xl">
                        <div className="flex items-center gap-3 border-b border-white/5 pb-4">
                            <Sliders className="w-5 h-5 text-primary" />
                            <h3 className="text-lg font-black text-white uppercase tracking-tight">Colores Bases y Transparencia</h3>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="space-y-6">
                                <div>
                                    <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-3">Color Primario (Acento)</label>
                                    <div className="flex items-center gap-4 p-3 bg-black/40 rounded-2xl border border-white/5 group hover:border-primary/20 transition-all">
                                        <div className="size-12 rounded-xl shadow-inner border border-white/10" style={{ backgroundColor: config.primaryColor }}></div>
                                        <div className="flex-1">
                                            <input
                                                type="text"
                                                value={config.primaryColor}
                                                onChange={(e) => setConfig({ ...config, primaryColor: e.target.value })}
                                                className="w-full bg-transparent border-none text-sm font-mono text-white uppercase focus:ring-0"
                                            />
                                        </div>
                                        <input
                                            type="color"
                                            value={config.primaryColor}
                                            onChange={(e) => setConfig({ ...config, primaryColor: e.target.value })}
                                            className="size-8 rounded-lg cursor-pointer bg-transparent border-none p-0"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-3">Color de Fondo (Background)</label>
                                    <div className="flex items-center gap-3 p-3 bg-black/40 rounded-2xl border border-white/5">
                                        <div className="size-12 rounded-xl border border-white/10" style={{ backgroundColor: config.backgroundColor }}></div>
                                        <input
                                            type="text"
                                            value={config.backgroundColor}
                                            onChange={(e) => setConfig({ ...config, backgroundColor: e.target.value })}
                                            className="flex-1 bg-transparent border-none text-sm font-mono text-white uppercase focus:ring-0"
                                        />
                                        <input
                                            type="color"
                                            value={config.backgroundColor.substring(0, 7)}
                                            onChange={(e) => setConfig({ ...config, backgroundColor: e.target.value + (config.backgroundColor.substring(7) || 'FF') })}
                                            className="size-8 cursor-pointer bg-transparent border-none p-0"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div>
                                    <div className="flex justify-between items-center mb-3">
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Glassmorphism (Blur)</label>
                                        <span className="text-xs font-black text-primary font-mono">{config.glassBlur}px</span>
                                    </div>
                                    <input
                                        type="range"
                                        min="0"
                                        max="40"
                                        value={config.glassBlur}
                                        onChange={(e) => setConfig({ ...config, glassBlur: parseInt(e.target.value) })}
                                        className="w-full accent-primary h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer"
                                    />
                                </div>

                                <div>
                                    <div className="flex justify-between items-center mb-3">
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Opacidad Cards (Alpha)</label>
                                        <span className="text-xs font-black text-primary font-mono">{Math.round(config.glassOpacity * 100)}%</span>
                                    </div>
                                    <input
                                        type="range"
                                        min="0"
                                        max="100"
                                        value={config.glassOpacity * 100}
                                        onChange={(e) => setConfig({ ...config, glassOpacity: parseInt(e.target.value) / 100 })}
                                        className="w-full accent-primary h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Layout & Specifics Section */}
                    <div className="glass-panel p-8 rounded-[2.5rem] border-white/5 space-y-8 shadow-xl">
                        <div className="flex items-center gap-3 border-b border-white/5 pb-4">
                            <Layout className="w-5 h-5 text-primary" />
                            <h3 className="text-lg font-black text-white uppercase tracking-tight">Estructura y Proporciones</h3>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-10">
                            <div>
                                <div className="flex justify-between items-center mb-2">
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Resplandor (Glow)</label>
                                    <span className="text-xs font-black text-primary font-mono">{Math.round(config.cardGlowIntensity * 100)}%</span>
                                </div>
                                <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    value={config.cardGlowIntensity * 100}
                                    onChange={(e) => setConfig({ ...config, cardGlowIntensity: parseInt(e.target.value) / 100 })}
                                    className="w-full accent-primary h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer"
                                />
                            </div>

                            <div>
                                <div className="flex justify-between items-center mb-2">
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Ancho de Portadas</label>
                                    <span className="text-xs font-black text-primary font-mono">{config.coverWidth}px</span>
                                </div>
                                <input
                                    type="range"
                                    min="80"
                                    max="240"
                                    value={config.coverWidth}
                                    onChange={(e) => setConfig({ ...config, coverWidth: parseInt(e.target.value) })}
                                    className="w-full accent-primary h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer"
                                />
                            </div>

                            {selectedLevelId === 'global' && (
                                <div className="md:col-span-2 p-6 rounded-2xl bg-amber-500/5 border border-amber-500/10">
                                    <div className="flex justify-between items-center mb-3">
                                        <div className="flex items-center gap-2">
                                            <label className="text-[10px] font-black text-amber-500 uppercase tracking-widest">Offset Banner Serie (PX)</label>
                                            <span className="px-2 py-0.5 rounded-full bg-amber-500 text-black text-[8px] font-black uppercase">Global-Only</span>
                                        </div>
                                        <span className="text-xs font-black text-amber-500 font-mono">{config.bannerContentOffset}px</span>
                                    </div>
                                    <input
                                        type="range"
                                        min="-100"
                                        max="200"
                                        step="5"
                                        value={config.bannerContentOffset}
                                        onChange={(e) => setConfig({ ...config, bannerContentOffset: parseInt(e.target.value) })}
                                        className="w-full h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer accent-amber-500"
                                    />
                                    <p className="mt-3 text-[9px] text-amber-500/60 italic font-medium">Ajusta la posición vertical del título y sinopsis en el banner de serie. Valores negativos suben el texto.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Column: Visibility / Exported Settings (The Checklist) */}
                <div className="lg:col-span-4 space-y-8">
                    <div className="glass-panel p-8 rounded-[2.5rem] border-primary/20 bg-primary/5 space-y-6 shadow-2xl relative overflow-hidden backdrop-blur-xl">
                        <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                            <Sliders className="w-24 h-24" />
                        </div>

                        <div className="border-b border-primary/20 pb-4">
                            <h3 className="text-lg font-black text-white uppercase tracking-tight flex items-center gap-2">
                                <Eye className="w-5 h-5 text-primary" />
                                Visibilidad
                            </h3>
                            <p className="text-[9px] text-primary font-black uppercase tracking-widest mt-1">Marca qué verá el usuario en su menú de ajustes</p>
                        </div>

                        <div className="space-y-3">
                            {exportedOptions.map((opt) => {
                                const isChecked = config.exportedSettings.includes(opt.key);
                                return (
                                    <div
                                        key={opt.key}
                                        onClick={() => toggleExported(opt.key)}
                                        className={`flex items-center justify-between p-4 rounded-2xl border transition-all cursor-pointer group ${isChecked
                                            ? 'bg-primary/20 border-primary/40 shadow-inner'
                                            : 'bg-black/20 border-white/5 hover:border-white/10'
                                            }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-xl border transition-all ${isChecked ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20' : 'bg-white/5 text-gray-500 border-white/5'}`}>
                                                <opt.icon className="w-4 h-4" />
                                            </div>
                                            <span className={`text-xs font-black uppercase tracking-tight transition-colors ${isChecked ? 'text-white' : 'text-gray-500'}`}>{opt.label}</span>
                                        </div>
                                        <div className={`size-5 rounded-md border-2 transition-all flex items-center justify-center ${isChecked ? 'bg-primary border-primary' : 'bg-transparent border-white/10'}`}>
                                            {isChecked && <CheckCircle2 className="size-3.5 text-white" strokeWidth={3} />}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        <div className="p-4 rounded-xl bg-black/40 border border-white/5">
                            <div className="flex items-center gap-3 mb-2">
                                <RotateCcw className="w-4 h-4 text-gray-500" />
                                <span className="text-[10px] font-black text-gray-400 uppercase">Forzar Aplicación</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-[9px] text-gray-500 font-bold uppercase w-2/3 leading-relaxed">Sobreescribir ajustes personales con estos valores</span>
                                <button
                                    onClick={() => setConfig({ ...config, forceSettings: !config.forceSettings })}
                                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${config.forceSettings ? 'bg-primary' : 'bg-white/10'}`}
                                >
                                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${config.forceSettings ? 'translate-x-6' : 'translate-x-1'}`} />
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Quick Preview Badge */}
                    <div className="p-8 rounded-[2.5rem] bg-gradient-to-br from-slate-900 to-black border border-white/5 shadow-xl flex flex-col items-center justify-center text-center gap-4 group">
                        <div className="size-20 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20 group-hover:scale-110 transition-transform duration-500">
                            <div className="size-14 rounded-full bg-primary shadow-[0_0_30px_rgba(var(--color-primary-rgb),0.5)] flex items-center justify-center">
                                <Eye className="w-8 h-8 text-white" />
                            </div>
                        </div>
                        <div>
                            <h4 className="text-white font-black uppercase tracking-tighter">Vista en Vivo</h4>
                            <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest mt-1 leading-relaxed">Los usuarios de este nivel {selectedLevelId === 'global' ? 'por defecto' : ''} verán estos cambios al navegar.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
