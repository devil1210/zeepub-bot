import React, { useState, useEffect } from 'react';
import {
    Copy,
    FileWarning,
    Trash2,
    CheckCircle,
    AlertTriangle,
    Search,
    RefreshCw,
    HardDrive,
    Info,
    ArrowRight
} from 'lucide-react';
import { api } from '../src/services/api';

interface DuplicateEntry {
    id: number;
    title: string;
    author: string;
    hash: string;
    original: string;
    duplicate: string;
    detectedAt: string;
}

export const DuplicatesDashboard: React.FC = () => {
    const [duplicates, setDuplicates] = useState<DuplicateEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [clearing, setClearing] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');

    const fetchDuplicates = async () => {
        setLoading(true);
        try {
            const res = await api.adminGetDuplicates();
            if (res.success) {
                setDuplicates(res.duplicates || []);
            }
        } catch (error) {
            console.error('Error fetching duplicates:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleClear = async () => {
        if (!confirm('¿Estás seguro de que quieres limpiar todo el historial de duplicados detectados? Esto no borrará los archivos, solo los registros de esta tabla.')) return;

        setClearing(true);
        try {
            const res = await api.adminClearDuplicates();
            if (res.success) {
                setDuplicates([]);
            }
        } catch (error) {
            console.error('Error clearing duplicates:', error);
        } finally {
            setClearing(false);
        }
    };

    useEffect(() => {
        fetchDuplicates();
    }, []);

    const filtered = duplicates.filter(d =>
        d.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.author?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.duplicate?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="flex flex-col gap-8 animate-in fade-in duration-500 pt-4">
            {/* Header Info */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 glass-panel p-8 rounded-3xl border border-white/5 flex items-center gap-6">
                    <div className="p-4 bg-amber-500/20 rounded-2xl text-amber-500 border border-amber-500/20">
                        <FileWarning className="w-8 h-8" />
                    </div>
                    <div>
                        <h3 className="text-xl font-black text-white uppercase tracking-tight mb-2">Duplicados Detectados</h3>
                        <p className="text-xs text-gray-500 leading-relaxed">
                            Esta tabla muestra archivos EPUB con contenido idéntico que fueron omitidos por el escáner para evitar duplicidad en la biblioteca.
                            Puedes usar esta lista para limpiar manualmente tus carpetas.
                        </p>
                    </div>
                </div>

                <div className="glass-panel p-8 rounded-3xl border border-white/5 flex flex-col justify-center items-center text-center">
                    <div className="text-4xl font-black text-primary mb-1">{duplicates.length}</div>
                    <div className="text-[10px] font-black text-gray-500 uppercase tracking-widest leading-none">Registros Totales</div>
                    <button
                        onClick={handleClear}
                        disabled={clearing || duplicates.length === 0}
                        className="mt-4 flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white border border-red-500/20 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all disabled:opacity-30"
                    >
                        <Trash2 className="w-3 h-3" />
                        Limpiar Historial
                    </button>
                </div>
            </div>

            {/* Content Table */}
            <div className="glass-panel rounded-3xl border border-white/5 overflow-hidden flex flex-col">
                {/* Table Controls */}
                <div className="p-6 border-b border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="relative w-full sm:w-80 group">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-primary transition-all" />
                        <input
                            type="text"
                            placeholder="Buscar por título, autor o ruta..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:ring-1 focus:ring-primary/40 transition-all"
                        />
                    </div>
                    <button
                        onClick={fetchDuplicates}
                        className="flex items-center gap-2 px-6 py-2.5 bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-95"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                        Refrescar
                    </button>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-white/[0.02] text-[10px] font-black text-gray-500 uppercase tracking-widest border-b border-white/5">
                                <th className="px-6 py-4">Libro / Información</th>
                                <th className="px-6 py-4">Conflicto de Rutas</th>
                                <th className="px-6 py-4 text-right">Detección</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {loading ? (
                                Array(5).fill(0).map((_, i) => (
                                    <tr key={i} className="animate-pulse">
                                        <td colSpan={3} className="px-6 py-12 text-center text-gray-600 text-xs">Cargando datos...</td>
                                    </tr>
                                ))
                            ) : filtered.length === 0 ? (
                                <tr>
                                    <td colSpan={3} className="px-6 py-24 text-center">
                                        <div className="flex flex-col items-center gap-4">
                                            <div className="p-4 bg-green-500/10 rounded-full text-green-500 border border-green-500/10">
                                                <CheckCircle className="w-8 h-8" />
                                            </div>
                                            <p className="text-sm font-bold text-gray-400">¡Bibloteca limpia! No se encontraron duplicados registrados.</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                filtered.map((dup) => (
                                    <tr key={dup.id} className="group hover:bg-white/[0.01] transition-all">
                                        <td className="px-6 py-6">
                                            <div className="flex flex-col gap-1">
                                                <span className="text-xs font-black text-white group-hover:text-primary transition-colors">{dup.title || 'Título desconocido'}</span>
                                                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-tight">{dup.author || 'Autor desconocido'}</span>
                                                <div className="flex items-center gap-2 mt-2">
                                                    <span className="px-2 py-0.5 bg-white/5 rounded text-[8px] font-mono text-gray-400 border border-white/5">HASH: {dup.hash.substring(0, 12)}...</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-6">
                                            <div className="flex flex-col gap-3">
                                                <div className="flex items-start gap-2 max-w-md">
                                                    <div className="mt-1 p-1 bg-green-500/20 rounded text-green-500 border border-green-500/20">
                                                        <CheckCircle className="w-2.5 h-2.5" />
                                                    </div>
                                                    <div className="flex flex-col">
                                                        <span className="text-[8px] font-black text-green-500 uppercase tracking-widest">Original (En DB)</span>
                                                        <span className="text-[10px] text-gray-400 font-mono break-all line-clamp-1">{dup.original}</span>
                                                    </div>
                                                </div>
                                                <div className="flex items-start gap-2 max-w-md">
                                                    <div className="mt-1 p-1 bg-red-500/20 rounded text-red-500 border border-red-500/20">
                                                        <AlertTriangle className="w-2.5 h-2.5" />
                                                    </div>
                                                    <div className="flex flex-col">
                                                        <span className="text-[8px] font-black text-red-500 uppercase tracking-widest">Copia Omitida</span>
                                                        <span className="text-[10px] text-gray-400 font-mono break-all line-clamp-1">{dup.duplicate}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-6 text-right">
                                            <div className="flex flex-col items-end gap-1">
                                                <span className="text-[10px] font-bold text-gray-300">
                                                    {new Date(dup.detectedAt).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' })}
                                                </span>
                                                <span className="text-[9px] text-gray-500 uppercase tracking-widest">
                                                    {new Date(dup.detectedAt).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                                                </span>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Help Card */}
            <div className="p-8 rounded-3xl bg-blue-500/5 border border-blue-500/10 flex items-start gap-6">
                <Info className="w-6 h-6 text-blue-400 flex-shrink-0 mt-1" />
                <div>
                    <h4 className="text-sm font-black text-blue-400 mb-2 uppercase tracking-wide">¿Por qué veo estos archivos?</h4>
                    <p className="text-xs text-gray-500 leading-relaxed max-w-4xl">
                        El sistema utiliza un algoritmo de hashing para identificar el contenido interno de cada EPUB. Si mueves un archivo de carpeta
                        o cambias su nombre, el sistema detectará que ya tiene ese contenido en la biblioteca y omitirá el escaneo de la copia
                        para no ensuciar la base de datos con duplicados. Estos registros sirven para que puedas localizar y borrar los archivos sobrantes de tu disco.
                    </p>
                </div>
            </div>
        </div>
    );
};
