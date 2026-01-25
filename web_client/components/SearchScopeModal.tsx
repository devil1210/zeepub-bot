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
    { id: 'SERIE', label: 'SERIE', icon: Folder },
    { id: 'AUTOR', label: 'AUTOR', icon: User },
    { id: 'ILUSTRADOR', label: 'ILUSTRADOR', icon: PenTool },
    { id: 'TRADUCTOR', label: 'TRADUCTOR', icon: Languages },
    { id: 'MAQUETADOR', label: 'MAQUETADOR', icon: FileBox },
    { id: 'GRUPO', label: 'GRUPO', icon: User },
    { id: 'GÉNEROS', label: 'GÉNEROS', icon: Folder },
  ];

  return (
    <div className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center pointer-events-auto">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/85 backdrop-blur-md transition-opacity duration-500"
        onClick={onClose}
      ></div>

      {/* Modal Content */}
      <div className="relative w-full max-w-md glass-panel rounded-t-[3rem] sm:rounded-[3rem] border-white/10 shadow-[0_50px_100px_-20px_rgba(0,0,0,0.6)] transform transition-all animate-in slide-in-from-bottom-20 fade-in duration-500 flex flex-col max-h-[90vh] overflow-hidden">

        {/* Shine Header */}
        <div className="absolute top-0 inset-x-0 h-32 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none"></div>

        {/* Handle for mobile drag feel */}
        <div className="w-full flex justify-center pt-4 pb-2 relative z-10">
          <div className="w-16 h-1.5 bg-white/10 rounded-full shadow-inner"></div>
        </div>

        <div className="p-8 pt-4 relative z-10">
          <h3 className="text-center text-primary font-black uppercase tracking-[0.3em] text-[11px] mb-8 drop-shadow-[0_0_10px_rgba(var(--color-primary-rgb),0.3)]">
            Tipo de Búsqueda
          </h3>

          <div className="grid grid-cols-1 gap-3 overflow-y-auto max-h-[55vh] custom-scrollbar pr-2 mb-2">
            {scopes.map((scope) => {
              const isSelected = selectedScope === scope.id;
              return (
                <button
                  key={scope.id}
                  onClick={() => {
                    onSelectScope(scope.id);
                    onClose();
                  }}
                  className={`w-full flex items-center justify-between p-4.5 rounded-2xl transition-all duration-500 relative group overflow-hidden ${isSelected
                    ? 'bg-primary/20 border-primary/30 text-white shadow-[0_0_20px_rgba(var(--color-primary-rgb),0.2)]'
                    : 'bg-white/[0.03] border-white/5 text-gray-500 hover:bg-white/[0.08] hover:text-white'
                    }`}
                >
                  {isSelected && <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent"></div>}

                  <div className="flex items-center gap-5 relative z-10">
                    <div className={`p-3 rounded-xl ${isSelected ? 'bg-primary text-white shadow-[0_0_15px_rgba(var(--color-primary-rgb),0.5)]' : 'bg-white/5 text-gray-600 group-hover:text-gray-300'} transition-all duration-500`}>
                      <scope.icon className="w-5 h-5" strokeWidth={2.5} />
                    </div>
                    <span className={`text-[13px] uppercase tracking-[0.15em] transition-all duration-500 ${isSelected ? 'font-black scale-105' : 'font-bold opacity-60 group-hover:opacity-100'}`}>{scope.label}</span>
                  </div>

                  {isSelected && <Check className="w-5 h-5 text-primary animate-in zoom-in duration-300" strokeWidth={3} />}
                </button>
              );
            })}
          </div>

          <button
            onClick={onClose}
            className="w-full mt-8 py-4.5 rounded-[1.5rem] bg-white/5 border border-white/10 text-gray-400 font-black text-[10px] uppercase tracking-[0.25em] hover:bg-white/10 hover:text-white transition-all duration-300"
          >
            Cerrar Panel
          </button>
        </div>
      </div>
    </div>
  );
};