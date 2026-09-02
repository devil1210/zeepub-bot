import React, { useState, useEffect } from 'react';
import { Send, ExternalLink, Calendar, RefreshCw, Loader2, CheckCircle2, MessageSquare } from 'lucide-react';
import { api } from '@shared/services/api';

export const EditorialPosts: React.FC = () => {
    const [posts, setPosts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchPosts = async () => {
        setLoading(true);
        try {
            const res = await api.pubGetQueue('published', 50);
            setPosts(res?.items || []);
        } catch (err) {
            console.error('Error cargando historial de posts:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPosts();
    }, []);

    return (
        <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
                        <Send className="w-6 h-6 text-indigo-400" /> Historial de Publicaciones
                    </h2>
                    <p className="text-xs text-gray-400 mt-1">
                        Registro de volúmenes lanzados exitosamente en Telegram y Facebook.
                    </p>
                </div>

                <button
                    onClick={fetchPosts}
                    className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white border border-white/10 transition-all active:scale-95"
                    title="Actualizar"
                >
                    <RefreshCw className="w-4 h-4" />
                </button>
            </div>

            {/* List */}
            <div className="bg-slate-900/40 border border-white/10 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-xl">
                {loading ? (
                    <div className="py-24 flex items-center justify-center">
                        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                    </div>
                ) : posts.length === 0 ? (
                    <div className="py-24 text-center text-gray-500 text-xs">
                        No hay publicaciones registradas como completadas.
                    </div>
                ) : (
                    <div className="divide-y divide-white/5">
                        {posts.map((post) => (
                            <div
                                key={post.id}
                                className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-white/[0.02] transition-colors"
                            >
                                <div className="flex items-center gap-4 min-w-0">
                                    <div className="p-3 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                                        <CheckCircle2 className="w-5 h-5" />
                                    </div>
                                    <div className="min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-xs font-bold text-white truncate">
                                                {post.series || 'Novela'}
                                            </span>
                                            <span className="text-[10px] font-black px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                                Vol. {post.volume || 1}
                                            </span>
                                        </div>
                                        <div className="text-[11px] text-gray-400 flex items-center gap-2">
                                            <span>Canal: <strong className="text-gray-200">{post.channel}</strong></span>
                                            <span>•</span>
                                            <span>{post.published_at ? new Date(post.published_at).toLocaleString() : 'Reciente'}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-2 self-end sm:self-center">
                                    <span className="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                        Publicado en {post.platform}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
