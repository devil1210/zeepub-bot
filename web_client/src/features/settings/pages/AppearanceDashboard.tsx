import React, { useState, useEffect } from 'react';
import { Palette, Sun, Moon, Contrast, Sliders, CheckCircle2, RotateCcw, Eye, Save, Loader2, XCircle, AlertCircle } from 'lucide-react';
import { api } from '@shared/services/api';

interface AppearanceDashboardProps {
    onSavingChange?: (saving: boolean) => void;
    onCanSaveChange?: (canSave: boolean) => void;
    onCanUndoChange?: (canUndo: boolean) => void;
    setSaveRef?: (fn: () => void) => void;
    setUndoRef?: (fn: () => void) => void;
}

export const AppearanceDashboard: React.FC<AppearanceDashboardProps> = ({
    onSavingChange,
    onCanSaveChange,
    setSaveRef
}) => {
    const [tiers, setTiers] = useState<any[]>([]);
    const [selectedLevelId, setSelectedLevelId] = useState<string>('global');
    const [config, setConfig] = useState<any>(null);
    const [initialConfig, setInitialConfig] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
    const [availableThemes, setAvailableThemes] = useState<any[]>([]);
    const [showSaveThemeModal, setShowSaveThemeModal] = useState(false);
    const [newThemeName, setNewThemeName] = useState('');
    const [livePreview, setLivePreview] = useState(false);

    const exportedOptions = [
        { key: 'theme', label: 'Modo (Claro/Oscuro)', icon: Moon },
        { key: 'primaryColor', label: 'Color de Acento', icon: Palette },
        { key: 'glassBlur', label: 'Efecto Blur', icon: Sliders },
        { key: 'coverWidth', label: 'Tamaño de Portadas', icon: CheckCircle2 },
        { key: 'cardGlowIntensity', label: 'Resplandor', icon: Eye },
        { key: 'fontSize', label: 'Tamaño de Fuente', icon: CheckCircle2 },
        { key: 'showRecommendations', label: 'Recomendaciones', icon: CheckCircle2 },
    ];

    useEffect(() => {
        loadData();
    }, []);

    useEffect(() => {
        if (setSaveRef) setSaveRef(handleSave);
    }, [config, selectedLevelId, tiers]);

    useEffect(() => {
        if (onCanSaveChange) {
            const hasChanged = JSON.stringify(config) !== JSON.stringify(initialConfig);
            onCanSaveChange(hasChanged);
        }
    }, [config, initialConfig]);

    useEffect(() => {
        if (onSavingChange) onSavingChange(saving);
    }, [saving]);

    // Live Preview Effect
    const { updateSettings } = (window as any).useTheme ? (window as any).useTheme() : { updateSettings: null };

    useEffect(() => {
        if (livePreview && config && updateSettings) {
            updateSettings({
                theme: config.theme,
                primaryColor: config.primaryColor,
                backgroundColor: config.backgroundColor,
                cardColor: config.cardColor,
                glassBlur: config.glassBlur,
                glassOpacity: config.glassOpacity,
                navOpacity: config.navOpacity,
                accentOpacity: config.accentOpacity,
                cardGlowIntensity: config.cardGlowIntensity,
                coverWidth: config.coverWidth,
                bannerContentOffset: config.bannerContentOffset
            });
        }
    }, [config, livePreview]);

    const [themesLoaded, setThemesLoaded] = useState(false);

    const loadData = async () => {
        try {
            setLoading(true);
            // Only load tiers on mount — themes are loaded lazily on demand
            const tiersRes = await api.getAdminTiers();

            if (tiersRes.success) {
                setTiers(tiersRes.tiers || tiersRes.levels || []);
            }

            // Load global by default
            await loadLevelConfig('global');
        } catch (err) {
            console.error("Error loading administration data:", err);
        } finally {
            setLoading(false);
        }
    };

    // Lazy theme loader — called when user opens the templates dropdown
    const loadThemesIfNeeded = async () => {
        if (themesLoaded) return;
        try {
            const themesRes = await api.getAvailableThemes();
            if (themesRes.success) {
                setAvailableThemes(themesRes.themes);
            }
        } catch (err) {
            console.error("Error loading themes:", err);
        }
        setThemesLoaded(true);
    };

    const loadLevelConfig = async (levelId: string) => {
        try {
            console.log("Loading config for level:", levelId);
            setLoading(true);
            const res = await api.getTierConfig(String(levelId));
            if (res.success) {
                console.log("Config loaded:", res.config);
                setConfig(res.config);
                setInitialConfig(res.config);
                setSelectedLevelId(String(levelId));
            } else {
                console.warn("Failed to load config:", res.message);
                if (levelId === 'global') {
                    // Provide a basic fallback if global fails to load
                    setConfig({
                        name: 'Global',
                        theme: 'dark',
                        primaryColor: '#2b6cee',
                        backgroundColor: '#0f172a',
                        cardColor: '#1e293b',
                        glassOpacity: 0.6,
                        glassBlur: 12,
                        exportedSettings: ['theme', 'primaryColor', 'fontSize']
                    });
                    setSelectedLevelId('global');
                }
            }
        } catch (err) {
            console.error("Error loading level config:", err);
            if (!config) {
                setConfig({
                    id: levelId === 'global' ? 'global' : levelId,
                    name: levelId === 'global' ? 'Global' : 'Nivel',
                    theme: 'dark',
                    primaryColor: '#3b82f6',
                    backgroundColor: '#0f172a',
                    cardColor: '#1e293b',
                    glassOpacity: 0.6,
                    glassBlur: 12,
                    exportedSettings: ['theme', 'primaryColor', 'fontSize']
                });
            }
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        if (!config) return;
        setSaving(true);
        setMessage(null);
        try {
            const res = await api.saveTierConfig({ ...config, level_id: selectedLevelId });
            if (res.success) {
                setMessage({ text: 'Configuración guardada correctamente', type: 'success' });
                setInitialConfig(config);
                // Optional: refresh local tiers list if name changed
                if (selectedLevelId !== 'global') {
                    const newTiers = tiers.map(t => t.id === selectedLevelId ? { ...t, name: config.name } : t);
                    setTiers(newTiers);
                }
            } else {
                setMessage({ text: res.message || 'Error al guardar', type: 'error' });
            }
        } catch (err) {
            setMessage({ text: 'Error de conexión', type: 'error' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 3000);
        }
    };

    const handleSaveAsTheme = async () => {
        if (!newThemeName.trim()) {
            setMessage({ text: 'Ingresa un nombre para el tema', type: 'error' });
            return;
        }

        setSaving(true);
        try {
            const themeData = {
                name: newThemeName,
                description: `Basado en ${selectedLevelId}`,
                ...config,
                is_new: true // Tell backend to ensure unique name
            };

            const res = await api.saveAsTheme(themeData);
            if (res.success) {
                setMessage({ text: `Tema "${res.theme.name}" guardado`, type: 'success' });
                setShowSaveThemeModal(false);
                setNewThemeName('');
                // Refresh themes list
                const themesRes = await api.getAvailableThemes();
                if (themesRes.success) {
                    setAvailableThemes(themesRes.themes);
                }
            } else {
                setMessage({ text: res.message || 'Error al guardar tema', type: 'error' });
            }
        } catch (err) {
            setMessage({ text: 'Error al conectar', type: 'error' });
        } finally {
            setSaving(false);
        }
    };

    const handleApplyTheme = (theme: any) => {
        setConfig({
            ...config,
            theme: theme.theme_type,
            primaryColor: theme.primaryColor || theme.primary_color,
            backgroundColor: theme.backgroundColor || theme.background_color,
            cardColor: theme.cardColor || theme.card_color,
            glassBlur: theme.glassBlur || theme.glass_blur,
            glassOpacity: theme.glassOpacity || theme.glass_opacity,
            navOpacity: theme.navOpacity || theme.nav_opacity,
            accentOpacity: theme.accentOpacity || theme.accent_opacity,
            cardGlowIntensity: theme.cardGlowIntensity || theme.card_glow_intensity || 0.5,
        });
    };

    const toggleExported = (key: string) => {
        const current = [...(config.exportedSettings || [])];
        if (current.includes(key)) {
            setConfig({ ...config, exportedSettings: current.filter(k => k !== key) });
        } else {
            setConfig({ ...config, exportedSettings: [...current, key] });
        }
    };

    const handleColorChange = (color: string) => {
        setConfig({ ...config, primaryColor: color });
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
            {/* Header: Selector de Nivel */}
            <div className="flex flex-col gap-6 glass-panel p-6 rounded-premium-lg border border-white/5 shadow-premium overflow-hidden relative">
                <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none">
                    <Palette className="w-32 h-32" />
                </div>

                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-primary/20 rounded-premium-sm border border-primary/20 shrink-0">
                            <Palette className="w-8 h-8 text-primary" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-black text-white uppercase tracking-tighter">Panel <span className="text-primary italic">Visual</span></h2>
                            <p className="text-gray-500 text-[10px] font-bold uppercase tracking-widest mt-0.5">Define colores, efectos y temas para cada nivel</p>
                        </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-4">
                        <div className="flex items-center gap-3 bg-primary/5 p-1.5 rounded-premium-sm border border-primary/10">
                            <label className="text-[9px] font-black text-primary/60 uppercase tracking-[0.2em] pl-3 hidden sm:block">PLANTILLAS:</label>
                            <select
                                onFocus={loadThemesIfNeeded}
                                onChange={(e) => {
                                    const theme = availableThemes.find(t => String(t.id) === e.target.value);
                                    if (theme) handleApplyTheme(theme);
                                }}
                                className="bg-primary/10 border-none rounded-premium-sm px-4 py-2 text-[10px] font-black uppercase text-primary tracking-widest focus:ring-0 transition-all cursor-pointer min-w-[160px] hover:bg-primary/20"
                                style={{ outline: 'none' }}
                                defaultValue=""
                            >
                                <option value="" disabled>Cargar Tema...</option>
                                {availableThemes.map(t => (
                                    <option key={t.id} value={t.id}>{t.name}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setLivePreview(!livePreview)}
                                className={`flex items-center gap-2 px-5 py-3 rounded-premium-sm border text-[10px] font-black uppercase transition-all ${livePreview ? 'bg-primary border-primary text-white shadow-lg shadow-primary/20' : 'bg-white/5 border-white/10 text-gray-400 hover:text-white'}`}
                            >
                                <Eye className="w-4 h-4" />
                                {livePreview ? 'Live: ON' : 'Vista Previa'}
                            </button>

                            <button
                                onClick={() => setShowSaveThemeModal(true)}
                                className="flex items-center gap-2 px-5 py-3 bg-purple-600/20 border border-purple-500/30 text-purple-400 rounded-premium-sm text-[10px] font-black uppercase hover:bg-purple-600/30 transition-all"
                            >
                                <Save className="w-4 h-4" />
                                <span className="hidden sm:inline">Guardar Tema</span>
                                <span className="sm:hidden">Tema</span>
                            </button>
                        </div>
                    </div>
                </div>

                <div className="h-px w-full bg-gradient-to-r from-transparent via-white/10 to-transparent" />

                <div className="flex flex-col gap-3">
                    <label className="text-[9px] font-black text-gray-400 uppercase tracking-widest pl-1">Selecciona el Nivel para editar:</label>
                    <div className="flex flex-wrap items-center gap-2">
                        {/* Global Selector */}
                        <button
                            onClick={() => loadLevelConfig('global')}
                            className={`px-5 py-3 rounded-premium-sm border-2 text-[10px] font-black uppercase tracking-widest transition-all ${selectedLevelId === 'global'
                                ? 'bg-indigo-600 border-indigo-600 text-white shadow-xl shadow-indigo-600/20 scale-105 z-10'
                                : 'bg-white/5 border-white/5 text-gray-400 hover:border-white/20'
                                }`}
                        >
                            Global
                        </button>

                        {tiers.map((t) => {
                            const isSelected = String(selectedLevelId) === String(t.id);
                            return (
                                <button
                                    key={t.id}
                                    onClick={() => loadLevelConfig(String(t.id))}
                                    className={`px-5 py-3 rounded-premium-sm border-2 text-[10px] font-black uppercase tracking-widest transition-all ${isSelected
                                        ? 'bg-primary border-primary text-white shadow-xl shadow-primary/20 scale-105 z-10'
                                        : 'bg-white/5 border-white/5 text-gray-500 hover:border-white/20 hover:text-gray-300'
                                        }`}
                                >
                                    {t.name}
                                </button>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Alert Message */}
            {message && (
                <div className={`p-4 rounded-premium-sm border flex items-center gap-3 animate-in slide-in-from-top-4 duration-300 ${message.type === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
                    {message.type === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                    <span className="text-sm font-bold">{message.text}</span>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Left Column: Configuration Sliders and Colors */}
                <div className="lg:col-span-8 space-y-8">
                    <div className="glass-panel p-8 rounded-premium-lg border border-white/5 space-y-10 shadow-premium">
                        <div className="flex items-center gap-3 border-b border-white/5 pb-6">
                            <Palette className="w-5 h-5 text-primary" />
                            <h3 className="text-lg font-black text-white uppercase tracking-tight">
                                Personalización Visual: <span className="text-primary italic">{selectedLevelId === 'global' ? 'Global' : config.name}</span>
                            </h3>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-12">
                            {/* Theme Selection */}
                            <div className="space-y-4">
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1">Apariencia del Sistema</label>
                                <div className="grid grid-cols-3 gap-3">
                                    {[
                                        { id: 'light', icon: Sun, label: 'Claro' },
                                        { id: 'dark', icon: Moon, label: 'Oscuro' },
                                        { id: 'amoled', icon: Contrast, label: 'AMOLED' },
                                    ].map((t) => (
                                        <button
                                            key={t.id}
                                            onClick={() => setConfig({ ...config, theme: t.id as any })}
                                            className={`flex flex-col items-center gap-3 p-4 rounded-premium-sm border-2 transition-all group ${config.theme === t.id
                                                ? 'bg-primary/10 border-primary text-primary shadow-lg shadow-primary/10 scale-105'
                                                : 'bg-black/20 border-white/5 text-gray-400 hover:border-white/10'
                                                }`}
                                        >
                                            <t.icon className={`w-6 h-6 transition-transform ${config.theme === t.id ? 'scale-110' : 'group-hover:scale-110'}`} />
                                            <span className="text-[10px] font-black uppercase tracking-widest">{t.label}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Accent Color Selection */}
                            <div className="space-y-4">
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1">Color de Énfasis (Primario)</label>
                                <div className="flex flex-wrap gap-4 p-4 bg-black/20 border border-white/5 rounded-premium-sm">
                                    {['#FB7185', '#38BDF8', '#4ADE80', '#FBBF24', '#818CF8', '#F472B6', '#A78BFA'].map((color) => (
                                        <button
                                            key={color}
                                            onClick={() => handleColorChange(color)}
                                            className={`w-10 h-10 rounded-premium-sm transition-all border-2 flex items-center justify-center group ${config.primaryColor === color ? 'border-white scale-110 shadow-lg' : 'border-transparent hover:scale-105'}`}
                                            style={{ backgroundColor: color }}
                                        >
                                            {config.primaryColor === color && <div className="w-1.5 h-1.5 bg-white rounded-premium-full shadow-lg" />}
                                        </button>
                                    ))}
                                    <div className="w-px h-8 bg-white/5 mx-1" />
                                    <label className="w-10 h-10 rounded-premium-sm bg-gradient-to-tr from-gray-700 to-gray-500 flex items-center justify-center cursor-pointer hover:scale-105 transition-all relative overflow-hidden">
                                        <Palette className="w-4 h-4 text-white" />
                                        <input
                                            type="color"
                                            value={config.primaryColor}
                                            onChange={(e) => handleColorChange(e.target.value)}
                                            className="absolute inset-0 opacity-0 cursor-pointer w-full h-full scale-150"
                                        />
                                    </label>
                                </div>
                            </div>

                            {/* Background Color Selection */}
                            <div className="space-y-4">
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1">Color de Fondo</label>
                                <div className="flex flex-wrap gap-4 p-4 bg-black/20 border border-white/5 rounded-premium-sm">
                                    {['#0f172a', '#1e293b', '#111827', '#18181b', '#0c0a09'].map((color) => (
                                        <button
                                            key={color}
                                            onClick={() => setConfig({ ...config, backgroundColor: color })}
                                            className={`w-10 h-10 rounded-premium-sm transition-all border-2 flex items-center justify-center group ${config.backgroundColor === color ? 'border-white scale-110 shadow-lg' : 'border-transparent hover:scale-105'}`}
                                            style={{ backgroundColor: color }}
                                        >
                                            {config.backgroundColor === color && <div className="w-1.5 h-1.5 bg-white rounded-premium-full shadow-lg" />}
                                        </button>
                                    ))}
                                    <div className="w-px h-8 bg-white/5 mx-1" />
                                    <label className="w-10 h-10 rounded-premium-sm bg-gradient-to-tr from-gray-900 to-gray-700 flex items-center justify-center cursor-pointer hover:scale-105 transition-all relative overflow-hidden">
                                        <Palette className="w-4 h-4 text-white" />
                                        <input
                                            type="color"
                                            value={config.backgroundColor || '#0f172a'}
                                            onChange={(e) => setConfig({ ...config, backgroundColor: e.target.value })}
                                            className="absolute inset-0 opacity-0 cursor-pointer w-full h-full scale-150"
                                        />
                                    </label>
                                </div>
                            </div>

                            {/* Card Color Selection */}
                            <div className="space-y-4">
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1">Color de Tarjetas</label>
                                <div className="flex flex-wrap gap-4 p-4 bg-black/20 border border-white/5 rounded-premium-sm">
                                    {['#1e293b', '#334155', '#1f2937', '#27272a', '#292524'].map((color) => (
                                        <button
                                            key={color}
                                            onClick={() => setConfig({ ...config, cardColor: color })}
                                            className={`w-10 h-10 rounded-premium-sm transition-all border-2 flex items-center justify-center group ${config.cardColor === color ? 'border-white scale-110 shadow-lg' : 'border-transparent hover:scale-105'}`}
                                            style={{ backgroundColor: color }}
                                        >
                                            {config.cardColor === color && <div className="w-1.5 h-1.5 bg-white rounded-premium-full shadow-lg" />}
                                        </button>
                                    ))}
                                    <div className="w-px h-8 bg-white/5 mx-1" />
                                    <label className="w-10 h-10 rounded-premium-sm bg-gradient-to-tr from-gray-700 to-gray-500 flex items-center justify-center cursor-pointer hover:scale-105 transition-all relative overflow-hidden">
                                        <Palette className="w-4 h-4 text-white" />
                                        <input
                                            type="color"
                                            value={config.cardColor || '#1e293b'}
                                            onChange={(e) => setConfig({ ...config, cardColor: e.target.value })}
                                            className="absolute inset-0 opacity-0 cursor-pointer w-full h-full scale-150"
                                        />
                                    </label>
                                </div>
                            </div>

                            {/* Transparency Sliders Section */}
                            <div className="space-y-8">
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1 inline-block">Efectos de Transparencia</label>
                                <div className="space-y-6">
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center bg-white/5 p-3 rounded-premium-sm border border-white/5">
                                            <span className="text-xs font-bold text-gray-300">Intensidad del Desenfoque (Blur)</span>
                                            <span className="text-sm font-black text-primary font-mono">{config.glassBlur}px</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="0"
                                            max="40"
                                            value={config.glassBlur}
                                            onChange={(e) => setConfig({ ...config, glassBlur: parseInt(e.target.value) })}
                                            className="w-full accent-primary h-1.5 bg-white/10 rounded-premium-full appearance-none cursor-pointer"
                                        />
                                    </div>
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center bg-white/5 p-3 rounded-premium-sm border border-white/5">
                                            <span className="text-xs font-bold text-gray-300">Opacidad de Paneles (Alpha)</span>
                                            <span className="text-sm font-black text-primary font-mono">{Math.round(config.glassOpacity * 100)}%</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={config.glassOpacity * 100}
                                            onChange={(e) => setConfig({ ...config, glassOpacity: parseInt(e.target.value) / 100 })}
                                            className="w-full accent-primary h-1.5 bg-white/10 rounded-premium-full appearance-none cursor-pointer"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Additional Spacings/Layout */}
                            <div className="space-y-8">
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1 inline-block">Proporciones y Opacidad</label>
                                <div className="space-y-6">
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center bg-white/5 p-3 rounded-premium-sm border border-white/5">
                                            <span className="text-xs font-bold text-gray-300">Ancho de Portadas</span>
                                            <span className="text-sm font-black text-primary font-mono">{config.coverWidth}px</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="80"
                                            max="240"
                                            value={config.coverWidth}
                                            onChange={(e) => setConfig({ ...config, coverWidth: parseInt(e.target.value) })}
                                            className="w-full accent-primary h-1.5 bg-white/10 rounded-premium-full appearance-none cursor-pointer"
                                        />
                                    </div>
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center bg-white/5 p-3 rounded-premium-sm border border-white/5">
                                            <span className="text-xs font-bold text-gray-300">Resplandor de Tarjetas (Glow)</span>
                                            <span className="text-sm font-black text-primary font-mono">{Math.round(config.cardGlowIntensity * 100)}%</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={config.cardGlowIntensity * 100}
                                            onChange={(e) => setConfig({ ...config, cardGlowIntensity: parseInt(e.target.value) / 100 })}
                                            className="w-full accent-primary h-1.5 bg-white/10 rounded-premium-full appearance-none cursor-pointer"
                                        />
                                    </div>
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center bg-white/5 p-3 rounded-premium-sm border border-white/5">
                                            <span className="text-xs font-bold text-gray-300">Opacidad Navegación</span>
                                            <span className="text-sm font-black text-primary font-mono">{Math.round(config.navOpacity * 100)}%</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={config.navOpacity * 100}
                                            onChange={(e) => setConfig({ ...config, navOpacity: parseInt(e.target.value) / 100 })}
                                            className="w-full accent-primary h-1.5 bg-white/10 rounded-premium-full appearance-none cursor-pointer"
                                        />
                                    </div>
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center bg-white/5 p-3 rounded-premium-sm border border-white/5">
                                            <span className="text-xs font-bold text-gray-300">Opacidad Acento</span>
                                            <span className="text-sm font-black text-primary font-mono">{Math.round(config.accentOpacity * 100)}%</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={config.accentOpacity * 100}
                                            onChange={(e) => setConfig({ ...config, accentOpacity: parseInt(e.target.value) / 100 })}
                                            className="w-full accent-primary h-1.5 bg-white/10 rounded-premium-full appearance-none cursor-pointer"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Global Specifics (Offset Banner) */}
                        {selectedLevelId === 'global' && (
                            <div className="border-t border-white/5 pt-8">
                                <div className="p-6 rounded-premium-sm bg-amber-500/5 border border-amber-500/10">
                                    <div className="flex justify-between items-center mb-3">
                                        <div className="flex items-center gap-2">
                                            <label className="text-[10px] font-black text-amber-500 uppercase tracking-widest">Offset Banner Serie (PX)</label>
                                            <span className="px-2 py-0.5 rounded-premium-sm bg-amber-500 text-black text-[8px] font-black uppercase">Global-Only</span>
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
                                        className="w-full h-1.5 bg-white/5 rounded-premium-full appearance-none cursor-pointer accent-amber-500"
                                    />
                                    <p className="mt-3 text-[9px] text-amber-500/60 italic font-medium">Ajusta la posición vertical del título y sinopsis en el banner.</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Column: Visibility / Exported Settings */}
                <div className="lg:col-span-4 space-y-8">
                    <div className="glass-panel p-8 rounded-premium-lg border border-primary/20 bg-primary/5 space-y-6 shadow-premium relative overflow-hidden backdrop-blur-xl">
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
                                const isChecked = (config.exportedSettings || []).includes(opt.key);
                                return (
                                    <div
                                        key={opt.key}
                                        onClick={() => toggleExported(opt.key)}
                                        className={`flex items-center justify-between p-4 rounded-premium-sm border transition-all cursor-pointer group ${isChecked
                                            ? 'bg-primary/20 border-primary/40 shadow-inner'
                                            : 'bg-black/20 border-white/5 hover:border-white/10'
                                            }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-premium-sm border transition-all ${isChecked ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20' : 'bg-white/5 text-gray-500 border-white/5'}`}>
                                                <opt.icon className="w-4 h-4" />
                                            </div>
                                            <span className={`text-xs font-black uppercase tracking-tight transition-colors ${isChecked ? 'text-white' : 'text-gray-500'}`}>{opt.label}</span>
                                        </div>
                                        <div className={`size-5 rounded-premium-sm border-2 transition-all flex items-center justify-center ${isChecked ? 'bg-primary border-primary' : 'bg-transparent border-white/10'}`}>
                                            {isChecked && <CheckCircle2 className="size-3.5 text-white" strokeWidth={3} />}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        <div className="space-y-4 pt-4 border-t border-white/5">
                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1 mb-2 inline-block">Permisos Especiales</label>

                            <label className="flex items-center justify-between p-4 rounded-premium-sm bg-black/40 border border-white/5 cursor-pointer group hover:border-primary/30 transition-all">
                                <div className="flex flex-col gap-1">
                                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest group-hover:text-primary transition-colors">Selección de Temas</span>
                                    <span className="text-[9px] text-gray-500 font-bold uppercase leading-relaxed">Permite al usuario elegir plantillas</span>
                                </div>
                                <div className="relative">
                                    <input
                                        type="checkbox"
                                        checked={config.allowThemeTemplates}
                                        onChange={(e) => setConfig({ ...config, allowThemeTemplates: e.target.checked })}
                                        className="sr-only"
                                    />
                                    <div className={`w-10 h-5 rounded-premium-full transition-all duration-300 ${config.allowThemeTemplates ? 'bg-primary shadow-lg shadow-primary/20' : 'bg-white/10'}`}></div>
                                    <div className={`absolute top-1 left-1 w-3 h-3 rounded-premium-full bg-white transition-all duration-300 ${config.allowThemeTemplates ? 'translate-x-5' : ''}`}></div>
                                </div>
                            </label>

                            <div className="p-4 rounded-premium-sm bg-black/40 border border-white/5">
                                <div className="flex items-center gap-3 mb-2">
                                    <RotateCcw className="w-4 h-4 text-gray-500" />
                                    <span className="text-[10px] font-black text-gray-400 uppercase">Forzar Aplicación</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-[9px] text-gray-500 font-bold uppercase w-2/3 leading-relaxed">Sobreescribir ajustes personales</span>
                                    <button
                                        onClick={() => setConfig({ ...config, forceSettings: !config.forceSettings })}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-premium-full transition-colors focus:outline-none ${config.forceSettings ? 'bg-primary' : 'bg-white/10'}`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-premium-full bg-white transition-transform ${config.forceSettings ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Save Button */}
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 text-white font-black uppercase tracking-widest py-4 rounded-premium-sm flex items-center justify-center gap-3 shadow-xl shadow-primary/20 transition-all active:scale-95 overflow-hidden group relative"
                        >
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
                            {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
                            <span>{saving ? 'Guardando...' : `Guardar Cambios (${selectedLevelId === 'global' ? 'Global' : config.name})`}</span>
                        </button>
                    </div>

                    {/* Quick Preview Badge */}
                    <div className="p-8 rounded-premium-lg bg-gradient-to-br from-slate-900 to-black border border-white/5 shadow-premium flex flex-col items-center justify-center text-center gap-4 group hover:border-primary/30 transition-all duration-500">
                        <div className="size-20 rounded-premium-full bg-primary/10 flex items-center justify-center border border-primary/20 group-hover:scale-110 transition-transform duration-500">
                            <div className="size-14 rounded-premium-full bg-primary shadow-premium flex items-center justify-center text-white">
                                <Eye className="w-8 h-8" />
                            </div>
                        </div>
                        <div>
                            <h4 className="text-white font-black uppercase tracking-tighter">Vista en Vivo</h4>
                            <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest mt-1 leading-relaxed">
                                Los usuarios de este nivel {selectedLevelId === 'global' ? 'por defecto' : ''} verán estos cambios al navegar.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            {/* Save Theme Modal */}
            {showSaveThemeModal && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-300">
                    <div className="bg-[#121212] border border-white/10 rounded-premium-lg p-8 max-w-md w-full shadow-premium space-y-6">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-purple-500/20 rounded-premium-sm border border-purple-500/20">
                                <Palette className="w-6 h-6 text-purple-400" />
                            </div>
                            <h3 className="text-xl font-black text-white uppercase tracking-tight">Nuevo Tema de Plantilla</h3>
                        </div>

                        <p className="text-xs text-gray-400 font-medium">
                            Esto guardará la configuración actual como una plantilla seleccionable en la biblioteca de temas.
                        </p>

                        <div className="space-y-2">
                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1">Nombre del Tema</label>
                            <input
                                type="text"
                                value={newThemeName}
                                onChange={(e) => setNewThemeName(e.target.value)}
                                placeholder="Ej: Ocean Blue, Cyberpunk..."
                                className="w-full bg-white/5 border border-white/10 rounded-premium-sm px-4 py-3 text-white focus:outline-none focus:ring-1 focus:ring-purple-500 transition-all"
                                autoFocus
                            />
                        </div>

                        <div className="flex gap-3 pt-4">
                            <button
                                onClick={() => setShowSaveThemeModal(false)}
                                className="flex-1 px-6 py-4 rounded-premium-sm border border-white/10 text-[10px] font-black uppercase text-gray-400 hover:bg-white/5"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleSaveAsTheme}
                                disabled={saving || !newThemeName.trim()}
                                className="flex-1 px-6 py-4 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded-premium-sm text-[10px] font-black uppercase text-white shadow-lg shadow-purple-600/20 transition-all"
                            >
                                {saving ? 'Guardando...' : 'Crear Tema'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
