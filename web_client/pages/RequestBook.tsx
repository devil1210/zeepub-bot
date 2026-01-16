import React from 'react';
import { 
  Zap, 
  Send, 
  Sparkles, 
  CheckCircle2, 
  Star,
  Home,
  Clock
} from 'lucide-react';

interface RequestBookProps {
  onNavigate?: (tab: string) => void;
}

export const RequestBook: React.FC<RequestBookProps> = ({ onNavigate }) => {
  return (
    <div className="font-sans text-gray-100 min-h-full animate-in fade-in duration-300 pb-24">
      <main className="max-w-3xl mx-auto px-4 py-8 md:py-12">
        
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-3xl md:text-4xl font-bold mb-3 tracking-tight text-white">Solicitar un Libro</h1>
          <p className="text-gray-400 text-lg max-w-lg mx-auto">
            ¿No encuentras lo que buscas? Envía una solicitud y nuestra comunidad ayudará a localizar el ePub por ti.
          </p>
        </div>

        {/* Request Form */}
        <div className="glass-panel rounded-2xl p-6 md:p-8 shadow-soft border border-white/10 mb-8 relative overflow-hidden">
          <div className="absolute top-0 right-0 -mt-10 -mr-10 w-40 h-40 bg-primary/10 rounded-full blur-3xl pointer-events-none"></div>
          
          <form className="space-y-6 relative z-10" onSubmit={(e) => e.preventDefault()}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-400 mb-2" htmlFor="book-title">
                  Título del Libro <span className="text-red-500">*</span>
                </label>
                <input 
                  className="w-full rounded-xl bg-black/20 border border-white/10 text-white focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none placeholder-gray-600 py-3 px-4 transition-all" 
                  id="book-title" 
                  placeholder="ej. Project Hail Mary" 
                  required 
                  type="text"
                />
              </div>
              <div className="col-span-2 md:col-span-1">
                <label className="block text-sm font-medium text-gray-400 mb-2" htmlFor="author">
                  Nombre del Autor <span className="text-red-500">*</span>
                </label>
                <input 
                  className="w-full rounded-xl bg-black/20 border border-white/10 text-white focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none placeholder-gray-600 py-3 px-4 transition-all" 
                  id="author" 
                  placeholder="ej. Andy Weir" 
                  required 
                  type="text"
                />
              </div>
              <div className="col-span-2 md:col-span-1">
                <label className="block text-sm font-medium text-gray-400 mb-2" htmlFor="isbn">
                  ISBN (Opcional)
                </label>
                <input 
                  className="w-full rounded-xl bg-black/20 border border-white/10 text-white focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none placeholder-gray-600 py-3 px-4 transition-all" 
                  id="isbn" 
                  placeholder="ej. 978-0593135204" 
                  type="text"
                />
              </div>
            </div>

            <div className="bg-white/5 rounded-xl p-4 border border-white/10 flex items-center justify-between group cursor-pointer hover:border-primary/50 transition-colors">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-full bg-primary/10 text-primary">
                  <Zap className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-medium text-white group-hover:text-primary transition-colors">Solicitud Prioritaria</h3>
                  <p className="text-xs text-gray-400 mt-0.5">Sube esta solicitud al principio de la cola</p>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input className="sr-only peer" id="priority-toggle" type="checkbox"/>
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>

            <div className="pt-2">
              <button className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-3.5 px-6 rounded-xl shadow-glow transition-all flex items-center justify-center gap-2" type="submit">
                <span>Enviar Solicitud</span>
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>

        {/* Donation / Support Section */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-black border border-gray-800 shadow-2xl">
          <div className="absolute top-0 left-1/4 w-64 h-64 bg-primary/20 rounded-full blur-[100px] pointer-events-none"></div>
          <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-yellow-500/10 rounded-full blur-[100px] pointer-events-none"></div>
          
          <div className="relative z-10 p-6 md:p-10 flex flex-col md:flex-row items-center gap-8">
            <div className="flex-1 text-center md:text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-xs font-bold uppercase tracking-wider mb-4">
                <Sparkles className="w-3 h-3" />
                Apoyo Comunitario
              </div>
              <h2 className="text-2xl font-bold text-white mb-3">Apoya a ZeepubBot</h2>
              <p className="text-gray-400 text-sm leading-relaxed mb-6">
                Somos un proyecto gratuito impulsado por la comunidad. Tus donaciones nos ayudan a mantener servidores, pagar costos de API y <span className="text-white font-medium">priorizar solicitudes de libros</span> en la cola de procesamiento.
              </p>
              <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-xs text-gray-500">
                <div className="flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                  <span>Servidores Rápidos</span>
                </div>
                <div className="flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                  <span>Cola Prioritaria</span>
                </div>
                <div className="flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                  <span>Actualizaciones</span>
                </div>
              </div>
            </div>

            <div className="w-full md:w-auto flex flex-col gap-3 min-w-[260px]">
              <button className="group relative w-full overflow-hidden rounded-xl bg-gradient-to-r from-yellow-600 to-yellow-500 p-[1px] focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:ring-offset-2 focus:ring-offset-gray-900">
                <span className="absolute inset-[-1000%] animate-[spin_2s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#E2E8F0_0%,#500_50%,#E2E8F0_100%)] opacity-0 group-hover:opacity-20 transition-opacity"></span>
                <span className="inline-flex h-full w-full cursor-pointer items-center justify-center rounded-xl bg-gray-900 px-6 py-3.5 text-sm font-medium text-white backdrop-blur-3xl transition-all group-hover:bg-gray-800">
                  <Star className="w-4 h-4 text-yellow-400 mr-2 animate-pulse-slow fill-current" />
                  Donar Telegram Stars
                </span>
              </button>
              
              <div className="grid grid-cols-2 gap-3">
                <button className="flex items-center justify-center gap-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 px-4 py-3 transition-all">
                  <span className="font-bold text-telegram-ton text-sm">TON</span>
                  <span className="text-xs text-gray-400">Crypto</span>
                </button>
                <button className="flex items-center justify-center gap-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 px-4 py-3 transition-all">
                  <span className="font-bold text-green-500 text-sm">USDT</span>
                  <span className="text-xs text-gray-400">TRC20</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <footer className="border-t border-white/10 mt-12 py-8 text-center">
          <p className="text-sm text-gray-500">
            © 2023 ZeepubBot. Construido para la comunidad lectora.
          </p>
        </footer>

      </main>

       {/* Floating Bottom Navigation */}
       <div className="md:hidden fixed bottom-6 left-4 right-4 z-40 animate-in slide-in-from-bottom-4 duration-300">
        <div className="glass-panel rounded-full p-1 border border-white/10 shadow-2xl bg-[#0f1115]/90 backdrop-blur-md flex items-center justify-between">
            {/* Home */}
            <button 
              onClick={() => onNavigate && onNavigate('dashboard')}
              className="flex-1 flex flex-col items-center justify-center py-2.5 px-2 rounded-l-full hover:bg-white/5 active:bg-white/10 transition-colors group text-gray-400 active:text-white"
            >
              <Home className="w-4 h-4 mb-0.5 group-active:-translate-y-1 transition-transform" />
              <span className="text-[9px] font-black uppercase tracking-widest">Inicio</span>
            </button>
            
            <div className="w-px h-8 bg-white/5"></div>

            {/* History Dummy */}
            <button 
              className="flex-1 flex flex-col items-center justify-center py-2.5 px-2 hover:bg-white/5 transition-colors group relative text-gray-400"
            >
              <Clock className="w-4 h-4 mb-0.5" />
              <span className="text-[9px] font-black uppercase tracking-widest">Historial</span>
            </button>
            
            <div className="w-px h-8 bg-white/5"></div>

             {/* Status Dummy */}
             <button 
              className="flex-1 flex flex-col items-center justify-center py-2.5 px-2 rounded-r-full hover:bg-white/5 active:bg-white/10 transition-colors group text-gray-400 active:text-white"
            >
              <Zap className="w-4 h-4 mb-0.5" />
              <span className="text-[9px] font-black uppercase tracking-widest">Estado</span>
            </button>
        </div>
      </div>

    </div>
  );
};