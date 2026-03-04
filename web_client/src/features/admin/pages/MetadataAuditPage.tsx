import React, { useState, useEffect } from 'react';
import {
    History,
    CheckCircle,
    RefreshCw,
    Database,
    AlertCircle,
    Check,
    Tag,
    Info,
    ArrowRight
} from 'lucide-react';
import { api } from '@shared/services/api';
import { useTelegram } from '@shared/contexts/TelegramContext';

interface MetadataAudit {
    id: number;
    series_hash: string;
    series_name: string;
    change_type: string;
    old_value: {
        tags: string[];
        demographics: string[];
    };
    new_value: {
        tags: string[];
        demographics: string[];
    };
    created_at: string;
}

export const MetadataAuditPage: React.FC = () => {
    const { webApp } = useTelegram();
    const [audits, setAudits] = useState<MetadataAudit[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [resolvingId, setResolvingId] = useState<number | null>(null);

    const fetchAudits = async () => {
        setLoading(true);
        try {
            const res = await api.getGenreAudits();
            if (res.success) {
                setAudits(res.audits || []);
            } else {
                setError(res.message || 'Error al cargar auditorías');
            }
        } catch (err: any) {
            setError(err.message || 'Error de conexión');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAudits();
    }, []);

    const handleResolve = async (id: number) => {
        setResolvingId(id);
        try {
            const res = await api.resolveGenreAudit(id);
            if (res.success) {
                webApp?.HapticFeedback?.notificationOccurred('success');
                setAudits(prev => prev.filter(a => a.id !== id));
            } else {
                webApp?.HapticFeedback?.notificationOccurred('error');
                alert(res.message || 'Error al resolver');
            }
        } catch (err: any) {
            alert(err.message || 'Error al conectar');
        } finally {
            setResolvingId(null);
        }
    };

    const renderDiff = (oldItems: string[], newItems: string[]) => {
        const added = newItems.filter(x => !oldItems.includes(x));
        const removed = oldItems.filter(x => !newItems.includes(x));
        const unchanged = newItems.filter(x => oldItems.includes(x));

        return (
            <div className="flex flex-wrap gap-1.5 mt-2">
                {unchanged.map(item => (
                    <span key={item} className="px-2 py-0.5 rounded-full bg-white/5 border border-white/5 text-xs text-gray-400">
                        {item}
                    </span>
                ))}
                {added.map(item => (
                    <span key={item} className="px-2 py-0.5 rounded-full bg-green-500/10 border border-green-500/30 text-xs text-green-400">
                        +{item}
                    </span>
                ))}
                {removed.map(item => (
                    <span key={item} className="px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/30 text-xs text-red-400 line-through decoration-red-500/50">
                        {item}
                    </span>
                ))}
            </div>
        );
    };

    if (loading && audits.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-20 animate-pulse">
                <RefreshCw className="w-12 h-12 text-primary animate-spin mb-4" />
                <p className="text-gray-400">Cargando auditorías de metadatos...</p>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header / Stats */}
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                <div>
                    <h1 className="text-2xl font-black text-white flex items-center gap-2">
                        <History className="text-primary w-6 h-6" />
                        Auriditoría de Metadatos
                    </h1>
                    <p className="text-gray-400 text-sm mt-1">
                        Revisiones automáticas pendientes de validación por maquetadores.
                    </p>
                </div>
                <button
                    onClick={fetchAudits}
                    className="p-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-premium-sm transition-all"
                    title="Refrescar"
                >
                    <RefreshCw className={`w-5 h-5 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
                </button>
            </div>

            {error && (
                <div className="p-4 rounded-premium-sm bg-red-500/10 border border-red-500/20 flex items-center gap-3">
                    <AlertCircle className="text-red-400 w-5 h-5 flex-shrink-0" />
                    <p className="text-red-400 text-sm">{error}</p>
                </div>
            )}

            {audits.length === 0 && !loading ? (
                <div className="glass-panel p-12 text-center rounded-premium border-white/5 backdrop-blur-xl">
                    <CheckCircle className="w-16 h-16 text-green-400/30 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">¡Todo al día!</h3>
                    <p className="text-gray-400 max-w-sm mx-auto">
                        No hay correcciones de metadatos pendientes de revisión.
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {audits.map((audit) => (
                        <div key={audit.id} className="glass-panel group overflow-hidden rounded-premium border border-white/5 hover:border-white/10 bg-white/5 backdrop-blur-xl transition-all duration-300">
                            <div className="p-5 flex flex-col md:flex-row gap-6">
                                {/* Left Content */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="min-w-0">
                                            <h4 className="text-lg font-bold text-white truncate group-hover:text-primary transition-colors">
                                                {audit.series_name}
                                            </h4>
                                            <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                                                <code className="px-1.5 py-0.5 bg-black/30 rounded border border-white/5">
                                                    {audit.series_hash.substring(0, 8)}
                                                </code>
                                                <span className="flex items-center gap-1">
                                                    <Info className="w-3 h-3" />
                                                    {audit.change_type}
                                                </span>
                                                <span>•</span>
                                                <span>{new Date(audit.created_at).toLocaleDateString()}</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Diff Section */}
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                                        <div className="p-3 bg-black/20 rounded-lg border border-white/5">
                                            <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-2">
                                                <Tag className="w-3 h-3" />
                                                Géneros
                                            </div>
                                            {renderDiff(audit.old_value.tags || [], audit.new_value.tags || [])}
                                        </div>
                                        <div className="p-3 bg-black/20 rounded-lg border border-white/5">
                                            <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-2">
                                                <Database className="w-3 h-3" />
                                                Demografía
                                            </div>
                                            {renderDiff(audit.old_value.demographics || [], audit.new_value.demographics || [])}
                                        </div>
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex items-center md:items-stretch">
                                    <button
                                        onClick={() => handleResolve(audit.id)}
                                        disabled={resolvingId === audit.id}
                                        className={`flex flex-col items-center justify-center gap-2 px-6 py-4 rounded-premium-sm border transition-all duration-300 w-full md:w-28
                                            ${resolvingId === audit.id
                                                ? 'bg-primary/20 border-primary/30 text-white cursor-wait'
                                                : 'bg-primary/10 border-primary/20 hover:bg-primary text-white hover:shadow-[0_0_20px_rgba(43,108,238,0.4)]'
                                            }
                                        `}
                                    >
                                        {resolvingId === audit.id ? (
                                            <RefreshCw className="w-6 h-6 animate-spin" />
                                        ) : (
                                            <Check className="w-6 h-6" />
                                        )}
                                        <span className="text-xs font-bold uppercase tracking-widest leading-none">
                                            Revisar
                                        </span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
