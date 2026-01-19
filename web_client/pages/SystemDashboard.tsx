import React, { useState, useEffect } from 'react';
import {
    Settings,
    Database,
    RefreshCw,
    Activity,
    Zap,
    Trash2,
    Shield,
    Users,
    Library,
    AlertTriangle,
    Loader2,
    Globe,
    HardDrive,
    RotateCcw,
    TrendingUp,
    Search,
    Bell
} from 'lucide-react';
import { api } from '../src/services/api';

export const SystemDashboard: React.FC = () => {
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleAction = async (name: string, fn: () => Promise<any>) => {
        setActionLoading(name);
        try {
            setLoading(true);
            const res = await fn();
            alert(res.message || `${name} completado`);
        } catch (error: any) {
            alert(`Error: ${error.message}`);
        } finally {
            setActionLoading(null);
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col gap-8 animate-in fade-in duration-500">
            {/* Consistent Header bar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-4 text-sm font-medium text-slate-600 dark:text-slate-400 bg-white/5 px-4 py-2 rounded-xl border border-white/5">
                    <span className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"></span>
                        Bot Status: Online
                    </span>
                    <span className="h-4 w-px bg-slate-300 dark:bg-slate-700"></span>
                    <span>Version: v7.1.1</span>
                </div>

                <div className="flex items-center gap-3">
                    <div className="relative hidden sm:block">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input
                            className="pl-10 pr-4 py-1.5 bg-black/20 border border-white/10 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary w-64 text-white placeholder-slate-500"
                            placeholder="Search settings..."
                            type="text"
                        />
                    </div>
                </div>
            </div>

            {/* Synchronization Strategy Table */}
            <div className="glass-panel p-8 rounded-3xl border border-white/5 bg-white/5 shadow-sm">
                <div className="flex items-center gap-3 mb-8">
                    <Database className="w-5 h-5 text-primary" />
                    <h3 className="text-sm font-black text-white uppercase tracking-widest">Synchronization Strategy</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                        <thead>
                            <tr className="border-b border-white/5 text-gray-500 font-black uppercase tracking-wider">
                                <th className="pb-4 px-2">Table / Record</th>
                                <th className="pb-4 px-2">Primary Storage</th>
                                <th className="pb-4 px-2">Sync Status</th>
                                <th className="pb-4 px-2">Cloud Backup Trigger</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            <tr className="group hover:bg-white/[0.01]">
                                <td className="py-4 px-2 font-bold text-gray-200">Books & Metadata</td>
                                <td className="py-4 px-2 text-gray-400">SQLite (Local)</td>
                                <td className="py-4 px-2"><span className="text-amber-500 font-black uppercase tracking-tighter text-[10px]">Manual Only</span></td>
                                <td className="py-4 px-2 italic text-gray-500 font-mono">Cloud Sync → Library</td>
                            </tr>
                            <tr className="group hover:bg-white/[0.01]">
                                <td className="py-4 px-2 font-bold text-gray-200">Library Sources</td>
                                <td className="py-4 px-2 text-gray-400">SQLite (Local)</td>
                                <td className="py-4 px-2"><span className="text-amber-500 font-black uppercase tracking-tighter text-[10px]">Manual Only</span></td>
                                <td className="py-4 px-2 italic text-gray-500 font-mono">Cloud Sync → Library</td>
                            </tr>
                            <tr className="group hover:bg-white/[0.01]">
                                <td className="py-4 px-2 font-bold text-gray-200">Users & Roles</td>
                                <td className="py-4 px-2 text-gray-400">SQLite (Local)</td>
                                <td className="py-4 px-2"><span className="text-amber-500 font-black uppercase tracking-tighter text-[10px]">Manual Only</span></td>
                                <td className="py-4 px-2 italic text-gray-500 font-mono">Cloud Sync → Users</td>
                            </tr>
                            <tr className="group hover:bg-white/[0.01]">
                                <td className="py-4 px-2 font-bold text-gray-200">User Levels (Tiers)</td>
                                <td className="py-4 px-2 text-gray-400">SQLite (Local)</td>
                                <td className="py-4 px-2"><span className="text-amber-500 font-black uppercase tracking-tighter text-[10px]">Manual Only</span></td>
                                <td className="py-4 px-2 italic text-gray-500 font-mono">Cloud Sync → Users</td>
                            </tr>
                            <tr className="group hover:bg-white/[0.01]">
                                <td className="py-4 px-2 font-bold text-gray-200">System Logs</td>
                                <td className="py-4 px-2 text-gray-400">Volatile (Memory)</td>
                                <td className="py-4 px-2 text-gray-600 font-black uppercase text-[10px]">None</td>
                                <td className="py-4 px-2 text-gray-600 italic">N/A</td>
                            </tr>
                            <tr className="group hover:bg-white/[0.01]">
                                <td className="py-4 px-2 font-bold text-gray-200">Audit Logs</td>
                                <td className="py-4 px-2 text-gray-400">Supabase (Remote)</td>
                                <td className="py-4 px-2"><span className="text-green-500 font-black uppercase tracking-tighter text-[10px]">Automatic / Real-time</span></td>
                                <td className="py-4 px-2 text-green-500 font-black uppercase tracking-widest text-[9px]">Live Push</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Maintenance Section - Refined layout */}
            <div className="glass-panel rounded-3xl p-8 border border-white/5 bg-white/5">
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-3">
                        <Settings className="text-primary w-5 h-5" /> Mantenimiento
                    </h3>
                    <span className="px-3 py-1 bg-green-500/10 text-green-500 text-[9px] font-black rounded-lg border border-green-500/20 uppercase tracking-widest">Operativo</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Scan Library */}
                    <div className="p-6 rounded-2xl bg-white/5 border border-white/5 hover:border-primary/50 transition-all group flex flex-col">
                        <div className="flex justify-between items-start mb-3">
                            <h4 className="font-bold text-white text-xs uppercase tracking-tight">Escanear Biblioteca</h4>
                            <Activity className="w-4 h-4 text-gray-500 group-hover:text-primary transition-colors" />
                        </div>
                        <p className="text-[11px] text-gray-500 mb-6 leading-relaxed">Indexar nuevo contenido en /mnt/books/incoming de forma forzada.</p>
                        <button
                            onClick={() => handleAction('Escaneo', () => api.adminScanLibrary(true))}
                            disabled={loading}
                            className="mt-auto w-full py-2.5 text-[10px] font-black text-center bg-primary hover:bg-primary-dark text-white rounded-xl transition-all uppercase tracking-widest shadow-lg shadow-primary/20 active:scale-95 disabled:opacity-50"
                        >
                            {actionLoading === 'Escaneo' ? "Ejecutando..." : "Ejecutar Escaneo"}
                        </button>
                    </div>

                    {/* Enrich Metadata */}
                    <div className="p-6 rounded-2xl bg-white/5 border border-white/5 hover:border-amber-500/50 transition-all group flex flex-col">
                        <div className="flex justify-between items-start mb-3">
                            <h4 className="font-bold text-white text-xs uppercase tracking-tight">Actualizar Metadatos</h4>
                            <Globe className="w-4 h-4 text-gray-500 group-hover:text-amber-400 transition-colors" />
                        </div>
                        <p className="text-[11px] text-gray-500 mb-6 leading-relaxed">Busca información extra (títulos ES/EN, descripción) via ISBN y web.</p>
                        <button
                            onClick={() => handleAction('Metadatos', api.adminEnrichMetadata)}
                            disabled={loading}
                            className="mt-auto w-full py-2.5 text-[10px] font-black text-center bg-amber-500/10 hover:bg-amber-500 text-amber-500 hover:text-white border border-amber-500/20 rounded-xl transition-all uppercase tracking-widest active:scale-95 disabled:opacity-50"
                        >
                            {actionLoading === 'Metadatos' ? "Ejecutando..." : "Sincronizar Web"}
                        </button>
                    </div>

                    {/* Cloud Sync */}
                    <div className="p-6 rounded-2xl bg-white/5 border border-white/5 hover:border-blue-500/50 transition-all group flex flex-col">
                        <div className="flex justify-between items-start mb-3">
                            <h4 className="font-bold text-white text-xs uppercase tracking-tight">Cloud Sync (Supabase)</h4>
                            <Shield className="w-4 h-4 text-gray-500 group-hover:text-blue-400 transition-colors" />
                        </div>
                        <p className="text-[11px] text-gray-500 mb-6 leading-relaxed">Sincroniza base de datos local a la nube para doble persistencia.</p>
                        <div className="grid grid-cols-2 gap-3 mt-auto">
                            <button
                                onClick={() => handleAction('Sync Usuarios', api.adminSyncUsersCloud)}
                                disabled={loading}
                                className="py-2.5 text-[9px] font-black text-center bg-blue-500/10 hover:bg-blue-500 text-blue-400 hover:text-white border border-blue-500/10 rounded-xl transition-all uppercase tracking-widest active:scale-95"
                            >
                                Usuarios
                            </button>
                            <button
                                onClick={() => handleAction('Backup Biblioteca', api.adminBackupLibrary)}
                                disabled={loading}
                                className="py-2.5 text-[9px] font-black text-center bg-purple-500/10 hover:bg-purple-500 text-purple-400 hover:text-white border border-purple-500/10 rounded-xl transition-all uppercase tracking-widest active:scale-95"
                            >
                                Biblioteca
                            </button>
                        </div>
                    </div>

                    {/* System Updates */}
                    <div className="p-6 rounded-2xl bg-white/5 border border-white/5 hover:border-green-500/50 transition-all group flex flex-col">
                        <div className="flex justify-between items-start mb-3">
                            <h4 className="font-bold text-white text-xs uppercase tracking-tight">System Update</h4>
                            <TrendingUp className="w-4 h-4 text-gray-500 group-hover:text-green-400 transition-colors" />
                        </div>
                        <p className="text-[11px] text-gray-500 mb-6 leading-relaxed">Ejecuta git pull para obtener los últimos cambios y reinicia.</p>
                        <button
                            onClick={() => handleAction('Actualizando', () => api.adminUpdateSystem({ force: false }))}
                            className="mt-auto w-full py-2.5 text-[10px] font-black text-center bg-green-600 hover:bg-green-700 text-white rounded-xl transition-all uppercase tracking-widest shadow-lg shadow-green-600/20 active:scale-95"
                        >
                            {actionLoading === 'Actualizando' ? <Loader2 className="w-3 h-3 animate-spin mx-auto" /> : "Update System"}
                        </button>
                    </div>

                    {/* Docker Restart */}
                    <div className="p-6 rounded-2xl bg-white/5 border border-white/5 hover:border-blue-400/50 transition-all group flex flex-col">
                        <div className="flex justify-between items-start mb-3">
                            <h4 className="font-bold text-white text-xs uppercase tracking-tight">Bot Docker</h4>
                            <RefreshCw className="w-4 h-4 text-gray-500 group-hover:text-blue-400 transition-colors" />
                        </div>
                        <p className="text-[11px] text-gray-500 mb-6 leading-relaxed">Reinicia el contenedor Docker del bot instantáneamente.</p>
                        <button
                            onClick={() => handleAction('Reiniciando', () => api.adminRestartDocker())}
                            className="mt-auto w-full py-2.5 text-[10px] font-black text-center bg-blue-500/20 hover:bg-blue-500 text-white rounded-xl transition-all uppercase tracking-widest active:scale-95"
                        >
                            Reset Container
                        </button>
                    </div>

                    {/* Reset Library */}
                    <div className="p-6 rounded-2xl bg-red-500/5 border border-red-500/10 hover:border-red-500/50 transition-all group flex flex-col">
                        <div className="flex justify-between items-start mb-3">
                            <h4 className="font-bold text-red-400 text-xs uppercase tracking-tight">Reset Library</h4>
                            <Trash2 className="w-4 h-4 text-gray-500 group-hover:text-red-400 transition-colors" />
                        </div>
                        <p className="text-[11px] text-gray-500 mb-6 leading-relaxed">Purga toda la base de datos de libros. <span className="text-red-500 font-bold italic">Irreversible.</span></p>
                        <button
                            onClick={() => {
                                if (confirm('¿ESTÁS ABSOLUTAMENTE SEGURO?')) {
                                    handleAction('Reset', () => api.adminResetLibrary(true));
                                }
                            }}
                            className="mt-auto w-full py-2.5 text-[10px] font-black text-center bg-red-600/10 hover:bg-red-600 text-red-600 hover:text-white border border-red-500/20 rounded-xl transition-all uppercase tracking-widest active:scale-95"
                        >
                            Purge Data
                        </button>
                    </div>
                </div>
            </div>

            {/* Extra Maintenance Tools */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-8 rounded-3xl bg-white/5 border border-white/5 hover:border-white/20 transition-all flex flex-col gap-4">
                    <div className="flex items-center gap-3">
                        <HardDrive className="w-5 h-5 text-gray-500" />
                        <h4 className="font-bold text-white text-xs uppercase tracking-widest">Backup Database (Local)</h4>
                    </div>
                    <p className="text-[11px] text-gray-500">Crea una instantánea .bak de la base de datos SQLite local para seguridad.</p>
                    <button className="w-full py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl text-[10px] font-black uppercase tracking-widest border border-white/5 transition-all active:scale-95">Generar .bak local</button>
                </div>

                <div className="p-8 rounded-3xl bg-red-500/5 border border-red-500/10 hover:border-red-500/20 transition-all flex flex-col gap-4">
                    <div className="flex items-center gap-3">
                        <RotateCcw className="w-5 h-5 text-red-500" />
                        <h4 className="font-bold text-red-400 text-xs uppercase tracking-widest">Global System Reset</h4>
                    </div>
                    <p className="text-[11px] text-gray-500">Reinicia todos los servicios, limpia caché y restablece sesiones activas.</p>
                    <button className="w-full py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-red-600/20 transition-all active:scale-95">Reset Global</button>
                </div>
            </div>
        </div>
    );
};
