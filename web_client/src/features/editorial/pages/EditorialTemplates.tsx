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
            name: 'Nueva Plantilla',
            content: '📚 <b>{serie}</b> [?volumen]║ <b>Vol. {volumen}</b>[/?]\n#{slug}\n\n[?autor]✍️ <b>Autor:</b> {autor}\n[/?][?illustrator]🎨 <b>Ilustrador:</b> {illustrator}\n[/?][?traductor]🌐 <b>Traducción:</b> {traductor}\n[/?][?editorial]🏢 <b>Grupo:</b> {editorial}\n[/?]\n[?sinopsis]📝 <b>Sinopsis:</b>\n<blockquote expandable>{sinopsis}</blockquote>\n[/?]\n\n#{slug}',
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
        <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
                        <FileCode2 className="w-6 h-6 text-indigo-400" /> Biblioteca de Plantillas Editorial
                    </h2>
                    <p className="text-xs text-gray-400 mt-1">
                        Estructura copys dinámicos enriquecidos para Telegram y publicaciones de Facebook con simulador en tiempo real.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleRestoreDefaults}
                        className="px-3.5 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold border border-white/10 flex items-center gap-1.5 transition-all"
                    >
                        <RotateCcw className="w-3.5 h-3.5" /> Restaurar Predeterminadas
                    </button>
                    <button
                        onClick={handleCreateNew}
                        className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-indigo-600/20 active:scale-95 transition-all"
                    >
                        <Plus className="w-4 h-4" /> Nueva Plantilla
                    </button>
                </div>
            </div>

            {statusMsg && (
                <div
                    className={`p-3 rounded-xl flex items-center gap-2 text-xs font-medium ${
                        statusMsg.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : 'bg-red-500/10 text-red-300 border border-red-500/20'
                    }`}
                >
                    {statusMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    <span>{statusMsg.text}</span>
                </div>
            )}

            {/* Main Layout Grid: Sidebar List + Editor Workspace */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left: Template Selector Sidebar */}
                <div className="lg:col-span-4 bg-slate-900/40 border border-white/10 rounded-2xl p-4 backdrop-blur-xl h-fit space-y-3">
                    <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider px-2">
                        Plantillas Disponibles ({templates.length})
                    </div>

                    {loading ? (
                        <div className="py-12 flex justify-center">
                            <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {templates.map((tpl) => (
                                <button
                                    key={tpl.id}
                                    onClick={() => selectTemplate(tpl)}
                                    className={`w-full p-3 rounded-xl text-left transition-all border flex items-center justify-between group ${
                                        selectedTemplate?.id === tpl.id
                                            ? 'bg-indigo-600/20 border-indigo-500/40 text-white shadow-lg'
                                            : 'bg-white/[0.02] border-white/5 text-gray-300 hover:bg-white/[0.06]'
                                    }`}
                                >
                                    <div className="min-w-0 pr-2">
                                        <div className="text-xs font-bold truncate group-hover:text-white">
                                            {tpl.name}
                                        </div>
                                        <div className="text-[10px] text-gray-500 uppercase tracking-widest mt-0.5">
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

                {/* Right: Rich Editor & Live Telegram Simulator */}
                <div className="lg:col-span-8">
                    {selectedTemplate ? (
                        <form
                            onSubmit={handleSave}
                            className="bg-slate-900/50 border border-white/10 rounded-2xl p-5 sm:p-6 space-y-6 backdrop-blur-xl shadow-2xl"
                        >
                            {/* Template Meta Inputs */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                        Nombre de la Plantilla
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="w-full px-3.5 py-2.5 bg-slate-950/80 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                        Plataforma Objetivo
                                    </label>
                                    <select
                                        value={formData.platform}
                                        onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
                                        className="w-full px-3.5 py-2.5 bg-slate-950/80 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    >
                                        <option value="telegram">Telegram (Canal / Grupo con Rich HTML)</option>
                                        <option value="facebook">Facebook (Página Oficial / Copys)</option>
                                    </select>
                                </div>
                            </div>

                            {/* 2-Column Split: Editor + Live Preview */}
                            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                                {/* Editor Column */}
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <label className="text-[11px] font-bold text-gray-400 uppercase flex items-center gap-1.5">
                                            <LayoutTemplate className="w-3.5 h-3.5 text-indigo-400" /> Editor de Copy
                                        </label>
                                    </div>

                                    <TelegramRichMessageEditor
                                        value={formData.content}
                                        onChange={(val) => setFormData({ ...formData, content: val })}
                                        platform={formData.platform as 'telegram' | 'facebook'}
                                    />
                                </div>

                                {/* Preview Column */}
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <label className="text-[11px] font-bold text-gray-400 uppercase flex items-center gap-1.5">
                                            <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Simulador {formData.platform === 'facebook' ? 'Facebook' : 'Telegram'}
                                        </label>
                                    </div>

                                    <div className="h-[460px]">
                                        <TelegramMessagePreview
                                            rawTemplate={formData.content}
                                            platform={formData.platform as 'telegram' | 'facebook'}
                                            isCaptionMode={true}
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="pt-4 border-t border-white/10 flex items-center justify-between">
                                {selectedTemplate.id ? (
                                    <button
                                        type="button"
                                        onClick={handleDelete}
                                        className="px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-bold flex items-center gap-1.5 transition-all"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" /> Eliminar
                                    </button>
                                ) : (
                                    <div />
                                )}

                                <button
                                    type="submit"
                                    disabled={isSaving}
                                    className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/30 active:scale-95 transition-all disabled:opacity-50"
                                >
                                    {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                    <span>Guardar Plantilla</span>
                                </button>
                            </div>
                        </form>
                    ) : (
                        <div className="py-24 text-center text-gray-500 text-xs bg-slate-900/30 rounded-2xl border border-white/5">
                            Selecciona una plantilla de la lista o crea una nueva para comenzar a editar.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
