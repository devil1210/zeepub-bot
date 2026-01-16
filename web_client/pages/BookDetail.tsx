import React, { useState } from 'react';
import { 
  ArrowLeft, 
  Share2, 
  Flag,
  Calendar,
  Hash,
  User,
  ArrowDownToLine,
  Tag,
  Info,
  Library,
  FileText,
  Clock,
  Database,
  PenTool,
  Languages,
  FileBox,
  Layers,
  BookOpen,
  Globe,
  Star,
  Download,
  Home,
  Reply,
  Check
} from 'lucide-react';
import { Volume, Series } from '../types';
import { ReportIssueModal } from '../components/ReportIssueModal';

interface BookDetailProps {
  volume: Volume;
  series: Series;
  onBack: () => void;
  onSearch?: (term: string, type?: string) => void;
  onNavigate?: (tab: string) => void;
}

export const BookDetail: React.FC<BookDetailProps> = ({ volume, series, onBack, onSearch, onNavigate }) => {
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [hasDownloaded, setHasDownloaded] = useState(false);

  // Helper to handle safe search navigation
  const handleSearch = (term?: string, type?: string) => {
    if (term && onSearch) {
      onSearch(term, type);
    }
  };

  const handleDownload = () => {
    // Simulate download process
    setHasDownloaded(true);
  };

  // Fallback data if fields are missing (mocking for display purposes based on screenshots)
  const displayData = {
    ...volume,
    romajiTitle: volume.romajiTitle || 'Byōsoku Go Senchimētoru + Hoshi wo Ou Kodomo',
    language: volume.language || 'Español',
    size: volume.size || '4.29 MB',
    format: volume.format || 'Epub',
    epubVersion: volume.epubVersion || '3.0',
    uploader: volume.uploader || 'ZeepubAdmin',
    wordCount: volume.wordCount || 68082,
    pages: volume.pages || 226,
    readTime: volume.readTime || '340 min / 5.7 horas',
    lastUpdated: '27/11/2025',
    downloadCount: volume.downloadCount || 4,
    description: volume.description || `5 Centímetros por Segundo: Cuando Takaki conoce a Akari en la escuela primaria, son tan amigos como los ladrones. Ella siempre le enseña las cosas importantes, mientras que él hace lo posible por protegerla. Sin embargo, cuando se separan en la escuela secundaria, tienen que encontrar su camino en la vida sin el otro... El director Makoto Shinkai describe con delicadeza los paisajes internos de sus personajes a través de tres capítulos de la vida de un chico. Niños que Persiguen Voces Perdidas: Asuna es una chica tranquila y tímida que vive en la ciudad montañosa de Mizunofuchi. Un día conoce a Shun, un chico que dice ser de una tierra mítica conocida como Agartha. Sin embargo, justo cuando empieza a formarse un vínculo entre ellos, Shun desaparece. Mientras Asuna desea volver a verlo, se encuentra con Shin, otro chico que se parece a Shun, y con Morisaki, un profesor que busca Agartha. Los tres parten hacia el legendario país, cada uno con su propio objetivo y sus propias lecciones que aprender en el camino.`,
    demography: volume.demography || ['MADURO', 'ADULTOS/SEINEN'],
    genres: ['Drama', 'Romance', 'Recuentos de la vida'],
    illustrator: volume.illustrator || 'Asahi Akisaka',
    translator: volume.translator || 'Traductor',
    group: volume.group || 'Grupo Traductor',
    typesetter: volume.typesetter || 'Resan', // Maquetador
    isbn: volume.isbn || '978-19-7531-569-6',
    asin: volume.asin || 'B08R3GGRWW'
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 relative font-sans text-gray-900 dark:text-gray-100 bg-transparent">
       <ReportIssueModal isOpen={isReportModalOpen} onClose={() => setIsReportModalOpen(false)} />

       {/* Navbar for Mobile */}
       <header className="md:hidden h-16 bg-white/80 dark:bg-background/90 backdrop-blur border-b border-black/5 dark:border-white/10 flex items-center justify-between px-4 shrink-0 sticky top-0 z-40">
        <button onClick={onBack} className="text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white transition-colors">
          <ArrowLeft className="w-6 h-6" />
        </button>
        <span className="font-bold text-sm text-gray-900 dark:text-gray-200 truncate max-w-[200px]">{displayData.title}</span>
        <button onClick={() => setIsReportModalOpen(true)} className="text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors">
          <Flag className="w-5 h-5" />
        </button>
      </header>

      {/* Desktop Back Button */}
      <div className="hidden md:flex pt-6 px-8 max-w-7xl mx-auto w-full">
          <button onClick={onBack} className="flex items-center gap-2 text-gray-500 dark:text-gray-400 hover:text-black dark:hover:text-white transition-colors group">
            <div className="p-2 rounded-full bg-black/5 dark:bg-white/5 group-hover:bg-black/10 dark:group-hover:bg-white/10 transition-colors">
               <ArrowLeft className="w-5 h-5" />
            </div>
            <span className="text-sm font-bold uppercase tracking-widest">Volver</span>
          </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto pb-32 md:pb-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
            
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">
                
                {/* LEFT COLUMN: Cover & Actions */}
                <div className="lg:col-span-4 xl:col-span-3 flex flex-col gap-6">
                    {/* Cover Wrapper */}
                    <div className="relative w-[70%] sm:w-[60%] lg:w-full mx-auto lg:mx-0">
                         <div className="aspect-[2/3] rounded-xl overflow-hidden shadow-[0_10px_30px_rgba(0,0,0,0.2)] dark:shadow-[0_20px_50px_rgba(0,0,0,0.5)] ring-1 ring-black/5 dark:ring-white/10 relative group">
                            <img src={displayData.coverUrl} alt={displayData.title} className="w-full h-full object-cover" />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
                         </div>
                    </div>

                     {/* Actions (Desktop mainly) */}
                     <div className="hidden md:flex flex-col gap-3">
                        <button 
                            onClick={handleDownload}
                            className={`w-full py-3.5 text-white text-sm font-black uppercase tracking-widest rounded-xl shadow-lg transition-all transform active:scale-95 flex items-center justify-center gap-2 ${hasDownloaded ? 'bg-green-600 hover:bg-green-700 shadow-green-500/20' : 'bg-[#2AABEE] hover:bg-[#2AABEE]/90 shadow-blue-500/20'}`}
                        >
                            {hasDownloaded ? (
                                <>
                                    <Check className="w-5 h-5" />
                                    Descargado
                                </>
                            ) : (
                                <>
                                    <ArrowDownToLine className="w-5 h-5" />
                                    Descargar
                                </>
                            )}
                        </button>
                        <div className="grid grid-cols-2 gap-3">
                           <button className="py-3.5 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-white rounded-xl border border-black/5 dark:border-white/10 transition-colors flex items-center justify-center gap-2 text-xs font-bold uppercase tracking-wider">
                                <Share2 className="w-4 h-4" />
                                Compartir
                           </button>
                           <button onClick={() => setIsReportModalOpen(true)} className="py-3.5 bg-red-50 dark:bg-red-500/10 hover:bg-red-100 dark:hover:bg-red-500/20 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 rounded-xl border border-red-200 dark:border-red-500/20 transition-colors flex items-center justify-center gap-2 text-xs font-bold uppercase tracking-wider">
                                <Flag className="w-4 h-4" />
                                Reportar
                           </button>
                        </div>
                     </div>
                     
                     {/* Mobile Inline Actions */}
                     <div className="md:hidden flex gap-3">
                        <button className="flex-1 py-3 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-white rounded-xl border border-black/5 dark:border-white/10 transition-colors flex items-center justify-center gap-2 text-xs font-bold uppercase tracking-wider">
                             <Share2 className="w-4 h-4" />
                             Compartir
                        </button>
                     </div>

                     {/* Extra Info visible in sidebar (Desktop) */}
                     <div className="hidden md:block glass-panel p-4 rounded-xl border border-black/5 dark:border-white/5 space-y-4 bg-white/50 dark:bg-transparent">
                        
                        {/* Rating Block */}
                        <div className="flex items-center justify-between pb-3 border-b border-black/5 dark:border-white/5">
                            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Valoración</span>
                            <div className="flex items-center gap-1.5 text-yellow-500">
                                <Star className="w-4 h-4 fill-current" />
                                <span className="text-gray-900 dark:text-white font-bold">{displayData.rating || 4.7}</span>
                            </div>
                        </div>

                        {/* Download Block */}
                        <div className="flex items-center justify-between pb-3 border-b border-black/5 dark:border-white/5">
                           <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Descargas Totales</span>
                           <div className="flex items-center gap-1.5 text-[#2AABEE]">
                                <Download className="w-4 h-4" />
                                <span className="text-gray-900 dark:text-white font-bold">{displayData.downloadCount}</span>
                           </div>
                        </div>

                        {/* Updated Block */}
                        <div className="flex items-center justify-between text-xs font-medium text-gray-500 dark:text-gray-400">
                           <span>Última Actualización</span>
                           <span className="text-gray-900 dark:text-white font-bold">{displayData.lastUpdated}</span>
                        </div>
                     </div>
                </div>

                {/* RIGHT COLUMN: Content */}
                <div className="lg:col-span-8 xl:col-span-9 flex flex-col gap-6">
                    
                    {/* Header Info */}
                    <div>
                         {/* Group/Translator Badges - CLICKABLE */}
                        <div className="mb-4 flex flex-wrap items-center gap-2 text-[10px] font-black uppercase tracking-wider">
                            <button 
                                onClick={() => handleSearch(displayData.group, 'group')}
                                className="bg-[#2AABEE]/10 text-[#2AABEE] border border-[#2AABEE]/20 px-2 py-1 rounded-md hover:bg-[#2AABEE] hover:text-white transition-colors cursor-pointer"
                            >
                                {displayData.group}
                            </button>
                            <span className="text-gray-400 dark:text-gray-600 px-1">/</span>
                            <button 
                                onClick={() => handleSearch(displayData.translator, 'translator')}
                                className="bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-400 border border-black/5 dark:border-white/10 px-2 py-1 rounded-md hover:bg-gray-200 dark:hover:bg-white/10 hover:text-black dark:hover:text-white transition-colors cursor-pointer"
                            >
                                {displayData.translator}
                            </button>
                        </div>

                        <h1 className="text-2xl sm:text-3xl lg:text-5xl font-extrabold text-gray-900 dark:text-white leading-tight mb-2">
                            {displayData.title}
                        </h1>
                        <h2 className="text-sm sm:text-lg text-gray-500 dark:text-gray-400 italic font-serif mb-6 leading-relaxed">
                            {displayData.romajiTitle}
                        </h2>

                        {/* Author/Stats Row - CLICKABLE */}
                        <div className="flex flex-wrap items-center gap-x-6 gap-y-3 text-sm text-gray-600 dark:text-gray-400 border-b border-black/5 dark:border-white/5 pb-6 mb-2">
                             <button onClick={() => handleSearch(series.author, 'author')} className="flex items-center gap-2 text-gray-900 dark:text-white group">
                                <User className="w-4 h-4 text-[#2AABEE] group-hover:scale-110 transition-transform" />
                                <span className="font-bold group-hover:underline cursor-pointer group-hover:text-[#2AABEE] transition-colors">{series.author}</span>
                             </button>
                             
                             {/* Added Rating & Downloads here for visibility on Mobile */}
                             <div className="flex items-center gap-1.5 text-yellow-500">
                                <Star className="w-4 h-4 fill-current" />
                                <span className="text-gray-900 dark:text-white font-bold">{displayData.rating || 4.7}</span>
                            </div>
                            <div className="flex items-center gap-1.5 text-[#2AABEE]">
                                <Download className="w-4 h-4" />
                                <span className="text-gray-900 dark:text-white font-bold">{displayData.downloadCount}</span>
                           </div>

                             <button onClick={() => handleSearch(displayData.illustrator, 'illustrator')} className="flex items-center gap-2 group hover:text-black dark:hover:text-gray-200 transition-colors">
                                <PenTool className="w-4 h-4" />
                                <span>{displayData.illustrator}</span>
                             </button>
                             <div className="flex items-center gap-2">
                                <Hash className="w-4 h-4" />
                                <span>{volume.volumeNumber > 0 ? `Volumen ${volume.volumeNumber}` : 'Volumen Único'}</span>
                             </div>
                             <div className="flex items-center gap-2">
                                <Calendar className="w-4 h-4" />
                                <span>{volume.publishedDate}</span>
                             </div>
                        </div>
                    </div>

                    {/* Genres & Tags - CLICKABLE */}
                     <div className="flex flex-wrap gap-2">
                        {displayData.demography.map((tag) => (
                          <button 
                            key={tag} 
                            onClick={() => handleSearch(tag, 'demography')}
                            className="px-3 py-1.5 rounded-lg bg-[#004d40] text-[#4db6ac] border border-[#00695c] text-[10px] font-black uppercase tracking-wider shadow-sm hover:bg-[#00695c] hover:text-white transition-colors"
                          >
                            {tag}
                          </button>
                        ))}
                        {displayData.genres.map((genre) => (
                           <button 
                             key={genre} 
                             onClick={() => handleSearch(genre, 'genre')}
                             className="px-3 py-1.5 rounded-lg bg-gray-200 dark:bg-[#1f2937] text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-[#374151] text-[10px] font-bold uppercase tracking-wider hover:bg-gray-300 dark:hover:bg-[#374151] hover:text-black dark:hover:text-white hover:border-gray-400 dark:hover:border-gray-500 transition-colors cursor-pointer"
                           >
                             {genre}
                           </button>
                        ))}
                     </div>

                    {/* Synopsis */}
                    <div className="glass-panel border border-black/5 dark:border-white/5 bg-white/50 dark:bg-transparent rounded-2xl p-6 lg:p-8 shadow-sm dark:shadow-xl">
                        <div className="flex items-center gap-2 mb-4 text-[#2AABEE]">
                            <FileText className="w-5 h-5" />
                            <h3 className="text-xs font-black uppercase tracking-widest">Sinopsis</h3>
                        </div>
                        <p className="text-gray-700 dark:text-gray-300 text-sm sm:text-base leading-7 sm:leading-8 whitespace-pre-line font-medium text-justify">
                            {displayData.description}
                        </p>
                    </div>

                    {/* Two Column Details Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                         {/* Book Details */}
                        <div className="glass-panel border border-black/5 dark:border-white/5 bg-white/50 dark:bg-transparent rounded-2xl p-6 shadow-sm dark:shadow-xl h-full">
                             <div className="flex items-center gap-2 mb-6 text-[#2AABEE]">
                                <Library className="w-5 h-5" />
                                <h3 className="text-xs font-black uppercase tracking-widest">Detalles del Libro</h3>
                             </div>
                             <div className="space-y-0.5">
                                {[
                                  { label: 'Serie', value: series.title, highlight: true, clickable: true, type: 'series' },
                                  { label: 'Volumen', value: `${volume.volumeNumber} (Único)` },
                                  { label: 'ISBN', value: displayData.isbn, highlight: true, font: 'mono' },
                                  { label: 'ASIN', value: displayData.asin, highlight: true, font: 'mono' },
                                  { label: 'Grupo', value: displayData.group, color: 'text-[#2AABEE]', clickable: true, type: 'group' },
                                  { label: 'Maquetador', value: displayData.typesetter, highlight: true, clickable: true, type: 'typesetter' },
                                ].map((item, idx) => (
                                   <div key={idx} className="flex justify-between py-3 border-b border-black/5 dark:border-white/5 last:border-0 hover:bg-black/5 dark:hover:bg-white/[0.02] px-2 -mx-2 rounded transition-colors">
                                      <span className="text-sm text-gray-500 font-medium">{item.label}</span>
                                      {item.clickable ? (
                                         <button 
                                            onClick={() => handleSearch(String(item.value), item.type)}
                                            className={`text-sm text-right ${item.color || (item.highlight ? 'text-gray-900 dark:text-gray-200 font-bold' : 'text-gray-600 dark:text-gray-400')} ${item.font === 'mono' ? 'font-mono' : ''} truncate max-w-[200px] hover:underline hover:text-primary transition-colors`}
                                         >
                                            {item.value}
                                         </button>
                                      ) : (
                                        <span className={`text-sm text-right ${item.color || (item.highlight ? 'text-gray-900 dark:text-gray-200 font-bold' : 'text-gray-600 dark:text-gray-400')} ${item.font === 'mono' ? 'font-mono' : ''} truncate max-w-[200px]`}>
                                            {item.value}
                                        </span>
                                      )}
                                   </div>
                                ))}
                             </div>
                        </div>

                         {/* Tech Specs */}
                         <div className="glass-panel border border-black/5 dark:border-white/5 bg-white/50 dark:bg-transparent rounded-2xl p-6 shadow-sm dark:shadow-xl h-full">
                             <div className="flex items-center gap-2 mb-6 text-[#2AABEE]">
                                <Database className="w-5 h-5" />
                                <h3 className="text-xs font-black uppercase tracking-widest">Ficha Técnica</h3>
                             </div>
                             <div className="space-y-0.5">
                                {[
                                  { label: 'Formato', value: displayData.format, highlight: true },
                                  { label: 'Versión Epub', value: `v${displayData.epubVersion}` },
                                  { label: 'Idioma', value: displayData.language },
                                  { label: 'Palabras', value: displayData.wordCount.toLocaleString() },
                                  { label: 'Páginas', value: displayData.pages },
                                  { label: 'Lectura Aprox.', value: displayData.readTime },
                                  { label: 'Tamaño', value: displayData.size, highlight: true, font: 'mono' },
                                  { label: 'Uploader', value: displayData.uploader, color: 'text-purple-600 dark:text-purple-400', clickable: true, type: 'uploader' },
                                ].map((item, idx) => (
                                   <div key={idx} className="flex justify-between py-3 border-b border-black/5 dark:border-white/5 last:border-0 hover:bg-black/5 dark:hover:bg-white/[0.02] px-2 -mx-2 rounded transition-colors">
                                      <span className="text-sm text-gray-500 font-medium">{item.label}</span>
                                      {item.clickable ? (
                                         <button 
                                            onClick={() => handleSearch(String(item.value), item.type)}
                                            className={`text-sm text-right ${item.color || (item.highlight ? 'text-gray-900 dark:text-gray-200 font-bold' : 'text-gray-600 dark:text-gray-400')} ${item.font === 'mono' ? 'font-mono' : ''} hover:underline hover:brightness-125 transition-all`}
                                         >
                                            {item.value}
                                         </button>
                                      ) : (
                                          <span className={`text-sm text-right ${item.color || (item.highlight ? 'text-gray-900 dark:text-gray-200 font-bold' : 'text-gray-600 dark:text-gray-400')} ${item.font === 'mono' ? 'font-mono' : ''}`}>
                                              {item.value}
                                          </span>
                                      )}
                                   </div>
                                ))}
                             </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
      </div>

       {/* Floating Bottom Navigation */}
       <div className="md:hidden fixed bottom-6 left-4 right-4 z-40 animate-in slide-in-from-bottom-4 duration-300">
        <div className="glass-panel rounded-full p-1 border border-black/10 dark:border-white/10 shadow-2xl bg-white/90 dark:bg-[#0f1115]/90 backdrop-blur-md flex items-center justify-between">
            {/* Back */}
            <button 
              onClick={onBack}
              className="flex-1 flex flex-col items-center justify-center py-2.5 px-2 rounded-l-full hover:bg-black/5 dark:hover:bg-white/5 active:bg-black/10 dark:active:bg-white/10 transition-colors group text-gray-500 dark:text-gray-400 active:text-black dark:active:text-white"
            >
              <Reply className="w-4 h-4 mb-0.5 group-active:-translate-y-1 transition-transform" />
              <span className="text-[9px] font-black uppercase tracking-widest">Volver</span>
            </button>
            
            <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

            {/* Home */}
            <button 
              onClick={() => onNavigate && onNavigate('dashboard')}
              className="flex-1 flex flex-col items-center justify-center py-2.5 px-2 hover:bg-black/5 dark:hover:bg-white/5 transition-colors group relative text-gray-500 dark:text-gray-400 active:text-black dark:active:text-white"
            >
              <Home className="w-4 h-4 mb-0.5 group-active:-translate-y-1 transition-transform" />
              <span className="text-[9px] font-black uppercase tracking-widest">Inicio</span>
            </button>
            
            <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

             {/* Rate (Only if downloaded) - ADDED, not replaced */}
             {hasDownloaded && (
                <>
                  <button 
                    className="flex-1 flex flex-col items-center justify-center py-2.5 px-2 hover:bg-black/5 dark:hover:bg-white/5 active:bg-black/10 dark:active:bg-white/10 transition-colors group text-yellow-500 active:text-yellow-600"
                  >
                    <Star className="w-4 h-4 mb-0.5 fill-current" />
                    <span className="text-[9px] font-black uppercase tracking-widest">Valorar</span>
                  </button>
                  <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>
                </>
             )}

             {/* Download - Always Available (with status change) */}
            <button 
              onClick={handleDownload}
              className={`flex-1 flex flex-col items-center justify-center py-2.5 px-2 rounded-r-full hover:bg-black/5 dark:hover:bg-white/5 active:bg-black/10 dark:active:bg-white/10 transition-colors group ${hasDownloaded ? 'text-green-600 dark:text-green-500' : 'text-gray-500 dark:text-gray-400 active:text-black dark:active:text-white'}`}
            >
              {hasDownloaded ? <Check className="w-4 h-4 mb-0.5" /> : <Download className="w-4 h-4 mb-0.5" />}
              <span className="text-[9px] font-black uppercase tracking-widest">Descargar</span>
            </button>
        </div>
      </div>

    </div>
  );
};