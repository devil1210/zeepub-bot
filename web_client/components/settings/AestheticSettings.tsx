import React, { useState } from 'react';
import { Palette, Sun, Moon, Contrast, PenTool, CheckCircle2, RotateCcw, Save } from 'lucide-react';
import { adjustBrightness } from '../../contexts/ThemeContext';

interface AestheticSettingsProps {
    settings: any;
    updateSettings: (s: any) => void;
    resetSettings: () => void;
    handleSave: () => void;
    isSaving: boolean;
    isAdmin: boolean;
    allowThemeTemplates: boolean;
    availableThemes: any[];
    isVisible: (key: string) => boolean;
}

export const AestheticSettings: React.FC<AestheticSettingsProps> = ({
    settings,
    updateSettings,
    resetSettings,
    handleSave,
    isSaving,
    isAdmin,
    allowThemeTemplates,
    availableThemes,
    isVisible
}) => {
    const [selectedElement, setSelectedElement] = useState<'nav' | 'searchbar' | 'header' | 'glass'>('nav');

    const handleColorChange = (color: string) => {
        updateSettings({
            primaryColor: color,
            primaryColorDark: adjustBrightness(color, -20)
        });
    };

    return (
        <div className="glass-panel p-10 rounded-premium-lg flex flex-col gap-12 border border-white/5 shadow-2xl relative overflow-hidden group">
            <div className="absolute -top-24 -right-24 w-64 h-64 bg-primary/10 rounded-full blur-[100px] pointer-events-none group-hover:bg-primary/20 transition-all duration-1000"></div>

            <div className="flex border-b border-white/5 pb-8">
                <div className="flex items-center gap-5">
                    <div className="p-3 rounded-[1.25rem] bg-indigo-500/20 text-indigo-400 border border-indigo-500/20 shadow-lg">
                        <Palette className="w-6 h-6" strokeWidth={2.5} />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-white uppercase tracking-tighter">Estética Pro Max</h2>
                        <p className="text-[10px] text-indigo-400/60 font-black uppercase tracking-[0.3em] leading-none mt-1.5">Arquitectura visual avanzada</p>
                    </div>
                </div>
            </div>

            {/* Theme Templates Selector */}
            {(allowThemeTemplates || isAdmin) && availableThemes.length > 0 && (
                <div className="space-y-6">
                    <div className="flex items-center justify-between px-1">
                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Templates de Autor</label>
                        <span className="text-[9px] font-black text-primary bg-primary/10 px-3 py-1 rounded-full uppercase tracking-widest">{availableThemes.length} Curados</span>
                    </div>
                    <div className="flex gap-5 overflow-x-auto pb-6 custom-scrollbar px-1">
                        {availableThemes.map((theme) => {
                            const isCurrent = settings.theme === theme.theme_type && (settings.primaryColor === theme.primary_color || settings.primaryColor === theme.primaryColor);
                            return (
                                <button
                                    key={theme.id}
                                    onClick={() => {
                                        updateSettings({
                                            theme: theme.theme_type,
                                            primaryColor: theme.primaryColor || theme.primary_color,
                                            primaryColorDark: adjustBrightness(theme.primaryColor || theme.primary_color, -20),
                                            backgroundColor: theme.backgroundColor || theme.background_color,
                                            cardColor: theme.cardColor || theme.card_color,
                                            glassBlur: theme.glassBlur || theme.glass_blur,
                                            glassOpacity: theme.glassOpacity || theme.glass_opacity,
                                            navOpacity: theme.navOpacity || theme.nav_opacity,
                                            accentOpacity: theme.accentOpacity || theme.accent_opacity,
                                            cardGlowIntensity: theme.cardGlowIntensity || theme.card_glow_intensity || 0.5,
                                        });
                                    }}
                                    className={`flex-shrink-0 w-44 p-5 rounded-[2rem] border-2 transition-all duration-500 flex flex-col gap-4 group/theme relative overflow-hidden ${isCurrent ? 'border-primary bg-primary/10 shadow-[0_20px_40px_-10px_rgba(var(--color-primary-rgb),0.3)]' : 'border-white/5 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.06]'}`}
                                >
                                    <div className="absolute top-0 right-0 p-3 opacity-5 group-hover/theme:rotate-12 transition-transform">
                                        <Palette className="w-10 h-10" />
                                    </div>

                                    <div className="flex flex-col gap-1 z-10 text-left">
                                        <span className={`text-[12px] font-black uppercase transition-colors ${isCurrent ? 'text-primary' : 'text-white'}`}>{theme.name}</span>
                                        <span className="text-[8px] font-black text-gray-500 uppercase tracking-widest">{theme.theme_type} Engine</span>
                                    </div>

                                    <div className="flex gap-2 mt-auto">
                                        <div className="size-5 rounded-full shadow-2xl border-2 border-[#0a0a0c]" style={{ backgroundColor: theme.primary_color || theme.primaryColor }}></div>
                                        <div className="size-5 rounded-full shadow-2xl border-2 border-[#0a0a0c]" style={{ backgroundColor: theme.background_color || theme.backgroundColor }}></div>
                                    </div>

                                    {isCurrent && (
                                        <div className="absolute top-3 right-3 animate-in zoom-in duration-500">
                                            <CheckCircle2 className="w-4 h-4 text-primary" strokeWidth={3} />
                                        </div>
                                    )}
                                </button>
                            );
                        })}
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-12">
                {/* Theme Selection */}
                {isVisible('theme') && (
                    <div className="space-y-6">
                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] px-1">Motor de Renderizado</label>
                        <div className="grid grid-cols-1 gap-3">
                            {[
                                { id: 'light', icon: Sun, label: 'Crystal Light', desc: 'Diseño suave y luminoso' },
                                { id: 'dark', icon: Moon, label: 'Midnight Glass', desc: 'Profundidad y elegancia' },
                                { id: 'amoled', icon: Contrast, label: 'Absolute Black', desc: 'Optimizado para OLED' },
                            ].map((t) => (
                                <button
                                    key={t.id}
                                    onClick={() => updateSettings({ theme: t.id as any })}
                                    className={`flex items-center gap-5 p-5 rounded-[1.75rem] border-2 transition-all duration-500 group/item relative overflow-hidden ${settings.theme === t.id
                                        ? 'bg-primary/10 border-primary text-primary shadow-[0_0_25px_rgba(var(--color-primary-rgb),0.1)]'
                                        : 'bg-white/[0.03] border-white/5 text-gray-500 hover:border-white/20'
                                        }`}
                                >
                                    <div className={`p-3 rounded-premium-sm transition-all duration-500 ${settings.theme === t.id ? 'bg-primary text-white shadow-lg' : 'bg-white/5 text-gray-600 group-hover/item:text-gray-300'}`}>
                                        <t.icon className="w-5 h-5" strokeWidth={2.5} />
                                    </div>
                                    <div className="text-left">
                                        <span className={`text-[13px] font-black uppercase tracking-tight block ${settings.theme === t.id ? 'text-white' : 'text-gray-400'}`}>{t.label}</span>
                                        <span className="text-[9px] font-bold uppercase tracking-widest opacity-40">{t.desc}</span>
                                    </div>
                                    {settings.theme === t.id && <div className="ml-auto pr-2"><div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_10px_rgba(var(--color-primary-rgb),0.8)]"></div></div>}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Accent Color Selection */}
                {isVisible('primaryColor') && (
                    <div className="space-y-6">
                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] px-1">Firma de Color (Énfasis)</label>
                        <div className="p-6 bg-white/[0.03] border border-white/5 rounded-[2rem] flex flex-col gap-8">
                            <div className="flex flex-wrap gap-4">
                                {['#FB7185', '#38BDF8', '#4ADE80', '#FBBF24', '#818CF8', '#F472B6', '#A78BFA'].map((color) => (
                                    <button
                                        key={color}
                                        onClick={() => handleColorChange(color)}
                                        className={`w-10 h-10 rounded-premium-sm transition-all duration-500 border-4 flex items-center justify-center relative overflow-hidden ${settings.primaryColor === color ? 'border-primary scale-110 shadow-2xl' : 'border-white/5 hover:scale-105'}`}
                                        style={{ backgroundColor: color }}
                                    >
                                        {settings.primaryColor === color && <div className="absolute inset-0 bg-white/20 animate-pulse" />}
                                    </button>
                                ))}
                            </div>
                            <div className="flex items-center gap-4 pt-6 border-t border-white/5">
                                <div className="p-2.5 rounded-premium-sm bg-white/5 text-gray-500"><PenTool className="w-4 h-4" /></div>
                                <div className="flex-1 text-[11px] font-black text-gray-500 uppercase tracking-widest">Personalizar Tono</div>
                                <label className="relative flex items-center gap-3 cursor-pointer group/native">
                                    <div className="w-12 h-12 rounded-premium-sm border-2 border-white/10 group-hover/native:border-primary transition-all p-1">
                                        <div className="w-full h-full rounded-premium-sm shadow-inner border border-white/10" style={{ backgroundColor: settings.primaryColor }}></div>
                                    </div>
                                    <input
                                        type="color"
                                        value={settings.primaryColor}
                                        onChange={(e) => handleColorChange(e.target.value)}
                                        className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                                    />
                                </label>
                            </div>
                        </div>
                    </div>
                )}

                {/* Transparency Effects */}
                {(isVisible('glassBlur') || isVisible('glassOpacity')) && (
                    <div className="space-y-8 col-span-full border-t border-white/5 pt-10">
                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] px-1">Arquitectura de Cristal</label>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                            {isVisible('glassBlur') && (
                                <div className="space-y-5">
                                    <div className="flex justify-between items-center px-1">
                                        <span className="text-[11px] font-black text-white uppercase tracking-widest">Difusión (Gaussian Blur)</span>
                                        <span className="text-[11px] font-black text-primary font-mono bg-primary/10 px-2 py-0.5 rounded-lg">{settings.glassBlur}px</span>
                                    </div>
                                    <div className="bg-white/[0.03] p-5 rounded-premium-sm border border-white/5">
                                        <input
                                            type="range"
                                            min="0"
                                            max="40"
                                            value={settings.glassBlur}
                                            onChange={(e) => updateSettings({ glassBlur: parseInt(e.target.value) })}
                                            className="w-full accent-primary h-1 bg-gray-800 rounded-full appearance-none cursor-pointer"
                                        />
                                    </div>
                                </div>
                            )}
                            {isVisible('glassOpacity') && (
                                <div className="space-y-6 col-span-full">
                                    <div className="flex items-center justify-between px-1">
                                        <span className="text-[11px] font-black text-white uppercase tracking-widest">Opacidad por Elemento</span>
                                        <div className="flex items-center gap-2 p-1 bg-white/5 rounded-xl border border-white/5">
                                            {[
                                                { id: 'glass', label: 'Paneles' },
                                                { id: 'nav', label: 'Menú' },
                                                { id: 'header', label: 'Cabecera' },
                                                { id: 'searchbar', label: 'Buscador' }
                                            ].map(elem => (
                                                <button
                                                    key={elem.id}
                                                    onClick={() => setSelectedElement(elem.id as any)}
                                                    className={`px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all ${selectedElement === elem.id ? 'bg-primary text-white shadow-lg' : 'text-gray-500 hover:text-gray-300'}`}
                                                >
                                                    {elem.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="bg-white/[0.03] p-6 rounded-premium border border-white/5 space-y-6">
                                        <div className="flex justify-between items-center">
                                            <div className="flex flex-col">
                                                <span className="text-[13px] font-black text-white uppercase tracking-tight">
                                                    {selectedElement === 'glass' && 'Cristal de Paneles'}
                                                    {selectedElement === 'nav' && 'Transparencia del Menú'}
                                                    {selectedElement === 'header' && 'Transparencia de Cabecera'}
                                                    {selectedElement === 'searchbar' && 'Barra de Búsqueda'}
                                                </span>
                                                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest opacity-60">Control de densidad alpha</span>
                                            </div>
                                            <span className="text-[12px] font-black text-primary font-mono bg-primary/10 px-3 py-1 rounded-lg">
                                                {Math.round((
                                                    selectedElement === 'glass' ? settings.glassOpacity :
                                                        selectedElement === 'nav' ? settings.navOpacity :
                                                            selectedElement === 'header' ? settings.headerOpacity :
                                                                settings.searchBarOpacity
                                                ) * 100)}%
                                            </span>
                                        </div>

                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={(
                                                selectedElement === 'glass' ? settings.glassOpacity :
                                                    selectedElement === 'nav' ? settings.navOpacity :
                                                        selectedElement === 'header' ? settings.headerOpacity :
                                                            settings.searchBarOpacity
                                            ) * 100}
                                            onChange={(e) => {
                                                const val = parseInt(e.target.value) / 100;
                                                if (selectedElement === 'glass') updateSettings({ glassOpacity: val });
                                                else if (selectedElement === 'nav') updateSettings({ navOpacity: val });
                                                else if (selectedElement === 'header') updateSettings({ headerOpacity: val });
                                                else updateSettings({ searchBarOpacity: val });
                                            }}
                                            className="w-full accent-primary h-1 bg-gray-800 rounded-full appearance-none cursor-pointer"
                                        />

                                        <p className="text-[10px] text-gray-600 font-medium leading-relaxed italic">
                                            * Ajusta qué tan translúcido se verán los elementos de cristal {selectedElement === 'glass' ? 'en toda la interfaz' : 'específicos'}. El modo AMOLED fuerza opacidad 100%.
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Structural Aesthetic Controls */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mt-12 pt-12 border-t border-white/5">
                            <div className="space-y-5">
                                <div className="flex justify-between items-center px-1">
                                    <span className="text-[11px] font-black text-white uppercase tracking-widest">Curvatura (Border Radius)</span>
                                    <span className="text-[11px] font-black text-primary font-mono bg-primary/10 px-2 py-0.5 rounded-lg">{settings.borderRadius}px</span>
                                </div>
                                <div className="bg-white/[0.03] p-5 rounded-premium-sm border border-white/5">
                                    <input
                                        type="range"
                                        min="0"
                                        max="48"
                                        value={settings.borderRadius}
                                        onChange={(e) => updateSettings({ borderRadius: parseInt(e.target.value) })}
                                        className="w-full accent-primary h-1 bg-gray-800 rounded-full appearance-none cursor-pointer"
                                    />
                                </div>
                            </div>

                            <div className="space-y-5">
                                <div className="flex justify-between items-center px-1">
                                    <span className="text-[11px] font-black text-white uppercase tracking-widest">Grosor de Línea (Border)</span>
                                    <span className="text-[11px] font-black text-primary font-mono bg-primary/10 px-2 py-0.5 rounded-lg">{settings.borderWidth}px</span>
                                </div>
                                <div className="bg-white/[0.03] p-5 rounded-premium-sm border border-white/5">
                                    <input
                                        type="range"
                                        min="0"
                                        max="4"
                                        step="1"
                                        value={settings.borderWidth}
                                        onChange={(e) => updateSettings({ borderWidth: parseInt(e.target.value) })}
                                        className="w-full accent-primary h-1 bg-gray-800 rounded-full appearance-none cursor-pointer"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <div className="flex items-center justify-between gap-6 pt-10 border-t border-white/5">
                <button
                    onClick={resetSettings}
                    className="px-8 py-4 rounded-[1.5rem] text-[10px] font-black uppercase tracking-[0.3em] text-gray-500 hover:text-white border border-white/10 hover:bg-white/5 transition-all flex items-center gap-3"
                >
                    <RotateCcw className="w-4 h-4" />
                    Resetear Perfil
                </button>
                <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className={`px-12 py-4 rounded-[1.5rem] text-[10px] font-black uppercase tracking-[0.3em] text-white shadow-2xl flex items-center gap-4 transition-all hover:scale-105 active:scale-95 ${isSaving ? 'bg-gray-800 cursor-not-allowed opacity-50 border-white/5' : 'bg-primary border border-white/20 shadow-primary/30'
                        }`}
                >
                    {isSaving ? <RotateCcw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    {isSaving ? 'Aplicando...' : 'Confirmar Cambios'}
                </button>
            </div>
        </div>
    );
};
