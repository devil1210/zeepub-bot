import React, { useState, useEffect } from 'react';
import {
    FileCode2,
    Plus,
    Trash2,
    Save,
    RotateCcw,
    Copy,
    Check,
    Sparkles,
    Loader2,
    CheckCircle2,
    AlertCircle
} from 'lucide-react';
import { api } from '@shared/services/api';

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
    const [copied, setCopied] = useState(false);

    const placeholders = [
        { key: '{serie}', desc: 'Nombre canónico de la serie' },
        { key: '{volumen}', desc: 'Número del volumen' },
        { key: '{titulo}', desc: 'Título oficial/subtítulo' },
        { key: '{autor}', desc: 'Nombre del autor' },
        { key: '{sinopsis}', desc: 'Sinopsis o descripción' },
        { key: '{hashtags}', desc: 'Hashtags automáticos' },
        { key: '{link}', desc: 'Enlace directo a bot' },
        { key: '{cta}', desc: 'Llamado a la acción' },
    ];

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
            content: '🌟 {serie} • Vol. {volumen}\n\n📖 {titulo}\n✍️ Autor: {autor}\n\n{sinopsis}\n\n#ZeePubs #NovelasLigeras',
            platform: 'telegram',
            is_default: false,
        });
        setStatusMsg(null);
    };

    const insertPlaceholder = (ph: string) => {
        setFormData((prev) => ({
            ...prev,
            content: prev.content + ' ' + ph,
        }));
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.pubSaveTemplate({
                id: selectedTemplate?.id || undefined,
                name: formData.name,
                content: formData.content,
                platform: formData.platform,
                is_default: formData.is_default,
            });
            setStatusMsg({ type: 'success', text: 'Plantilla guardada correctamente' });
            fetchTemplates();
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error al guardar plantilla' });
        }
    };

    const handleDelete = async () => {
        if (!selectedTemplate?.id) return;
        if (!confirm('¿Deseas eliminar esta plantilla?')) return;
        try {
            await api.pubDeleteTemplate(selectedTemplate.id);
            setStatusMsg({ type: 'success', text: 'Plantilla eliminada' });
            setSelectedTemplate(null);
            fetchTemplates();
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error al eliminar' });
        }
    };

    const getSimulatedPreview = () => {
        return formData.content
            .replace(/{serie}/g, 'Mushoku Tensei')
            .replace(/{volumen}/g, '26')
            .replace(/{titulo}/g, 'Edición Conmemorativa')
            .replace(/{autor}/g, 'Rifujin na Magonote')
            .replace(/{sinopsis}/g, 'El viaje de Rudeus llega a su clímax decisivo. Tras años de lucha y aprendizaje, el destino final se revela en este épico desenlace.')
            .replace(/{hashtags}/g, '#MushokuTensei #ZeePubs')
            .replace(/{link}/g, 'https://t.me/zeepub_bot?start=dl_mushoku_26')
            .replace(/{cta}/g, 'Descarga el EPUB oficial en nuestra biblioteca digital.');
    };

    const handleCopyPreview = () => {
        navigator.clipboard.writeText(getSimulatedPreview());
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
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
                        Estructura copys dinámicos reutilizables para canales de Telegram y publicaciones de Facebook.
                    </p>
                </div>

                <button
                    onClick={handleCreateNew}
                    className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/20 active:scale-95 transition-all"
                >
                    <Plus className="w-4 h-4" />
                    Nueva Plantilla
                </button>
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

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: Template Selector List */}
                <div className="space-y-3">
                    <h3 className="text-xs font-black uppercase tracking-wider text-gray-400">
                        Plantillas Disponibles
                    </h3>

                    {loading ? (
                        <div className="py-12 flex items-center justify-center">
                            <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {templates.map((tpl) => (
                                <button
                                    key={tpl.id}
                                    onClick={() => selectTemplate(tpl)}
                                    className={`w-full p-3.5 rounded-xl border text-left transition-all flex items-center justify-between group ${
                                        selectedTemplate?.id === tpl.id
                                            ? 'bg-indigo-600/15 border-indigo-500/50 text-white shadow-lg'
                                            : 'bg-slate-900/50 border-white/10 text-gray-300 hover:bg-white/5'
                                    }`}
                                >
                                    <div className="truncate">
                                        <div className="text-xs font-bold truncate group-hover:text-indigo-300">
                                            {tpl.name}
                                        </div>
                                        <div className="text-[10px] text-gray-500 uppercase tracking-widest mt-0.5">
                                            {tpl.platform} {tpl.is_default ? '• Default' : ''}
                                        </div>
                                    </div>
                                    <span className="text-[9px] px-2 py-0.5 rounded-full font-black uppercase bg-white/10 text-gray-400">
                                        {tpl.platform}
                                    </span>
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Center & Right: Template Editor & Live Preview */}
                <div className="lg:col-span-2 space-y-6">
                    {selectedTemplate ? (
                        <form onSubmit={handleSave} className="bg-slate-900/50 border border-white/10 rounded-2xl p-6 space-y-5 backdrop-blur-xl shadow-2xl">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                        Nombre de la Plantilla
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
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
                                        className="w-full px-3.5 py-2.5 bg-slate-900 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    >
                                        <option value="telegram">Telegram (Canal / Grupo)</option>
                                        <option value="facebook">Facebook (Página Oficial)</option>
                                    </select>
                                </div>
                            </div>

                            {/* Variable Placeholders Palette */}
                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-2">
                                    Variables Dinámicas (Haz clic para insertar)
                                </label>
                                <div className="flex flex-wrap gap-2">
                                    {placeholders.map((ph) => (
                                        <button
                                            key={ph.key}
                                            type="button"
                                            onClick={() => insertPlaceholder(ph.key)}
                                            className="px-2.5 py-1 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[11px] font-mono font-bold transition-all active:scale-95"
                                            title={ph.desc}
                                        >
                                            {ph.key}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Textarea Content */}
                            <div>
                                <div className="flex items-center justify-between mb-1">
                                    <label className="text-[11px] font-bold text-gray-400 uppercase">
                                        Cuerpo del Mensaje / Copy
                                    </label>
                                    <span className="text-[10px] text-gray-500 font-mono">
                                        {formData.content.length} caracteres
                                    </span>
                                </div>
                                <textarea
                                    value={formData.content}
                                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                                    rows={8}
                                    className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-xs text-white font-mono leading-relaxed focus:outline-none focus:border-indigo-500"
                                    required
                                />
                            </div>

                            {/* Live Simulation Preview */}
                            <div>
                                <div className="flex items-center justify-between mb-1.5">
                                    <label className="text-[11px] font-bold text-gray-400 uppercase flex items-center gap-1.5">
                                        <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Previsualización Simulada
                                    </label>
                                    <button
                                        type="button"
                                        onClick={handleCopyPreview}
                                        className="text-[11px] font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                                    >
                                        {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                                        {copied ? 'Copiado' : 'Copiar para Facebook'}
                                    </button>
                                </div>
                                <div className="p-4 rounded-xl bg-black/60 border border-white/5 font-mono text-xs text-gray-300 whitespace-pre-wrap leading-relaxed">
                                    {getSimulatedPreview()}
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="pt-3 border-t border-white/10 flex items-center justify-between">
                                {selectedTemplate.id ? (
                                    <button
                                        type="button"
                                        onClick={handleDelete}
                                        className="px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-bold flex items-center gap-1.5 transition-all"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" /> Eliminar
                                    </button>
                                ) : <div />}

                                <button
                                    type="submit"
                                    className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/30 active:scale-95 transition-all"
                                >
                                    <Save className="w-4 h-4" /> Guardar Plantilla
                                </button>
                            </div>
                        </form>
                    ) : (
                        <div className="py-24 text-center text-gray-500 text-xs">
                            Selecciona una plantilla o crea una nueva para comenzar a editar.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
