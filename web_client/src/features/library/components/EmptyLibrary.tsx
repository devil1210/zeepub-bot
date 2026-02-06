import React from 'react';
import { Download } from 'lucide-react';

interface EmptyLibraryProps {
    onGoToCatalog: () => void;
}

export const EmptyLibrary: React.FC<EmptyLibraryProps> = ({ onGoToCatalog }) => {
    return (
        <div className="glass-panel rounded-[2.5rem] p-12 text-center border border-white/5 flex flex-col items-center justify-center gap-6 mb-12">
            <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center text-gray-500">
                <Download className="w-10 h-10" />
            </div>
            <div>
                <h2 className="text-xl font-bold text-white mb-2">Biblioteca vacía</h2>
                <p className="text-gray-400 max-w-xs mx-auto text-sm">Explora el catálogo y descarga libros para verlos aquí.</p>
            </div>
            <button
                onClick={onGoToCatalog}
                className="px-8 py-3 bg-primary hover:bg-primary-dark text-white rounded-premium-sm text-xs font-black uppercase tracking-widest transition-all"
            >
                IR AL CATÁLOGO
            </button>
        </div>
    );
};
