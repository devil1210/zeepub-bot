import React, { useState, useRef } from 'react';
import {
    ArrowLeft,
    Upload,
    FileText,
    CheckCircle2,
    AlertCircle,
    Loader2,
    X,
    Info,
    BookOpen,
    Tag,
    Globe,
    Hash,
    Calendar,
    Building,
    Edit3,
    Check
} from 'lucide-react';
import { api } from '@shared/services/api';
import { useTheme } from '@shared/contexts/ThemeContext';

interface UploadProps {
    onNavigate?: (tab: string) => void;
}

interface UploadMetadata {
    title: string;
    author: string;
    series?: string;
    volume?: string;
    publisher?: string;
    publish_date?: string;
    language?: string;
    isbn?: string;
    tags?: string;
    suggested_path: string;
    book_hash?: string;
    file_exists?: boolean;
    identity_match?: any;
    path_match?: any;
}

export const UploadEpub: React.FC<UploadProps> = ({ onNavigate }) => {
    const { settings } = useTheme();
    const [file, setFile] = useState<File | null>(null);
    const [uploadId, setUploadId] = useState<string | null>(null);
    const [metadata, setMetadata] = useState<UploadMetadata | null>(null);
    const [status, setStatus] = useState<'idle' | 'uploading' | 'analyzing' | 'reviewing' | 'confirming' | 'success' | 'error'>('idle');
    const [uploadProgress, setUploadProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [editingPath, setEditingPath] = useState(false);
    const [customPath, setCustomPath] = useState('');
    const [bulkResults, setBulkResults] = useState<{
        filename: string;
        success: boolean;
        upload_id?: string;
        metadata?: UploadMetadata;
        error?: string;
    }[]>([]);
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [isBulk, setIsBulk] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const [discardedCount, setDiscardedCount] = useState(0);
    const [pendingFilesCount, setPendingFilesCount] = useState(0);
    const [currentFilesIndex, setCurrentFilesIndex] = useState(0);
    const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);

    const fileInputRef = useRef<HTMLInputElement>(null);

    const toggleSelection = (id: string) => {
        const newSelected = new Set(selectedIds);
        if (newSelected.has(id)) {
            newSelected.delete(id);
        } else {
            newSelected.add(id);
        }
        setSelectedIds(newSelected);
    };

    const toggleAll = () => {
        const allSuccessIds = bulkResults.filter(r => r.success && r.upload_id).map(r => r.upload_id as string);
        if (selectedIds.size === allSuccessIds.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(allSuccessIds));
        }
    };

    const processFiles = (files: File[]) => {
        if (files.length === 0) return;

        if (files.length === 1) {
            const selectedFile = files[0];
            if (!selectedFile.name.toLowerCase().endsWith('.epub')) {
                setError('Solo se admiten archivos EPUB (.epub)');
                return;
            }
            setFile(selectedFile);
            setPendingFilesCount(1);
            setIsBulk(false);
            setError(null);
            startUpload(selectedFile);
        } else {
            // Bulk mode
            const validFiles = files.filter(f => f.name.toLowerCase().endsWith('.epub'));
            if (validFiles.length === 0) {
                setError('Ninguno de los archivos seleccionados es un EPUB válido');
                return;
            }
            setPendingFilesCount(validFiles.length);
            setIsBulk(true);
            setError(null);
            startBulkUpload(validFiles);
        }
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || []) as File[];
        processFiles(files);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = Array.from(e.dataTransfer.files) as File[];
        processFiles(files);
    };

    const startUpload = async (fileToUpload: File) => {
        setStatus('uploading');
        setUploadProgress(0);

        try {
            const res = await api.uploadEpub(fileToUpload, (progress) => {
                setUploadProgress(progress);
                if (progress === 100) setStatus('analyzing');
            });

            if (res.success) {
                setUploadId(res.upload_id);
                setMetadata(res.metadata);
                setCustomPath(res.metadata.suggested_path);
                setStatus('reviewing');
            } else {
                setError(res.error || 'Error al procesar el archivo');
                setStatus('error');
            }
        } catch (err: any) {
            console.error('Upload error:', err);
            setError(err.message || 'Error en la conexión con el servidor');
            setStatus('error');
        }
    };

    const startBulkUpload = async (files: File[]) => {
        setStatus('uploading');
        setUploadProgress(0);
        setCurrentFilesIndex(0);
        setBulkResults([]);
        setUploadingFiles(files);

        const results: any[] = [];
        let completed = 0;

        for (let i = 0; i < files.length; i++) {
            const f = files[i];
            setCurrentFilesIndex(i + 1);
            setUploadProgress(0);

            try {
                const res = await api.uploadEpub(f, (progress) => {
                    setUploadProgress(progress);
                });

                if (res.success) {
                    results.push({
                        filename: f.name,
                        success: true,
                        upload_id: res.upload_id,
                        metadata: res.metadata
                    });
                } else {
                    results.push({
                        filename: f.name,
                        success: false,
                        error: res.error || 'Error de análisis'
                    });
                }
            } catch (err: any) {
                console.error(`Error uploading ${f.name}:`, err);
                results.push({
                    filename: f.name,
                    success: false,
                    error: err.message || 'Error de conexión'
                });
            }

            completed++;
            // Actualizar vista previa parcial para dar feedback
            setBulkResults([...results]);
        }

        if (results.length > 0) {
            // Pre-seleccionar automáticamente lo que no es duplicado
            const preSelected = new Set<string>();
            results.forEach(r => {
                if (r.success && r.upload_id && !r.metadata?.identity_match) {
                    preSelected.add(r.upload_id);
                }
            });
            setSelectedIds(preSelected);
            setStatus('reviewing');
        } else {
            setError('No se pudo procesar ningún archivo');
            setStatus('error');
        }
    };

    const handleConfirm = async () => {
        if (isBulk) {
            handleBulkConfirm();
            return;
        }

        if (!uploadId) return;

        // Si hay conflicto de archivo y NO es match de identidad, es sobrescritura
        if (metadata?.file_exists && !metadata?.identity_match) {
            if (!window.confirm("Ya existe un archivo con este nombre pero diferente contenido. ¿Deseas sobrescribirlo?")) {
                return;
            }
        }

        setStatus('confirming');
        try {
            const res = await api.confirmEpubUpload({
                upload_id: uploadId,
                path: customPath
            });

            if (res.data?.success) {
                setStatus('success');
            } else {
                setError(res.data?.error || 'Error al confirmar la subida');
                setStatus('error');
            }
        } catch (err: any) {
            console.error('Confirm error:', err);
            setError(err.message || 'Error al confirmar la subida');
            setStatus('error');
        }
    };

    const handleBulkConfirm = async () => {
        const allIds: string[] = bulkResults
            .filter(r => r.success && r.upload_id)
            .map(r => r.upload_id as string);

        const selectedList: string[] = Array.from(selectedIds);
        const discardedList: string[] = allIds.filter(id => !selectedIds.has(id));

        if (selectedList.length === 0 && discardedList.length === 0) return;

        setStatus('confirming');
        try {
            const res = await api.confirmEpubUploadBulk({
                selected_ids: selectedList,
                discarded_ids: discardedList
            });

            if (res.data?.success) {
                // Actualizar resultados para mostrar solo los procesados exitosamente en la pantalla final
                // Opcional: filtrar bulkResults para mostrar lo que pasó
                setDiscardedCount(discardedList.length);
                setStatus('success');
            } else {
                setError(res.data?.error || 'Error al confirmar la subida masiva');
                setStatus('error');
            }
        } catch (err: any) {
            console.error('Bulk confirm error:', err);
            setError(err.message || 'Error al confirmar la subida masiva');
            setStatus('error');
        }
    };

    const resetUpload = () => {
        setFile(null);
        setUploadId(null);
        setMetadata(null);
        setBulkResults([]);
        setIsBulk(false);
        setStatus('idle');
        setUploadProgress(0);
        setError(null);
        setEditingPath(false);
        setCustomPath('');
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const glassStyle = {
        background: `rgba(var(--glass-rgb), ${settings.glassOpacity})`,
        backdropFilter: `blur(${settings.glassBlur}px)`,
        WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
    };

    return (
        <div className="max-w-[1700px] mx-auto p-4 md:p-8 animate-in fade-in slide-in-from-bottom-4 duration-500 font-sans text-gray-100 pb-32">
            <header className="flex items-center gap-4 mb-8">
                <button
                    onClick={() => onNavigate && onNavigate('dashboard')}
                    className="p-2 -ml-2 rounded-full hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                >
                    <ArrowLeft className="w-6 h-6" />
                </button>
                <div>
                    <h1 className="text-3xl font-black text-white tracking-tight uppercase">Subir EPUB</h1>
                    <p className="text-gray-500 text-[11px] font-bold uppercase tracking-[0.2em] mt-1">
                        Contribuye a la biblioteca con nuevo contenido
                    </p>
                </div>
            </header>

            <div className="space-y-6">
                {status === 'idle' && (
                    <div
                        onClick={() => fileInputRef.current?.click()}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        className={`glass-panel group rounded-[2.5rem] p-12 border-2 border-dashed transition-all duration-500 cursor-pointer flex flex-col items-center justify-center gap-8 relative overflow-hidden
                            ${isDragging ? 'border-primary bg-primary/5 scale-[1.02] shadow-2xl shadow-primary/20' : 'border-white/10 hover:border-primary/50'}
                        `}
                        style={glassStyle}
                    >
                        {/* Decorative Gradient Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>

                        <div className="relative">
                            <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform duration-500 relative z-10">
                                <Upload className="w-10 h-10" />
                            </div>
                            {/* Animated Pulse Ring */}
                            <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping opacity-20"></div>
                        </div>

                        <div className="text-center relative z-10">
                            <h2 className="text-2xl font-black text-white mb-3">Selecciona archivos EPUB</h2>
                            <p className="text-gray-400 max-w-sm mx-auto text-sm leading-relaxed">
                                Arrastra tus archivos aquí o haz clic para explorar. Puedes seleccionar varios archivos a la vez.
                            </p>
                        </div>

                        <input
                            type="file"
                            multiple
                            ref={fileInputRef}
                            onChange={handleFileSelect}
                            accept=".epub"
                            className="hidden"
                        />

                        <div className="flex gap-4 relative z-10">
                            <span className="px-4 py-2 rounded-full bg-white/5 border border-white/5 text-[10px] font-black uppercase tracking-widest text-gray-400">EPUB 3.0+</span>
                            <span className="px-4 py-2 rounded-full bg-white/5 border border-white/5 text-[10px] font-black uppercase tracking-widest text-gray-400">Soporte Masivo</span>
                        </div>
                    </div>
                )}

                {(status === 'uploading' || status === 'analyzing') && (
                    <div className="glass-panel rounded-[2.5rem] p-16 text-center border border-white/5 flex flex-col items-center justify-center gap-12 relative overflow-hidden" style={glassStyle}>
                        {/* Progressive Background Glow */}
                        <div
                            className="absolute -top-24 -left-24 w-64 h-64 bg-primary/20 blur-[100px] transition-all duration-1000"
                            style={{ opacity: (status === 'uploading' ? uploadProgress : 100) / 100 }}
                        ></div>

                        <div className="relative group">
                            {/* Outer Glow Ring */}
                            <div className="absolute inset-[-12px] bg-primary/10 rounded-full blur-xl animate-pulse"></div>

                            <svg className="w-40 h-40 transform -rotate-90 relative z-10" viewBox="0 0 140 140">
                                {/* Track */}
                                <circle
                                    cx="70"
                                    cy="70"
                                    r="62"
                                    stroke="currentColor"
                                    strokeWidth="8"
                                    fill="transparent"
                                    className="text-white/[0.03]"
                                />
                                {/* Progress with Glow */}
                                <circle
                                    cx="70"
                                    cy="70"
                                    r="62"
                                    stroke="currentColor"
                                    strokeWidth="8"
                                    fill="transparent"
                                    strokeLinecap="round"
                                    strokeDasharray={389.5} // 2 * PI * 62
                                    strokeDashoffset={389.5 - (389.5 * (status === 'uploading' ? uploadProgress : 100)) / 100}
                                    className="text-primary transition-all duration-500 ease-out shadow-[0_0_15px_rgba(var(--color-primary-rgb),0.5)]"
                                    style={{
                                        filter: 'drop-shadow(0 0 8px rgba(var(--color-primary-rgb), 0.6))'
                                    }}
                                />
                            </svg>

                            <div className="absolute inset-0 flex flex-col items-center justify-center z-20">
                                {status === 'uploading' ? (
                                    <>
                                        <span className="text-3xl font-black text-white leading-none">{uploadProgress}%</span>
                                        <span className="text-[10px] font-black text-primary uppercase tracking-[0.2em] mt-1">Subiendo</span>
                                    </>
                                ) : (
                                    <div className="flex flex-col items-center">
                                        <Loader2 className="w-12 h-12 text-primary animate-spin" />
                                        <span className="text-[10px] font-black text-primary uppercase tracking-[0.2em] mt-2">Analizando</span>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="relative z-10">
                            <h2 className="text-3xl font-black text-white mb-4 tracking-tight">
                                {status === 'uploading' ? 'Transfiriendo archivos...' : 'Procesando Inteligencia...'}
                            </h2>
                            <div className="flex flex-col items-center gap-2">
                                <div className="px-6 py-2 rounded-full bg-white/5 border border-white/5 backdrop-blur-md">
                                    <p className="text-gray-300 text-xs font-bold uppercase tracking-wider">
                                        {isBulk ? `Archivo ${currentFilesIndex} de ${pendingFilesCount}` : file?.name}
                                    </p>
                                </div>
                                {isBulk && (
                                    <p className="text-primary/70 text-[10px] font-black uppercase tracking-widest mt-1">
                                        {uploadingFiles[currentFilesIndex - 1]?.name}
                                    </p>
                                )}
                                <p className="text-gray-500 text-[10px] font-medium uppercase tracking-[0.1em] h-4">
                                    {status === 'analyzing' && 'Extrayendo metadatos y normalizando series...'}
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {(status === 'reviewing' || status === 'confirming') && (isBulk ? bulkResults : metadata) && (
                    <div className="space-y-6">
                        {isBulk ? (
                            <div className="space-y-4">
                                <div className="flex items-center justify-between mb-4 bg-white/5 p-3 rounded-premium-sm border border-white/5">
                                    <div className="flex items-center gap-3">
                                        <input
                                            type="checkbox"
                                            checked={bulkResults.filter(r => r.success).length > 0 && selectedIds.size === bulkResults.filter(r => r.success).length}
                                            onChange={toggleAll}
                                            className="w-4 h-4 rounded border-gray-500 bg-black/50 text-primary focus:ring-primary focus:ring-offset-0 cursor-pointer"
                                        />
                                        <span className="text-xs font-bold text-gray-300 uppercase tracking-widest">
                                            {selectedIds.size} Seleccionados
                                        </span>
                                    </div>
                                    <span className="px-3 py-1 rounded-full bg-primary/10 text-primary text-[10px] font-black uppercase">
                                        {bulkResults.filter(r => r.success).length} Listos / {bulkResults.length} Total
                                    </span>
                                </div>

                                <div className="grid grid-cols-1 gap-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                                    {bulkResults.map((res, i) => {
                                        const isDuplicate = res.metadata?.identity_match;
                                        const isSuccess = res.success;
                                        const isSelected = res.upload_id ? selectedIds.has(res.upload_id) : false;

                                        return (
                                            <div
                                                key={i}
                                                onClick={() => isSuccess && res.upload_id && toggleSelection(res.upload_id)}
                                                className={`p-4 rounded-premium-sm border flex items-center gap-4 transition-all cursor-pointer relative overflow-hidden group
                                                    ${!isSuccess ? 'bg-red-500/5 border-red-500/20 opacity-80' :
                                                        isDuplicate ? (isSelected ? 'bg-amber-500/10 border-amber-500/40' : 'bg-amber-500/5 border-amber-500/20') :
                                                            (isSelected ? 'bg-primary/10 border-primary/40' : 'bg-white/5 border-white/5 hover:border-white/10')
                                                    }
                                                `}
                                            >
                                                {/* Selection Checkbox */}
                                                {isSuccess && (
                                                    <div className={`
                                                        w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all flex-shrink-0
                                                        ${isSelected
                                                            ? (isDuplicate ? 'bg-amber-500 border-amber-500 text-black' : 'bg-primary border-primary text-white')
                                                            : 'border-gray-600 bg-black/20 group-hover:border-gray-400'}
                                                    `}>
                                                        {isSelected && <Check className="w-3 h-3 stroke-[4]" />}
                                                    </div>
                                                )}

                                                <div className={`p-2.5 rounded-premium-sm flex-shrink-0 ${!isSuccess ? 'bg-red-500/10 text-red-400' :
                                                    isDuplicate ? 'bg-amber-500/20 text-amber-500' :
                                                        'bg-blue-500/10 text-blue-400'
                                                    }`}>
                                                    {!isSuccess ? <AlertCircle className="w-5 h-5" /> :
                                                        isDuplicate ? <AlertCircle className="w-5 h-5" /> :
                                                            <FileText className="w-5 h-5" />}
                                                </div>

                                                <div className="flex-1 min-w-0 z-10">
                                                    <div className="flex items-center gap-2 mb-0.5">
                                                        <p className={`text-xs font-bold truncate ${isDuplicate ? 'text-amber-200' : 'text-gray-200'}`}>
                                                            {res.filename}
                                                        </p>
                                                        {isDuplicate && (
                                                            <span className="px-2 py-0.5 rounded bg-amber-500 text-black text-[9px] font-black uppercase tracking-wider animate-pulse">
                                                                Duplicado Exacto
                                                            </span>
                                                        )}
                                                        {res.metadata?.file_exists && !isDuplicate && (
                                                            <span className="px-2 py-0.5 rounded bg-purple-500 text-white text-[9px] font-black uppercase tracking-wider">
                                                                Sobrescribir
                                                            </span>
                                                        )}
                                                    </div>

                                                    {isSuccess ? (
                                                        <div className="flex flex-col gap-0.5">
                                                            <p className="text-[11px] text-gray-400 font-medium truncate">{res.metadata?.title || 'Metadatos extraídos'}</p>
                                                            <p className="text-[9px] text-gray-600 font-mono truncate">
                                                                {res.metadata?.suggested_path}
                                                            </p>
                                                        </div>
                                                    ) : (
                                                        <p className="text-[10px] text-red-400 mt-0.5 font-medium">{res.error || 'Error desconocido'}</p>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>

                                {selectedIds.size < bulkResults.filter(r => r.success).length && (
                                    <div className="p-3 rounded-premium-sm bg-white/5 border border-white/5 text-center">
                                        <p className="text-[11px] text-gray-400">
                                            Se descartarán <strong className="text-white">{bulkResults.filter(r => r.success).length - selectedIds.size}</strong> libros no seleccionados.
                                        </p>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <>
                                {/* Conflict Warnings */}
                                {(metadata!.identity_match || metadata!.file_exists) && (
                                    <div className={`p-4 rounded-premium-sm border flex items-start gap-4 ${metadata!.identity_match
                                        ? 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                                        : 'bg-red-500/10 border-red-500/20 text-red-400'
                                        }`}>
                                        <AlertCircle className="w-6 h-6 flex-shrink-0" />
                                        <div>
                                            <h4 className="font-bold text-sm uppercase tracking-tight">
                                                {metadata!.identity_match ? 'Duplicado Detectado' : 'Conflicto de Ruta'}
                                            </h4>
                                            <p className="text-xs opacity-80 mt-1 leading-relaxed">
                                                {metadata!.identity_match
                                                    ? 'Este libro ya existe en la biblioteca. Si continúas, se reemplazará la versión actual.'
                                                    : 'Ya existe un archivo diferente en esta ubicación. Si continúas, será sobrescrito.'}
                                            </p>
                                        </div>
                                    </div>
                                )}

                                {/* Metadata Review Card */}
                                <div className="glass-panel rounded-[2.5rem] overflow-hidden border border-white/5" style={glassStyle}>
                                    <div className="p-8 border-b border-white/5 bg-white/[0.02]">
                                        <h3 className="text-xs font-black text-gray-500 uppercase tracking-widest mb-4">Revisión de Metadatos</h3>
                                        <div className="flex flex-col md:flex-row gap-6 md:items-center">
                                            <div className="w-20 h-28 bg-white/5 rounded-premium-sm border border-white/10 flex items-center justify-center text-gray-600 shadow-inner">
                                                <BookOpen className="w-8 h-8" />
                                            </div>
                                            <div className="flex-1">
                                                <h2 className="text-2xl font-black text-white leading-tight mb-1">{metadata!.title}</h2>
                                                <p className="text-primary font-bold text-sm tracking-tight">{metadata!.author}</p>
                                                <div className="flex flex-wrap gap-2 mt-4">
                                                    {metadata!.series && (
                                                        <span className="px-2.5 py-1 rounded-lg bg-white/5 text-[10px] font-black uppercase text-gray-400 border border-white/10">
                                                            Serie: {metadata!.series} {metadata!.volume ? `v${metadata!.volume}` : ''}
                                                        </span>
                                                    )}
                                                    {metadata!.language && (
                                                        <span className="px-2.5 py-1 rounded-lg bg-white/5 text-[10px] font-black uppercase text-gray-400 border border-white/10 flex items-center gap-1.5">
                                                            <Globe className="w-3 h-3" /> {metadata!.language.toUpperCase()}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-8">
                                        <div className="space-y-6">
                                            <div className="flex items-start gap-4">
                                                <div className="p-2 rounded-lg bg-white/5 text-gray-500">
                                                    <Building className="w-4 h-4" />
                                                </div>
                                                <div>
                                                    <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-1">Editorial</p>
                                                    <p className="text-sm text-gray-300 font-bold">{metadata!.publisher || 'N/A'}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-start gap-4">
                                                <div className="p-2 rounded-lg bg-white/5 text-gray-500">
                                                    <Calendar className="w-4 h-4" />
                                                </div>
                                                <div>
                                                    <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-1">Fecha de Publicación</p>
                                                    <p className="text-sm text-gray-300 font-bold">{metadata!.publish_date || 'N/A'}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-start gap-4">
                                                <div className="p-2 rounded-lg bg-white/5 text-gray-500">
                                                    <Hash className="w-4 h-4" />
                                                </div>
                                                <div>
                                                    <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-1">ISBN / ID</p>
                                                    <p className="text-xs text-gray-400 font-mono">{metadata!.isbn || 'N/A'}</p>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="space-y-6">
                                            <div className="flex items-start gap-4">
                                                <div className="p-2 rounded-lg bg-white/5 text-gray-500">
                                                    <Tag className="w-4 h-4" />
                                                </div>
                                                <div>
                                                    <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-1">Géneros / Tags</p>
                                                    <div className="flex flex-wrap gap-1.5 mt-1">
                                                        {metadata!.tags?.split(',').map((tag, i) => (
                                                            <span key={i} className="text-[10px] text-primary/70 font-bold">{tag.trim()}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="pt-4 border-t border-white/5">
                                                <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-2">Ruta de Destino</p>
                                                <div className="flex items-center gap-3 p-3 bg-black/40 border border-white/10 rounded-premium-sm group/path">
                                                    {editingPath ? (
                                                        <input
                                                            autoFocus
                                                            type="text"
                                                            value={customPath}
                                                            onChange={(e) => setCustomPath(e.target.value)}
                                                            onBlur={() => setEditingPath(false)}
                                                            className="flex-1 bg-transparent text-xs text-white outline-none font-mono"
                                                        />
                                                    ) : (
                                                        <p className="flex-1 text-[11px] text-primary font-mono truncate">{customPath}</p>
                                                    )}
                                                    <button
                                                        onClick={() => setEditingPath(!editingPath)}
                                                        className="p-1.5 rounded-lg hover:bg-white/10 text-gray-500 hover:text-white transition-all"
                                                    >
                                                        {editingPath ? <Check className="w-4 h-4" /> : <Edit3 className="w-4 h-4" />}
                                                    </button>
                                                </div>
                                                <p className="mt-2 text-[9px] text-gray-600 italic">Puedes editar la ruta si el formato no es correcto.</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </>
                        )}

                        {/* Action Buttons */}
                        <div className="flex gap-4">
                            <button
                                onClick={resetUpload}
                                className="flex-1 py-4 rounded-[1.5rem] bg-white/5 hover:bg-white/10 text-white text-xs font-black uppercase tracking-widest transition-all border border-white/5 flex items-center justify-center gap-2"
                            >
                                <X className="w-4 h-4" />
                                Cancelar
                            </button>
                            <button
                                onClick={handleConfirm}
                                disabled={status === 'confirming' || (isBulk && selectedIds.size === 0)}
                                className="flex-[2] py-4 rounded-[1.5rem] bg-primary hover:bg-primary-dark text-white text-xs font-black uppercase tracking-widest transition-all shadow-xl shadow-primary/20 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {status === 'confirming' ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                                {isBulk ? `Confirmar ${selectedIds.size} libros` : 'Finalizar y Guardar'}
                            </button>
                        </div>
                    </div>
                )}

                {status === 'success' && (
                    <div className="glass-panel rounded-[2.5rem] p-16 text-center border border-green-500/20 bg-green-500/5 flex flex-col items-center justify-center gap-10" style={glassStyle}>
                        <div className="relative">
                            <div className="w-24 h-24 rounded-full bg-green-500/20 flex items-center justify-center text-green-400 relative z-10">
                                <CheckCircle2 className="w-12 h-12" />
                            </div>
                            <div className="absolute inset-0 bg-green-500/20 rounded-full animate-ping opacity-20"></div>
                        </div>

                        <div className="max-w-xs mx-auto">
                            <h2 className="text-3xl font-black text-white mb-4">¡Subida Completada!</h2>
                            <p className="text-gray-400 text-sm leading-relaxed mb-8">
                                {isBulk
                                    ? `Se han procesado ${bulkResults.filter(r => r.success).length} libros exitosamente. Ya están disponibles en la biblioteca.`
                                    : 'El libro ha sido agregado a la biblioteca. Ya está disponible en el catálogo.'}
                            </p>
                        </div>

                        <button
                            onClick={resetUpload}
                            className="px-10 py-4 bg-primary hover:bg-primary-dark text-white rounded-premium-sm text-xs font-black uppercase tracking-widest transition-all shadow-xl shadow-primary/20"
                        >
                            Subir más libros
                        </button>
                    </div>
                )}

                {status === 'error' && (
                    <div className="glass-panel rounded-[2.5rem] p-16 text-center border border-red-500/20 bg-red-500/5 flex flex-col items-center justify-center gap-10" style={glassStyle}>
                        <div className="w-24 h-24 rounded-full bg-red-500/20 flex items-center justify-center text-red-500">
                            <AlertCircle className="w-12 h-12" />
                        </div>

                        <div className="max-w-sm mx-auto">
                            <h2 className="text-3xl font-black text-white mb-4">Oops, algo salió mal</h2>
                            <p className="text-red-400/80 text-sm font-medium leading-relaxed">
                                {error || 'Ocurrió un error inesperado al procesar el archivo.'}
                            </p>
                        </div>

                        <div className="flex gap-4">
                            <button
                                onClick={resetUpload}
                                className="px-8 py-3 bg-white/5 hover:bg-white/10 text-white rounded-premium-sm text-xs font-black uppercase tracking-widest transition-all"
                            >
                                Reintentar
                            </button>
                            <button
                                onClick={() => onNavigate && onNavigate('dashboard')}
                                className="px-8 py-3 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-premium-sm text-xs font-black uppercase tracking-widest transition-all"
                            >
                                Volver
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Hint Footer */}
            <footer className="mt-12 p-6 glass-panel rounded-[2rem] border border-white/5 flex gap-4 items-center" style={glassStyle}>
                <div className="p-3 rounded-premium-sm bg-primary/10 text-primary">
                    <Info className="w-5 h-5" />
                </div>
                <p className="text-[11px] text-gray-500 leading-relaxed font-bold uppercase tracking-tight">
                    Tip: Los archivos subidos se verifican automáticamente contra la base de datos para evitar duplicados. Si detectamos un conflicto, te pediremos confirmación antes de sobrescribir.
                </p>
            </footer>
        </div>
    );
};
