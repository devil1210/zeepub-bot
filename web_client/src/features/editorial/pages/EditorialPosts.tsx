import React, { useState, useEffect } from 'react';
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
    BookOpen
} from 'lucide-react';
import { api } from '@shared/services/api';
import { EditPublishedPostModal } from '../components/EditPublishedPostModal';

export const EditorialPosts: React.FC = () => {
    const [posts, setPosts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [editingPost, setEditingPost] = useState<any | null>(null);

    const fetchPosts = async () => {
        setLoading(true);
        try {
            // Query both 'sent' and all items as fallback to capture completed posts
            const res = await api.pubGetQueue('sent', 50);
            let items = res?.items || [];
            if (items.length === 0) {
                const allRes = await api.pubGetQueue(undefined, 100);
                items = (allRes?.items || []).filter((i: any) => {
                    const st = (i.status || '').toLowerCase();
                    return st === 'sent' || st === 'published' || st === 'completado';
                });
            }
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

    return (
        <div className="w-full max-w-[2100px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <Send className="w-7 h-7 text-indigo-400" /> Historial de Publicaciones
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Registro de volúmenes lanzados exitosamente en Telegram y Facebook con opción de edición in-place.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 font-mono">
                        {posts.length} publicaciones registradas
                    </span>
                    <button
                        onClick={fetchPosts}
                        className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white border border-white/10 transition-all active:scale-95"
                        title="Actualizar Historial"
                    >
                        <RefreshCw className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* List */}
            <div className="bg-slate-900/40 border border-white/10 rounded-3xl overflow-hidden shadow-2xl backdrop-blur-xl">
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
                                className="p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-white/[0.02] transition-colors"
                            >
                                <div className="flex items-center gap-4 min-w-0">
                                    <div className="p-3.5 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0 shadow-lg">
                                        <CheckCircle2 className="w-6 h-6" />
                                    </div>
                                    <div className="min-w-0">
                                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                                            <span className="text-sm font-bold text-white truncate">
                                                {post.series || 'Novela'}
                                            </span>
                                            <span className="text-[11px] font-black px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                                Volumen {post.volume || 1}
                                            </span>
                                            <span className="px-2.5 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                                {post.platform}
                                            </span>
                                        </div>
                                        <div className="text-xs text-gray-400 flex items-center gap-3 flex-wrap">
                                            <span className="flex items-center gap-1 text-gray-300">
                                                <Building2 className="w-3.5 h-3.5 text-indigo-400" /> {post.channel}
                                            </span>
                                            <span>•</span>
                                            <span className="flex items-center gap-1 text-gray-400 font-mono text-[11px]">
                                                <Calendar className="w-3 h-3" />
                                                {post.published_at ? new Date(post.published_at).toLocaleString() : 'Reciente'}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-3 self-end md:self-center shrink-0">
                                    <button
                                        onClick={() => setEditingPost(post)}
                                        className="px-4 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 hover:text-white text-xs font-bold flex items-center gap-2 border border-indigo-500/30 transition-all active:scale-95 shadow-md"
                                        title="Editar mensaje en Telegram"
                                    >
                                        <Edit3 className="w-4 h-4" /> Editar en Telegram
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Edit Sent Post Modal */}
            <EditPublishedPostModal
                isOpen={!!editingPost}
                post={editingPost}
                onClose={() => setEditingPost(null)}
                onSuccess={fetchPosts}
            />
        </div>
    );
};
