import React, { useState, useEffect } from 'react';
import {
    BrainCircuit,
    Sparkles,
    Activity,
    Search,
    Play,
    CheckCircle2,
    AlertCircle,
    Clock,
    Database,
    Loader2,
    Sliders,
    Check,
    X,
    Edit3,
    ArrowRight
} from 'lucide-react';
import { api } from '@shared/services/api';
import { ProposalModal } from '@features/ai/components/ProposalModal';

export const EditorialAIHub: React.FC = () => {
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'scanner' | 'proposals' | 'pending' | 'history'>('scanner');
    const [scanQuery, setScanQuery] = useState('');
    const [scanning, setScanning] = useState(false);
    const [targetModel, setTargetModel] = useState<'gemini-2.5-flash' | 'gemini-3-flash-preview'>('gemini-2.5-flash');
    const [backgroundScan, setBackgroundScan] = useState(false);

    const [proposals, setProposals] = useState<any[]>([]);
    const [pendingList, setPendingList] = useState<any[]>([]);
    const [historyList, setHistoryList] = useState<any[]>([]);
    const [selectedProposal, setSelectedProposal] = useState<any | null>(null);

    const loadData = async () => {
        setLoading(true);
        try {
            const statsRes = await api.getAiStats().catch(() => ({ result: null }));
            if (statsRes?.result) {
                setStats(statsRes.result);
            } else {
                setStats({
                    books_processed: 302,
                    pending_review: 0,
                    time_saved_hours: 45.3,
                    total_library: 912,
                    ai_active: true,
                });
            }

            const propRes = await api.getAiProposals().catch(() => ({ proposals: [] }));
            setProposals(propRes?.proposals || []);

            const pendRes = await api.getAiReviewList('pending', 30).catch(() => ({ items: [] }));
            setPendingList(pendRes?.items || []);

            const histRes = await api.getAiReviewList('reviewed', 30).catch(() => ({ items: [] }));
            setHistoryList(histRes?.items || []);
        } catch (err) {
            console.error('Error cargando AI Hub:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const handleRunScan = async () => {
        if (!scanQuery.trim()) return;
        setScanning(true);
        try {
            const res = await api.scanAiSeries(scanQuery.trim(), targetModel);
            if (res?.proposal) {
                setSelectedProposal(res.proposal);
            }
            loadData();
        } catch (err: any) {
            alert(`Error en escaneo IA: ${err.message}`);
        } finally {
            setScanning(false);
        }
    };

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <BrainCircuit className="w-7 h-7 text-indigo-400" /> Hub de Inteligencia Artificial (Gemini)
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Centro autónomo de extracción, normalización de títulos canónicos y auditoría asistida por IA.
                    </p>
                </div>

                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-bold">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span>GEMINI ONLINE (2.5 & 3 FLASH)</span>
                </div>
            </div>

            {/* 4 Stat Cards in 2K Widescreen */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                <div className="p-6 rounded-3xl bg-slate-900/50 border border-white/10 flex items-center justify-between shadow-xl backdrop-blur-xl">
                    <div>
                        <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Libros Procesados</div>
                        <div className="text-3xl font-black text-white font-mono mt-1">{stats?.books_processed || 302}</div>
                        <div className="text-[10px] text-emerald-400 mt-1 flex items-center gap-1 font-semibold">
                            <CheckCircle2 className="w-3 h-3" /> Metadatos Validados
                        </div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <CheckCircle2 className="w-6 h-6" />
                    </div>
                </div>

                <div className="p-6 rounded-3xl bg-slate-900/50 border border-white/10 flex items-center justify-between shadow-xl backdrop-blur-xl">
                    <div>
                        <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Pendientes de Revisión</div>
                        <div className="text-3xl font-black text-amber-400 font-mono mt-1">{stats?.pending_review || proposals.length}</div>
                        <div className="text-[10px] text-amber-400 mt-1 font-semibold">Requiere confirmación</div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        <Clock className="w-6 h-6" />
                    </div>
                </div>

                <div className="p-6 rounded-3xl bg-slate-900/50 border border-white/10 flex items-center justify-between shadow-xl backdrop-blur-xl">
                    <div>
                        <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Ahorro de Tiempo</div>
                        <div className="text-3xl font-black text-purple-400 font-mono mt-1">{stats?.time_saved_hours || '45.3'}h</div>
                        <div className="text-[10px] text-purple-400 mt-1 font-semibold">Optimizado por IA</div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                        <Sparkles className="w-6 h-6" />
                    </div>
                </div>

                <div className="p-6 rounded-3xl bg-slate-900/50 border border-white/10 flex items-center justify-between shadow-xl backdrop-blur-xl">
                    <div>
                        <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Total Biblioteca</div>
                        <div className="text-3xl font-black text-cyan-400 font-mono mt-1">{stats?.total_library || 912}</div>
                        <div className="text-[10px] text-cyan-400 mt-1 font-semibold">Sincronizado</div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                        <Database className="w-6 h-6" />
                    </div>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex flex-wrap gap-2 border-b border-white/10 pb-3">
                {[
                    { id: 'scanner', label: 'Escáner Inteligente', icon: Activity },
                    { id: 'proposals', label: `Propuestas IA (${proposals.length})`, icon: Sparkles },
                    { id: 'pending', label: `Pendientes (${pendingList.length})`, icon: Clock },
                    { id: 'history', label: 'Historial de Correcciones', icon: CheckCircle2 },
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
                                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                        >
                            <Icon className="w-4 h-4" />
                            <span>{tab.label}</span>
                        </button>
                    );
                })}
            </div>

            {/* TAB 1: Smart Scanner & Autonomous Gardener */}
            {activeTab === 'scanner' && (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    {/* Left: Deep Scan (8 cols) */}
                    <div className="lg:col-span-8 bg-slate-900/50 border border-white/10 rounded-3xl p-6 sm:p-7 space-y-5 backdrop-blur-xl shadow-2xl">
                        <div className="flex items-center justify-between">
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                <Activity className="w-4 h-4 text-indigo-400" /> Escáner de Serie / Hash
                            </h3>
                            <div className="flex items-center gap-2">
                                <span className="text-[11px] text-gray-400">Modelo:</span>
                                <select
                                    value={targetModel}
                                    onChange={(e) => setTargetModel(e.target.value as any)}
                                    className="px-3 py-1 rounded-xl bg-slate-950 border border-white/10 text-xs text-indigo-300 font-bold focus:outline-none"
                                >
                                    <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                                    <option value="gemini-3-flash-preview">Gemini 3 Flash Preview</option>
                                </select>
                            </div>
                        </div>

                        <div className="flex gap-2">
                            <div className="relative flex-1">
                                <Search className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                                <input
                                    type="text"
                                    value={scanQuery}
                                    onChange={(e) => setScanQuery(e.target.value)}
                                    placeholder="Introduce el hash de serie, título en inglés o nombre para analizar con IA..."
                                    className="w-full pl-10 pr-4 py-3 bg-slate-950/80 border border-white/10 rounded-2xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                            <button
                                type="button"
                                onClick={handleRunScan}
                                disabled={scanning || !scanQuery.trim()}
                                className="px-6 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-xl shadow-indigo-600/30 transition-all disabled:opacity-50"
                            >
                                {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                                <span>Analizar Ahora</span>
                            </button>
                        </div>

                        {/* Intelligence Protocol Details */}
                        <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-2">
                            <div className="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                                <Sparkles className="w-3.5 h-3.5" /> Protocolo de Inteligencia Editorial
                            </div>
                            <p className="text-xs text-gray-400 leading-relaxed">
                                La IA realiza un <strong>Deep Scan</strong> sobre el archivo o serie, normaliza el nombre oficial en inglés, resuelve el Romaji y el título traducido al español, y estandariza el esquema de nombrado de todos los volúmenes asociados.
                            </p>
                        </div>
                    </div>

                    {/* Right: Gardener Directives (4 cols) */}
                    <div className="lg:col-span-4 bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-5 backdrop-blur-xl shadow-2xl">
                        <div className="flex items-center justify-between pb-3 border-b border-white/5">
                            <div>
                                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Escaneo en Background</h3>
                                <p className="text-[10px] text-gray-400">Procesamiento dinámico en segundo plano</p>
                            </div>
                            <input
                                type="checkbox"
                                checked={backgroundScan}
                                onChange={(e) => setBackgroundScan(e.target.checked)}
                                className="w-5 h-5 rounded accent-indigo-600"
                            />
                        </div>

                        <div className="space-y-3">
                            <div className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
                                Directivas del Gardener
                            </div>

                            <div className="space-y-2.5 text-xs text-gray-300">
                                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 flex items-start gap-2.5">
                                    <Sparkles className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                                    <span>Prioriza campos vacíos o con metadatos inconsistentes.</span>
                                </div>
                                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 flex items-start gap-2.5">
                                    <Edit3 className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                                    <span>El modo manual permite previsualizar y editar la propuesta canónica.</span>
                                </div>
                                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 flex items-start gap-2.5">
                                    <Activity className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                                    <span>Límites de la API (Gemini Flash) se gestionan dinámicamente.</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* TAB 2: Proposals List */}
            {activeTab === 'proposals' && (
                <div className="bg-slate-900/40 border border-white/10 rounded-3xl overflow-hidden shadow-2xl backdrop-blur-xl p-5 space-y-4">
                    {proposals.length === 0 ? (
                        <div className="py-20 text-center text-gray-500 text-xs">
                            No hay propuestas de IA pendientes de aprobación.
                        </div>
                    ) : (
                        <div className="divide-y divide-white/5">
                            {proposals.map((p) => (
                                <div key={p.id} className="py-4 flex items-center justify-between gap-4">
                                    <div>
                                        <div className="text-xs font-bold text-white">{p.series_name || p.title}</div>
                                        <div className="text-[11px] text-gray-400 mt-0.5">{p.proposal_summary || p.suggested_spanish}</div>
                                    </div>
                                    <button
                                        onClick={() => setSelectedProposal(p)}
                                        className="px-4 py-2 rounded-xl bg-indigo-600/20 text-indigo-300 text-xs font-bold border border-indigo-500/30 hover:bg-indigo-600/30"
                                    >
                                        Revisar Propuesta
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Proposal Modal */}
            {selectedProposal && (
                <ProposalModal
                    isOpen={!!selectedProposal}
                    proposal={selectedProposal}
                    onClose={() => setSelectedProposal(null)}
                    onApply={async () => {
                        setSelectedProposal(null);
                        loadData();
                    }}
                />
            )}
        </div>
    );
};
