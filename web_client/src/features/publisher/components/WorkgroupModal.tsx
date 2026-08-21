import React, { useState, useEffect } from 'react';
import { X, Globe, Facebook, MessageSquare, Heart, Twitter, Coffee, Save, Trash2, Building2 } from 'lucide-react';
import { useTheme } from '@shared/contexts/ThemeContext';
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
    const { settings } = useTheme();
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
        if (!window.confirm(`¿Estás seguro de eliminar el grupo "${group.name}"?`)) return;

        setDeleting(true);
        try {
            await onDelete(group.id);
            onClose();
        } catch (err: any) {
            setError(err.message || 'Error al eliminar el grupo');
        } finally {
            setDeleting(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div
                className="w-full max-w-lg glass-panel rounded-premium overflow-hidden border border-white/10 flex flex-col max-h-[90vh] shadow-2xl"
                style={{
                    background: `rgba(var(--glass-rgb), 0.92)`,
                    backdropFilter: `blur(${settings.glassBlur + 4}px)`
                }}
            >
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-white/5 bg-white/5">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-primary/10 text-primary">
                            <Building2 className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-sm font-bold text-white">
                                {group ? 'Editar Grupo Traductor' : 'Nuevo Grupo Traductor / Fansub'}
                            </h2>
                            <p className="text-[11px] text-gray-400">
                                Redes y enlaces oficiales para plantillas de publicación
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Form Body */}
                <form onSubmit={handleSubmit} className="p-4 flex flex-col gap-4 overflow-y-auto custom-scrollbar">
                    {error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs flex items-center gap-2">
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Basic Info */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <div className="sm:col-span-2 flex flex-col gap-1">
                            <label className="text-[11px] font-bold text-gray-300">
                                Nombre del Grupo / Fansub <span className="text-primary">*</span>
                            </label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Ej. Tamashi's Project, MK & LnF"
                                className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-primary transition-all"
                                required
                            />
                        </div>

                        <div className="flex flex-col gap-1">
                            <label className="text-[11px] font-bold text-gray-300">Siglas / Tag</label>
                            <input
                                type="text"
                                value={siglas}
                                onChange={(e) => setSiglas(e.target.value)}
                                placeholder="Ej. [TP], [MK]"
                                className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-primary transition-all"
                            />
                        </div>
                    </div>

                    <div className="flex flex-col gap-1">
                        <label className="text-[11px] font-bold text-gray-300">Descripción / Notas</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={2}
                            placeholder="Información interna o notas sobre este grupo..."
                            className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-primary resize-none transition-all"
                        />
                    </div>

                    {/* Social & Contact Links */}
                    <div className="flex flex-col gap-2 pt-2 border-t border-white/5">
                        <h3 className="text-[11px] font-black uppercase tracking-wider text-primary">
                            Enlaces Oficiales de Contacto
                        </h3>
                        <p className="text-[10px] text-gray-400">
                            Disponibles como {'{grupo_web}'}, {'{grupo_fb}'}, {'{grupo_discord}'}, etc.
                        </p>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-1">
                            {/* Web */}
                            <div className="flex flex-col gap-1">
                                <label className="text-[10px] font-bold text-gray-400 flex items-center gap-1.5">
                                    <Globe className="w-3.5 h-3.5 text-blue-400" /> Sitio Web Oficial
                                </label>
                                <input
                                    type="url"
                                    value={links.web || ''}
                                    onChange={(e) => handleLinkChange('web', e.target.value)}
                                    placeholder="https://mitraductor.com"
                                    className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-xl text-xs text-white placeholder-gray-600 focus:outline-none focus:border-primary transition-all"
                                />
                            </div>

                            {/* Facebook */}
                            <div className="flex flex-col gap-1">
                                <label className="text-[10px] font-bold text-gray-400 flex items-center gap-1.5">
                                    <Facebook className="w-3.5 h-3.5 text-blue-500" /> Página de Facebook
                                </label>
                                <input
                                    type="url"
                                    value={links.fb || ''}
                                    onChange={(e) => handleLinkChange('fb', e.target.value)}
                                    placeholder="https://facebook.com/mifansub"
                                    className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-xl text-xs text-white placeholder-gray-600 focus:outline-none focus:border-primary transition-all"
                                />
                            </div>

                            {/* Discord */}
                            <div className="flex flex-col gap-1">
                                <label className="text-[10px] font-bold text-gray-400 flex items-center gap-1.5">
                                    <MessageSquare className="w-3.5 h-3.5 text-indigo-400" /> Servidor de Discord
                                </label>
                                <input
                                    type="url"
                                    value={links.discord || ''}
                                    onChange={(e) => handleLinkChange('discord', e.target.value)}
                                    placeholder="https://discord.gg/invitacion"
                                    className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-xl text-xs text-white placeholder-gray-600 focus:outline-none focus:border-primary transition-all"
                                />
                            </div>

                            {/* Patreon */}
                            <div className="flex flex-col gap-1">
                                <label className="text-[10px] font-bold text-gray-400 flex items-center gap-1.5">
                                    <Heart className="w-3.5 h-3.5 text-red-400" /> Patreon / Membresía
                                </label>
                                <input
                                    type="url"
                                    value={links.patreon || ''}
                                    onChange={(e) => handleLinkChange('patreon', e.target.value)}
                                    placeholder="https://patreon.com/fansub"
                                    className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-xl text-xs text-white placeholder-gray-600 focus:outline-none focus:border-primary transition-all"
                                />
                            </div>

                            {/* Twitter / X */}
                            <div className="flex flex-col gap-1">
                                <label className="text-[10px] font-bold text-gray-400 flex items-center gap-1.5">
                                    <Twitter className="w-3.5 h-3.5 text-sky-400" /> Twitter / X
                                </label>
                                <input
                                    type="url"
                                    value={links.twitter || ''}
                                    onChange={(e) => handleLinkChange('twitter', e.target.value)}
                                    placeholder="https://x.com/fansub"
                                    className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-xl text-xs text-white placeholder-gray-600 focus:outline-none focus:border-primary transition-all"
                                />
                            </div>

                            {/* Donations / Ko-fi */}
                            <div className="flex flex-col gap-1">
                                <label className="text-[10px] font-bold text-gray-400 flex items-center gap-1.5">
                                    <Coffee className="w-3.5 h-3.5 text-amber-400" /> Donaciones / Ko-fi
                                </label>
                                <input
                                    type="url"
                                    value={links.donations || ''}
                                    onChange={(e) => handleLinkChange('donations', e.target.value)}
                                    placeholder="https://ko-fi.com/fansub"
                                    className="w-full px-3 py-2 bg-black/20 border border-white/10 rounded-xl text-xs text-white placeholder-gray-600 focus:outline-none focus:border-primary transition-all"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Actions Footer */}
                    <div className="flex items-center justify-between pt-3 border-t border-white/5 mt-2">
                        {group?.id && onDelete ? (
                            <button
                                type="button"
                                onClick={handleDelete}
                                disabled={deleting || saving}
                                className="px-3 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-50"
                            >
                                <Trash2 className="w-3.5 h-3.5" />
                                {deleting ? 'Eliminando...' : 'Eliminar'}
                            </button>
                        ) : <div />}

                        <div className="flex items-center gap-2">
                            <button
                                type="button"
                                onClick={onClose}
                                disabled={saving}
                                className="px-4 py-2 bg-white/5 hover:bg-white/10 text-gray-300 rounded-xl text-xs font-semibold transition-all"
                            >
                                Cancelar
                            </button>
                            <button
                                type="submit"
                                disabled={saving}
                                className="px-5 py-2 bg-primary hover:brightness-110 text-white rounded-xl text-xs font-bold shadow-lg shadow-primary/20 flex items-center gap-1.5 active:scale-95 transition-all disabled:opacity-50"
                            >
                                <Save className="w-3.5 h-3.5" />
                                {saving ? 'Guardando...' : 'Guardar Grupo'}
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
};
