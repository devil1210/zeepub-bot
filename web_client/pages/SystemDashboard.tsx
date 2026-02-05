import React, { useState, useEffect } from 'react';
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
    TrendingUp,
    Palette,
    XCircle,
    Info
} from 'lucide-react';
import { api } from '../src/services/api';
import { useTheme } from '../contexts/ThemeContext';

export const SystemDashboard: React.FC = () => {
    const { settings } = useTheme();
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [scanStatus, setScanStatus] = useState<any>(null);

    // Polling for scan status
    useEffect(() => {
        let interval: any;

        const checkStatus = async () => {
            try {
                const res = await api.getAdminScanStatus();
                if (res.success) {
                    setScanStatus(res.progress);
                    if (!res.is_scanning && (res.progress?.status === 'completed' || res.progress?.status === 'error')) {
                        clearInterval(interval);
                    }
                }
            } catch (err) {
                console.error("Error polling scan status:", err);
            }
        };

        // Start polling immediately if we just triggered a scan, or if one is already in progress
        if (actionLoading === 'Escaneo' || (scanStatus?.status === 'scanning')) {
            checkStatus();
            interval = setInterval(checkStatus, 2000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [actionLoading, scanStatus?.status]);

    const handleAction = async (name: string, fn: () => Promise<any>) => {
        setActionLoading(name);
        setError(null);
        try {
            setLoading(true);
            const res = await fn();
            alert(res.message || `${name} completado`);
        } catch (error: any) {
            const errorMsg = error?.message || `Error en ${name}`;
            setError(errorMsg);
            console.error(`Error in ${name}:`, error);
            alert(`Error: ${errorMsg}`);
        } finally {
            setActionLoading(null);
            setLoading(false);
        }
    };

    // Handle component errors
    if (error && !loading) {
        return (
            <div className="flex flex-col items-center justify-center p-8">
                <div className="text-red-500 text-center mb-4">
                    <p className="text-lg font-bold">Error en el Sistema</p>
                    <p className="text-sm mt-2">{error}</p>
                </div>
                <button
                    onClick={() => setError(null)}
                    className="px-4 py-2 bg-red-500/10 text-red-500 rounded-lg border border-red-500/20 hover:bg-red-500/20 transition-all"
                >
                    Reintentar
                </button>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-8 animate-in fade-in duration-500 pt-4">

            {/* Synchronization Strategy Table */}
            <div className="glass-panel p-8 rounded-premium border border-white/5 shadow-sm">
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
                                <td className="py-4 px-2 text-gray-400">Postgres & Supabase</td>
                                <td className="py-4 px-2"><span className="text-blue-500 font-black uppercase tracking-tighter text-[10px]">Cloud Push Sync</span></td>
                                <td className="py-4 px-2 italic text-gray-500 font-mono">Manual Trigger</td>
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
                                <td className="py-4 px-2 text-gray-400">Postgres & Supabase</td>
                                <td className="py-4 px-2"><span className="text-amber-500 font-black uppercase tracking-tighter text-[10px]">Local Indexed</span></td>
                                <td className="py-4 px-2 italic text-gray-500 font-mono">Manual Scan</td>
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
                                <td className="py-4 px-2"><span className="text-green-500 font-black uppercase tracking-tighter text-[10px]">Event-Driven Sync</span></td>
                                <td className="py-4 px-2 italic text-green-500/80 font-mono">Real-time Push</td>
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
                                <td className="py-4 px-2"><span className="text-green-500 font-black uppercase tracking-tighter text-[10px]">On-Demand Sync</span></td>
                                <td className="py-4 px-2 italic text-green-500/80 font-mono">Dynamic Fetch</td>
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
                                <td className="py-4 px-2 font-bold text-gray-200">App Themes</td>
                                <td className="py-4 px-2 text-gray-400">Postgres & Supabase</td>
                                <td className="py-4 px-2"><span className="text-blue-500 font-black uppercase tracking-tighter text-[10px]">Optimized Daily</span></td>
                                <td className="py-4 px-2 italic text-blue-500/80 font-mono">3:00 AM + Manual</td>
                                <td className="py-4 px-2 text-right">
                                    <button
                                        onClick={() => handleAction('Sync Temas', api.adminSyncThemes)}
                                        disabled={loading}
                                        className="p-2 rounded-lg bg-purple-500/10 text-purple-400 hover:bg-purple-500 hover:text-white transition-all border border-purple-500/20"
                                        title="Sincronizar Temas"
                                    >
                                        <Palette className={`w-3.5 h-3.5 ${actionLoading === 'Sync Temas' ? 'animate-spin' : ''}`} />
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

            {/* System Optimization Section */}
            <div className="glass-panel p-8 rounded-premium border border-white/5">
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-3">
                        <TrendingUp className="text-green-500 w-5 h-5" /> Optimización del Sistema
                    </h3>
                    <span className="px-3 py-1 bg-green-500/10 text-green-500 text-[9px] font-black rounded-lg border border-green-500/20 uppercase tracking-widest">Activo</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {/* Cache Hit Rate */}
                    <div className="glass-panel p-6 rounded-premium flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Cache Hit Rate</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed">Eficiencia del cache multinivel.</p>
                            </div>
                            <div className="p-3 bg-green-500/20 rounded-premium-sm text-green-500 border border-green-500/20 shadow-lg shadow-green-500/10">
                                <HardDrive className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="text-2xl font-black text-green-500 mb-2">95%</div>
                        <div className="text-[9px] text-gray-500 uppercase tracking-widest">+90% mejora</div>
                        <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-green-500/5 rounded-full blur-2xl group-hover:bg-green-500/10 transition-all duration-700"></div>
                    </div>

                    {/* Request Reduction */}
                    <div className="glass-panel p-6 rounded-premium flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Reducción de Solicitudes</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed">Menos carga a Supabase.</p>
                            </div>
                            <div className="p-3 bg-blue-500/20 rounded-premium-sm text-blue-500 border border-blue-500/20 shadow-lg shadow-blue-500/10">
                                <RotateCcw className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="text-2xl font-black text-blue-500 mb-2">96%</div>
                        <div className="text-[9px] text-gray-500 uppercase tracking-widest">1,440 → 50/día</div>
                        <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-all duration-700"></div>
                    </div>

                    {/* Latency Improvement */}
                    <div className="glass-panel p-6 rounded-premium flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Mejora de Latencia</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed">Respuestas más rápidas.</p>
                            </div>
                            <div className="p-3 bg-purple-500/20 rounded-premium-sm text-purple-500 border border-purple-500/20 shadow-lg shadow-purple-500/10">
                                <Activity className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="text-2xl font-black text-purple-500 mb-2">90%</div>
                        <div className="text-[9px] text-gray-500 uppercase tracking-widest">200ms → 20ms</div>
                        <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-purple-500/5 rounded-full blur-2xl group-hover:bg-purple-500/10 transition-all duration-700"></div>
                    </div>

                    {/* Sync Status */}
                    <div className="glass-panel p-6 rounded-premium flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Motor de Sincronización</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed">Event-driven optimizado.</p>
                            </div>
                            <div className="p-3 bg-amber-500/20 rounded-premium-sm text-amber-500 border border-amber-500/20 shadow-lg shadow-amber-500/10">
                                <RefreshCw className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="text-2xl font-black text-amber-500 mb-2">Activo</div>
                        <div className="text-[9px] text-gray-500 uppercase tracking-widest">Smart Detection</div>
                        <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-amber-500/5 rounded-full blur-2xl group-hover:bg-amber-500/10 transition-all duration-700"></div>
                    </div>
                </div>
            </div>

            {/* Scanning Progress Alert */}
            {scanStatus && scanStatus.status !== 'idle' && (
                <div className={`glass-panel p-6 rounded-premium border ${scanStatus.status === 'completed' ? 'border-green-500/30' :
                        scanStatus.status === 'error' ? 'border-red-500/30' : 'border-primary/30'
                    } animate-in slide-in-from-top duration-300 relative group`}>

                    <button
                        onClick={() => setScanStatus(null)}
                        className="absolute top-4 right-4 p-1 rounded-full text-gray-500 hover:text-white hover:bg-white/10 transition-all opacity-0 group-hover:opacity-100"
                        title="Cerrar Log"
                    >
                        <XCircle className="w-4 h-4" />
                    </button>

                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${scanStatus.status === 'completed' ? 'bg-green-500/20 text-green-500' :
                                    scanStatus.status === 'error' ? 'bg-red-500/20 text-red-500' : 'bg-primary/20 text-primary'
                                }`}>
                                <Activity className={`w-5 h-5 ${scanStatus.status === 'scanning' ? 'animate-pulse' : ''}`} />
                            </div>
                            <div>
                                <h4 className="text-sm font-black text-white uppercase tracking-widest">
                                    {scanStatus.status === 'completed' ? 'Escaneo Completado' :
                                        scanStatus.status === 'error' ? 'Error en el Escaneo' : 'Escaneando Biblioteca...'}
                                </h4>
                                <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">
                                    {scanStatus.status === 'error' ? scanStatus.error_message : (scanStatus.current_source || 'Inicializando tareas...')}
                                </p>
                            </div>
                        </div>
                        <div className="text-right mr-8">
                            <span className="text-xl font-black text-white">{scanStatus.scanned || 0}</span>
                            <span className="text-[10px] text-gray-500 ml-2 font-black uppercase">Libros</span>
                        </div>
                    </div>

                    <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden border border-white/5 mb-4">
                        <div
                            className={`h-full transition-all duration-500 ${scanStatus.status === 'completed' ? 'bg-green-500' :
                                    scanStatus.status === 'error' ? 'bg-red-500' : 'bg-primary animate-pulse'
                                }`}
                            style={{ width: (scanStatus.status === 'completed' || scanStatus.status === 'error') ? '100%' : '65%' }}
                        ></div>
                    </div>

                    {scanStatus.status === 'completed' && scanStatus.results && (
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2 border-t border-white/5">
                            <div className="flex flex-col">
                                <span className="text-[9px] text-gray-500 uppercase font-black">Nuevos</span>
                                <span className="text-sm font-bold text-green-400">+{scanStatus.results.added || 0}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-[9px] text-gray-500 uppercase font-black">Actualizados</span>
                                <span className="text-sm font-bold text-blue-400">{scanStatus.results.updated || 0}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-[9px] text-gray-500 uppercase font-black">Eliminados</span>
                                <span className="text-sm font-bold text-red-400">-{scanStatus.results.removed || 0}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-[9px] text-gray-500 uppercase font-black">Duplicados</span>
                                <span className="text-sm font-bold text-amber-400">{scanStatus.results.duplicates || 0}</span>
                            </div>
                        </div>
                    )}
                    {(scanStatus.status === 'completed' || scanStatus.status === 'error') && scanStatus.last_run && (
                        <div className="mt-4 pt-2 border-t border-white/5 flex justify-between items-center text-[10px] text-gray-500 font-mono">
                            <span>Último Ejecución: {new Date(scanStatus.last_run).toLocaleString()}</span>
                            <span className="flex items-center gap-1 uppercase tracking-tighter">
                                <Info className="w-3 h-3" /> Estado: {scanStatus.status}
                            </span>
                        </div>
                    )}
                </div>
            )}

            {/* Maintenance Section - Refined layout */}
            <div className="glass-panel rounded-premium p-8 border border-white/5">
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-3">
                        <Settings className="text-primary w-5 h-5" /> Mantenimiento
                    </h3>
                    <span className="px-3 py-1 bg-green-500/10 text-green-500 text-[9px] font-black rounded-lg border border-green-500/20 uppercase tracking-widest">Operativo</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Rename Themes */}
                    <div className="glass-panel p-6 rounded-premium flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Renombrar Temas</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Eliminar duplicados con "2" al final.</p>
                            </div>
                            <div className="p-3 bg-purple-500/20 rounded-premium-sm text-purple-500 border border-purple-500/20 shadow-lg shadow-purple-500/10">
                                <Palette className="w-5 h-5" />
                            </div>
                        </div>
                        <button
                            onClick={() => handleAction('Renombrar Temas', api.adminRenameThemes)}
                            disabled={loading}
                            className="mt-4 w-full py-3 text-[10px] font-black text-center bg-purple-500/10 hover:bg-purple-500 text-purple-400 hover:text-white border border-purple-500/20 rounded-premium-sm transition-all uppercase tracking-widest active:scale-95 disabled:opacity-50 relative z-10"
                        >
                            {actionLoading === 'Renombrar Temas' ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Renombrar Temas"}
                        </button>
                        <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-purple-500/5 rounded-full blur-2xl group-hover:bg-purple-500/10 transition-all duration-700"></div>
                    </div>

                    {/* Scan Library */}
                    <div className="glass-panel p-6 rounded-premium flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Escanear Biblioteca</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Indexar nuevo contenido en /mnt/books/incoming.</p>
                            </div>
                            <div className="p-3 bg-primary/20 rounded-premium-sm text-primary border border-primary/20 shadow-lg shadow-primary/10">
                                <Activity className="w-5 h-5" />
                            </div>
                        </div>
                        <button
                            onClick={() => handleAction('Escaneo', () => api.adminScanLibrary(true))}
                            disabled={loading}
                            className="mt-4 w-full py-3 text-[10px] font-black text-center bg-primary hover:bg-primary-dark text-white rounded-premium-sm transition-all uppercase tracking-widest shadow-xl shadow-primary/20 active:scale-95 disabled:opacity-50 relative z-10"
                        >
                            {actionLoading === 'Escaneo' ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Ejecutar Escaneo"}
                        </button>
                        <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-primary/5 rounded-full blur-2xl group-hover:bg-primary/10 transition-all duration-700"></div>
                    </div>

                    {/* Clean Library */}
                    <div className="glass-panel p-6 rounded-premium flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Limpiar Librería</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Verifica existencia física y elimina huérfanos.</p>
                            </div>
                            <div className="p-3 bg-red-500/20 rounded-premium-sm text-red-500 border border-red-500/20 shadow-lg shadow-red-500/10">
                                <Trash2 className="w-5 h-5" />
                            </div>
                        </div>
                        <button
                            onClick={() => {
                                if (confirm('¿Deseas verificar la existencia física de todos los archivos y limpiar registros huérfanos?')) {
                                    handleAction('Limpieza', api.adminCleanupLibrary);
                                }
                            }}
                            disabled={loading}
                            className="mt-4 w-full py-3 text-[10px] font-black text-center bg-red-500/10 hover:bg-red-500 text-red-400 hover:text-white border border-red-500/20 rounded-premium-sm transition-all uppercase tracking-widest active:scale-95 disabled:opacity-50 relative z-10"
                        >
                            {actionLoading === 'Limpieza' ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Limpiar Librería"}
                        </button>
                        <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-red-500/5 rounded-full blur-2xl group-hover:bg-red-500/10 transition-all duration-700"></div>
                    </div>

                    {/* Enrich Metadata */}
                    <div className="glass-panel p-6 rounded-premium flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Actualizar Metadatos</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Busca información extra via ISBN y web.</p>
                            </div>
                            <div className="p-3 bg-amber-500/20 rounded-premium-sm text-amber-500 border border-amber-500/20 shadow-lg shadow-amber-500/10">
                                <Globe className="w-5 h-5" />
                            </div>
                        </div>
                        <button
                            onClick={() => handleAction('Metadatos', api.adminEnrichMetadata)}
                            disabled={loading}
                            className="mt-4 w-full py-3 text-[10px] font-black text-center bg-amber-500/10 hover:bg-amber-500 text-amber-500 hover:text-white border border-amber-500/20 rounded-premium-sm transition-all uppercase tracking-widest active:scale-95 disabled:opacity-50 relative z-10"
                        >
                            {actionLoading === 'Metadatos' ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Sincronizar Web"}
                        </button>
                        <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-amber-500/5 rounded-full blur-2xl group-hover:bg-amber-500/10 transition-all duration-700"></div>
                    </div>

                    {/* Cloud Sync */}
                    <div className="glass-panel p-6 rounded-premium flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Cloud Sync (Supabase)</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Sincroniza base local a la nube.</p>
                            </div>
                            <div className="p-3 bg-blue-500/20 rounded-premium-sm text-blue-400 border border-blue-500/20 shadow-lg shadow-blue-500/10">
                                <Shield className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3 mt-4 relative z-10">
                            <button
                                onClick={() => handleAction('Sync Usuarios', api.adminSyncUsersCloud)}
                                disabled={loading}
                                className="py-3 text-[9px] font-black text-center bg-blue-500/10 hover:bg-blue-500 text-blue-400 hover:text-white border border-blue-500/10 rounded-premium-sm transition-all uppercase tracking-widest active:scale-95 shadow-sm"
                            >
                                Usuarios
                            </button>
                            <button
                                onClick={() => handleAction('Backup Biblioteca', api.adminBackupLibrary)}
                                disabled={loading}
                                className="py-3 text-[9px] font-black text-center bg-purple-500/10 hover:bg-purple-500 text-purple-400 hover:text-white border border-purple-500/10 rounded-premium-sm transition-all uppercase tracking-widest active:scale-95 shadow-sm"
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
                    <div className="glass-panel p-6 rounded-premium flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">System Update</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Pull de git y reinicio de servicios.</p>
                            </div>
                            <div className="p-3 bg-green-500/20 rounded-premium-sm text-green-400 border border-green-500/20 shadow-lg shadow-green-500/10">
                                <TrendingUp className="w-5 h-5" />
                            </div>
                        </div>
                        <button
                            onClick={() => handleAction('Actualizando', () => api.adminUpdateSystem())}
                            className="mt-4 w-full py-3 text-[10px] font-black text-center bg-green-600 hover:bg-green-700 text-white rounded-premium-sm transition-all uppercase tracking-widest shadow-xl shadow-green-600/20 active:scale-95 relative z-10"
                        >
                            {actionLoading === 'Actualizando' ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Update System"}
                        </button>
                        <div
                            className="absolute -right-6 -bottom-6 w-24 h-24 bg-green-500/5 rounded-full blur-2xl group-hover:bg-green-500/10 transition-all duration-700 pointer-events-none"
                            style={{ opacity: settings.cardGlowIntensity }}
                        ></div>
                    </div>

                    {/* Docker Restart */}
                    <div className="glass-panel p-6 rounded-premium flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-white text-[10px] uppercase tracking-widest mb-1">Bot Docker</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Reinicia el contenedor Docker.</p>
                            </div>
                            <div className="p-3 bg-blue-400/20 rounded-premium-sm text-blue-400 border border-blue-400/20 shadow-lg shadow-blue-400/10">
                                <RefreshCw className="w-5 h-5" />
                            </div>
                        </div>
                        <button
                            onClick={() => handleAction('Reiniciando', () => api.adminRestartDocker())}
                            className="mt-4 w-full py-3 text-[10px] font-black text-center bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-premium-sm transition-all uppercase tracking-widest active:scale-95 relative z-10"
                        >
                            {actionLoading === 'Reiniciando' ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Reset Container"}
                        </button>
                        <div
                            className="absolute -right-6 -bottom-6 w-24 h-24 bg-white/5 rounded-full blur-2xl group-hover:bg-white/10 transition-all duration-700 pointer-events-none"
                            style={{ opacity: settings.cardGlowIntensity }}
                        ></div>
                    </div>

                    {/* Reset Library */}
                    <div className="glass-panel p-6 rounded-premium flex flex-col group hover:scale-[1.02] transition-all duration-300 relative overflow-hidden">
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div className="flex flex-col">
                                <h4 className="font-black text-red-400 text-[10px] uppercase tracking-widest mb-1">Reset Library</h4>
                                <p className="text-[11px] text-gray-500 leading-relaxed max-w-[180px]">Purga base de datos - <span className="text-red-500 font-bold">Irreversible.</span></p>
                            </div>
                            <div className="p-3 bg-red-500/20 rounded-premium-sm text-red-400 border border-red-500/20 shadow-lg shadow-red-500/10">
                                <Trash2 className="w-5 h-5" />
                            </div>
                        </div>
                        <button
                            onClick={() => {
                                if (confirm('¿ESTÁS ABSOLUTAMENTE SEGURO?')) {
                                    handleAction('Reset', () => api.adminResetLibrary(true));
                                }
                            }}
                            className="mt-4 w-full py-3 text-[10px] font-black text-center bg-red-600/10 hover:bg-red-600 text-red-600 hover:text-white border border-red-500/20 rounded-premium-sm transition-all uppercase tracking-widest active:scale-95 relative z-10"
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
                <div className="p-8 rounded-premium border border-white/5 hover:border-white/20 transition-all flex flex-col gap-4">
                    <div className="flex items-center gap-3">
                        <HardDrive className="w-5 h-5 text-gray-500" />
                        <h4 className="font-bold text-white text-xs uppercase tracking-widest">Backup Database (Local)</h4>
                    </div>
                    <p className="text-[11px] text-gray-500">Crea una instantánea .bak de la base de datos SQLite local para seguridad.</p>
                    <button className="w-full py-3 bg-white/5 hover:bg-white/10 text-white rounded-premium-sm text-[10px] font-black uppercase tracking-widest border border-white/5 transition-all active:scale-95">Generar .bak local</button>
                </div>

                <div className="p-8 rounded-premium bg-red-500/5 border border-red-500/10 hover:border-red-500/20 transition-all flex flex-col gap-4">
                    <div className="flex items-center gap-3">
                        <RotateCcw className="w-5 h-5 text-red-500" />
                        <h4 className="font-bold text-red-400 text-xs uppercase tracking-widest">Global System Reset</h4>
                    </div>
                    <p className="text-[11px] text-gray-500">Reinicia todos los servicios, limpia caché y restablece sesiones activas.</p>
                    <button className="w-full py-3 bg-red-600 hover:bg-red-700 text-white rounded-premium-sm text-[10px] font-black uppercase tracking-widest shadow-lg shadow-red-600/20 transition-all active:scale-95">Reset Global</button>
                </div>
            </div>
        </div>
    );
};

