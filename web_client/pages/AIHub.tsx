
import React, { useEffect, useState } from 'react';
import {
    BrainCircuit,
    Sparkles,
    Clock,
    Database,
    Search,
    Activity,
    CheckCircle,
    AlertTriangle,
    Play
} from 'lucide-react';
import { api } from '../src/services/api';

export const AIHub: React.FC = () => {
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [scanHash, setScanHash] = useState('');
    const [scanResult, setScanResult] = useState<any>(null);
    const [scanning, setScanning] = useState(false);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            setLoading(true);
            const res = await api.getAiStats();
            if (res.result) {
                setStats(res.result);
            }
        } catch (e) {
            console.error("Failed to load stats", e);
        } finally {
            setLoading(false);
        }
    };

    const handleScan = async () => {
        if (!scanHash) return;
        setScanning(true);
        setScanResult(null);
        try {
            const res = await api.scanSeriesAi(scanHash);
            setScanResult(res.result || res);
        } catch (e: any) {
            setScanResult({ success: false, message: e.message || "Error desconocido" });
        } finally {
            setScanning(false);
            loadStats(); // Refresh stats
        }
    };

    if (loading && !stats) {
        return <div className="p-10 text-center text-gray-500 animate-pulse">Cargando Cerebro...</div>;
    }

    const aiActive = stats?.ai_active;

    return (
        <div className="max-w-6xl mx-auto px-4 py-8 animate-in fade-in duration-500">

            {/* Header */}
            <div className="flex items-center gap-4 mb-10">
                <div className="p-4 bg-purple-500/10 rounded-3xl border border-purple-500/20">
                    <BrainCircuit className="w-10 h-10 text-purple-400" />
                </div>
                <div>
                    <h1 className="text-4xl font-black text-white tracking-tight">AI Hub</h1>
                    <p className="text-gray-400 font-medium">Centro de Control de Inteligencia Artificial</p>
                </div>
                {aiActive ? (
                    <div className="ml-auto flex items-center gap-2 px-4 py-1.5 bg-green-500/10 border border-green-500/20 rounded-full text-green-400 text-xs font-black uppercase tracking-widest">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                        Online
                    </div>
                ) : (
                    <div className="ml-auto flex items-center gap-2 px-4 py-1.5 bg-red-500/10 border border-red-500/20 rounded-full text-red-400 text-xs font-black uppercase tracking-widest">
                        <div className="w-2 h-2 rounded-full bg-red-500"></div>
                        Offline (Sin API Key)
                    </div>
                )}
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                <StatCard
                    label="Libros Procesados"
                    value={stats?.total_processed || 0}
                    icon={CheckCircle}
                    color="text-emerald-400"
                    bg="bg-emerald-500/10"
                />
                <StatCard
                    label="Pendientes"
                    value={stats?.pending_optimization || 0}
                    icon={Clock}
                    color="text-amber-400"
                    bg="bg-amber-500/10"
                />
                <StatCard
                    label="Ahorro Tiempo (Hrs)"
                    value={stats?.time_saved_hours || 0}
                    icon={Sparkles}
                    color="text-purple-400"
                    bg="bg-purple-500/10"
                />
                <StatCard
                    label="Total Biblioteca"
                    value={stats?.total_books || 0}
                    icon={Database}
                    color="text-blue-400"
                    bg="bg-blue-500/10"
                />
            </div>

            {/* Action Area */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Manual Scan */}
                <div className="lg:col-span-8">
                    <div className="glass-panel p-8 rounded-[2rem] border border-white/5 bg-gradient-to-b from-white/5 to-transparent relative overflow-hidden">
                        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                            <Activity className="w-5 h-5 text-primary" />
                            Optimización Manual
                        </h3>

                        <div className="flex gap-4 mb-6">
                            <div className="relative flex-1">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                                <input
                                    type="text"
                                    placeholder="Pegar Hash de Serie (series_hash)..."
                                    value={scanHash}
                                    onChange={(e) => setScanHash(e.target.value)}
                                    className="w-full bg-black/20 border border-white/10 rounded-xl py-3 pl-12 pr-4 text-white placeholder-gray-500 focus:outline-none focus:border-primary/50 transition-all font-mono text-sm"
                                />
                            </div>
                            <button
                                onClick={handleScan}
                                disabled={scanning || !scanHash || !aiActive}
                                className="bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-white px-8 rounded-xl font-bold flex items-center gap-2 transition-all active:scale-95"
                            >
                                {scanning ? (
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                ) : (
                                    <>
                                        <Play className="w-4 h-4 fill-current" />
                                        Ejecutar
                                    </>
                                )}
                            </button>
                        </div>

                        {scanResult && (
                            <div className={`p-4 rounded-xl border ${scanResult.success ? 'bg-green-500/10 border-green-500/20 text-green-200' : 'bg-red-500/10 border-red-500/20 text-red-200'} animate-in slide-in-from-top-2`}>
                                <div className="flex items-center gap-2 font-bold mb-1">
                                    {scanResult.success ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                                    {scanResult.success ? "Éxito" : "Error"}
                                </div>
                                <p className="text-sm opacity-90">
                                    {scanResult.message}
                                </p>
                                {scanResult.updated_count !== undefined && (
                                    <p className="text-xs mt-2 opacity-70 uppercase tracking-wider font-bold">
                                        Libros actualizados: {scanResult.updated_count}
                                    </p>
                                )}
                            </div>
                        )}

                        <div className="mt-8 bg-black/20 rounded-xl p-4 border border-white/5">
                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Cómo funciona</h4>
                            <p className="text-sm text-gray-500 leading-relaxed">
                                Introduce el <code>series_hash</code> de un libro (puedes verlo en la URL del detalle del libro).
                                La IA analizará un libro representativo de ese grupo, determinará el nombre canónico y normalizará toda la serie.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Info Side */}
                <div className="lg:col-span-4">
                    <div className="glass-panel p-6 rounded-[2rem] border border-white/5 relative h-full">
                        <h3 className="text-lg font-bold text-white mb-4">Notas del Jardinero</h3>
                        <ul className="space-y-4">
                            <li className="flex gap-3 text-sm text-gray-400">
                                <span className="w-2 h-2 mt-1.5 rounded-full bg-blue-500 shrink-0"></span>
                                La IA solo actúa sobre campos vacíos o inconsistentes en modo automático.
                            </li>
                            <li className="flex gap-3 text-sm text-gray-400">
                                <span className="w-2 h-2 mt-1.5 rounded-full bg-purple-500 shrink-0"></span>
                                El modo manual fuerza una re-evaluación del nombre de la serie.
                            </li>
                            <li className="flex gap-3 text-sm text-gray-400">
                                <span className="w-2 h-2 mt-1.5 rounded-full bg-amber-500 shrink-0"></span>
                                Las cuotas de la API Gemini se respetan automáticamente (Rate Limit).
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};

const StatCard = ({ label, value, icon: Icon, color, bg }: any) => (
    <div className="glass-panel p-6 rounded-3xl border border-white/5 bg-gradient-to-br from-white/5 to-transparent hover:scale-[1.02] transition-transform duration-500 group">
        <div className="flex justify-between items-start mb-4">
            <div className={`p-3 rounded-2xl ${bg} ${color} border border-white/5 group-hover:scale-110 transition-transform duration-500`}>
                <Icon className="w-6 h-6" />
            </div>
        </div>
        <div className="space-y-1">
            <h4 className="text-3xl font-black text-white tracking-tight">{value}</h4>
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">{label}</p>
        </div>
    </div>
);
