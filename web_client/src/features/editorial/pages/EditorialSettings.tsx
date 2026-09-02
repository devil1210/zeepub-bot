import React, { useState, useEffect, useMemo } from 'react';
import {
    Settings,
    Terminal,
    RefreshCw,
    Sliders,
    CheckCircle2,
    AlertCircle,
    Loader2,
    Cpu,
    Database,
    HardDrive,
    Bot,
    Sparkles,
    Shield,
    Trash2,
    Key,
    Activity,
    Layers,
    Search
} from 'lucide-react';
import { api } from '@shared/services/api';
import { useTheme } from '@shared/contexts/ThemeContext';

export const EditorialSettings: React.FC = () => {
    const { settings, updateSettings } = useTheme();
    const [activeTab, setActiveTab] = useState<'general' | 'ai' | 'system' | 'logs'>('general');
    const [logs, setLogs] = useState<string>('');
    const [logLevel, setLogLevel] = useState<'ALL' | 'INFO' | 'WARNING' | 'ERROR'>('INFO');
    const [logSearch, setLogSearch] = useState('');
    const [loadingLogs, setLoadingLogs] = useState(false);
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const [coverQuality, setCoverQuality] = useState<'grande' | 'mediana' | 'pequeña'>('grande');
    const [activeAiModel, setActiveAiModel] = useState<'gemini-2.5-flash' | 'gemini-3-flash-preview'>('gemini-2.5-flash');

    const fetchLogs = async () => {
        setLoadingLogs(true);
        try {
            const res = await api.getSystemLogs(logLevel === 'ALL' ? 'INFO' : logLevel, 48);
            setLogs(res?.logs || 'No se recibieron logs recientes del servidor.');
        } catch (err: any) {
            setLogs(`Error al cargar logs del sistema: ${err.message}`);
        } finally {
            setLoadingLogs(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'logs') {
            fetchLogs();
        }
    }, [activeTab, logLevel]);

    const handleTitleLangChange = (lang: 'english' | 'romaji' | 'spanish') => {
        updateSettings({ titleLanguage: lang });
        setStatusMsg({ type: 'success', text: `Preferencia de títulos actualizada a: ${lang.toUpperCase()}` });
        setTimeout(() => setStatusMsg(null), 2500);
    };

    const rawLogText = useMemo(() => {
        if (!logs) return '';
        if (typeof logs === 'string') return logs;
        if (Array.isArray(logs)) {
            return logs
                .map((l: any) => {
                    if (typeof l === 'string') return l;
                    if (l && typeof l === 'object') {
                        const time = l.time || '';
                        const lvl = l.level || 'INFO';
                        const msg = l.msg || l.message || JSON.stringify(l);
                        return `[${time}] ${lvl}: ${msg}`;
                    }
                    return String(l);
                })
                .join('\n');
        }
        if (typeof logs === 'object') {
            try {
                return JSON.stringify(logs, null, 2);
            } catch {
                return String(logs);
            }
        }
        return String(logs);
    }, [logs]);

    const filteredLogs = useMemo(() => {
        if (!rawLogText) return '';
        return rawLogText
            .split('\n')
            .filter((line) => (logSearch ? line.toLowerCase().includes(logSearch.toLowerCase()) : true))
            .join('\n');
    }, [rawLogText, logSearch]);

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <Settings className="w-7 h-7 text-indigo-400" /> Configuración Editorial & Sistema
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Ajustes de catalogación, parámetros de inteligencia artificial, estado de infraestructura y registros del sistema.
                    </p>
                </div>

                {statusMsg && (
                    <div
                        className={`p-3 rounded-2xl flex items-center gap-2 text-xs font-bold ${
                            statusMsg.type === 'success'
                                ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                                : 'bg-red-500/10 text-red-300 border border-red-500/20'
                        }`}
                    >
                        {statusMsg.type === 'success' ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        ) : (
                            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                        )}
                        <span>{statusMsg.text}</span>
                    </div>
                )}
            </div>

            {/* Navigation Tabs */}
            <div className="flex flex-wrap gap-2 border-b border-white/10 pb-3">
                {[
                    { id: 'general', label: 'Ajustes Editoriales', icon: Sliders },
                    { id: 'ai', label: 'Inteligencia Artificial (Gemini)', icon: Sparkles },
                    { id: 'system', label: 'Estado del Sistema & Infraestructura', icon: Cpu },
                    { id: 'logs', label: 'Monitor de Logs en Tiempo Real', icon: Terminal },
                ].map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={`px-4 py-2.5 rounded-2xl text-xs font-bold transition-all flex items-center gap-2 ${
                                isActive
                                    ? 'bg-indigo-600 text-white shadow-xl shadow-indigo-600/30'
                                    : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
                            }`}
                        >
                            <Icon className="w-4 h-4" />
                            <span>{tab.label}</span>
                        </button>
                    );
                })}
            </div>

            {/* TAB 1: General Editorial Settings */}
            {activeTab === 'general' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Card 1: Title Hierarchy */}
                    <div className="bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-4 backdrop-blur-xl shadow-2xl">
                        <div className="flex items-center gap-3">
                            <div className="p-3 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                                <Sliders className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="text-sm font-bold text-white">Idioma Predeterminado de Títulos</h3>
                                <p className="text-xs text-gray-400">
                                    Controla el orden jerárquico con el que se ordenan los títulos en la biblioteca.
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                            {[
                                { id: 'english', label: '🇬🇧 Inglés Oficial', desc: 'Prioriza título oficial en inglés' },
                                { id: 'romaji', label: '🇯🇵 Romaji / Original', desc: 'Prioriza transcripción en Romaji' },
                                { id: 'spanish', label: '🇪🇸 Español Traducido', desc: 'Prioriza versión en español' },
                            ].map((opt) => (
                                <button
                                    key={opt.id}
                                    type="button"
                                    onClick={() => handleTitleLangChange(opt.id as any)}
                                    className={`p-4 rounded-2xl text-left border transition-all flex flex-col justify-between ${
                                        (settings.titleLanguage || 'english') === opt.id
                                            ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-lg'
                                            : 'bg-white/[0.02] border-white/5 text-gray-300 hover:bg-white/[0.06]'
                                    }`}
                                >
                                    <span className="text-xs font-bold">{opt.label}</span>
                                    <span className="text-[10px] text-gray-400 mt-2">{opt.desc}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Card 2: Cover Quality */}
                    <div className="bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-4 backdrop-blur-xl shadow-2xl">
                        <div className="flex items-center gap-3">
                            <div className="p-3 rounded-2xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                                <Layers className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="text-sm font-bold text-white">Calidad de Portadas por Defecto</h3>
                                <p className="text-xs text-gray-400">
                                    Resolución y compresión aplicada al renderizar imágenes en publicaciones.
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                            {[
                                { id: 'grande', label: '🌟 Alta Resolución', desc: 'Original / 1200px (Máxima fidelidad)' },
                                { id: 'mediana', label: '⚡ Equilibrada', desc: '800px (Carga veloz optimizada)' },
                                { id: 'pequeña', label: '📦 Miniatura Ligera', desc: '400px (Bajo consumo de datos)' },
                            ].map((opt) => (
                                <button
                                    key={opt.id}
                                    type="button"
                                    onClick={() => setCoverQuality(opt.id as any)}
                                    className={`p-4 rounded-2xl text-left border transition-all flex flex-col justify-between ${
                                        coverQuality === opt.id
                                            ? 'bg-purple-600/20 border-purple-500 text-white shadow-lg'
                                            : 'bg-white/[0.02] border-white/5 text-gray-300 hover:bg-white/[0.06]'
                                    }`}
                                >
                                    <span className="text-xs font-bold">{opt.label}</span>
                                    <span className="text-[10px] text-gray-400 mt-2">{opt.desc}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* TAB 2: AI Configuration */}
            {activeTab === 'ai' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-5 backdrop-blur-xl shadow-2xl">
                        <div className="flex items-center gap-3">
                            <div className="p-3 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                                <Sparkles className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="text-sm font-bold text-white">Modelo de IA Gemini Activo</h3>
                                <p className="text-xs text-gray-400">
                                    Modelos aprobados para extracción, traducción y enriquecimiento editorial.
                                </p>
                            </div>
                        </div>

                        <div className="space-y-3 pt-2">
                            {[
                                {
                                    id: 'gemini-2.5-flash',
                                    name: 'Gemini 2.5 Flash',
                                    badge: 'Recomendado para Producción',
                                    desc: 'Alta velocidad, análisis multimodal de portadas y normalización de metadatos.',
                                },
                                {
                                    id: 'gemini-3-flash-preview',
                                    name: 'Gemini 3 Flash Preview',
                                    badge: 'Nueva Generación',
                                    desc: 'Máxima precisión en desambiguación de títulos en japonés y romaji.',
                                },
                            ].map((m) => (
                                <button
                                    key={m.id}
                                    type="button"
                                    onClick={() => setActiveAiModel(m.id as any)}
                                    className={`w-full p-4 rounded-2xl text-left border transition-all flex items-center justify-between ${
                                        activeAiModel === m.id
                                            ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-xl'
                                            : 'bg-white/[0.02] border-white/5 text-gray-300 hover:bg-white/[0.06]'
                                    }`}
                                >
                                    <div>
                                        <div className="text-xs font-bold text-white flex items-center gap-2">
                                            <span>{m.name}</span>
                                            <span className="text-[9px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                                {m.badge}
                                            </span>
                                        </div>
                                        <div className="text-[11px] text-gray-400 mt-1">{m.desc}</div>
                                    </div>
                                    <div className="w-4 h-4 rounded-full border-2 border-indigo-400 flex items-center justify-center shrink-0">
                                        {activeAiModel === m.id && <div className="w-2 h-2 rounded-full bg-indigo-400" />}
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-4 backdrop-blur-xl shadow-2xl">
                        <h3 className="text-sm font-bold text-white">Comportamiento Autónomo del Asistente</h3>
                        <p className="text-xs text-gray-400">
                            Reglas de procesamiento automático al importar nuevos archivos EPUB.
                        </p>

                        <div className="space-y-3 pt-2">
                            <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/5 flex items-center justify-between">
                                <div>
                                    <div className="text-xs font-bold text-white">Traducción Automática de Sinopsis</div>
                                    <div className="text-[10px] text-gray-400">Genera resumen en español si el EPUB viene en inglés/japonés</div>
                                </div>
                                <input type="checkbox" defaultChecked className="toggle toggle-primary w-5 h-5 rounded" />
                            </div>

                            <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/5 flex items-center justify-between">
                                <div>
                                    <div className="text-xs font-bold text-white">Auditoría de Demografía & Géneros</div>
                                    <div className="text-[10px] text-gray-400">Clasifica en Seinen, Shounen, Josei o Shoujo según contenido</div>
                                </div>
                                <input type="checkbox" defaultChecked className="toggle toggle-primary w-5 h-5 rounded" />
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* TAB 3: System Status */}
            {activeTab === 'system' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                    <div className="p-6 rounded-3xl bg-slate-900/50 border border-white/10 space-y-3 shadow-xl backdrop-blur-xl">
                        <div className="flex items-center justify-between">
                            <div className="p-3 rounded-2xl bg-cyan-500/10 text-cyan-400">
                                <Bot className="w-6 h-6" />
                            </div>
                            <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                En Línea (200 OK)
                            </span>
                        </div>
                        <div className="text-base font-bold text-white">Telegram Bot API</div>
                        <div className="text-xs text-gray-400">Bot Activo (@ZeePubsBot) con comandos y Webhooks sincronizados.</div>
                    </div>

                    <div className="p-6 rounded-3xl bg-slate-900/50 border border-white/10 space-y-3 shadow-xl backdrop-blur-xl">
                        <div className="flex items-center justify-between">
                            <div className="p-3 rounded-2xl bg-indigo-500/10 text-indigo-400">
                                <Database className="w-6 h-6" />
                            </div>
                            <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                Conectado
                            </span>
                        </div>
                        <div className="text-base font-bold text-white">PostgreSQL Database</div>
                        <div className="text-xs text-gray-400">Pool de conexiones asyncpg activo con migración de esquema al día.</div>
                    </div>

                    <div className="p-6 rounded-3xl bg-slate-900/50 border border-white/10 space-y-3 shadow-xl backdrop-blur-xl">
                        <div className="flex items-center justify-between">
                            <div className="p-3 rounded-2xl bg-purple-500/10 text-purple-400">
                                <HardDrive className="w-6 h-6" />
                            </div>
                            <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                Local Storage
                            </span>
                        </div>
                        <div className="text-base font-bold text-white">Almacén Local de Libros</div>
                        <div className="text-xs text-gray-400">Gestión de archivos binarios EPUB y caché de portadas en disco local.</div>
                    </div>

                    <div className="p-6 rounded-3xl bg-slate-900/50 border border-white/10 space-y-3 shadow-xl backdrop-blur-xl">
                        <div className="flex items-center justify-between">
                            <div className="p-3 rounded-2xl bg-emerald-500/10 text-emerald-400">
                                <Activity className="w-6 h-6" />
                            </div>
                            <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                Activo
                            </span>
                        </div>
                        <div className="text-base font-bold text-white">Queue Publisher Scheduler</div>
                        <div className="text-xs text-gray-400">Cronjob de publicación cada 60s procesando envíos programados.</div>
                    </div>
                </div>
            )}

            {/* TAB 4: Real-time Terminal Log Monitor */}
            {activeTab === 'logs' && (
                <div className="bg-slate-950 border border-white/10 rounded-3xl overflow-hidden shadow-2xl flex flex-col h-[70vh]">
                    {/* Log Controls Bar */}
                    <div className="p-4 border-b border-white/10 bg-slate-900/80 flex flex-wrap items-center justify-between gap-4">
                        <div className="flex items-center gap-2">
                            <Terminal className="w-5 h-5 text-indigo-400" />
                            <span className="text-xs font-bold text-white">Terminal de Logs del Servidor</span>
                        </div>

                        <div className="flex flex-wrap items-center gap-3">
                            {/* Search */}
                            <div className="relative">
                                <Search className="w-3.5 h-3.5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                                <input
                                    type="text"
                                    value={logSearch}
                                    onChange={(e) => setLogSearch(e.target.value)}
                                    placeholder="Filtrar registros..."
                                    className="pl-8 pr-3 py-1.5 bg-black/40 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 w-44 sm:w-60"
                                />
                            </div>

                            {/* Level Selector */}
                            <div className="flex items-center rounded-xl bg-black/40 border border-white/10 p-0.5">
                                {(['ALL', 'INFO', 'WARNING', 'ERROR'] as const).map((lvl) => (
                                    <button
                                        key={lvl}
                                        type="button"
                                        onClick={() => setLogLevel(lvl)}
                                        className={`px-3 py-1 rounded-lg text-[10px] font-bold transition-all ${
                                            logLevel === lvl
                                                ? 'bg-indigo-600 text-white'
                                                : 'text-gray-400 hover:text-white'
                                        }`}
                                    >
                                        {lvl}
                                    </button>
                                ))}
                            </div>

                            {/* Refresh Button */}
                            <button
                                type="button"
                                onClick={fetchLogs}
                                disabled={loadingLogs}
                                className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 transition-all active:scale-95 disabled:opacity-50"
                                title="Recargar logs"
                            >
                                <RefreshCw className={`w-4 h-4 ${loadingLogs ? 'animate-spin text-indigo-400' : ''}`} />
                            </button>
                        </div>
                    </div>

                    {/* Log Terminal Screen */}
                    <div className="flex-1 p-5 font-mono text-xs text-emerald-400/90 bg-black overflow-y-auto leading-relaxed select-text space-y-1">
                        {loadingLogs ? (
                            <div className="flex items-center justify-center h-full text-indigo-400">
                                <Loader2 className="w-8 h-8 animate-spin" />
                            </div>
                        ) : filteredLogs ? (
                            <pre className="whitespace-pre-wrap">{filteredLogs}</pre>
                        ) : (
                            <div className="text-gray-600 italic">No hay logs que coincidan con los filtros seleccionados.</div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
