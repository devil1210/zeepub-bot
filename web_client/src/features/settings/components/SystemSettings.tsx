import React from 'react';
import { Palette, Wrench, ChevronRight } from 'lucide-react';

interface SystemSettingsProps {
    settings: any;
    updateSettings: (s: any) => void;
}

export const SystemSettings: React.FC<SystemSettingsProps> = ({ settings, updateSettings }) => {
    return (
        <div className="glass-panel p-10 rounded-premium-lg shadow-2xl border-white/5 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity duration-1000">
                <Wrench className="w-32 h-32" />
            </div>

            <h3 className="text-xl font-black text-white flex items-center gap-4 mb-10 uppercase tracking-tighter">
                <div className="p-2 rounded-premium-sm bg-primary/20 text-primary border border-primary/20">
                    <Palette className="w-5 h-5" />
                </div>
                Sistema e Interfaz
            </h3>

            <div className="space-y-12">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                    <div className="space-y-4">
                        <div className="flex justify-between items-center px-1">
                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Escala de Texto</label>
                            <span className="text-[11px] font-black text-primary bg-primary/10 px-2 py-0.5 rounded-lg font-mono">{settings.fontSize}px</span>
                        </div>
                        <div className="flex items-center gap-4 bg-white/[0.03] p-4 rounded-premium-sm border border-white/5 group/slider hover:bg-white/[0.05] transition-all">
                            <span className="text-[10px] text-gray-600 font-black">A</span>
                            <input
                                type="range"
                                min="12"
                                max="20"
                                value={settings.fontSize}
                                onChange={(e) => updateSettings({ fontSize: parseInt(e.target.value) })}
                                className="w-full h-1 bg-gray-800 rounded-full appearance-none cursor-pointer accent-primary"
                            />
                            <span className="text-lg text-gray-400 font-black">A</span>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <label className="block text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] px-1">Localización</label>
                        <div className="relative group/select">
                            <select className="block w-full px-5 py-4 text-[13px] font-black border border-white/5 bg-white/[0.03] text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-premium-sm appearance-none group-hover/select:bg-white/[0.05] transition-all uppercase tracking-widest">
                                <option>English (US)</option>
                                <option selected>Español</option>
                                <option>Français</option>
                                <option>Русский</option>
                                <option>简体中文</option>
                            </select>
                            <div className="absolute inset-y-0 right-0 flex items-center pr-5 pointer-events-none text-gray-600 group-hover/select:text-primary transition-colors">
                                <ChevronRight className="w-5 h-5 rotate-90" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Cover Quality Preference */}
                <div className="pt-8 border-t border-white/5">
                    <label className="block text-[10px] font-black text-gray-500 mb-6 uppercase tracking-[0.2em] px-1">Motor de Portadas (Calidad de Renderizado)</label>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        {[
                            { id: 'pequeña', label: 'Eco', desc: 'Ahorro' },
                            { id: 'mediana', label: 'Estandar', desc: 'Media' },
                            { id: 'grande', label: 'Premium', desc: 'Res.' },
                            { id: 'original', label: 'Ultra', desc: 'Max.' }
                        ].map((q) => (
                            <label key={q.id} className="cursor-pointer group/radio">
                                <input
                                    type="radio"
                                    name="coverQuality"
                                    className="hidden peer"
                                    checked={settings.coverQuality === q.id}
                                    onChange={() => updateSettings({ coverQuality: q.id as any })}
                                />
                                <div className="p-4 rounded-premium-sm border border-white/5 bg-white/[0.03] flex flex-col items-center justify-center text-center peer-checked:border-primary peer-checked:bg-primary/10 peer-checked:shadow-[0_0_20px_rgba(var(--color-primary-rgb),0.2)] transition-all hover:bg-white/[0.06]">
                                    <span className="text-[11px] font-black text-white uppercase tracking-widest transition-colors peer-checked:text-primary">{q.label}</span>
                                    <span className="text-[8px] text-gray-500 font-black uppercase tracking-widest mt-1 opacity-50">{q.desc}</span>
                                </div>
                            </label>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};
