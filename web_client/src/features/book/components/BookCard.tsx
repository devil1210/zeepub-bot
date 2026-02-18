import React, { memo } from 'react';
import { Download, Star } from 'lucide-react';
import { Book } from '@shared/types';
import { ProgressiveImage } from '@shared/components/ProgressiveImage';
import { useTheme } from '@shared/contexts/ThemeContext';
import { getCoverUrl } from '@shared/utils/imageUtils';

interface BookCardProps {
  book: Book;
  onDownload: (book: Book) => void;
  compact?: boolean;
}

export const BookCard = memo<BookCardProps>(({ book, onDownload, compact = false }) => {
  const { settings } = useTheme();
  const coverSrc = getCoverUrl(book.coverUrl, book.coverThumbUrl, settings.coverQuality);

  return (
    <div className="group relative glass-panel rounded-premium-sm overflow-hidden border border-white/5 hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 transition-all duration-300 flex flex-col h-full bg-slate-900/50">
      <div className={`relative overflow-hidden ${compact ? 'aspect-[3/4]' : 'aspect-[2/3]'} shrink-0`}>
        <div className="absolute top-3 left-3 z-20 flex flex-col gap-1.5">
          <span className="bg-black/60 shadow-lg backdrop-blur-md text-white text-[9px] font-black px-2 py-1 rounded-md uppercase tracking-widest border border-white/10">
            {book.book_type || book.format}
          </span>
          {book.is_uncensored && (
            <span className="bg-red-600/90 text-white text-[8px] font-black px-2 py-0.5 rounded-md uppercase tracking-widest shadow-lg border border-white/10 w-min">
              S/C
            </span>
          )}
        </div>

        <ProgressiveImage
          alt={book.title}
          className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-700 opacity-90 group-hover:opacity-100"
          src={coverSrc}
          containerClassName="w-full h-full"
        />

        {/* Subtle Gradient for depth only, no text overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-40 transition-opacity duration-500 pointer-events-none"></div>

        {/* Glow Effect */}
        <div className="absolute -inset-full bg-primary/20 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
      </div>

      <div className="p-3 flex flex-col flex-1 gap-2 relative z-10">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-yellow-500 bg-yellow-500/10 px-1.5 py-0.5 rounded border border-yellow-500/10">
            <Star className="w-3 h-3 fill-current" />
            <span className="text-[10px] font-black tracking-wider text-yellow-500">{book.rating > 0 ? book.rating.toFixed(1) : '-'}</span>
          </div>
          <span className="text-[9px] font-mono text-gray-500 uppercase px-1.5 py-0.5 bg-white/5 rounded border border-white/5">{book.size}</span>
        </div>

        <div className="space-y-0.5">
          <h3 className="text-gray-100 font-bold text-sm leading-tight line-clamp-2 group-hover:text-primary transition-colors">{book.cleanTitle || book.title}</h3>
          <p className="text-gray-500 text-[10px] font-bold uppercase tracking-wider line-clamp-1">{book.author}</p>
        </div>

        <div className="mt-auto pt-2 flex items-center justify-between">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDownload(book);
            }}
            className="w-full py-1.5 bg-white/5 hover:bg-primary text-gray-400 hover:text-white rounded-lg flex items-center justify-center gap-2 transition-all group/btn"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="text-[10px] font-black uppercase tracking-wider">Descargar</span>
          </button>
        </div>
      </div>
    </div>
  );
});

BookCard.displayName = 'BookCard';
