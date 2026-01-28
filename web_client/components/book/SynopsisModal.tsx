import React from 'react';
import { ArrowLeft, BookOpen } from 'lucide-react';

interface SynopsisModalProps {
    isOpen: boolean;
    onClose: () => void;
    description?: string;
}

export const SynopsisModal: React.FC<SynopsisModalProps> = ({ isOpen, onClose, description }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div
                className="bg-[#0d1117] border border-white/10 rounded-premium-sm w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="p-6 border-b border-white/5 flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <BookOpen className="w-5 h-5 text-primary" />
                        Sinopsis Completa
                    </h3>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-white/5 rounded-lg text-gray-400 hover:text-white transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                </div>
                <div className="p-6 overflow-y-auto custom-scrollbar">
                    <p className="text-gray-300 text-sm sm:text-base leading-relaxed whitespace-pre-line text-justify">
                        {description || "Sin descripción disponible."}
                    </p>
                </div>
                <div className="p-4 bg-black/20 border-t border-white/5 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-primary text-white text-xs font-black uppercase tracking-widest rounded-lg hover:bg-primary/80"
                    >
                        Cerrar
                    </button>
                </div>
            </div>
            {/* Overlay to close */}
            <div className="absolute inset-0 -z-10" onClick={onClose}></div>
        </div>
    );
};
