import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Send,
    ExternalLink,
    Calendar,
    RefreshCw,
    Loader2,
    CheckCircle2,
    Edit3,
    MessageSquare,
    Sparkles,
    Building2,
    BookOpen,
    Globe,
    Share2,
    Eye,
    ChevronDown,
    ChevronUp
} from 'lucide-react';
import { api } from '@shared/services/api';

export const EditorialPosts: React.FC = () => {
    const navigate = useNavigate();
    const [posts, setPosts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [syncingFb, setSyncingFb] = useState(false);
    const [selectedTab, setSelectedTab] = useState<'all' | 'telegram' | 'facebook'>('all');
    const [expandedTextIds, setExpandedTextIds] = useState<Record<string, boolean>>({});
    const [syncMsg, setSyncMsg] = useState<string | null>(null);

    const formatDateSafe = (dateStr?: string | null) => {
        if (!dateStr) return 'Reciente';
        try {
            const cleaned = String(dateStr).replace(/\+00:00Z$/, 'Z').replace(/\+00:00$/, 'Z');
            const d = new Date(cleaned);
            if (!isNaN(d.getTime())) {
                return d.toLocaleString('es-ES', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                });
            }
            const d2 = new Date(String(dateStr).replace('Z', ''));
            if (!isNaN(d2.getTime())) {
                return d2.toLocaleString('es-ES', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                });
            }
            return dateStr;
        } catch {
            return dateStr || 'Reciente';
        }
    };

    const fetchPosts = async () => {
        setLoading(true);
        try {
            const res = await api.pubGetQueue('all', 150);
            const items = res?.items || [];
            setPosts(items);
        } catch (err) {
            console.error('Error cargando historial de posts:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPosts();
    }, []);

    const handleSyncFacebook = async () => {
        setSyncingFb(true);
        setSyncMsg(null);
        try {
            const res = await api.syncFacebookPublications(50, false);
            if (res?.success) {
                setSyncMsg(`Sincronización completada: ${res.new_publications_synced || 0} nuevos posts vinculados`);
                await fetchPosts();
            } else {
                setSyncMsg(`Aviso: ${res?.error || res?.message || 'Error al conectar con Facebook'}`);
            }
        } catch (err: any) {
            console.error('Error sincronizando Facebook:', err);
            setSyncMsg(`Error: ${err.message || 'No se pudo sincronizar Facebook'}`);
        } finally {
            setSyncingFb(false);
            setTimeout(() => setSyncMsg(null), 6000);
        }
    };

    const toggleExpandText = (id: string) => {
        setExpandedTextIds((prev) => ({ ...prev, [id]: !prev[id] }));
    };

    const filteredPosts = useMemo(() => {
        if (selectedTab === 'all') return posts;
        return posts.filter((p) => (p.platform || '').toLowerCase() === selectedTab);
    }, [posts, selectedTab]);

    const telegramCount = useMemo(() => posts.filter((p) => (p.platform || '').toLowerCase() === 'telegram').length, [posts]);
    const facebookCount = useMemo(() => posts.filter((p) => (p.platform || '').toLowerCase() === 'facebook').length, [posts]);

    return (
        <div className="w-full max-w-[2400px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <Send className="w-7 h-7 text-indigo-400" /> Historial de Publicaciones
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Registro unificado de emisiones oficiales en Telegram y página de Facebook con editor dedicado.
                    </p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                    <button
                        onClick={handleSyncFacebook}
                        disabled={syncingFb}
                        className="px-4 py-2.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 hover:text-white border border-blue-500/30 text-xs font-bold flex items-center gap-2 transition-all shadow-lg active:scale-95 disabled:opacity-50"
                        title="Consultar Graph API de Facebook para importar posts recientes"
                    >
                        {syncingFb ? <Loader2 className="w-4 h-4 animate-spin text-blue-400" /> : <Globe className="w-4 h-4 text-blue-400" />}
                        <span>{syncingFb ? 'Sincronizando Facebook...' : 'Sincronizar Facebook'}</span>
                    </button>

                    <button
                        onClick={fetchPosts}
                        className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white border border-white/10 transition-all active:scale-95"
                        title="Actualizar Historial"
                    >
                        <RefreshCw className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {syncMsg && (
                <div className="p-3.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-indigo-400 shrink-0" />
                    <span>{syncMsg}</span>
                </div>
            )}

            {/* Filter Tabs */}
            <div className="flex items-center gap-2 border-b border-white/10 pb-3 overflow-x-auto">
                <button
                    onClick={() => setSelectedTab('all')}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 flex items-center gap-2 ${
                        selectedTab === 'all'
                            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                            : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10'
                    }`}
                >
                    <span>Todos los Posts</span>
                    <span className="px-2 py-0.5 rounded-full bg-black/30 text-[10px] font-mono">
                        {posts.length}
                    </span>
                </button>

                <button
                    onClick={() => setSelectedTab('telegram')}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 flex items-center gap-2 ${
                        selectedTab === 'telegram'
                            ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-600/30'
                            : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10'
                    }`}
                >
                    <Send className="w-3.5 h-3.5" />
                    <span>Telegram</span>
                    <span className="px-2 py-0.5 rounded-full bg-black/30 text-[10px] font-mono">
                        {telegramCount}
                    </span>
                </button>

                <button
                    onClick={() => setSelectedTab('facebook')}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 flex items-center gap-2 ${
                        selectedTab === 'facebook'
                            ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                            : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10'
                    }`}
                >
                    <Globe className="w-3.5 h-3.5" />
                    <span>Facebook</span>
                    <span className="px-2 py-0.5 rounded-full bg-black/30 text-[10px] font-mono">
                        {facebookCount}
                    </span>
                </button>
            </div>

            {/* Publication Cards List */}
            <div className="bg-slate-900/40 border border-white/10 rounded-3xl overflow-hidden shadow-2xl backdrop-blur-xl">
                {loading ? (
                    <div className="py-24 flex items-center justify-center">
                        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                    </div>
                ) : filteredPosts.length === 0 ? (
                    <div className="py-24 text-center text-gray-500 text-xs">
                        No se encontraron publicaciones registradas en esta categoría.
                    </div>
                ) : (
                    <div className="divide-y divide-white/5">
                        {filteredPosts.map((post) => {
                            const isFb = (post.platform || '').toLowerCase() === 'facebook';
                            const postKey = String(post.id || post.post_id || post.book_hash);
                            const isExpanded = !!expandedTextIds[postKey];
                            const captionText = post.caption || post.payload?.caption || '';

                            return (
                                <div
                                    key={postKey}
                                    className="p-5 sm:p-6 flex flex-col gap-4 hover:bg-white/[0.02] transition-colors"
                                >
                                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                        <div className="flex items-start sm:items-center gap-4 min-w-0">
                                            {/* Platform Icon Avatar */}
                                            <div
                                                className={`p-3.5 rounded-2xl shrink-0 shadow-lg ${
                                                    isFb
                                                        ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                                                        : 'bg-cyan-600/20 text-cyan-400 border border-cyan-500/30'
                                                }`}
                                            >
                                                {isFb ? <Globe className="w-6 h-6" /> : <Send className="w-6 h-6" />}
                                            </div>

                                            <div className="min-w-0 space-y-1">
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    <span className="text-sm sm:text-base font-bold text-white truncate">
                                                        {post.series || post.series_name || 'Publicación Editorial'}
                                                    </span>
                                                    {post.volume && (
                                                        <span className="text-[11px] font-black px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                                            Volumen {post.volume}
                                                        </span>
                                                    )}
                                                    <span
                                                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider border ${
                                                            isFb
                                                                ? 'bg-blue-500/10 text-blue-300 border-blue-500/30'
                                                                : 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
                                                        }`}
                                                    >
                                                        {post.platform || 'Telegram'}
                                                    </span>

                                                    {post.post_id && (
                                                        <span className="text-[10px] font-mono text-gray-500">
                                                            ID: {post.post_id}
                                                        </span>
                                                    )}
                                                </div>

                                                <div className="text-xs text-gray-400 flex items-center gap-3 flex-wrap">
                                                    <span className="flex items-center gap-1 text-gray-300">
                                                        <Building2 className="w-3.5 h-3.5 text-indigo-400" />
                                                        {post.channel || (isFb ? 'Página Oficial Facebook' : 'Canal Oficial')}
                                                    </span>
                                                    <span>•</span>
                                                    <span className="flex items-center gap-1 text-gray-400 font-mono text-[11px]">
                                                        <Calendar className="w-3 h-3" />
                                                        {formatDateSafe(post.published_at || post.scheduled_for)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Actions Bar */}
                                        <div className="flex items-center gap-2.5 self-end md:self-center shrink-0">
                                            {captionText && (
                                                <button
                                                    type="button"
                                                    onClick={() => toggleExpandText(postKey)}
                                                    className="px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold flex items-center gap-1.5 border border-white/10 transition-all"
                                                >
                                                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                                    <span>{isExpanded ? 'Ocultar Texto' : 'Ver Texto'}</span>
                                                </button>
                                            )}

                                            {post.post_url && (
                                                <a
                                                    href={post.post_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold flex items-center gap-1.5 border border-white/10 transition-all"
                                                >
                                                    <ExternalLink className="w-3.5 h-3.5" />
                                                    <span>Ver Publicación</span>
                                                </a>
                                            )}

                                            <button
                                                onClick={() => navigate(`/app-v2/posts/${post.id}`)}
                                                className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 border transition-all active:scale-95 shadow-md group ${
                                                    isFb
                                                        ? 'bg-blue-600/20 hover:bg-blue-600 text-blue-300 hover:text-white border-blue-500/30'
                                                        : 'bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border-indigo-500/30'
                                                }`}
                                                title={`Editar post en ${isFb ? 'Facebook' : 'Telegram'}`}
                                            >
                                                <Edit3 className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                                                <span>{isFb ? 'Editar en Facebook' : 'Editar en Telegram'}</span>
                                            </button>
                                        </div>
                                    </div>

                                    {/* Expandable Caption Box */}
                                    {isExpanded && captionText && (
                                        <div className="p-4 rounded-2xl bg-slate-950/80 border border-white/10 space-y-2 animate-in fade-in duration-200">
                                            <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider flex items-center justify-between">
                                                <span>Texto Emitido:</span>
                                                <span className="font-mono text-gray-500">{captionText.length} caracteres</span>
                                            </div>
                                            <pre className="text-xs text-gray-200 font-mono whitespace-pre-wrap leading-relaxed select-text overflow-x-auto">
                                                {captionText}
                                            </pre>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};
