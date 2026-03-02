import React, { useState, useEffect, useMemo } from 'react';
import {
    ShieldCheck,
    Search,
    Filter,
    CheckCircle,
    AlertTriangle,
    X,
    CheckSquare,
    Square,
    Play,
    Pause,
    RefreshCw,
    Database,
    Zap,
    Eye,
    Edit2,
    Save,
    XCircle
} from 'lucide-react';
import { api } from '@shared/services/api';
import { useTheme } from '@shared/contexts/ThemeContext';
import { useNavigation } from '@shared/contexts/NavigationContext';
import { useTelegram } from '@shared/contexts/TelegramContext';

interface BulkIssue {
    type: string;
    series_id: number;
    series_hash: string;
    current_value: string;
    suggested_value: string;
    field: string;
    severity: 'low' | 'medium' | 'high';
    description: string;
}

interface AnalysisResult {
    issues: BulkIssue[];
    total_series: number;
    processed: number;
    issues_count: number;
}

export const BulkReviewPage: React.FC = () => {
    const { settings } = useTheme();
    const { webApp } = useTelegram();
    const { setContextType, setCustomActions, setVisible } = useNavigation();

    // Estado
    const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
    const [selectedIssues, setSelectedIssues] = useState<Set<string>>(new Set());
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isUpdating, setIsUpdating] = useState(false);
    const [progress, setProgress] = useState(0);
    const [currentStep, setCurrentStep] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'analyze' | 'review' | 'apply'>('analyze');
    const [filterSeverity, setFilterSeverity] = useState<'all' | 'low' | 'medium' | 'high'>('all');
    const [filterType, setFilterType] = useState<string>('all');

    useEffect(() => {
        setContextType('admin');
        setVisible(true);
        setCustomActions({
            title: 'Revisión Masiva',
            buttons: []
        });
    }, [setContextType, setVisible, setCustomActions]);

    // Filtrar issues
    const filteredIssues = useMemo(() => {
        if (!analysisResult) return [];

        return analysisResult.issues.filter(issue => {
            if (filterSeverity !== 'all' && issue.severity !== filterSeverity) return false;
            if (filterType !== 'all' && issue.type !== filterType) return false;
            return true;
        });
    }, [analysisResult, filterSeverity, filterType]);

    // Análisis masivo
    const handleAnalyze = async () => {
        setIsAnalyzing(true);
        setError(null);
        setProgress(0);
        setCurrentStep('Iniciando análisis...');

        try {
            webApp?.HapticFeedback?.notificationOccurred('start');

            const response = await api.rpc('bulk-analyze-library', {
                filters: {},
                batch_size: 100
            });

            if (response.success) {
                setAnalysisResult(response.result);
                setActiveTab('review');
                webApp?.HapticFeedback?.notificationOccurred('success');
            } else {
                throw new Error('Error en el análisis');
            }
        } catch (err: any) {
            setError(err?.message || 'Error al analizar la librería');
            webApp?.HapticFeedback?.notificationOccurred('error');
        } finally {
            setIsAnalyzing(false);
            setProgress(0);
            setCurrentStep('');
        }
    };

    // Selección de issues
    const toggleIssueSelection = (issueId: string) => {
        const newSelected = new Set(selectedIssues);
        if (newSelected.has(issueId)) {
            newSelected.delete(issueId);
        } else {
            newSelected.add(issueId);
        }
        setSelectedIssues(newSelected);
    };

    const toggleSelectAll = () => {
        if (selectedIssues.size === filteredIssues.length) {
            setSelectedIssues(new Set());
        } else {
            setSelectedIssues(new Set(filteredIssues.map(issue => `${issue.series_id}-${issue.field}`)));
        }
    };

    // Aplicar correcciones
    const handleApplyCorrections = async () => {
        if (selectedIssues.size === 0) {
            setError('No hay correcciones seleccionadas');
            return;
        }

        setIsUpdating(true);
        setError(null);
        setProgress(0);
        setCurrentStep('Aplicando correcciones...');

        try {
            webApp?.HapticFeedback?.notificationOccurred('start');

            // Preparar actualizaciones
            const updates = Array.from(selectedIssues).map(issueId => {
                const [seriesId, field] = issueId.split('-');
                const issue = filteredIssues.find(i =>
                    i.series_id === parseInt(seriesId) && i.field === field
                );

                return {
                    series_id: parseInt(seriesId),
                    field: field,
                    new_value: issue?.suggested_value || ''
                };
            });

            const response = await api.rpc('bulk-update-metadata', {
                updates: updates
            });

            if (response.success) {
                const { updated, errors } = response.result;

                if (errors.length > 0) {
                    setError(`${updated} correcciones aplicadas, ${errors.length} errores`);
                } else {
                    webApp?.HapticFeedback?.notificationOccurred('success');
                    // Limpiar selección y re-analizar
                    setSelectedIssues(new Set());
                    await handleAnalyze();
                }
            } else {
                throw new Error('Error al aplicar correcciones');
            }
        } catch (err: any) {
            setError(err?.message || 'Error al aplicar correcciones');
            webApp?.HapticFeedback?.notificationOccurred('error');
        } finally {
            setIsUpdating(false);
            setProgress(0);
            setCurrentStep('');
        }
    };

    // Renderizado de severidad
    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'high': return 'text-red-400 bg-red-400/10 border-red-400/30';
            case 'medium': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30';
            case 'low': return 'text-blue-400 bg-blue-400/10 border-blue-400/30';
            default: return 'text-gray-400 bg-gray-400/10 border-gray-400/30';
        }
    };

    const getSeverityLabel = (severity: string) => {
        switch (severity) {
            case 'high': return 'Alto';
            case 'medium': return 'Medio';
            case 'low': return 'Bajo';
            default: return 'Desconocido';
        }
    };

    return (
        <div className="min-h-screen bg-black/40 backdrop-blur-xl p-4">
            <div className="max-w-6xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                            <Database className="w-6 h-6 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-black text-white">Revisión Masiva</h1>
                            <p className="text-gray-400 text-sm">Análisis y corrección de metadatos</p>
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 p-1 bg-white/5 rounded-xl border border-white/10">
                    <button
                        onClick={() => setActiveTab('analyze')}
                        className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-all ${
                            activeTab === 'analyze'
                                ? 'bg-primary text-white shadow-lg'
                                : 'text-gray-400 hover:text-white hover:bg-white/10'
                        }`}
                    >
                        <Search className="w-4 h-4" />
                        Analizar
                    </button>
                    <button
                        onClick={() => setActiveTab('review')}
                        disabled={!analysisResult}
                        className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-all ${
                            activeTab === 'review'
                                ? 'bg-primary text-white shadow-lg'
                                : 'text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed'
                        }`}
                    >
                        <Eye className="w-4 h-4" />
                        Revisar
                        {analysisResult && (
                            <span className="bg-white/20 px-2 py-0.5 rounded-full text-xs">
                                {analysisResult.issues_count}
                            </span>
                        )}
                    </button>
                    <button
                        onClick={() => setActiveTab('apply')}
                        disabled={selectedIssues.size === 0}
                        className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-all ${
                            activeTab === 'apply'
                                ? 'bg-primary text-white shadow-lg'
                                : 'text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed'
                        }`}
                    >
                        <Zap className="w-4 h-4" />
                        Aplicar
                        {selectedIssues.size > 0 && (
                            <span className="bg-white/20 px-2 py-0.5 rounded-full text-xs">
                                {selectedIssues.size}
                            </span>
                        )}
                    </button>
                </div>

                {/* Error */}
                {error && (
                    <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                        <div className="flex items-start gap-3">
                            <XCircle className="w-5 h-5 text-red-400 mt-0.5" />
                            <div>
                                <p className="text-red-400 font-medium">Error</p>
                                <p className="text-red-300 text-sm mt-1">{error}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Tab: Analyze */}
                {activeTab === 'analyze' && (
                    <div className="space-y-6">
                        <div className="p-6 rounded-xl bg-white/5 border border-white/10">
                            <h2 className="text-lg font-bold text-white mb-4">Análisis de Librería</h2>
                            <p className="text-gray-400 mb-6">
                                Analiza toda la librería en busca de problemas comunes en metadatos como títulos incompletos,
                                caracteres especiales faltantes, o inconsistencias en slugs.
                            </p>

                            <button
                                onClick={handleAnalyze}
                                disabled={isAnalyzing}
                                className="w-full py-3 px-6 bg-primary text-white rounded-xl font-bold
                                         hover:bg-primary/80 transition-all disabled:opacity-50 disabled:cursor-not-allowed
                                         flex items-center justify-center gap-2"
                            >
                                {isAnalyzing ? (
                                    <>
                                        <RefreshCw className="w-5 h-5 animate-spin" />
                                        {currentStep || 'Analizando...'}
                                    </>
                                ) : (
                                    <>
                                        <Search className="w-5 h-5" />
                                        Iniciar Análisis Masivo
                                    </>
                                )}
                            </button>
                        </div>

                        {isAnalyzing && (
                            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                <div className="flex items-center gap-3">
                                    <RefreshCw className="w-5 h-5 animate-spin text-primary" />
                                    <div className="flex-1">
                                        <p className="text-white font-medium">{currentStep}</p>
                                        <div className="mt-2 h-2 bg-white/10 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-primary transition-all duration-300"
                                                style={{ width: `${progress}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Tab: Review */}
                {activeTab === 'review' && analysisResult && (
                    <div className="space-y-6">
                        {/* Stats */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                <p className="text-gray-400 text-sm">Total Series</p>
                                <p className="text-2xl font-black text-white">{analysisResult.total_series}</p>
                            </div>
                            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                <p className="text-gray-400 text-sm">Procesadas</p>
                                <p className="text-2xl font-black text-white">{analysisResult.processed}</p>
                            </div>
                            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                <p className="text-gray-400 text-sm">Problemas</p>
                                <p className="text-2xl font-black text-primary">{analysisResult.issues_count}</p>
                            </div>
                        </div>

                        {/* Filters */}
                        <div className="flex flex-wrap gap-2">
                            <select
                                value={filterSeverity}
                                onChange={(e) => setFilterSeverity(e.target.value as any)}
                                className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm"
                            >
                                <option value="all">Todas las Severidades</option>
                                <option value="high">Alta</option>
                                <option value="medium">Media</option>
                                <option value="low">Baja</option>
                            </select>

                            <select
                                value={filterType}
                                onChange={(e) => setFilterType(e.target.value)}
                                className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm"
                            >
                                <option value="all">Todos los Tipos</option>
                                <option value="missing_question_mark">Signos de Interrogación</option>
                                <option value="title_cleanup">Limpieza de Títulos</option>
                                <option value="slug_inconsistency">Inconsistencia de Slugs</option>
                            </select>
                        </div>

                        {/* Issues List */}
                        <div className="space-y-3">
                            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                                <button
                                    onClick={toggleSelectAll}
                                    className="flex items-center gap-2 text-white hover:text-primary transition-colors"
                                >
                                    {selectedIssues.size === filteredIssues.length ? (
                                        <CheckSquare className="w-4 h-4" />
                                    ) : (
                                        <Square className="w-4 h-4" />
                                    )}
                                    <span className="text-sm">
                                        {selectedIssues.size === filteredIssues.length
                                            ? 'Deseleccionar todo'
                                            : 'Seleccionar todo'
                                        }
                                    </span>
                                </button>
                                <span className="text-gray-400 text-sm">
                                    {selectedIssues.size} de {filteredIssues.length} seleccionados
                                </span>
                            </div>

                            {filteredIssues.map((issue) => {
                                const issueId = `${issue.series_id}-${issue.field}`;
                                const isSelected = selectedIssues.has(issueId);

                                return (
                                    <div
                                        key={issueId}
                                        className={`p-4 rounded-xl border transition-all cursor-pointer ${
                                            isSelected
                                                ? 'bg-primary/10 border-primary/30'
                                                : 'bg-white/5 border-white/10 hover:bg-white/10'
                                        }`}
                                        onClick={() => toggleIssueSelection(issueId)}
                                    >
                                        <div className="flex items-start gap-3">
                                            <button
                                                className="mt-1"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    toggleIssueSelection(issueId);
                                                }}
                                            >
                                                {isSelected ? (
                                                    <CheckSquare className="w-4 h-4 text-primary" />
                                                ) : (
                                                    <Square className="w-4 h-4 text-gray-400" />
                                                )}
                                            </button>

                                            <div className="flex-1 space-y-2">
                                                <div className="flex items-center gap-2">
                                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(issue.severity)}`}>
                                                        {getSeverityLabel(issue.severity)}
                                                    </span>
                                                    <span className="text-gray-400 text-xs">
                                                        {issue.field === 'series_name' ? 'Título' : 'Slug'}
                                                    </span>
                                                </div>

                                                <p className="text-white font-medium">{issue.description}</p>

                                                <div className="space-y-1">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-gray-400 text-sm">Actual:</span>
                                                        <span className="text-red-400 text-sm font-mono">
                                                            "{issue.current_value}"
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-gray-400 text-sm">Sugerido:</span>
                                                        <span className="text-green-400 text-sm font-mono">
                                                            "{issue.suggested_value}"
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Tab: Apply */}
                {activeTab === 'apply' && (
                    <div className="space-y-6">
                        <div className="p-6 rounded-xl bg-white/5 border border-white/10">
                            <h2 className="text-lg font-bold text-white mb-4">Aplicar Correcciones</h2>

                            <div className="space-y-4">
                                <div className="p-4 rounded-lg bg-white/5">
                                    <p className="text-white font-medium mb-2">
                                        Se aplicarán {selectedIssues.size} correcciones:
                                    </p>
                                    <div className="space-y-2">
                                        {Array.from(selectedIssues).slice(0, 5).map(issueId => {
                                            const [seriesId, field] = issueId.split('-');
                                            const issue = filteredIssues.find(i =>
                                                i.series_id === parseInt(seriesId) && i.field === field
                                            );
                                            return issue ? (
                                                <div key={issueId} className="text-sm text-gray-300">
                                                    • {issue.field === 'series_name' ? 'Título' : 'Slug'}:
                                                    "{issue.current_value}" → "{issue.suggested_value}"
                                                </div>
                                            ) : null;
                                        })}
                                        {selectedIssues.size > 5 && (
                                            <div className="text-sm text-gray-400">
                                                ... y {selectedIssues.size - 5} más
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <button
                                    onClick={handleApplyCorrections}
                                    disabled={isUpdating || selectedIssues.size === 0}
                                    className="w-full py-3 px-6 bg-primary text-white rounded-xl font-bold
                                             hover:bg-primary/80 transition-all disabled:opacity-50 disabled:cursor-not-allowed
                                             flex items-center justify-center gap-2"
                                >
                                    {isUpdating ? (
                                        <>
                                            <RefreshCw className="w-5 h-5 animate-spin" />
                                            {currentStep || 'Aplicando...'}
                                        </>
                                    ) : (
                                        <>
                                            <Zap className="w-5 h-5" />
                                            Aplicar {selectedIssues.size} Correcciones
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>

                        {isUpdating && (
                            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                                <div className="flex items-center gap-3">
                                    <RefreshCw className="w-5 h-5 animate-spin text-primary" />
                                    <div className="flex-1">
                                        <p className="text-white font-medium">{currentStep}</p>
                                        <div className="mt-2 h-2 bg-white/10 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-primary transition-all duration-300"
                                                style={{ width: `${progress}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};
