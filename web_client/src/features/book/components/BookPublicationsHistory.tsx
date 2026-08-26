import React, { useState, useEffect } from 'react';
import {
  ExternalLink,
  Calendar,
  ChevronDown,
  ChevronUp,
  Radio,
  FileText,
  CheckCircle2,
  Edit3,
  Save,
  X,
  Loader2
} from 'lucide-react';
import { BookPublication } from '@shared/types';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { api } from '@shared/services/api';

interface BookPublicationsHistoryProps {
  publications?: BookPublication[];
}

export const BookPublicationsHistory: React.FC<BookPublicationsHistoryProps> = ({ publications = [] }) => {
  const { webApp, isAdmin, isStaff } = useTelegram();
  const canEdit = isAdmin || isStaff;

  const [localPubs, setLocalPubs] = useState<BookPublication[]>([]);
  const [expandedCaptions, setExpandedCaptions] = useState<Record<number, boolean>>({});
  const [editingPubId, setEditingPubId] = useState<number | null>(null);
  const [editCaptionText, setEditCaptionText] = useState<string>('');
  const [isSaving, setIsSaving] = useState<boolean>(false);

  useEffect(() => {
    if (publications && publications.length > 0) {
      const sorted = [...publications].sort((a, b) => {
        const timeA = a.published_at ? new Date(a.published_at).getTime() : 0;
        const timeB = b.published_at ? new Date(b.published_at).getTime() : 0;
        return timeB - timeA;
      });
      setLocalPubs(sorted);
    } else {
      setLocalPubs([]);
    }
  }, [publications]);

  if (!localPubs || localPubs.length === 0) {
    return null;
  }

  const toggleCaption = (id: number) => {
    setExpandedCaptions(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const handleStartEdit = (pub: BookPublication) => {
    setEditingPubId(pub.id);
    setEditCaptionText(pub.caption || '');
    setExpandedCaptions(prev => ({ ...prev, [pub.id]: true }));
    webApp?.HapticFeedback?.impactOccurred('light');
  };

  const handleCancelEdit = () => {
    setEditingPubId(null);
    setEditCaptionText('');
  };

  const handleSaveEdit = async (pub: BookPublication) => {
    if (!editCaptionText.trim()) {
      if (webApp?.showAlert) webApp.showAlert('El texto del post no puede estar vacío.');
      else alert('El texto del post no puede estar vacío.');
      return;
    }

    setIsSaving(true);
    webApp?.HapticFeedback?.impactOccurred('medium');

    try {
      const res = await api.updatePublicationCaption(pub.id, editCaptionText);
      if (res.success) {
        webApp?.HapticFeedback?.notificationOccurred('success');
        
        // Actualizar estado local inmediatamente
        setLocalPubs(prev =>
          prev.map(p => (p.id === pub.id ? { ...p, caption: editCaptionText } : p))
        );
        setEditingPubId(null);

        const platName = pub.platform.toLowerCase().includes('fb') || pub.platform.toLowerCase().includes('facebook')
          ? 'Facebook'
          : pub.platform.toLowerCase().includes('tg') || pub.platform.toLowerCase().includes('telegram')
          ? 'Telegram'
          : 'Red Social';

        const successMsg = `✅ ¡Publicación actualizada exitosamente en ${platName} y guardada en la base de datos!`;
        if (webApp?.showAlert) {
          webApp.showAlert(successMsg);
        } else {
          alert(successMsg);
        }
      } else {
        webApp?.HapticFeedback?.notificationOccurred('error');
        const errMsg = res.message || res.error || 'No se pudo actualizar el post.';
        if (webApp?.showAlert) webApp.showAlert(`⚠️ Error al actualizar: ${errMsg}`);
        else alert(`⚠️ Error al actualizar: ${errMsg}`);
      }
    } catch (error: any) {
      console.error('Error updating publication caption:', error);
      webApp?.HapticFeedback?.notificationOccurred('error');
      const errMsg = error.message || 'Error de conexión con el servidor.';
      if (webApp?.showAlert) webApp.showAlert(`❌ Error: ${errMsg}`);
      else alert(`❌ Error: ${errMsg}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleOpenUrl = (url?: string | null) => {
    if (!url) return;

    webApp?.HapticFeedback?.impactOccurred('light');

    if (webApp) {
      if (url.includes('t.me/') && webApp.openTelegramLink) {
        webApp.openTelegramLink(url);
        return;
      }
      if (webApp.openLink) {
        webApp.openLink(url);
        return;
      }
    }

    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return 'Fecha no disponible';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;

    return d.toLocaleDateString('es-ES', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getPlatformDetails = (platform: string) => {
    const p = platform.toLowerCase();
    if (p.includes('facebook') || p.includes('fb')) {
      return {
        name: 'Facebook',
        badgeClass: 'bg-[#1877F2]/15 text-[#1877F2] border-[#1877F2]/30',
        glowClass: 'from-[#1877F2]/10 to-transparent',
        btnBgClass: 'bg-[#1877F2] hover:bg-[#1877F2]/80',
        icon: (
          <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
          </svg>
        )
      };
    }

    if (p.includes('telegram') || p.includes('tg')) {
      return {
        name: 'Telegram',
        badgeClass: 'bg-[#229ED9]/15 text-[#229ED9] border-[#229ED9]/30',
        glowClass: 'from-[#229ED9]/10 to-transparent',
        btnBgClass: 'bg-[#229ED9] hover:bg-[#229ED9]/80',
        icon: (
          <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
            <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
          </svg>
        )
      };
    }

    return {
      name: platform.toUpperCase(),
      badgeClass: 'bg-primary/15 text-primary border-primary/30',
      glowClass: 'from-primary/10 to-transparent',
      btnBgClass: 'bg-primary hover:bg-primary/80',
      icon: <Radio className="w-4 h-4" />
    };
  };

  return (
    <div className="glass-panel border border-white/10 rounded-premium-sm p-6 lg:p-8 shadow-xl space-y-6 animate-in fade-in slide-in-from-bottom-3 duration-300">
      {/* Header with Title and Badges */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20 shadow-lg shadow-primary/5">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-black uppercase tracking-wider text-white">
                Historial de Publicaciones
              </h3>
              <span className="px-2 py-0.5 rounded-full bg-white/10 text-white font-mono text-[10px] font-bold">
                {localPubs.length}
              </span>
            </div>
            <p className="text-[11px] text-gray-400 mt-0.5">
              Registro de emisiones oficiales en redes sociales (Solo Staff / Admin)
            </p>
          </div>
        </div>

        {localPubs.length > 1 && (
          <div className="flex items-center gap-1.5 self-start sm:self-center px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-black uppercase tracking-wider">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Publicado {localPubs.length} veces</span>
          </div>
        )}
      </div>

      {/* Publications Timeline List */}
      <div className="space-y-3">
        {localPubs.map((pub, idx) => {
          const plat = getPlatformDetails(pub.platform);
          const isCaptionOpen = !!expandedCaptions[pub.id] || editingPubId === pub.id;
          const isCurrentEditing = editingPubId === pub.id;

          return (
            <div
              key={pub.id || idx}
              className="glass-panel border border-white/5 hover:border-white/15 rounded-xl p-4 sm:p-5 transition-all duration-300 relative overflow-hidden group/item"
            >
              {/* Subtle Ambient Platform Glow */}
              <div className={`absolute -right-10 -top-10 w-32 h-32 bg-gradient-to-br ${plat.glowClass} blur-2xl pointer-events-none opacity-40 group-hover/item:opacity-75 transition-opacity`}></div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 relative z-10">
                {/* Left: Platform Badge & Date */}
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-bold ${plat.badgeClass}`}>
                      {plat.icon}
                      <span>{plat.name}</span>
                    </span>

                    {pub.post_id && (
                      <span className="text-[10px] text-gray-500 font-mono bg-white/5 px-2 py-0.5 rounded border border-white/5">
                        ID: {pub.post_id}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <Calendar className="w-3.5 h-3.5 text-gray-500" />
                    <span>{formatDate(pub.published_at)}</span>
                  </div>
                </div>

                {/* Right: Actions */}
                <div className="flex items-center gap-2 self-end sm:self-center">
                  {pub.caption && !isCurrentEditing && (
                    <button
                      onClick={() => toggleCaption(pub.id)}
                      className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-semibold flex items-center gap-1.5 transition-colors border border-white/5"
                      title="Ver mensaje publicado"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>{isCaptionOpen ? 'Ocultar Texto' : 'Ver Texto'}</span>
                      {isCaptionOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  )}

                  {pub.post_url ? (
                    <button
                      onClick={() => handleOpenUrl(pub.post_url)}
                      className="px-3.5 py-1.5 rounded-lg bg-primary hover:bg-primary/80 text-white text-xs font-bold flex items-center gap-1.5 transition-all shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-95"
                    >
                      <span>Ver Publicación</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </button>
                  ) : (
                    <span className="text-[11px] text-gray-500 italic px-2 py-1">
                      Sin enlace directo
                    </span>
                  )}
                </div>
              </div>

              {/* Caption Area (View Mode or Inline Edit Mode) */}
              {(pub.caption || isCurrentEditing) && isCaptionOpen && (
                <div className="mt-4 pt-3 border-t border-white/5 text-xs text-gray-300 leading-relaxed bg-black/25 p-4 rounded-xl border border-white/5 font-sans animate-in slide-in-from-top-2 fade-in duration-200">
                  <div className="flex items-center justify-between gap-2 mb-2 pb-2 border-b border-white/5">
                    <span className="text-[10px] font-black uppercase text-primary tracking-wider flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5" />
                      {isCurrentEditing ? `Editando Post en ${plat.name}` : 'Texto del Post'}
                    </span>

                    {/* Edit Button (View Mode) */}
                    {!isCurrentEditing && canEdit && (
                      <button
                        onClick={() => handleStartEdit(pub)}
                        className="px-2.5 py-1 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 text-[11px] font-bold flex items-center gap-1.5 transition-all hover:scale-[1.02] active:scale-95"
                        title="Modificar este texto y actualizar el post en Facebook/Telegram"
                      >
                        <Edit3 className="w-3 h-3" />
                        <span>Editar Texto</span>
                      </button>
                    )}
                  </div>

                  {/* Edit Mode Content */}
                  {isCurrentEditing ? (
                    <div className="space-y-3">
                      <textarea
                        value={editCaptionText}
                        onChange={e => setEditCaptionText(e.target.value)}
                        disabled={isSaving}
                        rows={10}
                        className="w-full bg-black/40 border border-primary/40 focus:border-primary rounded-xl p-3.5 text-xs text-white leading-relaxed focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all font-mono resize-y"
                        placeholder="Escribe el nuevo texto del post..."
                      />

                      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 pt-1">
                        <span className="text-[10px] text-gray-400 font-mono">
                          {editCaptionText.length} caracteres
                        </span>

                        <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                          <button
                            onClick={handleCancelEdit}
                            disabled={isSaving}
                            className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 text-xs font-semibold flex items-center gap-1.5 transition-colors border border-white/5 disabled:opacity-50"
                          >
                            <X className="w-3.5 h-3.5" />
                            <span>Cancelar</span>
                          </button>

                          <button
                            onClick={() => handleSaveEdit(pub)}
                            disabled={isSaving}
                            className={`px-4 py-1.5 rounded-lg ${plat.btnBgClass} text-white text-xs font-bold flex items-center gap-1.5 transition-all shadow-lg hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed`}
                          >
                            {isSaving ? (
                              <>
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                <span>Actualizando en {plat.name}...</span>
                              </>
                            ) : (
                              <>
                                <Save className="w-3.5 h-3.5" />
                                <span>Guardar y Actualizar en {plat.name}</span>
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* Normal Display View */
                    <div className="whitespace-pre-wrap text-gray-200 select-text leading-relaxed">
                      {pub.caption}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
