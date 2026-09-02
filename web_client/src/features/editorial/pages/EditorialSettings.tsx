import React, { useState, useEffect } from 'react';
import { Settings, Terminal, RefreshCw, Sliders, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '@shared/services/api';
import { useTheme } from '@shared/contexts/ThemeContext';

export const EditorialSettings: React.FC = () => {
    const { settings, updateSettings } = useTheme();
    const [activeTab, setActiveTab] = useState<'general' | 'logs'>('general');
    const [logs, setLogs] = useState<string>('');
    const [loadingLogs, setLoadingLogs] = useState(false);
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const fetchLogs = async () => {
        setLoadingLogs(true);
        try {
            const res = await api.getSystemLogs('INFO', 24);
            setLogs(res?.logs || 'No se recibieron logs recientes.');
        } catch (err: any) {
            setLogs(`Error al cargar logs: ${err.message}`);
        } finally {
            setLoadingLogs(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'logs') {
            fetchLogs();
        }
    }, [activeTab]);

    const handleTitleLangChange = (lang: 'english' | 'romaji' | 'spanish') => {
        updateSettings({ titleLanguage: lang });
        setStatusMsg({ type: 'success', text: `Preferencia de títulos actualizada a: ${lang.toUpperCase()}` });
        setTimeout(() => setStatusMsg(null), 2500);
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
                    <Settings className="w-6 h-6 text-indigo-400" /> Configuración Editorial & Logs
                </h2>
                <p className="text-xs text-gray-400 mt-1">
                    Preferencias de catalogación, idioma por defecto de títulos y monitor de registros del sistema.
                </p>
            </div>

            {statusMsg && (
                <div
                    className={`p-3 rounded-xl flex items-center gap-2 text-xs font-medium ${
                        statusMsg.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : 'bg-red-500/10 text-red-300 border border-red-500/20'
                    }`}
                >
                    {statusMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    <span>{statusMsg.text}</span>
                </div>
            )}

            {/* Tab Navigation */}
            <div className="flex gap-2 border-b border-white/10 pb-2">
                <button
                    onClick={() => setActiveTab('general')}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                        activeTab === 'general'
                            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                >
                    <Sliders className="w-4 h-4" /> Ajustes Editoriales
                </button>
                <button
                    onClick={() => setActiveTab('logs')}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                        activeTab === 'logs'
                            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                >
                    <Terminal className="w-4 h-4" /> Monitor de Logs
                </button>
            </div>

            {/* General Settings Tab */}
            {activeTab === 'general' && (
                <div className="bg-slate-900/50 border border-white/10 rounded-2xl p-6 space-y-6 backdrop-blur-xl">
                    <div>
                        <h3 className="text-sm font-bold text-white mb-1">Idioma Predeterminado de Títulos</h3>
                        <p className="text-xs text-gray-400 mb-3">
                            Controla el orden jerárquico canónico con el que se visualizan los títulos en la consola.
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                            {[
                                { id: 'english', label: '🇬🇧 Inglés Oficial', desc: 'Prioriza título oficial en inglés' },
                                { id: 'romaji', label: '🇯🇵 Romaji / Original', desc: 'Prioriza transcripción en Romaji' },
                                { id: 'spanish', label: '🇪🇸 Español Traducido', desc: 'Prioriza versión en español' },
                            ].map((opt) => (
                                <button
                                    key={opt.id}
                                    type="button"
                                    onClick={() => handleTitleLangChange(opt.id as any)}
                                    className={`p-4 rounded-xl border text-left transition-all ${
                                        settings.titleLanguage === opt.id
                                            ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-lg'
                                            : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10'
                                    }`}
                                >
                                    <div className="text-xs font-bold">{opt.label}</div>
                                    <div className="text-[10px] text-gray-400 mt-1">{opt.desc}</div>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Logs Tab */}
            {activeTab === 'logs' && (
                <div className="bg-slate-900/50 border border-white/10 rounded-2xl p-6 space-y-4 backdrop-blur-xl">
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-gray-300">Últimos registros del servidor</span>
                        <button
                            onClick={fetchLogs}
                            disabled={loadingLogs}
                            className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white text-xs font-bold flex items-center gap-1.5 transition-all border border-white/10"
                        >
                            {loadingLogs ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                            Recargar Logs
                        </button>
                    </div>

                    <div className="p-4 rounded-xl bg-black/80 border border-white/5 font-mono text-[11px] text-emerald-400 whitespace-pre-wrap max-h-[500px] overflow-y-auto leading-relaxed select-all">
                        {loadingLogs ? 'Cargando registros...' : logs}
                    </div>
                </div>
            )}
        </div>
    );
};
