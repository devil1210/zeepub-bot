import React from 'react';
import { 
  Bell, 
  Send, 
  SlidersHorizontal,
  Home,
  ArrowDownUp,
  Filter
} from 'lucide-react';

interface LibraryProps {
    onNavigate?: (tab: string) => void;
    onSelectBook?: (title: string, author: string, cover: string) => void;
}

export const Library: React.FC<LibraryProps> = ({ onNavigate, onSelectBook }) => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 animate-in fade-in duration-500 pb-28">
      
      {/* Page Header */}
      <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between mb-8">
        <div>
          <h1 className="text-4xl font-black tracking-tight text-white mb-2">Mi Biblioteca</h1>
          <p className="text-gray-400">Gestiona tu lista de lectura y actualizaciones.</p>
        </div>
        {/* Filter Chips */}
        <div className="flex flex-wrap gap-2">
          <button className="flex h-9 items-center gap-2 rounded-full bg-white text-black px-4 text-sm font-medium transition-transform active:scale-95 hover:bg-gray-100 border border-transparent">
             Todas
          </button>
          <button className="flex h-9 items-center gap-2 rounded-full bg-white/5 border border-white/5 hover:bg-white/10 px-4 text-sm font-medium text-white transition-all active:scale-95">
             Actualizadas
             <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-white">1</span>
          </button>
          <button className="flex h-9 items-center gap-2 rounded-full bg-white/5 border border-white/5 hover:bg-white/10 px-4 text-sm font-medium text-gray-400 transition-all active:scale-95">
             Completadas
          </button>
        </div>
      </div>

      {/* Grid Section */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 mb-12">
        
        {/* Active Card (Arifureta) */}
        <div 
            onClick={() => onSelectBook && onSelectBook('Arifureta', 'Ryo Shirakome', 'https://lh3.googleusercontent.com/aida-public/AB6AXuCIAvtXCCRr1DdCjOnabIOkCW2Sp6NMP7ps9Nh9nuV_k-OPfIhoftkSihrTpVchLKRuoFU4fRS-wUvbfri_69LtYsT6-OiNoRKy2vpTL4abAb84gdP0HT-3nw27q294CKcSeM9qQ98RACjZTquO0jZlaRhjPg8Lk-_7cLPYgI-OKPyYEHezSVpxxow6kOLq5uc_BAk1vaqzt-vfqIRvpYIUnbhZBhoCNa4VIHVA6O00lJYYKX6MHmmspDSauVh0OBzSKb_jjxO3Y6I')}
            className="group relative flex flex-col gap-3 rounded-xl p-3 transition-all duration-300 glass-panel hover:bg-white/10 hover:-translate-y-0.5 ring-1 ring-primary/30 shadow-[0_0_20px_rgba(19,127,236,0.15)] cursor-pointer"
        >
          {/* Badge */}
          <div className="absolute -right-1 -top-1 z-20 flex items-center gap-1 rounded bg-primary px-2 py-1 text-[10px] font-black uppercase tracking-wider text-white shadow-lg">
             Nuevo
          </div>
          {/* Image Container */}
          <div className="relative aspect-[2/3] w-full overflow-hidden rounded-lg bg-gray-800 shadow-md">
             <div 
               className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-110" 
               style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuCIAvtXCCRr1DdCjOnabIOkCW2Sp6NMP7ps9Nh9nuV_k-OPfIhoftkSihrTpVchLKRuoFU4fRS-wUvbfri_69LtYsT6-OiNoRKy2vpTL4abAb84gdP0HT-3nw27q294CKcSeM9qQ98RACjZTquO0jZlaRhjPg8Lk-_7cLPYgI-OKPyYEHezSVpxxow6kOLq5uc_BAk1vaqzt-vfqIRvpYIUnbhZBhoCNa4VIHVA6O00lJYYKX6MHmmspDSauVh0OBzSKb_jjxO3Y6I")' }}
             ></div>
             {/* Dark Gradient Overlay for text readability on hover */}
             <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60"></div>
             {/* Pulsing Dot Notification on Image */}
             <div className="absolute bottom-3 left-3 flex items-center gap-2">
                <span className="relative flex h-3 w-3">
                   <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                   <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
                </span>
                <span className="text-[10px] font-bold text-blue-100 uppercase tracking-widest drop-shadow-md">Updated</span>
             </div>
          </div>
          {/* Content */}
          <div className="flex flex-col gap-1">
             <h3 className="truncate text-base font-bold text-white group-hover:text-primary transition-colors">Arifureta</h3>
             <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-white">Vol 13</span>
                <span className="text-gray-400">Hace poco</span>
             </div>
          </div>
        </div>

        {/* Standard Card 2 */}
        <div 
            onClick={() => onSelectBook && onSelectBook('Mushoku Tensei', 'Rifujin na Magonote', 'https://lh3.googleusercontent.com/aida-public/AB6AXuCfiOnuSU03lAssHkL9Pk67gxh-aQXuxzds5tvWpBDy7wMjZZDhAcPlRr8VWLyVSS382qrLuq_WoruRpU3ZKP6rDt2CPPUNZMlRaIEBM8oSPhKgPnqAFOA6zq1j5BF4m35Ignmy1qONB_Io1M9KBPST0EIkrWrnZydC0mieoJmcqF2FqOjsj9ExlITAIwcuLZKL51JaTdLLzHRDZaxhPAdNWzQROTqAzG_ycKbrfAyMlPeksUWl9duDX-ZFFKzRYQ2MtuO5IEVG7MY')}
            className="group relative flex flex-col gap-3 rounded-xl p-3 transition-all duration-300 glass-panel hover:bg-white/10 hover:-translate-y-0.5 cursor-pointer"
        >
           <div className="relative aspect-[2/3] w-full overflow-hidden rounded-lg bg-gray-800 shadow-md">
              <div 
                className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-110" 
                style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuCfiOnuSU03lAssHkL9Pk67gxh-aQXuxzds5tvWpBDy7wMjZZDhAcPlRr8VWLyVSS382qrLuq_WoruRpU3ZKP6rDt2CPPUNZMlRaIEBM8oSPhKgPnqAFOA6zq1j5BF4m35Ignmy1qONB_Io1M9KBPST0EIkrWrnZydC0mieoJmcqF2FqOjsj9ExlITAIwcuLZKL51JaTdLLzHRDZaxhPAdNWzQROTqAzG_ycKbrfAyMlPeksUWl9duDX-ZFFKzRYQ2MtuO5IEVG7MY")' }}
              ></div>
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
           </div>
           <div className="flex flex-col gap-1">
              <h3 className="truncate text-base font-bold text-white group-hover:text-primary transition-colors">Mushoku Tensei</h3>
              <div className="flex items-center justify-between text-xs">
                 <span className="text-gray-400">Vol 26</span>
              </div>
           </div>
        </div>

        {/* Standard Card 3 */}
        <div 
            onClick={() => onSelectBook && onSelectBook('Overlord', 'Kugane Maruyama', 'https://lh3.googleusercontent.com/aida-public/AB6AXuCKNIZwQN3zeokE87YW_n3IPKpm3nUgRIXkNX-3OHx-fOLRO_rZErpdu7PPDE3lpKhqeTagdxkjLnZBChqx9WYKJBwk34EnqhYHb51ga6GV_pJidZmngMNiS30D_fDpbmjtxOpIjv5oyQrbJ1uvhZOUSAOTpAwV4g6DyIZ8HUh1twTCboRzi8BX3TRTQbP5gq_FcvNidtO4ntNm05XZFesAF7_eV7ZyVCIcJKXph7cISdNUSt5Iy4-3yqSM2i7iwHMV6Djfd4SxifY')}
            className="group relative flex flex-col gap-3 rounded-xl p-3 transition-all duration-300 glass-panel hover:bg-white/10 hover:-translate-y-0.5 cursor-pointer"
        >
           <div className="relative aspect-[2/3] w-full overflow-hidden rounded-lg bg-gray-800 shadow-md">
              <div 
                className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-110" 
                style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuCKNIZwQN3zeokE87YW_n3IPKpm3nUgRIXkNX-3OHx-fOLRO_rZErpdu7PPDE3lpKhqeTagdxkjLnZBChqx9WYKJBwk34EnqhYHb51ga6GV_pJidZmngMNiS30D_fDpbmjtxOpIjv5oyQrbJ1uvhZOUSAOTpAwV4g6DyIZ8HUh1twTCboRzi8BX3TRTQbP5gq_FcvNidtO4ntNm05XZFesAF7_eV7ZyVCIcJKXph7cISdNUSt5Iy4-3yqSM2i7iwHMV6Djfd4SxifY")' }}
              ></div>
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
           </div>
           <div className="flex flex-col gap-1">
              <h3 className="truncate text-base font-bold text-white group-hover:text-primary transition-colors">Overlord</h3>
              <div className="flex items-center justify-between text-xs">
                 <span className="text-gray-400">Vol 16</span>
              </div>
           </div>
        </div>

        {/* Standard Card 4 */}
        <div 
            onClick={() => onSelectBook && onSelectBook('Slime Isekai', 'Fuse', 'https://lh3.googleusercontent.com/aida-public/AB6AXuAEH5pFFmH_qC2YnQFl6ycA962y11h1tzGNDS9Ke5lyI5uoAG3-n4_W0HFRt9y8BCx7KcD3JMemxEttvm58KFcwlX7GsGcPH1Jg5_HMVKggU578SReEnal9deMDGnvaRK_LrPEP0kHg4I3gttm_aCynHmzo9hGq0s7gxTVyu6Xad5OWjikUVTVWsVWwCzvfNKCux0hI5Ygv5cLnc9dleS5WxB5ghaDIYNkz5q6-fbMteTXgNN3Ptgu18mwJTYM7bRfLN5Mvv4NsSM0')}
            className="group relative flex flex-col gap-3 rounded-xl p-3 transition-all duration-300 glass-panel hover:bg-white/10 hover:-translate-y-0.5 cursor-pointer"
        >
           <div className="relative aspect-[2/3] w-full overflow-hidden rounded-lg bg-gray-800 shadow-md">
              <div 
                className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-110" 
                style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuAEH5pFFmH_qC2YnQFl6ycA962y11h1tzGNDS9Ke5lyI5uoAG3-n4_W0HFRt9y8BCx7KcD3JMemxEttvm58KFcwlX7GsGcPH1Jg5_HMVKggU578SReEnal9deMDGnvaRK_LrPEP0kHg4I3gttm_aCynHmzo9hGq0s7gxTVyu6Xad5OWjikUVTVWsVWwCzvfNKCux0hI5Ygv5cLnc9dleS5WxB5ghaDIYNkz5q6-fbMteTXgNN3Ptgu18mwJTYM7bRfLN5Mvv4NsSM0")' }}
              ></div>
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
           </div>
           <div className="flex flex-col gap-1">
              <h3 className="truncate text-base font-bold text-white group-hover:text-primary transition-colors">Slime Isekai</h3>
              <div className="flex items-center justify-between text-xs">
                 <span className="text-gray-400">Vol 21</span>
              </div>
           </div>
        </div>

        {/* Standard Card 5 */}
        <div 
            onClick={() => onSelectBook && onSelectBook('Ascendance of Bookworm', 'Miya Kazuki', 'https://lh3.googleusercontent.com/aida-public/AB6AXuBhhAc828PEvGhsWOq-OVw_UphG1nC9uKyj72NYJp9XFzhZpQqvhFEyR7MM58oPNd9JSOQjFu173G5JCD7Aoioj1jmUQ6KvBJsunvMzQWacM748PiT494Y6MN0TS-IWEn6r4AlilDwT70TeEt7bOn7Brws4eJ-bkcD02w0WpaP8Rx1p46OjYEffz9bPTAQvNrKUAyQS17jVHfEV8uXwTtzF2zEArhl6UzpJCoL_OLRS_eC9G_yhLeUTgW3MpoNzZRG-RAkJEpQi2uU')}
            className="group relative flex flex-col gap-3 rounded-xl p-3 transition-all duration-300 glass-panel hover:bg-white/10 hover:-translate-y-0.5 cursor-pointer"
        >
           <div className="relative aspect-[2/3] w-full overflow-hidden rounded-lg bg-gray-800 shadow-md">
              <div 
                className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-110" 
                style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBhhAc828PEvGhsWOq-OVw_UphG1nC9uKyj72NYJp9XFzhZpQqvhFEyR7MM58oPNd9JSOQjFu173G5JCD7Aoioj1jmUQ6KvBJsunvMzQWacM748PiT494Y6MN0TS-IWEn6r4AlilDwT70TeEt7bOn7Brws4eJ-bkcD02w0WpaP8Rx1p46OjYEffz9bPTAQvNrKUAyQS17jVHfEV8uXwTtzF2zEArhl6UzpJCoL_OLRS_eC9G_yhLeUTgW3MpoNzZRG-RAkJEpQi2uU")' }}
              ></div>
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
           </div>
           <div className="flex flex-col gap-1">
              <h3 className="truncate text-base font-bold text-white group-hover:text-primary transition-colors">Ascendance of Bookworm</h3>
              <div className="flex items-center justify-between text-xs">
                 <span className="text-gray-400">Part 5 Vol 7</span>
              </div>
           </div>
        </div>

      </div>

      {/* Floating Bottom Action Bar (Same style as Catalog) */}
      <div className="md:hidden fixed bottom-6 left-4 right-4 z-40 animate-in slide-in-from-bottom-4 duration-300">
        <div className="glass-panel rounded-full p-1 border border-white/10 shadow-2xl bg-[#0f1115]/90 backdrop-blur-md flex items-center justify-between">
            {/* Home/Back */}
            <button 
              onClick={() => onNavigate && onNavigate('dashboard')}
              className="flex-1 flex flex-col items-center justify-center py-2.5 px-2 rounded-l-full hover:bg-white/5 active:bg-white/10 transition-colors group text-gray-400 active:text-white"
            >
              <Home className="w-4 h-4 mb-0.5 group-active:-translate-y-1 transition-transform" />
              <span className="text-[9px] font-black uppercase tracking-widest">Inicio</span>
            </button>
            
            <div className="w-px h-8 bg-white/5"></div>

            {/* Sort Toggle */}
            <button 
              className="flex-1 flex flex-col items-center justify-center py-2.5 px-2 hover:bg-white/5 transition-colors group relative text-gray-300"
            >
              <ArrowDownUp className="w-4 h-4 mb-0.5" />
              <span className="text-[9px] font-black uppercase tracking-widest">Ordenar</span>
            </button>
            
            <div className="w-px h-8 bg-white/5"></div>

            {/* Filter Toggle */}
            <button 
              className="flex-1 flex flex-col items-center justify-center py-2.5 px-2 rounded-r-full hover:bg-white/5 active:bg-white/10 transition-colors group text-gray-400 active:text-white"
            >
              <Filter className="w-4 h-4 mb-0.5" />
              <span className="text-[9px] font-black uppercase tracking-widest">Filtrar</span>
            </button>
        </div>
      </div>

    </div>
  );
};