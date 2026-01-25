import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import {
   Bell,
   Send,
   SlidersHorizontal,
   Home,
   ArrowDownUp,
   Filter,
   ArrowUp,
   Star,
   Calendar,
   Clock,
   Download
} from 'lucide-react';
import { preloadImages } from '../src/utils/imagePreloader';

interface LibraryProps {
   onNavigate?: (tab: string) => void;
   onSelectBook?: (title: string, author: string, cover: string) => void;
}

export const Library: React.FC<LibraryProps> = ({ onNavigate, onSelectBook }) => {
   const { settings } = useTheme();
   const [isSortMenuOpen, setIsSortMenuOpen] = React.useState(false);
   const [activeSort, setActiveSort] = React.useState('a-z');

   const sortOptions = [
      { id: 'a-z', label: 'A-Z', icon: ArrowUp },
      { id: 'z-a', label: 'Z-A', icon: ArrowUp },
      { id: 'downloads', label: 'DESCARGAS', icon: Download },
      { id: 'rating', label: 'VALORACIÓN', icon: Star },
      { id: 'added', label: 'AÑADIDO', icon: Calendar },
      { id: 'updated', label: 'ACTUALIZADO', icon: Clock },
   ];

   const initialBooks = [
      { id: 1, title: 'Arifureta', author: 'Ryo Shirakome', vol: '13', time: 'Hace poco', cover: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCIAvtXCCRr1DdCjOnabIOkCW2Sp6NMP7ps9Nh9nuV_k-OPfIhoftkSihrTpVchLKRuoFU4fRS-wUvbfri_69LtYsT6-OiNoRKy2vpTL4abAb84gdP0HT-3nw27q294CKcSeM9qQ98RACjZTquO0jZlaRhjPg8Lk-_7cLPYgI-OKPyYEHezSVpxxow6kOLq5uc_BAk1vaqzt-vfqIRvpYIUnbhZBhoCNa4VIHVA6O00lJYYKX6MHmmspDSauVh0OBzSKb_jjxO3Y6I', isNew: true, updated: true },
      { id: 2, title: 'Mushoku Tensei', author: 'Rifujin na Magonote', vol: '26', time: 'Ayer', cover: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCfiOnuSU03lAssHkL9Pk67gxh-aQXuxzds5tvWpBDy7wMjZZDhAcPlRr8VWLyVSS382qrLuq_WoruRpU3ZKP6rDt2CPPUNZMlRaIEBM8oSPhKgPnqAFOA6zq1j5BF4m35Ignmy1qONB_Io1M9KBPST0EIkrWrnZydC0mieoJmcqF2FqOjsj9ExlITAIwcuLZKL51JaTdLLzHRDZaxhPAdNWzQROTqAzG_ycKbrfAyMlPeksUWl9duDX-ZFFKzRYQ2MtuO5IEVG7MY', isNew: false, updated: false },
      { id: 3, title: 'Overlord', author: 'Kugane Maruyama', vol: '16', time: '3 días', cover: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCKNIZwQN3zeokE87YW_n3IPKpm3nUgRIXkNX-3OHx-fOLRO_rZErpdu7PPDE3lpKhqeTagdxkjLnZBChqx9WYKJBwk34EnqhYHb51ga6GV_pJidZmngMNiS30D_fDpbmjtxOpIjv5oyQrbJ1uvhZOUSAOTpAwV4g6DyIZ8HUh1twTCboRzi8BX3TRTQbP5gq_FcvNidtO4ntNm05XZFesAF7_eV7ZyVCIcJKXph7cISdNUSt5Iy4-3yqSM2i7iwHMV6Djfd4SxifY', isNew: false, updated: false },
      { id: 4, title: 'Slime Isekai', author: 'Fuse', vol: '21', time: '1 semana', cover: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAEH5pFFmH_qC2YnQFl6ycA962y11h1tzGNDS9Ke5lyI5uoAG3-n4_W0HFRt9y8BCx7KcD3JMemxEttvm58KFcwlX7GsGcPH1Jg5_HMVKggU578SReEnal9deMDGnvaRK_LrPEP0kHg4I3gttm_aCynHmzo9hGq0s7gxTVyu6Xad5OWjikUVTVWsVWwCzvfNKCux0hI5Ygv5cLnc9dleS5WxB5ghaDIYNkz5q6-fbMteTXgNN3Ptgu18mwJTYM7bRfLN5Mvv4NsSM0', isNew: false, updated: false },
      { id: 5, title: 'Ascendance of Bookworm', author: 'Miya Kazuki', vol: 'P5 V7', time: '2 semanas', cover: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBhhAc828PEvGhsWOq-OVw_UphG1nC9uKyj72NYJp9XFzhZpQqvhFEyR7MM58oPNd9JSOQjFu173G5JCD7Aoioj1jmUQ6KvBJsunvMzQWacM748PiT494Y6MN0TS-IWEn6r4AlilDwT70TeEt7bOn7Brws4eJ-bkcD02w0WpaP8Rx1p46OjYEffz9bPTAQvNrKUAyQS17jVHfEV8uXwTtzF2zEArhl6UzpJCoL_OLRS_eC9G_yhLeUTgW3MpoNzZRG-RAkJEpQi2uU', isNew: false, updated: false },
   ];

   const sortedBooks = React.useMemo(() => {
      const sorted = [...initialBooks];
      if (activeSort === 'a-z') return sorted.sort((a, b) => (a.title || '').localeCompare(b.title || '', undefined, { numeric: true, sensitivity: 'base' }));
      if (activeSort === 'z-a') return sorted.sort((a, b) => (b.title || '').localeCompare(a.title || '', undefined, { numeric: true, sensitivity: 'base' }));
      return sorted;
   }, [activeSort]);

   React.useEffect(() => {
      preloadImages(initialBooks.map(b => b.cover));
   }, []);

   return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 animate-in fade-in duration-500 pb-28">

         {/* Page Header */}
         <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between mb-12">
            <div>
               <h1 className="text-5xl font-black tracking-tighter text-white mb-3">Mi Biblioteca</h1>
               <p className="text-gray-500 font-medium tracking-wide">Gestiona tu colección y sigue tus lecturas.</p>
            </div>
            {/* Filter Chips */}
            <div className="flex flex-wrap gap-2">
               <button className="h-10 px-6 rounded-full bg-primary text-white text-[11px] font-black uppercase tracking-[0.2em] shadow-[0_10px_20px_-5px_rgba(var(--color-primary-rgb),0.5)] active:scale-95 transition-all">
                  Todas
               </button>
               <button className="h-10 px-6 rounded-full bg-white/[0.03] border border-white/5 hover:bg-white/10 text-gray-400 hover:text-white text-[11px] font-black uppercase tracking-[0.2em] transition-all flex items-center gap-3">
                  Actualizadas
                  <span className="flex h-5 w-5 items-center justify-center rounded-lg bg-primary text-[9px] font-black text-white shadow-lg">1</span>
               </button>
               <button className="h-10 px-6 rounded-full bg-white/[0.03] border border-white/5 hover:bg-white/10 text-gray-400 hover:text-white text-[11px] font-black uppercase tracking-[0.2em] transition-all">
                  Completadas
               </button>
            </div>
         </div>

         {/* Grid Section */}
         <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 mb-12">
            {sortedBooks.map((book) => (
               <div
                  key={book.id}
                  onClick={() => onSelectBook && onSelectBook(book.title, book.author, book.cover)}
                  className={`group relative flex flex-col gap-4 rounded-[2.5rem] p-4 transition-all duration-700 glass-panel hover:bg-white/[0.08] hover:border-primary/40 hover:-translate-y-2 cursor-pointer shadow-premium ${book.isNew ? 'border-primary/30 ring-1 ring-primary/20' : ''}`}
               >
                  {/* Status Badges */}
                  <div className="absolute top-6 right-6 z-20 flex flex-col gap-2">
                     {book.isNew && (
                        <div className="bg-primary text-white px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest shadow-xl animate-pulse">
                           Nuevo
                        </div>
                     )}
                     {book.updated && (
                        <div className="bg-emerald-500 text-white px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest shadow-xl">
                           Upd
                        </div>
                     )}
                  </div>

                  {/* Image Container */}
                  <div className="relative aspect-[2/3] w-full overflow-hidden rounded-[1.75rem] bg-white/5 shadow-2xl border border-white/10">
                     <div
                        className="absolute inset-0 bg-cover bg-center transition-all duration-1000 group-hover:scale-110 grayscale-[30%] group-hover:grayscale-0"
                        style={{ backgroundImage: `url("${book.cover}")` }}
                     ></div>

                     {/* Modern Multi-Layer Gradient */}
                     <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black via-black/40 to-transparent"></div>

                     {/* Pulsing Notification */}
                     {book.updated && (
                        <div className="absolute bottom-4 left-4 flex items-center gap-2">
                           <div className="relative flex h-3 w-3">
                              <div className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></div>
                              <div className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></div>
                           </div>
                           <span className="text-[10px] font-black text-white uppercase tracking-[0.2em] drop-shadow-md">Updated</span>
                        </div>
                     )}
                  </div>

                  {/* Content */}
                  <div className="flex flex-col gap-1 px-1">
                     <h3 className="truncate text-[15px] font-black text-white group-hover:text-primary transition-colors tracking-tight">{book.title}</h3>
                     <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-gray-500">
                        <span>Vol {book.vol}</span>
                        <span className="opacity-50">{book.time}</span>
                     </div>
                  </div>

                  {/* Hover Accent Glow */}
                  <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
               </div>
            ))}
         </div>

         {/* Floating Bottom Action Bar (Same style as Catalog) */}
         <div className="md:hidden fixed bottom-6 left-8 right-8 z-40 animate-in slide-in-from-bottom-4 duration-300 flex flex-col gap-3 max-w-5xl mx-auto">
            {isSortMenuOpen && (
               <div
                  className="glass-panel rounded-3xl p-3 border border-white/10 shadow-2xl animate-in slide-in-from-bottom-2 fade-in duration-200"
                  style={{
                     background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                     backdropFilter: `blur(${settings.glassBlur}px)`,
                     WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
                  }}
               >
                  <div className="grid grid-cols-3 gap-2">
                     {sortOptions.map((option) => {
                        const isActive = activeSort === option.id;
                        return (
                           <button
                              key={option.id}
                              onClick={() => {
                                 setActiveSort(option.id);
                                 setIsSortMenuOpen(false);
                              }}
                              className={`flex flex-col items-center gap-1 px-2 py-2.5 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all border ${isActive
                                 ? 'bg-primary text-white border-primary shadow-lg shadow-blue-500/20'
                                 : 'bg-white/5 text-gray-400 border-transparent hover:bg-white/10 hover:text-white'
                                 }`}
                           >
                              {option.icon && <option.icon className={`w-4 h-4 ${option.id === 'z-a' ? 'rotate-180' : ''}`} />}
                              <span className="text-center leading-tight">{option.label}</span>
                           </button>
                        );
                     })}
                  </div>
               </div>
            )}

            <div
               className="glass-panel rounded-3xl p-1 border border-black/10 dark:border-white/10 shadow-2xl flex items-center justify-between overflow-hidden"
               style={{
                  background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                  backdropFilter: `blur(${settings.glassBlur}px)`,
                  WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
               }}
            >
               {/* Home/Back */}
               <button
                  onClick={() => onNavigate && onNavigate('dashboard')}
                  className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 text-gray-500 hover:text-black dark:hover:text-white"
               >
                  <div className="p-1.5 rounded-full transition-all duration-300">
                     <Home className="w-4 h-4" strokeWidth={2} />
                  </div>
                  <span className="text-[9px] font-black uppercase tracking-widest mt-1">Inicio</span>
               </button>

               <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

               {/* Sort Toggle */}
               <button
                  onClick={() => setIsSortMenuOpen(!isSortMenuOpen)}
                  className={`flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 relative z-10 ${isSortMenuOpen ? 'text-black dark:text-white' : 'text-gray-500 hover:text-black dark:hover:text-white'}`}
               >
                  <div className={`p-1.5 rounded-full transition-all duration-300 ${isSortMenuOpen ? 'bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)] translate-y-[-2px]' : ''}`}>
                     <ArrowDownUp className={`w-4 h-4 ${isSortMenuOpen ? 'text-white' : ''}`} strokeWidth={isSortMenuOpen ? 2.5 : 2} />
                  </div>
                  <span className="text-[9px] font-black uppercase tracking-widest mt-1">Ordenar</span>
               </button>

               <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

               {/* Filter Toggle */}
               <button
                  className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 text-gray-500 hover:text-black dark:hover:text-white"
               >
                  <div className="p-1.5 rounded-full transition-all duration-300">
                     <Filter className="w-4 h-4" strokeWidth={2} />
                  </div>
                  <span className="text-[9px] font-black uppercase tracking-widest mt-1">Filtrar</span>
               </button>
            </div>
         </div>

      </div>
   );
};