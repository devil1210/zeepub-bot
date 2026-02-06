import React, { useState } from 'react';
import { X, Bug, Loader2, Check } from 'lucide-react';
import { api } from '../services/api';

interface ReportIssueModalProps {
  isOpen: boolean;
  onClose: () => void;
  contextData?: string;
}

export const ReportIssueModal: React.FC<ReportIssueModalProps> = ({ isOpen, onClose, contextData }) => {
  const [selectedReason, setSelectedReason] = useState('formatting');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    if (isSubmitting) return;

    setIsSubmitting(true);
    try {
      const reasonMap: Record<string, string> = {
        'metadata': 'Metadatos Incorrectos',
        'formatting': 'Problema de Formato',
        'order': 'Orden de Capítulos',
        'other': 'Otro Problema'
      };

      const category = 'Bug'; // Default category for issues
      let message = `[${reasonMap[selectedReason] || selectedReason}] ${description}`;

      if (contextData) {
        message += `\n\n[Context: ${contextData}]`;
      }

      await api.sendFeedback(message, category);

      setIsSuccess(true);
      setTimeout(() => {
        onClose();
        setIsSuccess(false);
        setDescription('');
        setSelectedReason('formatting');
      }, 1500);
    } catch (error) {
      console.error('Error submitting report:', error);
      setIsSubmitting(false);
      // Could show error state here if needed
    }
  };

  return (
    <div className="fixed inset-0 z-[60] overflow-y-auto" role="dialog" aria-modal="true">
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onClick={onClose}></div>
      <div className="flex min-h-full items-center justify-center p-4 text-center sm:p-0">
        <div className="relative transform overflow-hidden rounded-premium-sm bg-[#1a1a1e] backdrop-blur-xl text-left shadow-2xl transition-all sm:my-8 sm:w-full sm:max-w-lg border border-white/10 ring-1 ring-black/5 animate-in fade-in zoom-in-95 duration-200">
          {/* Header */}
          <div className="relative px-6 py-5 border-b border-white/5 flex justify-between items-center bg-gradient-to-b from-white/5 to-transparent">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-premium-sm bg-blue-500/20 text-primary">
                <Bug className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white leading-none">Reportar Problema</h3>
                <p className="text-xs text-gray-400 mt-1">Ayúdanos a mejorar la biblioteca</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors focus:outline-none p-2 rounded-full hover:bg-white/10"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="px-6 py-6">
            <div className="space-y-3">
              {[
                { id: 'metadata', title: 'Metadatos Incorrectos', desc: 'Título, autor o portada errónea' },
                { id: 'formatting', title: 'Problema de Formato', desc: 'Diseño roto o caracteres extraños' },
                { id: 'order', title: 'Orden de Capítulos', desc: 'La secuencia de contenido es incorrecta' },
                { id: 'other', title: 'Otro Problema', desc: 'Algo más no listado aquí' }
              ].map((option) => (
                <label
                  key={option.id}
                  className={`group relative flex cursor-pointer rounded-premium-sm border p-3.5 transition-all duration-200 ${selectedReason === option.id
                    ? 'bg-blue-500/10 border-blue-500/30 shadow-[0_0_0_1px_rgba(51,144,236,0.2)]'
                    : 'bg-black/20 border-white/5 hover:border-primary/40 hover:bg-black/30'
                    }`}
                  onClick={() => setSelectedReason(option.id)}
                >
                  <div className="flex w-full items-center gap-3.5">
                    <div className="flex items-center h-5">
                      <input
                        type="radio"
                        name="report_reason"
                        checked={selectedReason === option.id}
                        onChange={() => setSelectedReason(option.id)}
                        className="h-5 w-5 border-gray-600 text-primary focus:ring-primary focus:ring-offset-0 bg-transparent"
                      />
                    </div>
                    <div className="flex-1">
                      <span className={`text-sm font-semibold block ${selectedReason === option.id ? 'text-blue-200' : 'text-gray-100'}`}>
                        {option.title}
                      </span>
                      <span className={`text-xs ${selectedReason === option.id ? 'text-blue-300/60' : 'text-gray-500'}`}>
                        {option.desc}
                      </span>
                    </div>
                  </div>
                </label>
              ))}
            </div>

            <div className="mt-5">
              <label className="block text-xs font-semibold text-gray-400 mb-2 ml-1 uppercase tracking-wider">
                Descripción (Opcional)
              </label>
              <div className="relative">
                <textarea
                  className="block w-full rounded-premium-sm border-white/10 bg-black/20 text-sm text-white shadow-sm focus:border-primary focus:ring-primary focus:bg-black/40 transition-colors placeholder:text-gray-600 p-3 outline-none"
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Por favor, proporciona más detalles..."
                ></textarea>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="bg-black/20 px-6 py-4 flex flex-row-reverse gap-3 border-t border-white/5 backdrop-blur-sm">
            <button
              className={`inline-flex w-full sm:w-auto justify-center items-center gap-2 rounded-premium-sm px-6 py-2.5 text-sm font-semibold text-white shadow-lg transition-all transform active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed ${isSuccess
                ? 'bg-green-500 shadow-green-500/20'
                : 'bg-primary shadow-blue-500/20 hover:bg-blue-600 hover:shadow-blue-500/30'
                }`}
              onClick={handleSubmit}
              disabled={isSubmitting || isSuccess}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Enviando...
                </>
              ) : isSuccess ? (
                <>
                  <Check className="w-4 h-4" />
                  ¡Enviado!
                </>
              ) : (
                'Enviar Reporte'
              )}
            </button>
            <button
              onClick={onClose}
              disabled={isSubmitting}
              className="inline-flex w-full sm:w-auto justify-center rounded-premium-sm bg-transparent border border-gray-600 px-6 py-2.5 text-sm font-semibold text-gray-300 shadow-sm hover:bg-white/5 transition-colors disabled:opacity-50"
            >
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
