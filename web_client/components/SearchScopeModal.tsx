import React from 'react';
import { 
  Library, 
  BookType, 
  User, 
  PenTool, 
  Languages, 
  FileBox, 
  Folder, 
  Check 
} from 'lucide-react';

interface SearchScopeModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedScope: string;
  onSelectScope: (scope: string) => void;
}

export const SearchScopeModal: React.FC<SearchScopeModalProps> = ({ 
  isOpen, 
  onClose, 
  selectedScope, 
  onSelectScope 
}) => {
  if (!isOpen) return null;

  const scopes = [
    { id: 'TODOS', label: 'TODOS', icon: Library },
    { id: 'TÍTULO', label: 'TÍTULO', icon: BookType },
    { id: 'AUTOR', label: 'AUTOR', icon: User },
    { id: 'ILUSTRADOR', label: 'ILUSTRADOR', icon: PenTool },
    { id: 'TRADUCTOR', label: 'TRADUCTOR', icon: Languages },
    { id: 'MAQUETADOR', label: 'MAQUETADOR', icon: FileBox },
    { id: 'GÉNEROS', label: 'GÉNEROS', icon: Folder },
  ];

  return (
    <div className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center pointer-events-auto">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/80 backdrop-blur-sm transition-opacity" 
        onClick={onClose}
      ></div>

      {/* Modal Content */}
      <div className="relative w-full max-w-md bg-[#0f1115] rounded-t-3xl sm:rounded-2xl border-t sm:border border-white/10 shadow-2xl transform transition-transform animate-in slide-in-from-bottom-full duration-300 flex flex-col max-h-[90vh]">
        
        {/* Handle for mobile drag feel */}
        <div className="w-full flex justify-center pt-3 pb-1">
            <div className="w-12 h-1.5 bg-gray-700 rounded-full"></div>
        </div>

        <div className="p-6 pt-2">
            <h3 className="text-center text-[#2AABEE] font-black uppercase tracking-widest text-sm mb-6">
                Tipo de Búsqueda
            </h3>

            <div className="space-y-2 overflow-y-auto max-h-[60vh] custom-scrollbar pr-1">
                {scopes.map((scope) => {
                    const isSelected = selectedScope === scope.id;
                    return (
                        <button
                            key={scope.id}
                            onClick={() => {
                                onSelectScope(scope.id);
                                onClose();
                            }}
                            className={`w-full flex items-center justify-between p-4 rounded-xl transition-all border ${
                                isSelected 
                                ? 'bg-[#2AABEE]/10 border-[#2AABEE]/30 text-[#2AABEE]' 
                                : 'bg-transparent border-transparent text-gray-400 hover:bg-white/5 hover:text-white'
                            }`}
                        >
                            <div className="flex items-center gap-4">
                                <scope.icon className={`w-5 h-5 ${isSelected ? 'text-[#2AABEE]' : 'text-gray-500'}`} />
                                <span className="text-xs font-black uppercase tracking-wider">{scope.label}</span>
                            </div>
                            {isSelected && <Check className="w-5 h-5 text-[#2AABEE]" />}
                        </button>
                    );
                })}
            </div>

            <button 
                onClick={onClose}
                className="w-full mt-6 py-3.5 rounded-xl border border-white/10 bg-[#1a1d24] text-gray-300 font-black text-xs uppercase tracking-widest hover:bg-white/10 transition-colors"
            >
                Cerrar
            </button>
        </div>
      </div>
    </div>
  );
};