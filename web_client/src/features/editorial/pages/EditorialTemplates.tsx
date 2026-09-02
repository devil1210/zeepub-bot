import React, { useState, useEffect } from 'react';
import {
    FileCode2,
    Plus,
    Trash2,
    Save,
    RotateCcw,
    Sparkles,
    Loader2,
    CheckCircle2,
    AlertCircle,
    LayoutTemplate,
    Send
} from 'lucide-react';
import { api } from '@shared/services/api';
import { TelegramRichMessageEditor } from '../components/TelegramRichMessageEditor';
import { TelegramMessagePreview } from '../components/TelegramMessagePreview';

export const EditorialTemplates: React.FC = () => {
    const [templates, setTemplates] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedTemplate, setSelectedTemplate] = useState<any | null>(null);
    const [formData, setFormData] = useState({
        name: '',
        content: '',
        platform: 'telegram',
        is_default: false,
    });
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    const fetchTemplates = async () => {
        setLoading(true);
        try {
            const res = await api.pubGetTemplates();
            const list = res?.templates || [];
            setTemplates(list);
            if (list.length > 0 && !selectedTemplate) {
                selectTemplate(list[0]);
            }
        } catch (err) {
            console.error('Error cargando plantillas:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTemplates();
    }, []);

    const selectTemplate = (tpl: any) => {
        setSelectedTemplate(tpl);
        setFormData({
            name: tpl.name,
            content: tpl.content,
            platform: tpl.platform || 'telegram',
            is_default: !!tpl.is_default,
        });
        setStatusMsg(null);
    };

    const handleCreateNew = () => {
        setSelectedTemplate({ id: null });
        setFormData({
            name: 'Nueva Plantilla Telegram',
            content:
                '📚 <b>{serie}</b> [?volumen]║ <b>Vol. {volumen}</b>[/?]\n#{slug}\n\n[?autor]✍️ <b>Autor:</b> {autor}\n[/?][?illustrator]🎨 <b>Ilustrador:</b> {illustrator}\n[/?][?traductor]🌐 <b>Traducción:</b> {traductor}\n[/?][?editorial]🏢 <b>Grupo:</b> {editorial}\n[/?]\n[?sinopsis]📝 <b>Sinopsis:</b>\n<blockquote expandable>{sinopsis}</blockquote>\n[/?]\n\n#{slug}',
            platform: 'telegram',
            is_default: false,
        });
        setStatusMsg(null);
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSaving(true);
        setStatusMsg(null);
        try {
            await api.pubSaveTemplate({
                id: selectedTemplate?.id || undefined,
                name: formData.name,
                content: formData.content,
                platform: formData.platform,
                is_default: formData.is_default,
            });
            setStatusMsg({ type: 'success', text: '¡Plantilla guardada correctamente!' });
            await fetchTemplates();
        } catch (err: any) {
            console.error('Error guardando plantilla:', err);
            setStatusMsg({ type: 'error', text: err.message || 'Error al guardar la plantilla' });
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async () => {
        if (!selectedTemplate?.id) return;
        if (!confirm(`¿Eliminar la plantilla "${formData.name}"?`)) return;

        try {
            await api.pubDeleteTemplate(selectedTemplate.id);
            setSelectedTemplate(null);
            fetchTemplates();
            setStatusMsg({ type: 'success', text: 'Plantilla eliminada' });
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error al eliminar' });
        }
    };

    const handleRestoreDefaults = async () => {
        if (!confirm('¿Restaurar las plantillas oficiales predeterminadas de Telegram?')) return;
        try {
            await api.pubRestoreTemplates();
            setStatusMsg({ type: 'success', text: 'Plantillas predeterminadas restauradas' });
            fetchTemplates();
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error al restaurar' });
        }
    };

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Top Bar Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <FileCode2 className="w-7 h-7 text-indigo-400" /> Biblioteca de Plantillas Editorial
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Estructura copys dinámicos enriquecidos para Telegram y publicaciones de Facebook con simulador oficial de canales.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleRestoreDefaults}
                        className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold border border-white/10 flex items-center gap-2 transition-all"
                    >
                        <RotateCcw className="w-4 h-4" /> Restaurar Predeterminadas
                    </button>
                    <button
                        onClick={handleCreateNew}
                        className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/30 active:scale-95 transition-all"
                    >
                        <Plus className="w-4 h-4" /> Nueva Plantilla
                    </button>
                </div>
            </div>

            {statusMsg && (
                <div
                    className={`p-3.5 rounded-2xl flex items-center gap-2.5 text-xs font-medium ${
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

            {/* 3-Column Wide 2K Layout: Templates List + Rich Editor + Channel Simulator */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* 1. Left Column: Templates Sidebar (3 cols on lg, 2 cols on 2K) */}
                <div className="lg:col-span-4 xl:col-span-3 2xl:col-span-3 bg-slate-900/40 border border-white/10 rounded-3xl p-4 sm:p-5 backdrop-blur-xl h-fit space-y-3 shadow-xl">
                    <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider px-2 flex items-center justify-between">
                        <span>Plantillas Guardadas</span>
                        <span className="px-2 py-0.5 rounded-full bg-white/10 text-white font-mono text-[10px]">
                            {templates.length}
                        </span>
                    </div>

                    {loading ? (
                        <div className="py-16 flex justify-center">
                            <Loader2 className="w-7 h-7 text-indigo-500 animate-spin" />
                        </div>
                    ) : (
                        <div className="space-y-2 max-h-[75vh] overflow-y-auto pr-1">
                            {templates.map((tpl) => (
                                <button
                                    key={tpl.id}
                                    onClick={() => selectTemplate(tpl)}
                                    className={`w-full p-3.5 rounded-2xl text-left transition-all border flex items-center justify-between group ${
                                        selectedTemplate?.id === tpl.id
                                            ? 'bg-indigo-600/20 border-indigo-500/50 text-white shadow-xl'
                                            : 'bg-white/[0.02] border-white/5 text-gray-300 hover:bg-white/[0.06]'
                                    }`}
                                >
                                    <div className="min-w-0 pr-2">
                                        <div className="text-xs font-bold truncate group-hover:text-white">
                                            {tpl.name}
                                        </div>
                                        <div className="text-[10px] text-gray-500 uppercase tracking-widest mt-0.5 font-medium">
                                            {tpl.platform} {tpl.is_default ? '• Predeterminada' : ''}
                                        </div>
                                    </div>
                                    <span
                                        className={`text-[9px] px-2 py-0.5 rounded-full font-black uppercase shrink-0 ${
                                            tpl.platform === 'telegram'
                                                ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/20'
                                                : 'bg-blue-500/10 text-blue-300 border border-blue-500/20'
                                        }`}
                                    >
                                        {tpl.platform}
                                    </span>
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* 2. Middle & Right Columns: Editor + Live Simulator (9 cols on lg, 9 cols on 2K) */}
                <div className="lg:col-span-8 xl:col-span-9 2xl:col-span-9">
                    {selectedTemplate ? (
                        <form
                            onSubmit={handleSave}
                            className="bg-slate-900/50 border border-white/10 rounded-3xl p-5 sm:p-7 space-y-6 backdrop-blur-2xl shadow-2xl"
                        >
                            {/* Meta inputs */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1.5">
                                        Nombre de la Plantilla
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="w-full px-4 py-2.5 bg-slate-950/80 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1.5">
                                        Plataforma Objetivo
                                    </label>
                                    <select
                                        value={formData.platform}
                                        onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
                                        className="w-full px-4 py-2.5 bg-slate-950/80 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-bold"
                                    >
                                        <option value="telegram">Telegram (Canal / Grupo con Rich HTML)</option>
                                        <option value="facebook">Facebook (Página Oficial / Copys Limpios)</option>
                                    </select>
                                </div>
                            </div>

                            {/* Split Grid: Editor (Left) & Channel Simulator (Right) */}
                            <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
                                {/* Editor (7 cols) */}
                                <div className="xl:col-span-7 space-y-2">
                                    <label className="text-[11px] font-bold text-gray-400 uppercase flex items-center gap-1.5">
                                        <LayoutTemplate className="w-3.5 h-3.5 text-indigo-400" /> Editor de Copy
                                    </label>

                                    <TelegramRichMessageEditor
                                        value={formData.content}
                                        onChange={(val) => setFormData({ ...formData, content: val })}
                                        platform={formData.platform as 'telegram' | 'facebook'}
                                    />
                                </div>

                                {/* Simulator (5 cols) */}
                                <div className="xl:col-span-5 space-y-2">
                                    <label className="text-[11px] font-bold text-gray-400 uppercase flex items-center gap-1.5">
                                        <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Simulador Oficial de Canal
                                    </label>

                                    <div className="h-[520px] 2xl:h-[580px]">
                                        <TelegramMessagePreview
                                            rawTemplate={formData.content}
                                            platform={formData.platform as 'telegram' | 'facebook'}
                                            isCaptionMode={true}
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Actions Bar */}
                            <div className="pt-4 border-t border-white/10 flex items-center justify-between">
                                {selectedTemplate.id ? (
                                    <button
                                        type="button"
                                        onClick={handleDelete}
                                        className="px-4 py-2.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-bold flex items-center gap-2 transition-all"
                                    >
                                        <Trash2 className="w-4 h-4" /> Eliminar Plantilla
                                    </button>
                                ) : (
                                    <div />
                                )}

                                <button
                                    type="submit"
                                    disabled={isSaving}
                                    className="px-7 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2.5 shadow-xl shadow-indigo-600/30 active:scale-95 transition-all disabled:opacity-50"
                                >
                                    {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                    <span>Guardar y Aplicar Plantilla</span>
                                </button>
                            </div>
                        </form>
                    ) : (
                        <div className="py-32 text-center text-gray-500 text-xs bg-slate-900/30 rounded-3xl border border-white/5">
                            Selecciona una plantilla de la lista o crea una nueva para comenzar a editar.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
