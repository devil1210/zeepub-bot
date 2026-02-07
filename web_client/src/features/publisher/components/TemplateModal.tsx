import React, { useState, useEffect } from 'react';
import { X, Type, Loader2, Check, Save, Smartphone, Globe } from 'lucide-react';
import { RichTextEditor } from '@shared/components/RichTextEditor/RichTextEditor';
import { PublicationTemplate } from '../services/publisherApi';

interface TemplateModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (template: Partial<PublicationTemplate>) => Promise<any>;
    editingTemplate?: PublicationTemplate | null;
}

export const TemplateModal: React.FC<TemplateModalProps> = ({ isOpen, onClose, onSave, editingTemplate }) => {
    const [name, setName] = useState('');
    const [content, setContent] = useState('');
    const [platform, setPlatform] = useState('telegram');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    useEffect(() => {
        if (editingTemplate) {
            setName(editingTemplate.name);
            setContent(editingTemplate.content);
            setPlatform(editingTemplate.platform);
        } else {
            setName('');
            setContent('');
            setPlatform('telegram');
        }
    }, [editingTemplate, isOpen]);

    if (!isOpen) return null;

    const handleSubmit = async () => {
        if (!name || !content || isSubmitting) return;

        setIsSubmitting(true);
        try {
            await onSave({
                id: editingTemplate?.id,
                name,
                content,
                platform
            });

            setIsSuccess(true);
            setTimeout(() => {
                onClose();
                setIsSuccess(false);
            }, 1000);
        } catch (error) {
            console.error('Error saving template:', error);
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[60] overflow-y-auto" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-black/70 backdrop-blur-md transition-opacity" onClick={onClose}></div>
            <div className="flex min-h-full items-center justify-center p-4 text-center sm:p-6">
                <div className="relative transform overflow-hidden rounded-premium bg-[#1a1a1e] text-left shadow-2xl transition-all w-full max-w-2xl border border-white/10 animate-in fade-in zoom-in-95 duration-200">
                    {/* Header */}
                    <div className="relative px-6 py-5 border-b border-white/5 flex justify-between items-center bg-gradient-to-b from-white/5 to-transparent">
                        <div className="flex items-center gap-3">
                            <div className="flex items-center justify-center w-10 h-10 rounded-premium-sm bg-primary/20 text-primary">
                                <Type className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="text-lg font-black uppercase tracking-widest text-white leading-none">
                                    {editingTemplate ? 'Editar Plantilla' : 'Nueva Plantilla'}
                                </h3>
                                <p className="text-[10px] font-bold text-gray-500 mt-1 uppercase tracking-tight">Personaliza tus publicaciones automáticas</p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-white transition-colors p-2 rounded-full hover:bg-white/10"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Body */}
                    <div className="px-6 py-6 space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Nombre de la Plantilla</label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="Ej: Lanzamientos Diarios"
                                    className="w-full bg-black/20 border border-white/10 rounded-premium-sm px-4 py-2.5 text-sm text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Plataforma</label>
                                <div className="flex gap-2">
                                    {(['telegram', 'facebook'] as const).map((p) => (
                                        <button
                                            key={p}
                                            type="button"
                                            onClick={() => setPlatform(p)}
                                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all border ${platform === p
                                                ? 'bg-primary/20 border-primary text-primary shadow-lg shadow-primary/10'
                                                : 'bg-black/20 border-white/5 text-gray-500 hover:text-gray-300'
                                                }`}
                                        >
                                            {p === 'telegram' ? <Smartphone className="w-3.5 h-3.5" /> : <Globe className="w-3.5 h-3.5" />}
                                            {p}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Contenido de la Publicación</label>
                            <RichTextEditor
                                value={content}
                                onChange={setContent}
                                placeholder="Escribe el mensaje de la publicación... Usa las variables de abajo para datos dinámicos."
                            />
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="bg-black/20 px-6 py-4 flex flex-row-reverse gap-3 border-t border-white/5">
                        <button
                            className={`inline-flex items-center gap-2 rounded-premium-sm px-8 py-2.5 text-xs font-black uppercase tracking-widest text-white shadow-lg transition-all transform active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed ${isSuccess
                                ? 'bg-green-500 shadow-green-500/20'
                                : 'bg-primary shadow-primary/20 hover:brightness-110'
                                }`}
                            onClick={handleSubmit}
                            disabled={isSubmitting || isSuccess || !name || !content}
                        >
                            {isSubmitting ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Guardando...
                                </>
                            ) : isSuccess ? (
                                <>
                                    <Check className="w-4 h-4" />
                                    ¡Guardado!
                                </>
                            ) : (
                                <>
                                    <Save className="w-4 h-4" />
                                    {editingTemplate ? 'Actualizar' : 'Crear Plantilla'}
                                </>
                            )}
                        </button>
                        <button
                            onClick={onClose}
                            disabled={isSubmitting}
                            className="px-6 py-2.5 text-xs font-black uppercase tracking-widest text-gray-400 hover:text-white transition-colors"
                        >
                            Cancelar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
