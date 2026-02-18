
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    BrainCircuit,
    Sparkles,
    Clock,
    Database,
    Search,
    Activity,
    CheckCircle,
    AlertTriangle,
    Play,
    X,
    ArrowRight,
    Edit2,
    Save,
    Check,
    Trash2
} from 'lucide-react';
import { api } from '@shared/services/api';
import { useTheme } from '@shared/contexts/ThemeContext';
import { useNavigation } from '@shared/contexts/NavigationContext';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { getCoverUrl } from '@shared/utils/imageUtils';

export const AIHub: React.FC = () => {
    const { settings } = useTheme();
    const { webApp } = useTelegram();
    const navigate = useNavigate();
    const { setContextType, registerCallbacks, setVisible, setCustomActions } = useNavigation();
    const [stats, setStats] = useState<any>(null);
    const [statsError, setStatsError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [scanHash, setScanHash] = useState('');
    const [scanResult, setScanResult] = useState<any>(null);
    const [scanning, setScanning] = useState(false);

    // Search State
    const [showSearch, setShowSearch] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [searching, setSearching] = useState(false);

    // Proposal State (Interactive Mode)
    const [proposal, setProposal] = useState<any>(null);
    const [showProposal, setShowProposal] = useState(false);
    const [approvedChanges, setApprovedChanges] = useState<any[]>([]);
    const [applyRenames, setApplyRenames] = useState(true);
    const [applyMeta, setApplyMeta] = useState(true);
    const [processingProposal, setProcessingProposal] = useState(false);
    const [isEditingSeries, setIsEditingSeries] = useState(false);
    const [editingBookId, setEditingBookId] = useState<number | null>(null);
    const [editedSeries, setEditedSeries] = useState('');
    const [editedSpanish, setEditedSpanish] = useState('');
    const [activeTab, setActiveTab] = useState('control');
    const [pendingList, setPendingList] = useState<any[]>([]);
    const [reviewedList, setReviewedList] = useState<any[]>([]);
    const [proposals, setProposals] = useState<any[]>([]);
    const [loadingLists, setLoadingLists] = useState(false);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            setLoading(true);
            setStatsError(null);
            const res = await api.getAiStats();
            if (res.result) {
                setStats(res.result);
            } else if (res.success === false) {
                // Backend returned an error — set fallback state so UI renders
                setStatsError(res.message || 'Error al cargar estadísticas de IA');
                setStats({ ai_active: false, ai_key_masked: 'ERROR', background_scan_enabled: false });
            }
            // Load initial lists
            loadProposals();
            loadLists('pending');
            loadLists('reviewed');
        } catch (e: any) {
            console.error("Failed to load stats", e);
            setStatsError(e?.message || 'Error de conexión');
            setStats({ ai_active: false, ai_key_masked: 'ERROR', background_scan_enabled: false });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        setContextType('ai');
        setVisible(true);

        const views = [
            { id: 'control', label: 'Monitor', icon: Activity },
            { id: 'proposals', label: 'Propuestas AI', icon: Sparkles },
            { id: 'pending', label: 'Cola Pendiente', icon: Clock },
            { id: 'reviewed', label: 'Historial', icon: CheckCircle }
        ];

        setCustomActions({
            title: views.find(v => v.id === activeTab)?.label || 'AI CEREBRO',
            buttons: views.map(v => ({
                id: v.id,
                label: v.label,
                icon: v.icon,
                onClick: () => setActiveTab(v.id),
                highlight: activeTab === v.id
            })),
            back: () => navigate('/dashboard')
        });

        registerCallbacks({
            onBack: () => navigate('/dashboard')
        });

        return () => {
            setContextType('main');
        };
    }, [setContextType, setVisible, setCustomActions, activeTab, registerCallbacks, navigate]);

    const loadLists = async (type: 'pending' | 'reviewed') => {
        try {
            setLoadingLists(true);
            // Map frontend tab names to backend list types
            const backendType = type === 'pending' ? 'queue' : 'learning';
            const res = await api.getAiLists(backendType as any, 50, 0);
            if (res.items) {
                if (type === 'pending') setPendingList(res.items);
                else setReviewedList(res.items);
            }
        } catch (e) {
            console.error(`Failed to load ${type} list`, e);
        } finally {
            setLoadingLists(false);
        }
    };

    const loadProposals = async () => {
        try {
            setLoadingLists(true);
            const res = await api.getAiProposals();
            if (res.proposals) {
                setProposals(res.proposals);
            }
        } catch (e) {
            console.error("Failed to load proposals", e);
        } finally {
            setLoadingLists(false);
        }
    };

    const handleScan = async () => {
        if (!scanHash) return;
        setScanning(true);
        setScanResult(null);
        setProposal(null);

        try {
            webApp?.HapticFeedback?.impactOccurred('medium');
            // ALWAYS use dry_run=true first for user safety
            const res = await api.scanSeriesAi(scanHash, true); // true = dry_run

            if (res.dry_run && res.proposal) {
                webApp?.HapticFeedback?.notificationOccurred('success');
                // Show interactive modal
                setProposal(res.proposal);
                setApprovedChanges(res.proposal?.changes || []);
                setEditedSeries(res.proposal?.proposed_series || '');
                setEditedSpanish(res.proposal?.proposed_spanish || '');
                setIsEditingSeries(false);
                setShowProposal(true);
            } else {
                // Fallback (shouldn't happen with new backend)
                setScanResult(res.result || res);
            }
        } catch (e: any) {
            webApp?.HapticFeedback?.notificationOccurred('error');
            setScanResult({ success: false, message: e.message || "Error desconocido" });
        } finally {
            setScanning(false);
        }
    };

    const handleApplyChanges = async () => {
        if (!proposal) return;
        setProcessingProposal(true);
        try {
            webApp?.HapticFeedback?.impactOccurred('heavy');
            const res = await api.applyAiChanges(
                proposal,
                approvedChanges,
                applyRenames,
                applyMeta,
                editedSeries, // Pass edited name
                editedSpanish // Pass edited spanish name
            );
            webApp?.HapticFeedback?.notificationOccurred('success');
            webApp?.showAlert?.("✅ Cambios aplicados con éxito.");
            setScanResult(res);
            setShowProposal(false);
            setProposal(null);
            loadStats(); // Refresh stats
            loadProposals(); // Refresh proposals list
        } catch (e: any) {
            webApp?.HapticFeedback?.notificationOccurred('error');
            webApp?.showAlert?.("Error aplicando cambios: " + e.message);
        } finally {
            setProcessingProposal(false);
        }
    };

    const handleEditFilename = (bookId: number, newFilename: string) => {
        setApprovedChanges(prev => prev.map(c =>
            c.book_id === bookId ? { ...c, proposed_filename: newFilename } : c
        ));
        setProposal((prev: any) => ({
            ...prev,
            changes: prev.changes.map((c: any) =>
                c.book_id === bookId ? { ...c, proposed_filename: newFilename } : c
            )
        }));
    };

    const toggleChange = (bookId: number) => {
        const exists = approvedChanges.find(c => c.book_id === bookId);
        if (exists) {
            setApprovedChanges(approvedChanges.filter(c => c.book_id !== bookId));
        } else {
            const originalChange = proposal?.changes?.find((c: any) => c.book_id === bookId);
            if (originalChange) {
                setApprovedChanges([...approvedChanges, originalChange]);
            }
        }
    };

    const runSearch = async () => {
        if (!searchTerm) return;
        setSearching(true);
        try {
            // Use sort='a-z' and type='all' for generic search
            const res = await api.searchBooks(searchTerm, 1, 'all', 'a-z');
            // Flatten results if they are mingled (LibraryService.search_series returns {results: [...]} )
            setSearchResults(res.results || []);
        } catch (e) {
            console.error("Search failed", e);
        } finally {
            setSearching(false);
        }
    };

    const selectSeries = (s: any) => {
        setScanHash(s.series_hash || '');
        setShowSearch(false);
        setSearchResults([]);
        setSearchTerm('');
    };

    if (loading && !stats) {
        return <div className="p-10 text-center text-gray-500 animate-pulse">Cargando Cerebro...</div>;
    }

    const aiActive = stats?.ai_active;
    const backgroundScanEnabled = stats?.background_scan_enabled;
    const aiKeyMasked = stats?.ai_key_masked;

    const handleToggleBackgroundScan = async () => {
        try {
            const nextState = !backgroundScanEnabled;
            // Optimistic update
            setStats({ ...stats, background_scan_enabled: nextState });
            await api.toggleAiBackgroundScan(nextState);
        } catch (e: any) {
            alert("Error cambiando configuración: " + e.message);
            loadStats(); // Revert
        }
    };

    return (
        <div className="max-w-[1800px] mx-auto px-4 py-8 animate-in fade-in duration-500">

            {/* Header */}
            <div className="flex items-center gap-4 mb-10">
                <div className="p-4 bg-purple-500/10 rounded-premium border border-purple-500/20">
                    <BrainCircuit className="w-10 h-10 text-purple-400" />
                </div>
                <div>
                    <h1 className="text-4xl font-black text-white tracking-tight">AI Hub</h1>
                    <p className="text-gray-400 font-medium">Centro de Control de Inteligencia Artificial</p>
                </div>
                {stats === null ? (
                    <div className="ml-auto flex items-center gap-2 px-4 py-1.5 bg-white/5 border border-white/10 rounded-full text-gray-500 text-xs font-black uppercase tracking-widest animate-pulse">
                        <div className="w-2 h-2 rounded-full bg-gray-500"></div>
                        Cargando...
                    </div>
                ) : aiActive ? (
                    <div className="ml-auto flex items-center gap-2 px-4 py-1.5 bg-green-500/10 border border-green-500/20 rounded-full text-green-400 text-xs font-black uppercase tracking-widest">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                        Online
                    </div>
                ) : (
                    <div className="ml-auto flex items-center gap-2 px-4 py-1.5 bg-red-500/10 border border-red-500/20 rounded-full text-red-400 text-xs font-black uppercase tracking-widest">
                        <div className="w-2 h-2 rounded-full bg-red-500"></div>
                        {statsError ? 'Error Backend' : 'Sin API Key'}
                    </div>
                )}
            </div>

            {/* Error Banner */}
            {statsError && (
                <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                    <div>
                        <p className="text-red-400 font-black text-sm uppercase tracking-wider">Error al conectar con el módulo IA</p>
                        <p className="text-red-400/70 text-xs font-mono mt-1">{statsError}</p>
                        <button
                            onClick={loadStats}
                            className="mt-2 text-xs text-red-400 hover:text-red-300 font-black uppercase tracking-wider underline"
                        >
                            Reintentar
                        </button>
                    </div>
                </div>
            )}

            {/* Navigation Tabs */}
            <div className="flex items-center gap-2 bg-white/5 p-2 rounded-[2rem] border border-white/5 w-fit mb-12 overflow-x-auto max-w-full no-scrollbar shadow-inner">
                {[
                    { id: 'control', label: 'Monitor', icon: BrainCircuit },
                    { id: 'proposals', label: 'Propuestas', icon: Sparkles },
                    { id: 'pending', label: 'Pendientes', icon: Clock },
                    { id: 'reviewed', label: 'Historial', icon: CheckCircle },
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`
                            flex items-center gap-3 px-8 py-4 rounded-[1.5rem] text-[11px] font-black uppercase tracking-[0.2em] transition-all duration-500 whitespace-nowrap
                            ${activeTab === tab.id
                                ? 'bg-primary text-white shadow-2xl shadow-primary/40 scale-100 ring-4 ring-primary/10'
                                : 'text-gray-500 hover:text-gray-300 hover:bg-white/5 scale-95 opacity-70'}
                        `}
                    >
                        <tab.icon className={`w-4 h-4 transition-transform duration-500 ${activeTab === tab.id ? 'scale-110' : ''}`} />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
                <StatCard
                    label="Libros Procesados"
                    value={stats?.total_processed || 0}
                    icon={CheckCircle}
                    color="text-emerald-400"
                    bg="bg-emerald-500/10"
                    delta="+8 NUEVOS ESTA SEMANA"
                />
                <StatCard
                    label="Pendientes"
                    value={stats?.pending_optimization || 0}
                    icon={Clock}
                    color="text-amber-400"
                    bg="bg-amber-500/10"
                    delta="REQUERIDO"
                />
                <StatCard
                    label="Ahorro Tiempo"
                    value={`${stats?.time_saved_hours || 0}h`}
                    icon={Sparkles}
                    color="text-purple-400"
                    bg="bg-purple-500/10"
                    delta="OPTIMIZADO POR IA"
                />
                <StatCard
                    label="Total Biblioteca"
                    value={stats?.total_books || 0}
                    icon={Database}
                    color="text-blue-400"
                    bg="bg-blue-500/10"
                    delta="SINCRONIZADO"
                />
            </div>

            {/* Action Area */}
            {activeTab === 'control' && (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
                    {/* Manual Scan */}
                    <div className="lg:col-span-8">
                        <div className="glass-panel p-10 rounded-[3rem] border border-white/5 bg-gradient-to-b from-white/5 to-transparent relative overflow-hidden shadow-2xl">
                            <div className="flex items-center justify-between mb-10">
                                <h3 className="text-2xl font-black text-white flex items-center gap-4">
                                    <Activity className="w-8 h-8 text-primary" />
                                    <span className="uppercase tracking-[0.3em] text-lg">Escaner Inteligente</span>
                                </h3>
                                <div className="flex items-center gap-3 px-4 py-2 bg-white/5 rounded-premium-sm border border-white/10">
                                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-500">Modelo:</span>
                                    <span className="text-[10px] font-black uppercase tracking-widest text-primary">Gemini 3 Flash Preview</span>
                                </div>
                            </div>

                            <div className="flex flex-col lg:flex-row gap-6 mb-10">
                                <div className="relative flex-1 group">
                                    <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-gray-500 group-focus-within:text-primary transition-colors" />
                                    <input
                                        type="text"
                                        placeholder="HASH DE SERIE O NOMBRE PARA ANALIZAR..."
                                        value={scanHash}
                                        onChange={(e) => setScanHash(e.target.value)}
                                        className="w-full bg-black/40 border-2 border-white/5 rounded-[2rem] py-6 pl-16 pr-32 text-white placeholder-gray-600 focus:outline-none focus:border-primary/50 focus:ring-8 focus:ring-primary/5 transition-all font-mono text-sm tracking-widest shadow-inner"
                                    />
                                    <button
                                        onClick={() => setShowSearch(true)}
                                        className="absolute right-4 top-1/2 -translate-y-1/2 px-6 py-3 rounded-premium-sm bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-all text-[11px] font-black uppercase tracking-[0.2em] border border-white/5 active:scale-95"
                                    >
                                        BUSCAR
                                    </button>
                                </div>
                                <button
                                    onClick={handleScan}
                                    disabled={!scanHash || scanning || !aiActive}
                                    className="px-12 py-6 bg-primary hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-[2rem] font-black uppercase tracking-[0.3em] text-xs transition-all shadow-2xl shadow-primary/30 flex items-center justify-center gap-4 active:scale-95 group"
                                >
                                    {scanning ? (
                                        <div className="w-5 h-5 border-3 border-white/30 border-t-white rounded-full animate-spin"></div>
                                    ) : <Play className="w-5 h-5 fill-current group-hover:scale-110 transition-transform" />}
                                    ANALIZAR AHORA
                                </button>
                            </div>

                            {scanResult && (
                                <div className={`p-6 rounded-[2rem] border-2 mb-8 ${scanResult.success ? 'bg-green-500/10 border-green-500/20 text-green-200' : 'bg-red-500/10 border-red-500/20 text-red-200'} animate-in slide-in-from-top-4 duration-500`}>
                                    <div className="flex items-center gap-3 font-black uppercase tracking-widest mb-2 text-xs">
                                        {scanResult.success ? <CheckCircle className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                                        {scanResult.success ? "Resultado de Optimización" : "Fallo en el Análisis"}
                                    </div>
                                    <p className="text-sm opacity-90 leading-relaxed">
                                        {scanResult.message}
                                    </p>
                                    {scanResult.updated_count !== undefined && (
                                        <div className="mt-4 flex items-center gap-3">
                                            <div className="px-3 py-1 bg-black/40 rounded-lg text-[10px] font-black text-primary border border-primary/20 uppercase tracking-widest">
                                                {scanResult.updated_count} Libros Actualizados
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            <div className="bg-white/5 rounded-[2rem] p-8 border border-white/5 ring-1 ring-white/5">
                                <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.3em] mb-4 flex items-center gap-2">
                                    <Database className="w-4 h-4" />
                                    Protocolo de Inteligencia
                                </h4>
                                <p className="text-sm text-gray-500 leading-relaxed font-medium">
                                    Introduce el <code className="text-primary bg-primary/5 px-2 py-0.5 rounded">series_hash</code> de un grupo de libros.
                                    La IA realizará un <span className="text-white font-bold">Deep Scan</span> sobre la metadata del archivo representante,
                                    normalizará el nombre de la serie oficial y estandarizará el esquema de nombrado de todos los volúmenes asociados.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Info Side */}
                    <div className="lg:col-span-4">
                        <div className="glass-panel p-8 rounded-[3rem] border border-white/5 relative h-full flex flex-col shadow-xl">
                            <h3 className="text-xl font-black text-white mb-8 uppercase tracking-widest">Configuración</h3>

                            {/* Toggle */}
                            <div className="flex flex-col gap-4">
                                <label className="flex items-center justify-between p-6 rounded-[2rem] bg-white/5 border border-white/10 cursor-pointer hover:bg-primary/5 hover:border-primary/20 transition-all group">
                                    <div className="flex flex-col">
                                        <h4 className="text-sm font-black text-white uppercase tracking-wider">Escaneo en Background</h4>
                                        <p className="text-[9px] text-gray-500 uppercase tracking-widest font-black mt-1">PROCESAMIENTO DINÁMICO</p>
                                    </div>
                                    <button
                                        onClick={handleToggleBackgroundScan}
                                        className={`w-14 h-8 rounded-full transition-all relative flex items-center ${backgroundScanEnabled ? 'bg-primary shadow-[0_0_20px_rgba(59,130,246,0.5)]' : 'bg-gray-800'}`}
                                    >
                                        <div className={`w-6 h-6 rounded-full bg-white transition-all shadow-lg ${backgroundScanEnabled ? 'translate-x-7' : 'translate-x-1'}`}></div>
                                    </button>
                                </label>
                            </div>

                            <div className="mt-12 space-y-6 flex-1">
                                <h3 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.3em]">Directivas del Gardener</h3>
                                <ul className="space-y-6">
                                    {[
                                        { color: 'bg-blue-500', text: 'La IA prioriza campos vacíos o con metadata inconsistente.', icon: BrainCircuit },
                                        { color: 'bg-purple-500', text: 'El modo manual permite previsualizar y editar la propuesta canónica.', icon: Sparkles },
                                        { color: 'bg-amber-500', text: 'Los límites de la API (Gemini Flash) se gestionan dinámicamente.', icon: Activity }
                                    ].map((note, i) => (
                                        <li key={i} className="flex gap-4 group">
                                            <div className={`w-10 h-10 rounded-premium-sm ${note.color}/10 flex items-center justify-center shrink-0 border border-white/5 group-hover:scale-110 transition-transform`}>
                                                <note.icon className={`w-5 h-5 ${note.color.replace('bg-', 'text-')}`} />
                                            </div>
                                            <p className="text-sm text-gray-400 font-medium leading-relaxed group-hover:text-gray-300 transition-colors pt-1">
                                                {note.text}
                                            </p>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            {/* Debug Info (Masked Key) */}
                            <div className="mt-12 pt-8 border-t border-white/5">
                                <p className="text-[10px] text-gray-600 font-black uppercase tracking-[0.2em] mb-4">Núcleo del Sistema</p>
                                <div className="flex flex-col gap-2">
                                    <div className="flex items-center justify-between text-[11px] font-mono bg-black/40 p-4 rounded-premium-sm border border-white/5">
                                        <span className="text-gray-500 uppercase">API Context:</span>
                                        <span className={aiActive ? "text-primary font-bold" : "text-red-500/50"}>{aiKeyMasked}</span>
                                    </div>
                                    <div className="flex items-center justify-between text-[11px] font-mono bg-black/40 p-4 rounded-premium-sm border border-white/5">
                                        <span className="text-gray-500 uppercase">Status:</span>
                                        <span className={aiActive ? "text-emerald-400 font-bold" : "text-red-500/50"}>{aiActive ? 'READY' : 'OFFLINE'}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'proposals' && (
                <div className="animate-in fade-in slide-in-from-bottom-8 duration-700">
                    <div className="glass-panel p-10 rounded-[3rem] border border-white/5 bg-gradient-to-b from-white/5 to-transparent shadow-2xl">
                        <div className="flex items-center justify-between mb-10">
                            <h3 className="text-2xl font-black text-white flex items-center gap-4">
                                <Sparkles className="w-8 h-8 text-purple-400" />
                                <span className="uppercase tracking-[0.3em] text-lg">Propuestas del Jardinero</span>
                            </h3>
                            <button
                                onClick={loadProposals}
                                className="p-3 bg-white/5 hover:bg-white/10 rounded-full border border-white/10 transition-all active:scale-95"
                                title="Refrescar propuestas"
                            >
                                <Activity className={`w-5 h-5 text-gray-400 ${loadingLists ? 'animate-spin text-primary' : ''}`} />
                            </button>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            {loadingLists && proposals.length === 0 ? (
                                <div className="col-span-full py-32 text-center text-gray-500 animate-pulse font-black uppercase tracking-[0.5em] text-xs font-mono">
                                    ESCANENDO REPOSITORIO DE PROPUESTAS...
                                </div>
                            ) : proposals.length > 0 ? (
                                proposals.map(p => (
                                    <div
                                        key={p.id}
                                        className="relative p-8 bg-white/5 border-2 border-white/5 rounded-[2.5rem] hover:border-primary/20 transition-all flex flex-col group overflow-hidden"
                                    >
                                        {/* Type Badge */}
                                        <div className={`absolute top-0 right-10 px-4 py-1.5 rounded-b-xl text-[9px] font-black uppercase tracking-widest ${p.type === 'merge' ? 'bg-amber-500/20 text-amber-400' : 'bg-primary/20 text-primary'
                                            }`}>
                                            {p.type === 'merge' ? 'FUSIÓN DETECTADA' : 'ENRIQUECIMIENTO'}
                                        </div>

                                        <div className="flex-1">
                                            <div className="flex items-start gap-4 mb-6">
                                                <div className={`p-4 rounded-2xl ${p.type === 'merge' ? 'bg-amber-500/10' : 'bg-primary/10'} shrink-0`}>
                                                    {p.type === 'merge' ? <Trash2 className="w-6 h-6 text-amber-400" /> : <Sparkles className="w-6 h-6 text-primary" />}
                                                </div>
                                                <div>
                                                    <h4 className="font-black text-white text-xl tracking-tight leading-tight mb-2">
                                                        {p.type === 'merge' ? p.proposal.suggested_main_name : p.proposal.proposed_series}
                                                    </h4>
                                                    <p className="text-xs text-gray-500 font-medium leading-relaxed">
                                                        {p.proposal.reason}
                                                    </p>
                                                </div>
                                            </div>

                                            {p.type === 'merge' && (
                                                <div className="bg-black/20 rounded-2xl p-4 border border-white/5 mb-6">
                                                    <div className="flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-gray-500 mb-3">
                                                        <span>Series a unificar</span>
                                                        <span className="text-amber-500/50">Probabilidad: {(p.proposal.confidence * 100).toFixed(0)}%</span>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <div className="flex-1 p-3 bg-white/5 rounded-xl border border-white/5">
                                                            <p className="text-[11px] text-white font-bold truncate">{p.proposal.series_a?.name || p.series_hash.substring(0, 8)}</p>
                                                        </div>
                                                        <ArrowRight className="w-4 h-4 text-gray-600" />
                                                        <div className="flex-1 p-3 bg-white/5 rounded-xl border border-white/5">
                                                            <p className="text-[11px] text-white font-bold truncate">{p.proposal.series_b?.name || p.secondary_hash?.substring(0, 8)}</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {p.type === 'enrich' && (
                                                <div className="flex items-center gap-2 mb-6">
                                                    {p.proposal.global_tags?.slice(0, 3).map((t: string) => (
                                                        <span key={t} className="px-3 py-1 bg-white/5 rounded-lg text-[10px] font-bold text-gray-400 border border-white/5">
                                                            {t}
                                                        </span>
                                                    ))}
                                                    {p.proposal.changes?.length > 0 && (
                                                        <span className="px-3 py-1 bg-primary/10 rounded-lg text-[10px] font-bold text-primary border border-primary/20">
                                                            {p.proposal.changes.length} RENOMBRADOS
                                                        </span>
                                                    )}
                                                </div>
                                            )}
                                        </div>

                                        <div className="grid grid-cols-2 gap-4 mt-auto">
                                            <button
                                                onClick={async () => {
                                                    if (window.confirm("¿Seguro que quieres descartar esta propuesta?")) {
                                                        await api.rejectAiProposal(p.id);
                                                        loadProposals();
                                                    }
                                                }}
                                                className="py-3 rounded-2xl bg-white/5 hover:bg-red-500/10 text-gray-500 hover:text-red-400 text-[10px] font-black uppercase tracking-widest border border-white/5 hover:border-red-500/20 transition-all active:scale-95"
                                            >
                                                DESCARTAR
                                            </button>
                                            <button
                                                onClick={async () => {
                                                    if (p.type === 'merge') {
                                                        if (window.confirm(`¿Confirmas la fusión de estas series? Todos los libros se moverán a '${p.proposal.suggested_main_name}'.`)) {
                                                            const res = await api.applyAiMerge(p.id);
                                                            if (res.success) {
                                                                alert(res.message);
                                                                loadProposals();
                                                                loadStats();
                                                            }
                                                        }
                                                    } else {
                                                        // Abrir modal de revisión para enriquecimiento
                                                        const propWithId = { ...p.proposal, id: p.id };
                                                        setProposal(propWithId);
                                                        setApprovedChanges(p.proposal.changes || []);
                                                        setEditedSeries(p.proposal.proposed_series || '');
                                                        setEditedSpanish(p.proposal.proposed_spanish || '');
                                                        // Guardar el hash de la serie para el contexto del modal
                                                        setScanHash(p.series_hash);
                                                        setShowProposal(true);
                                                    }
                                                }}
                                                className={`py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 shadow-lg ${p.type === 'merge'
                                                    ? 'bg-amber-500 hover:bg-amber-600 text-black shadow-amber-500/20'
                                                    : 'bg-primary hover:bg-primary-dark text-white shadow-primary/20'
                                                    }`}
                                            >
                                                {p.type === 'merge' ? 'FUSIONAR' : 'REVISAR Y APLICAR'}
                                            </button>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="col-span-full py-40 text-center flex flex-col items-center gap-6">
                                    <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                                        <Sparkles className="w-10 h-10 text-gray-600" />
                                    </div>
                                    <p className="text-gray-500 font-black uppercase tracking-[0.5em] text-xs">No hay propuestas automáticas todavía</p>
                                    <p className="text-[10px] text-gray-600 max-w-xs leading-relaxed uppercase font-bold tracking-widest">
                                        Activa el Escaneo en Background o ejecuta el Gardener para generar sugerencias inteligentes.
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'pending' && (
                <div className="animate-in fade-in slide-in-from-bottom-8 duration-700">
                    <div className="glass-panel p-10 rounded-[3rem] border border-white/5 bg-gradient-to-b from-white/5 to-transparent shadow-2xl">
                        <h3 className="text-2xl font-black text-white mb-8 flex items-center gap-4">
                            <Clock className="w-8 h-8 text-amber-400" />
                            <span className="uppercase tracking-[0.3em] text-lg">Series por Optimizar</span>
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {loadingLists && pendingList.length === 0 ? (
                                <div className="col-span-full py-32 text-center text-gray-500 animate-pulse font-black uppercase tracking-[0.5em] text-xs">Sincronizando...</div>
                            ) : pendingList.length > 0 ? (
                                pendingList.map(item => (
                                    <div
                                        key={item.series_hash}
                                        onClick={() => {
                                            setScanHash(item.series_hash);
                                            setActiveTab('control');
                                        }}
                                        className="flex flex-col justify-between p-8 bg-white/5 border-2 border-white/5 rounded-[2.5rem] hover:bg-white/10 hover:border-primary/40 transition-all cursor-pointer group shadow-sm hover:shadow-primary/5 h-full"
                                    >
                                        <div className="min-w-0 mb-6">
                                            <h4 className="font-black text-white text-lg group-hover:text-primary transition-colors truncate mb-2">{item.name || 'Sin nombre'}</h4>
                                            <p className="text-[10px] text-gray-500 font-mono tracking-widest opacity-60 truncate uppercase">{item.series_hash}</p>
                                        </div>
                                        <div className="flex items-center justify-between mt-auto">
                                            <div className="px-4 py-2 bg-black/40 text-[10px] font-black text-primary rounded-premium-sm border border-primary/20 shadow-inner">
                                                {item.books_count} VOLÚMENES
                                            </div>
                                            <div className="w-10 h-10 bg-white/5 rounded-premium-sm flex items-center justify-center group-hover:bg-primary group-hover:text-white transition-all group-hover:scale-110 active:scale-95">
                                                <ArrowRight className="w-5 h-5" />
                                            </div>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="col-span-full py-40 text-center flex flex-col items-center gap-6">
                                    <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                                        <CheckCircle className="w-10 h-10 text-emerald-500" />
                                    </div>
                                    <p className="text-gray-500 font-black uppercase tracking-[0.5em] text-xs">Cerebro al día - 0 Pendientes</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'reviewed' && (
                <div className="animate-in fade-in slide-in-from-bottom-8 duration-700">
                    <div className="glass-panel p-10 rounded-[3rem] border border-white/5 bg-gradient-to-b from-white/5 to-transparent shadow-2xl">
                        <h3 className="text-2xl font-black text-white mb-8 flex items-center gap-4">
                            <CheckCircle className="w-8 h-8 text-emerald-400" />
                            <span className="uppercase tracking-[0.3em] text-lg">Historial de Auditoría</span>
                        </h3>

                        <div className="space-y-6">
                            {loadingLists && reviewedList.length === 0 ? (
                                <div className="py-32 text-center text-gray-500 animate-pulse font-black uppercase tracking-[0.5em] text-xs">Cargando Historial...</div>
                            ) : reviewedList.length > 0 ? (
                                reviewedList.map(item => (
                                    <div
                                        key={item.series_hash}
                                        className="p-8 bg-white/5 border-2 border-white/5 rounded-[3rem] hover:bg-white/10 transition-all shadow-sm relative overflow-hidden group"
                                    >
                                        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 relative z-10">
                                            <div className="flex-1">
                                                <div className="flex flex-wrap items-center gap-4 mb-3">
                                                    <h4 className="font-black text-white text-xl tracking-tight">{item.final_name || item.proposed_name}</h4>
                                                    <span className={`px-4 py-1.5 rounded-full text-[9px] font-black uppercase tracking-[0.2em] border shadow-sm ${item.status === 'accepted' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                                        item.status === 'edited' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                                                            'bg-gray-500/10 text-gray-400 border-white/10'
                                                        }`}>
                                                        {item.status}
                                                    </span>
                                                </div>
                                                <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
                                                    <div className="flex flex-col">
                                                        <span className="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">Nombre Original</span>
                                                        <span className="text-xs text-gray-400 italic font-medium truncate max-w-[200px]">{item.original_name}</span>
                                                    </div>
                                                    <div className="flex flex-col">
                                                        <span className="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">Hash de Identidad</span>
                                                        <span className="text-[10px] text-gray-400 font-mono tracking-wider opacity-60 uppercase">{item.series_hash}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="text-right flex flex-col items-end gap-3 lg:border-l border-white/5 lg:pl-8">
                                                <div className="flex items-center gap-3 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] bg-black/40 px-4 py-2 rounded-premium-sm border border-white/5 ring-4 ring-white/5">
                                                    <Clock className="w-4 h-4 text-primary" />
                                                    {new Date(item.reviewed_at).toLocaleDateString()}
                                                    <span className="text-primary opacity-40 mx-1">|</span>
                                                    {new Date(item.reviewed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </div>
                                                <div className="px-5 py-2 bg-primary/10 text-[10px] font-black text-primary rounded-premium-sm border border-primary/20 uppercase tracking-[0.2em] shadow-sm">
                                                    {item.books_count} VOLÚMENES ACTUALIZADOS
                                                </div>
                                            </div>
                                        </div>
                                        {/* Corner Decoration */}
                                        <div className={`absolute -right-10 -bottom-10 w-40 h-40 blur-[100px] opacity-10 rounded-full ${item.status === 'accepted' ? 'bg-emerald-500' : 'bg-primary'}`}></div>
                                    </div>
                                ))
                            ) : (
                                <div className="py-40 text-center flex flex-col items-center gap-6">
                                    <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                                        <Database className="w-10 h-10 text-gray-600" />
                                    </div>
                                    <p className="text-gray-500 font-black uppercase tracking-[0.5em] text-xs">Sin registros de revisión</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Proposal Modal (New) */}
            {showProposal && proposal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="w-full max-w-4xl bg-[#0a0a0c] border border-white/10 rounded-premium overflow-hidden flex flex-col max-h-[90vh] shadow-2xl">
                        {/* Modal Header */}
                        <div className="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
                            <div>
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    <Sparkles className="w-5 h-5 text-purple-400" />
                                    Propuesta de Estandarización
                                </h3>
                                <p className="text-xs text-gray-400 mt-1 uppercase tracking-wider font-bold">
                                    Confianza IA: {(proposal.confidence * 100).toFixed(0)}%
                                </p>
                            </div>
                            <button
                                onClick={() => setShowProposal(false)}
                                className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-all"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">

                            {/* Series Name Proposal */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <h4 className="text-sm font-bold text-gray-300 uppercase tracking-wide">Nombre de la Serie (Identificación)</h4>
                                    <label className="flex items-center gap-2 text-xs font-bold text-primary cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={applyMeta}
                                            onChange={(e) => setApplyMeta(e.target.checked)}
                                            className="rounded border-white/20 bg-white/5"
                                        />
                                        Aplicar cambio
                                    </label>
                                </div>
                                <div className="grid grid-cols-1 gap-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {/* Current Name Card */}
                                        <div className="p-5 rounded-premium-sm bg-red-500/5 border border-red-500/10">
                                            <p className="text-[10px] text-red-400 font-black uppercase mb-3 tracking-widest">Estado Actual en DB</p>
                                            <p className="text-lg font-medium text-white break-words leading-relaxed whitespace-pre-wrap">
                                                {proposal.current_series}
                                            </p>
                                            {proposal.current_spanish && (
                                                <p className="text-sm text-red-500/50 mt-2 flex items-center gap-2">
                                                    <span className="text-[10px] font-black bg-red-500/10 px-1.5 rounded text-red-500/70">ES</span>
                                                    {proposal.current_spanish}
                                                </p>
                                            )}
                                        </div>

                                        {/* Proposed Name Card */}
                                        <div className="p-5 rounded-premium-sm bg-green-500/5 border border-green-500/10 relative group">
                                            <ArrowRight className="absolute -left-6 top-1/2 -translate-y-1/2 w-8 h-8 text-white/10 hidden md:block" />
                                            <div className="flex justify-between items-start mb-3">
                                                <p className="text-[10px] text-green-400 font-black uppercase tracking-widest text-glow-green">Propuesta IA</p>
                                                {!isEditingSeries ? (
                                                    <button
                                                        onClick={() => setIsEditingSeries(true)}
                                                        className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-all opacity-0 group-hover:opacity-100"
                                                        title="Editar propuesta"
                                                    >
                                                        <Edit2 className="w-4 h-4" />
                                                    </button>
                                                ) : (
                                                    <button
                                                        onClick={() => setIsEditingSeries(false)}
                                                        className="p-1.5 rounded-lg bg-primary/20 text-primary border border-primary/30"
                                                    >
                                                        <Save className="w-4 h-4" />
                                                    </button>
                                                )}
                                            </div>

                                            {isEditingSeries ? (
                                                <div className="space-y-4 animate-in fade-in duration-300">
                                                    <div className="flex items-center gap-4 p-4 rounded-xl bg-white/5 border border-white/10">
                                                        <div className="p-3 rounded-lg bg-blue-500/10">
                                                            <BrainCircuit className="w-6 h-6 text-blue-400" />
                                                        </div>
                                                        <div>
                                                            <p className="text-sm text-gray-400">Modelo Activo</p>
                                                            <p className="font-medium text-white">Gemini 3 Flash Preview</p>
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <label className="text-[10px] text-gray-500 uppercase font-bold mb-1 block">Nombre Inglés (Serie)</label>
                                                        <input
                                                            type="text"
                                                            value={editedSeries}
                                                            onChange={(e) => setEditedSeries(e.target.value)}
                                                            className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-primary outline-none"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="text-[10px] text-gray-500 uppercase font-bold mb-1 block">Nombre Español (Visualización)</label>
                                                        <input
                                                            type="text"
                                                            value={editedSpanish}
                                                            onChange={(e) => setEditedSpanish(e.target.value)}
                                                            className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-primary outline-none"
                                                        />
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="space-y-4">
                                                    <div>
                                                        <p className="text-lg font-bold text-green-100 break-words leading-relaxed whitespace-pre-wrap">
                                                            <DiffHighlighter
                                                                oldText={proposal.current_series}
                                                                newText={editedSeries}
                                                            />
                                                        </p>
                                                        {editedSpanish !== editedSeries && (
                                                            <p className="text-sm text-gray-400 mt-2 flex items-center gap-2">
                                                                <span className="text-[10px] font-black bg-white/5 px-1.5 rounded text-gray-500">ES</span>
                                                                {editedSpanish}
                                                            </p>
                                                        )}
                                                    </div>
                                                    {proposal.reason && (
                                                        <div className="bg-white/5 p-3 rounded-premium-sm border border-white/5">
                                                            <p className="text-xs text-gray-400 leading-relaxed italic">
                                                                "{proposal.reason}"
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Tags Detected */}
                            {proposal.global_tags?.length > 0 && (
                                <div>
                                    <h4 className="text-sm font-bold text-gray-300 uppercase tracking-wide mb-3">Tags Detectados</h4>
                                    <div className="flex gap-2">
                                        {proposal.global_tags?.map((tag: string) => (
                                            <span key={tag} className="px-3 py-1 rounded-lg bg-blue-500/20 border border-blue-500/30 text-blue-300 text-xs font-bold">
                                                {tag}
                                            </span>
                                        ))}
                                        {proposal.is_uncensored_series && (
                                            <span className="px-3 py-1 rounded-lg bg-red-500/20 border border-red-500/30 text-red-300 text-xs font-bold">
                                                Uncensored
                                            </span>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* File Renames */}
                            <div>
                                <div className="flex items-center justify-between mb-4">
                                    <h4 className="text-sm font-bold text-gray-300 uppercase tracking-wide">
                                        Archivos a Renombrar ({approvedChanges.length}/{proposal.changes?.length || 0})
                                    </h4>
                                    <label className="flex items-center gap-2 text-xs font-bold text-primary cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={applyRenames}
                                            onChange={(e) => setApplyRenames(e.target.checked)}
                                            className="rounded border-white/20 bg-white/5"
                                        />
                                        Habilitar Renombrado
                                    </label>
                                </div>

                                <div className="space-y-2">
                                    {proposal.changes?.map((change: any) => {
                                        const isSelected = approvedChanges.some(c => c.book_id === change.book_id);
                                        return (
                                            <div
                                                key={change.book_id}
                                                className={`p-3 rounded-premium-sm border flex items-center gap-4 text-sm transition-all group ${isSelected && applyRenames
                                                    ? 'bg-white/5 border-white/10 opacity-100'
                                                    : 'bg-black/20 border-white/5 opacity-40 grayscale'
                                                    }`}
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={isSelected}
                                                    onChange={() => toggleChange(change.book_id)}
                                                    disabled={!applyRenames}
                                                    className="w-5 h-5 rounded-lg border-white/20 bg-white/5 cursor-pointer accent-primary"
                                                />
                                                <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                                                    <div className="text-red-300/50 break-words line-through decoration-red-500/30 text-[11px] leading-tight">
                                                        {change.current_filename}
                                                    </div>
                                                    <div className="flex items-center gap-2 group/field">
                                                        {editingBookId === change.book_id ? (
                                                            <div className="flex-1 flex items-center gap-2 animate-in slide-in-from-right-2 duration-200">
                                                                <input
                                                                    type="text"
                                                                    autoFocus
                                                                    value={change.proposed_filename}
                                                                    onChange={(e) => handleEditFilename(change.book_id, e.target.value)}
                                                                    onKeyDown={(e) => e.key === 'Enter' && setEditingBookId(null)}
                                                                    onBlur={() => setEditingBookId(null)}
                                                                    className="flex-1 bg-black/60 border border-primary/50 rounded px-2 py-1 text-xs text-white outline-none focus:ring-1 ring-primary"
                                                                />
                                                                <button
                                                                    onClick={() => setEditingBookId(null)}
                                                                    className="p-1 text-green-400 hover:text-green-300 transition-colors"
                                                                >
                                                                    <Check className="w-4 h-4" />
                                                                </button>
                                                            </div>
                                                        ) : (
                                                            <>
                                                                <div className="flex-1 text-green-300 font-medium break-words leading-tight text-[13px]">
                                                                    <DiffHighlighter
                                                                        oldText={change.current_filename}
                                                                        newText={change.proposed_filename}
                                                                    />
                                                                </div>
                                                                <button
                                                                    onClick={() => setEditingBookId(change.book_id)}
                                                                    className="p-1 rounded bg-white/5 hover:bg-white/10 text-gray-500 hover:text-white transition-all opacity-0 group-hover:opacity-100"
                                                                    title="Editar nombre"
                                                                >
                                                                    <Edit2 className="w-3.5 h-3.5" />
                                                                </button>
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                        </div>

                        {/* Footer */}
                        <div className="p-6 border-t border-white/10 bg-white/5 flex justify-end gap-3">
                            <button
                                onClick={() => setShowProposal(false)}
                                className="px-6 py-3 rounded-premium-sm font-bold text-gray-400 hover:bg-white/5 transition-all"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleApplyChanges}
                                disabled={processingProposal}
                                className="px-8 py-3 rounded-premium-sm font-bold bg-primary hover:bg-primary/90 text-white flex items-center gap-2 transition-all shadow-lg shadow-primary/20"
                            >
                                {processingProposal ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                        Aplicando...
                                    </>
                                ) : (
                                    <>
                                        <Save className="w-4 h-4" />
                                        Aplicar Cambios
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Search Modal */}
            {showSearch && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="w-full max-w-2xl bg-[#0a0a0c] border border-white/10 rounded-premium p-6 shadow-2xl relative">
                        <button
                            onClick={() => setShowSearch(false)}
                            className="absolute top-4 right-4 text-gray-500 hover:text-white"
                        >
                            <X className="w-6 h-6" />
                        </button>

                        <h3 className="text-xl font-bold text-white mb-6">Buscar Serie</h3>

                        <div className="flex gap-4 mb-6">
                            <input
                                type="text"
                                placeholder="Nombre de la serie..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && runSearch()}
                                className="flex-1 bg-white/5 border border-white/10 rounded-premium-sm px-4 py-3 text-white focus:outline-none focus:border-primary"
                                autoFocus
                            />
                            <button
                                onClick={runSearch}
                                disabled={searching}
                                className="bg-primary hover:bg-primary/90 text-white px-6 rounded-premium-sm font-bold transition-all"
                            >
                                {searching ? "..." : "Buscar"}
                            </button>
                        </div>

                        <div className="max-h-[300px] overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                            {searchResults.map((s: any, idx) => (
                                <div
                                    key={idx}
                                    onClick={() => selectSeries(s)}
                                    className="p-3 rounded-premium-sm bg-white/5 hover:bg-white/10 border border-white/5 cursor-pointer flex items-center gap-4 transition-all"
                                >
                                    {s.cover ? (
                                        <img src={getCoverUrl(s, s.cover_thumb || s.cover, settings.coverQuality)} className="w-10 h-14 object-cover rounded-md" alt="" />
                                    ) : (
                                        <div className="w-10 h-14 bg-white/10 rounded-md flex items-center justify-center">
                                            <Search className="w-4 h-4 opacity-50" />
                                        </div>
                                    )}
                                    <div>
                                        <h4 className="font-bold text-white text-sm">{s.title || s.series}</h4>
                                        <p className="text-xs text-gray-400 font-black uppercase tracking-widest">{s.author || 'Autor desconocido'}</p>
                                        {s.categories && (
                                            <p className="text-[10px] text-gray-500 italic opacity-60 mt-0.5 line-clamp-1">
                                                {Array.isArray(s.categories) ? s.categories.join(', ') : s.categories}
                                            </p>
                                        )}
                                        <div className="flex flex-wrap gap-1.5 mt-2">
                                            {s.book_type && (
                                                <span className="px-2 py-0.5 rounded-md text-[8px] font-black bg-white/5 text-gray-400 border border-white/10 uppercase">{s.book_type}</span>
                                            )}
                                            {s.color_mode === 'color' && (
                                                <span className="px-2 py-0.5 rounded-md text-[8px] font-black bg-gradient-to-r from-orange-400 to-pink-500 text-white uppercase">Color</span>
                                            )}
                                            {s.is_uncensored && (
                                                <span className="px-2 py-0.5 rounded-md text-[8px] font-black bg-red-500/10 text-red-500 border border-red-500/20 uppercase">S/C</span>
                                            )}
                                        </div>
                                        <p className="text-[10px] text-gray-600 font-mono mt-2">{s.series_hash}</p>
                                    </div>
                                    <div className="ml-auto">
                                        <ArrowRight className="w-4 h-4 text-gray-600" />
                                    </div>
                                </div>
                            ))}
                            {searchTerm && !searching && searchResults.length === 0 && (
                                <p className="text-center text-gray-500 py-8">No se encontraron resultados</p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

interface DiffHighlighterProps {
    oldText: string;
    newText: string;
}

const DiffHighlighter: React.FC<DiffHighlighterProps> = ({ oldText, newText }) => {
    if (!oldText || !newText) return <>{newText}</>;

    const oldWords = oldText.split(' ');
    const newWords = newText.split(' ');

    return (
        <span className="leading-relaxed">
            {newWords.map((word, i) => {
                const isMatch = oldWords.includes(word);
                return (
                    <span
                        key={i}
                        className={isMatch ? "" : "bg-green-500/20 text-green-300 px-0.5 rounded border-b border-green-500/30 font-bold"}
                    >
                        {word}{' '}
                    </span>
                );
            })}
        </span>
    );
};

const StatCard = ({ label, value, icon: Icon, color, bg, delta }: any) => (
    <div className="glass-panel p-6 rounded-[2rem] border border-white/5 bg-gradient-to-br from-white/5 to-transparent hover:scale-[1.02] transition-all duration-500 group relative overflow-hidden">
        <div className="flex justify-between items-start relative z-10">
            <div className="space-y-1">
                <p className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] mb-2">{label}</p>
                <h4 className="text-3xl font-black text-white tracking-tight">{value}</h4>
                {delta && (
                    <p className="text-[10px] font-black text-emerald-400 uppercase tracking-widest mt-3 flex items-center gap-1.5 anim-pulse">
                        <Activity className="w-3 h-3" />
                        {delta}
                    </p>
                )}
            </div>
            <div className={`p-4 rounded-premium-sm ${bg} ${color} border border-white/5 group-hover:scale-110 group-hover:rotate-6 transition-all duration-500 shadow-lg`}>
                <Icon className="w-6 h-6" />
            </div>
        </div>

        {/* Background Decorative Gradient */}
        <div className={`absolute -right-4 -bottom-4 w-24 h-24 blur-3xl opacity-10 rounded-full ${bg}`}></div>
    </div>
);

