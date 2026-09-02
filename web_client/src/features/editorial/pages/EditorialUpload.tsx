import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    UploadCloud,
    FileText,
    CheckCircle2,
    AlertCircle,
    Loader2,
    X,
    BookOpen,
    Sparkles,
    ArrowLeft,
    Tag,
    HardDrive,
    Info,
    Check
} from 'lucide-react';
import { api } from '@shared/services/api';

export const EditorialUpload: React.FC = () => {
    const navigate = useNavigate();
    const [files, setFiles] = useState<File[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [results, setResults] = useState<any[]>([]);

    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const droppedFiles = Array.from(e.dataTransfer.files).filter((f) => f.name.endsWith('.epub'));
        if (droppedFiles.length > 0) {
            setFiles((prev) => [...prev, ...droppedFiles]);
        }
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const selectedFiles = Array.from(e.target.files).filter((f) => f.name.endsWith('.epub'));
            setFiles((prev) => [...prev, ...selectedFiles]);
        }
    };

    const handleRemoveFile = (idx: number) => {
        setFiles((prev) => prev.filter((_, i) => i !== idx));
    };

    const handleUploadAll = async () => {
        if (files.length === 0) return;
        setUploading(true);
        setProgress(0);
        setStatusMsg(null);
        const uploadResults: any[] = [];

        try {
            for (let i = 0; i < files.length; i++) {
                const f = files[i];
                try {
                    const res = await api.uploadEpub(f);
                    uploadResults.push({ file: f.name, success: true, res });
                } catch (err: any) {
                    uploadResults.push({ file: f.name, success: false, error: err.message });
                }
                setProgress(Math.round(((i + 1) / files.length) * 100));
            }

            setResults(uploadResults);
            const successful = uploadResults.filter((r) => r.success).length;
            setStatusMsg({
                type: 'success',
                text: `¡${successful} de ${files.length} archivos subidos y analizados exitosamente!`,
            });
            setFiles([]);
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error durante la subida' });
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <UploadCloud className="w-7 h-7 text-indigo-400" /> Ingesta y Carga de Archivos EPUB
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Sube nuevos tomos o lotes completos con extracción automática de metadatos y prevención de duplicados.
                    </p>
                </div>

                <button
                    onClick={() => navigate('/app-v2/volumes')}
                    className="px-4 py-2 rounded-2xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold flex items-center gap-2 border border-white/5 transition-all self-start sm:self-auto"
                >
                    <ArrowLeft className="w-4 h-4" /> Ir a Matriz de Volúmenes
                </button>
            </div>

            {statusMsg && (
                <div
                    className={`p-4 rounded-2xl flex items-center gap-2.5 text-xs font-medium ${
                        statusMsg.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : 'bg-red-500/10 text-red-300 border border-red-500/20'
                    }`}
                >
                    {statusMsg.type === 'success' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                        <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                    )}
                    <span>{statusMsg.text}</span>
                </div>
            )}

            {/* Drag & Drop Zone (2K Widescreen) */}
            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`relative rounded-3xl border-2 border-dashed p-10 sm:p-16 text-center cursor-pointer transition-all shadow-2xl backdrop-blur-2xl flex flex-col items-center justify-center space-y-4 ${
                    isDragging
                        ? 'border-indigo-500 bg-indigo-500/10 scale-[1.01]'
                        : 'border-white/10 hover:border-indigo-500/40 bg-slate-900/40 hover:bg-slate-900/60'
                }`}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".epub"
                    onChange={handleFileSelect}
                    className="hidden"
                />

                <div className="w-16 h-16 rounded-3xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center shadow-lg shadow-indigo-600/20 group-hover:scale-110 transition-transform">
                    <UploadCloud className="w-8 h-8 animate-pulse" />
                </div>

                <div>
                    <h3 className="text-base sm:text-lg font-bold text-white">
                        Arrastra tus archivos EPUB aquí o haz clic para explorar
                    </h3>
                    <p className="text-xs text-gray-400 mt-1">
                        Compatible con EPUB 3.0+ y subida masiva por lotes
                    </p>
                </div>

                <div className="flex items-center gap-2 pt-2">
                    <span className="px-3 py-1 rounded-full text-[10px] font-black uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        EPUB 3.0+
                    </span>
                    <span className="px-3 py-1 rounded-full text-[10px] font-black uppercase bg-white/5 text-gray-400 border border-white/10">
                        Soporte Masivo
                    </span>
                </div>
            </div>

            {/* Selected Files Queue */}
            {files.length > 0 && (
                <div className="bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-4 shadow-xl backdrop-blur-xl">
                    <div className="flex items-center justify-between">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <BookOpen className="w-4 h-4 text-indigo-400" />
                            Archivos Listos para Subir ({files.length})
                        </h3>

                        <button
                            onClick={handleUploadAll}
                            disabled={uploading}
                            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/30 active:scale-95 transition-all disabled:opacity-50"
                        >
                            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
                            <span>Iniciar Ingesta de Metadatos</span>
                        </button>
                    </div>

                    {uploading && (
                        <div className="space-y-1.5 pt-2">
                            <div className="flex justify-between text-xs text-gray-400 font-mono">
                                <span>Procesando archivos...</span>
                                <span>{progress}%</span>
                            </div>
                            <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden">
                                <div
                                    className="h-full bg-indigo-600 transition-all duration-300 rounded-full"
                                    style={{ width: `${progress}%` }}
                                />
                            </div>
                        </div>
                    )}

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-60 overflow-y-auto pr-1">
                        {files.map((f, i) => (
                            <div
                                key={i}
                                className="p-3 rounded-2xl bg-black/40 border border-white/5 flex items-center justify-between gap-3 text-xs"
                            >
                                <div className="flex items-center gap-2.5 min-w-0">
                                    <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                                    <span className="text-white truncate font-medium">{f.name}</span>
                                </div>
                                <button
                                    onClick={() => handleRemoveFile(i)}
                                    className="p-1 text-gray-500 hover:text-red-400 rounded-lg"
                                >
                                    <X className="w-3.5 h-3.5" />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Ingestion Info Banner */}
            <div className="p-5 rounded-3xl bg-slate-900/40 border border-white/10 flex items-start gap-4 backdrop-blur-xl">
                <div className="p-3 rounded-2xl bg-indigo-500/10 text-indigo-400 shrink-0">
                    <Info className="w-5 h-5" />
                </div>
                <div className="text-xs text-gray-400 space-y-1">
                    <div className="font-bold text-white">Protocolo de Normalización Automática</div>
                    <p className="leading-relaxed">
                        Los archivos subidos se verifican automáticamente contra la base de datos para evitar duplicados por hash. Si detectamos un conflicto o falta de metadatos, Gemini extraerá la portada, serie y sinopsis automáticamente.
                    </p>
                </div>
            </div>
        </div>
    );
};
