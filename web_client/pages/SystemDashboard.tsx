import React, { useState } from 'react';
import {
    Settings,
    Database,
    RefreshCw,
    Activity,
    Trash2,
    Shield,
    Library,
    Loader2,
    Globe,
    HardDrive,
    RotateCcw,
    TrendingUp
} from 'lucide-react';
import { api } from '../src/services/api';
import { useTheme } from '../contexts/ThemeContext';

export const SystemDashboard: React.FC = () => {
    const { settings } = useTheme();
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
        <div className="flex flex-col gap-8 animate-in fade-in duration-500 pt-4">

            {/* Synchronization Strategy Table */}
            <div className="glass-panel p-8 rounded-3xl border border-white/5 shadow-sm">
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
                                <th className="pb-4 px-2 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            <tr className="group hover:bg-white/[0.01]">
                                <td className="py-4 px-2 font-bold text-gray-200">Books & Metadata</td>
                                <td className="py-4 px-2 text-gray-400">SQLite (Local)</td>
                                <td className="py-4 px-2"><span className="text-amber-500 font-black uppercase tracking-tighter text-[10px]">Manual Only</span></td>
                                <td className="py-4 px-2 italic text-gray-500 font-mono">Cloud Sync → Library</td>
                                <td className="py-4 px-2 text-right">
                                    <button
                                        onClick={() => handleAction('Backup Biblioteca', api.adminBackupLibrary)}
                                        disabled={loading}
                                        className="p-2 rounded-lg bg-primary/10 text-primary hover:bg-primary hover:text-white transition-all border border-primary/20"
                                        title="Sincronizar Biblioteca"
                                    >
                                        <RefreshCw className={`w-3.5 h-3.5 ${actionLoading === 'Backup Biblioteca' ? 'animate-spin' : ''}`} />
                                    </button>
                                </td>
                            </tr>
                            <tr className="group hover:bg-white/[0.01]">
                                <td className="py-4 px-2 font-bold text-gray-200">Library Sources</td>
                                <td className="py-4 px-2 text-gray-400">SQLite (Local)</td>
                                <td className="py-4 px-2"><span className="text-amber-500 font-black uppercase tracking-tighter text-[10px]">Manual Only</span></td>
                                <td className="py-4 px-2 italic text-gray-500 font-mono">Cloud Sync → Library</td>
                                <td className="py-4 px-2 text-right">
                                    <button
                                        onClick={() => handleAction('Escaneo', () => api.adminScanLibrary(true))}
                                        disabled={loading}
                                        className="p-2 rounded-lg bg-primary/10 text-primary hover:bg-primary hover:text-white transition-all border border-primary/20"
                                        title="Escanear Fuentes"
                                    >
                                        <Library className={`w-3.5 h-3.5 ${actionLoading === 'Escaneo' ? 'animate-spin' : ''}`} />
                                    </button>
                                </td>
                            </tr>
                            <tr className="group hover:bg-white/[0.01]">
                                <td className="py-4 px-2 font-bold text-gray-200">Users & Roles</td>
                                <td className="py-4 px-2 text-gray-400">Postgres & Supabase</td>
                                <td className="py-4 px-2"><span className="text-green-500 font-black uppercase tracking-tighter text-[10px]">Automatic / Real-time</span></td>
                                <td className="py-4 px-2 italic text-green-500/80 font-mono">Instant Sync</td>
                                <td className="py-4 px-2 text-right">
                                    <button
                                        onClick={() => handleAction('Sync Usuarios', api.adminSyncUsersCloud)}
                                        disabled={loading}
                                        className="p-2 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500 hover:text-white transition-all border border-blue-500/20"
                                        title="Forzar Sync Manual"
                                    >
                                        <Globe className={`w-3.5 h-3.5 ${actionLoading === 'Sync Usuarios' ? 'animate-spin' : ''}`} />
                                    </button>
                                </td>
                            </tr>
                            <tr className="group hover:bg-white/[0.01]">
                                <td className="py-4 px-2 font-bold text-gray-200">User Levels (Tiers)</td>
                                <td className="py-4 px-2 text-gray-400">Postgres & Supabase</td>
                                <td className="py-4 px-2"><span className="text-green-500 font-black uppercase tracking-tighter text-[10px]">Automatic / Real-time</span></td>
                                <td className="py-4 px-2 italic text-green-500/80 font-mono">Instant Sync</td>
                                <td className="py-4 px-2 text-right">
                                    <button
                                        onClick={() => handleAction('Sync Usuarios', api.adminSyncUsersCloud)}
                                        disabled={loading}
                                        className="p-2 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500 hover:text-white transition-all border border-blue-500/20"
                                        title="Forzar Sync Manual"
                                    >
                                        <Shield className={`w-3.5 h-3.5 ${actionLoading === 'Sync Usuarios' ? 'animate-spin' : ''}`} />
                                    </button>
                                </td>
                            </tr>
                            <tr className="group hover:bg-white/[0.01]">
                                <td className="py-4 px-2 font-bold text-gray-200">System Logs</td>
                                <td className="py-4 px-2 text-gray-400">Volatile (Memory)</td>
                                <td className="py-4 px-2 text-gray-600 font-black uppercase text-[10px]">None</td>
                                <td className="py-4 px-2 text-gray-600 italic">N/A</td>
                                <td className="py-4 px-2 text-right opacity-20"><RefreshCw className="w-3.5 h-3.5 ml-auto" /></td>
                            </tr>
                            <tr className="group hover:bg-white/[0.01]">
                                <td className="py-4 px-2 font-bold text-gray-200">Audit Logs</td>
                                <td className="py-4 px-2 text-gray-400">Supabase (Remote)</td>
                                <td className="py-4 px-2"><span className="text-green-500 font-black uppercase tracking-tighter text-[10px]">Automatic / Real-time</span></td>
                                <td className="py-4 px-2 text-green-500 font-black uppercase tracking-widest text-[9px]">Live Push</td>
                                <td className="py-4 px-2 text-right opacity-20"><RefreshCw className="w-3.5 h-3.5 ml-auto" /></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Maintenance Section - Refined layout */}
            <div className="glass-panel rounded-3xl p-8 border border-white/5">
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-3">
                        <Settings className="text-primary w-5 h-5" /> Mantenimiento
                    </h3>
                    <span className="px-3 py-1 bg-green-500/10 text-green-500 text-[9px] font-black rounded-lg border border-green-500/20 uppercase tracking-widest">Operativo</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Scan Library */}
                    <div className="glass-panel p-6 rounded-3xl flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Escanear Biblioteca</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Indexar nuevo contenido en /mnt/books/incoming.</p>
                            </div>
                            <div className="p-3 bg-primary/20 rounded-2xl text-primary border border-primary/20 shadow-lg shadow-primary/10">
                                <Activity className="w-5 h-5" />
                            </div>
                        </div>
                        <button
                            onClick={() => handleAction('Escaneo', () => api.adminScanLibrary(true))}
                            disabled={loading}
                            className="mt-4 w-full py-3 text-[10px] font-black text-center bg-primary hover:bg-primary-dark text-white rounded-2xl transition-all uppercase tracking-widest shadow-xl shadow-primary/20 active:scale-95 disabled:opacity-50 relative z-10"
                        >
                            {actionLoading === 'Escaneo' ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Ejecutar Escaneo"}
                        </button>
                        <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-primary/5 rounded-full blur-2xl group-hover:bg-primary/10 transition-all duration-700"></div>
                    </div>

                    {/* Enrich Metadata */}
                    <div className="glass-panel p-6 rounded-3xl flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Actualizar Metadatos</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Busca información extra via ISBN y web.</p>
                            </div>
                            <div className="p-3 bg-amber-500/20 rounded-2xl text-amber-500 border border-amber-500/20 shadow-lg shadow-amber-500/10">
                                <Globe className="w-5 h-5" />
                            </div>
                        </div>
                        <button
                            onClick={() => handleAction('Metadatos', api.adminEnrichMetadata)}
                            disabled={loading}
                            className="mt-4 w-full py-3 text-[10px] font-black text-center bg-amber-500/10 hover:bg-amber-500 text-amber-500 hover:text-white border border-amber-500/20 rounded-2xl transition-all uppercase tracking-widest active:scale-95 disabled:opacity-50 relative z-10"
                        >
                            {actionLoading === 'Metadatos' ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Sincronizar Web"}
                        </button>
                        <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-amber-500/5 rounded-full blur-2xl group-hover:bg-amber-500/10 transition-all duration-700"></div>
                    </div>

                    {/* Cloud Sync */}
                    <div className="glass-panel p-6 rounded-3xl flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Cloud Sync (Supabase)</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Sincroniza base local a la nube.</p>
                            </div>
                            <div className="p-3 bg-blue-500/20 rounded-2xl text-blue-400 border border-blue-500/20 shadow-lg shadow-blue-500/10">
                                <Shield className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3 mt-4 relative z-10">
                            <button
                                onClick={() => handleAction('Sync Usuarios', api.adminSyncUsersCloud)}
                                disabled={loading}
                                className="py-3 text-[9px] font-black text-center bg-blue-500/10 hover:bg-blue-500 text-blue-400 hover:text-white border border-blue-500/10 rounded-2xl transition-all uppercase tracking-widest active:scale-95 shadow-sm"
                            >
                                Usuarios
                            </button>
                            <button
                                onClick={() => handleAction('Backup Biblioteca', api.adminBackupLibrary)}
                                disabled={loading}
                                className="py-3 text-[9px] font-black text-center bg-purple-500/10 hover:bg-purple-500 text-purple-400 hover:text-white border border-purple-500/10 rounded-2xl transition-all uppercase tracking-widest active:scale-95 shadow-sm"
                            >
                                Biblioteca
                            </button>
                        </div>
                        <div
                            className="absolute -right-6 -bottom-6 w-24 h-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-all duration-700 pointer-events-none"
                            style={{ opacity: settings.cardGlowIntensity }}
                        ></div>
                    </div>

                    {/* System Updates */}
                    <div className="glass-panel p-6 rounded-3xl flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">System Update</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Pull de git y reinicio de servicios.</p>
                            </div>
                            <div className="p-3 bg-green-500/20 rounded-2xl text-green-400 border border-green-500/20 shadow-lg shadow-green-500/10">
                                <TrendingUp className="w-5 h-5" />
                            </div>
                        </div>
                        <button
                            onClick={() => handleAction('Actualizando', () => api.adminUpdateSystem())}
                            className="mt-4 w-full py-3 text-[10px] font-black text-center bg-green-600 hover:bg-green-700 text-white rounded-2xl transition-all uppercase tracking-widest shadow-xl shadow-green-600/20 active:scale-95 relative z-10"
                        >
                            {actionLoading === 'Actualizando' ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Update System"}
                        </button>
                        <div
                            className="absolute -right-6 -bottom-6 w-24 h-24 bg-green-500/5 rounded-full blur-2xl group-hover:bg-green-500/10 transition-all duration-700 pointer-events-none"
                            style={{ opacity: settings.cardGlowIntensity }}
                        ></div>
                    </div>

                    {/* Docker Restart */}
                    <div className="glass-panel p-6 rounded-3xl flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Bot Docker</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Reinicia el contenedor Docker.</p>
                            </div>
                            <div className="p-3 bg-blue-400/20 rounded-2xl text-blue-400 border border-blue-400/20 shadow-lg shadow-blue-400/10">
                                <RefreshCw className="w-5 h-5" />
                            </div>
                        </div>
                        <button
                            onClick={() => handleAction('Reiniciando', () => api.adminRestartDocker())}
                            className="mt-4 w-full py-3 text-[10px] font-black text-center bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-2xl transition-all uppercase tracking-widest active:scale-95 relative z-10"
                        >
                            {actionLoading === 'Reiniciando' ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Reset Container"}
                        </button>
                        <div
                            className="absolute -right-6 -bottom-6 w-24 h-24 bg-white/5 rounded-full blur-2xl group-hover:bg-white/10 transition-all duration-700 pointer-events-none"
                            style={{ opacity: settings.cardGlowIntensity }}
                        ></div>
                    </div>

                    {/* Reset Library */}
                    <div className="glass-panel p-6 rounded-3xl flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-red-400 text-[10px] uppercase tracking-widest mb-1">Reset Library</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Purga base de datos - <span className="text-red-500 font-bold">Irreversible.</span></p>
                            </div>
                            <div className="p-3 bg-red-500/20 rounded-2xl text-red-400 border border-red-500/20 shadow-lg shadow-red-500/10">
                                <Trash2 className="w-5 h-5" />
                            </div>
                        </div>
                        <button
                            onClick={() => {
                                if (confirm('¿ESTÁS ABSOLUTAMENTE SEGURO?')) {
                                    handleAction('Reset', () => api.adminResetLibrary(true));
                                }
                            }}
                            className="mt-4 w-full py-3 text-[10px] font-black text-center bg-red-600/10 hover:bg-red-600 text-red-600 hover:text-white border border-red-500/20 rounded-2xl transition-all uppercase tracking-widest active:scale-95 relative z-10"
                        >
                            {actionLoading === 'Reset' ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Purge Data"}
                        </button>
                        <div
                            className="absolute -right-6 -bottom-6 w-24 h-24 bg-red-500/5 rounded-full blur-2xl group-hover:bg-red-500/10 transition-all duration-700 pointer-events-none"
                            style={{ opacity: settings.cardGlowIntensity }}
                        ></div>
                    </div>
                </div>
            </div>

            {/* Extra Maintenance Tools */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-8 rounded-3xl border border-white/5 hover:border-white/20 transition-all flex flex-col gap-4">
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
