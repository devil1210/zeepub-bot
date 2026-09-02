import React, { useState, useEffect } from 'react';
import { X, Globe, Facebook, MessageSquare, Heart, Twitter, Coffee, Save, Trash2, Building2, Tag, Loader2, Sparkles } from 'lucide-react';
import { TranslatorsGroupItem, GroupContactLinks } from '../services/workgroupsApi';

interface WorkgroupModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (group: {
        id?: number;
        name: string;
        siglas?: string;
        description?: string;
        links: GroupContactLinks;
    }) => Promise<void>;
    onDelete?: (id: number) => Promise<void>;
    group: TranslatorsGroupItem | null;
}

export const WorkgroupModal: React.FC<WorkgroupModalProps> = ({
    isOpen,
    onClose,
    onSave,
    onDelete,
    group
}) => {
    const [name, setName] = useState('');
    const [siglas, setSiglas] = useState('');
    const [description, setDescription] = useState('');
    const [links, setLinks] = useState<GroupContactLinks>({
        web: '',
        fb: '',
        discord: '',
        patreon: '',
        twitter: '',
        donations: ''
    });
    const [saving, setSaving] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (group) {
            setName(group.name || '');
            setSiglas(group.siglas || '');
            setDescription(group.description || '');
            setLinks({
                web: group.links?.web || '',
                fb: group.links?.fb || '',
                discord: group.links?.discord || '',
                patreon: group.links?.patreon || '',
                twitter: group.links?.twitter || '',
                donations: group.links?.donations || ''
            });
        } else {
            setName('');
            setSiglas('');
            setDescription('');
            setLinks({
                web: '',
                fb: '',
                discord: '',
                patreon: '',
                twitter: '',
                donations: ''
            });
        }
        setError(null);
    }, [group, isOpen]);

    if (!isOpen) return null;

    const handleLinkChange = (key: keyof GroupContactLinks, value: string) => {
        setLinks(prev => ({ ...prev, [key]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) {
            setError('El nombre del grupo traductor es obligatorio');
            return;
        }

        setSaving(true);
        setError(null);
        try {
            await onSave({
                id: group?.id,
                name: name.trim(),
                siglas: siglas.trim() || undefined,
                description: description.trim() || undefined,
                links
            });
            onClose();
        } catch (err: any) {
            setError(err.message || 'Error al guardar el grupo traductor');
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async () => {
        if (!group?.id || !onDelete) return;
        if (!confirm(`¿Eliminar definitivamente el grupo "${group.name}"?`)) return;

        setDeleting(true);
        try {
            await onDelete(group.id);
            onClose();
        } catch (err: any) {
            setError(err.message || 'Error al eliminar');
        } finally {
            setDeleting(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
            <div className="relative w-full max-w-2xl bg-slate-900 border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-slate-950/60">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                            <Building2 className="w-5 h-5" />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                                {group ? 'Editar Grupo Traductor / Fansub' : 'Nuevo Grupo Traductor / Fansub'}
                            </h3>
                            <p className="text-xs text-gray-400">
                                Redes y enlaces oficiales para plantillas de publicación
                            </p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {error && (
                    <div className="mx-6 mt-4 p-3 rounded-2xl bg-red-500/10 border border-red-500/20 text-xs text-red-300 font-medium">
                        {error}
                    </div>
                )}

                {/* Form Body */}
                <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-5">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div className="sm:col-span-2">
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1.5">
                                Nombre del Grupo / Fansub <span className="text-indigo-400">*</span>
                            </label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Ej. Tamashi's Project, Lanove, MK & LnF"
                                className="w-full px-4 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1.5">
                                Siglas / Tag
                            </label>
                            <input
                                type="text"
                                value={siglas}
                                onChange={(e) => setSiglas(e.target.value)}
                                placeholder="Ej. [TP], [LANOVE]"
                                className="w-full px-4 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1.5">
                            Descripción / Notas
                        </label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Información interna, proyectos activos o notas editoriales..."
                            rows={2}
                            className="w-full px-4 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 resize-none"
                        />
                    </div>

                    {/* Contact Links Grid */}
                    <div className="pt-3 border-t border-white/5 space-y-3">
                        <div className="text-[11px] font-bold text-indigo-300 uppercase tracking-wider">
                            Enlaces Oficiales de Contacto
                        </div>
                        <p className="text-[10px] text-gray-400">
                            Disponibles en variables de plantilla como <code>{'{grupo_web}'}</code>, <code>{'{grupo_fb}'}</code>, etc.
                        </p>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                            <div className="relative">
                                <Globe className="w-3.5 h-3.5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                                <input
                                    type="url"
                                    value={links.web || ''}
                                    onChange={(e) => handleLinkChange('web', e.target.value)}
                                    placeholder="https://sitio-oficial.com"
                                    className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div className="relative">
                                <Facebook className="w-3.5 h-3.5 text-blue-400 absolute left-3 top-1/2 -translate-y-1/2" />
                                <input
                                    type="url"
                                    value={links.fb || ''}
                                    onChange={(e) => handleLinkChange('fb', e.target.value)}
                                    placeholder="https://facebook.com/fansub"
                                    className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div className="relative">
                                <MessageSquare className="w-3.5 h-3.5 text-indigo-400 absolute left-3 top-1/2 -translate-y-1/2" />
                                <input
                                    type="url"
                                    value={links.discord || ''}
                                    onChange={(e) => handleLinkChange('discord', e.target.value)}
                                    placeholder="https://discord.gg/invitacion"
                                    className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div className="relative">
                                <Heart className="w-3.5 h-3.5 text-pink-400 absolute left-3 top-1/2 -translate-y-1/2" />
                                <input
                                    type="url"
                                    value={links.patreon || ''}
                                    onChange={(e) => handleLinkChange('patreon', e.target.value)}
                                    placeholder="https://patreon.com/fansub"
                                    className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div className="relative">
                                <Twitter className="w-3.5 h-3.5 text-sky-400 absolute left-3 top-1/2 -translate-y-1/2" />
                                <input
                                    type="url"
                                    value={links.twitter || ''}
                                    onChange={(e) => handleLinkChange('twitter', e.target.value)}
                                    placeholder="https://x.com/fansub"
                                    className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div className="relative">
                                <Coffee className="w-3.5 h-3.5 text-amber-400 absolute left-3 top-1/2 -translate-y-1/2" />
                                <input
                                    type="url"
                                    value={links.donations || ''}
                                    onChange={(e) => handleLinkChange('donations', e.target.value)}
                                    placeholder="https://ko-fi.com/fansub"
                                    className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                        </div>
                    </div>
                </form>

                {/* Footer Controls */}
                <div className="px-6 py-4 border-t border-white/10 bg-slate-950/60 flex items-center justify-between">
                    {group?.id && onDelete ? (
                        <button
                            type="button"
                            onClick={handleDelete}
                            disabled={deleting}
                            className="px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-bold border border-red-500/20 flex items-center gap-1.5 transition-all"
                        >
                            <Trash2 className="w-3.5 h-3.5" />
                            <span>Eliminar</span>
                        </button>
                    ) : (
                        <div />
                    )}

                    <div className="flex items-center gap-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-xs font-bold text-gray-400 hover:text-white transition-all"
                        >
                            Cancelar
                        </button>
                        <button
                            type="button"
                            onClick={handleSubmit}
                            disabled={saving}
                            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/30 active:scale-95 transition-all disabled:opacity-50"
                        >
                            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            <span>Guardar Grupo</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
