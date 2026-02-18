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
    <div className="group relative glass-panel rounded-premium-sm overflow-hidden border border-white/5 hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 transition-all duration-300 flex flex-col h-full">
      <div className={`relative overflow-hidden bg-slate-900 ${compact ? 'aspect-[3/4]' : 'aspect-[2/3]'}`}>
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
        <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/40 to-transparent opacity-80 group-hover:opacity-90 transition-opacity duration-500 pointer-events-none"></div>

        {/* Glow Effect */}
        <div className="absolute -inset-full bg-primary/20 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>

        {!compact && (
          <div className="absolute bottom-4 left-4 right-4 z-10 translate-y-2 group-hover:translate-y-0 transition-transform duration-500">
            <div className="flex items-center gap-2 mb-2">
              <div className="flex items-center gap-1 text-yellow-500">
                <Star className="w-3 h-3 fill-current" />
                <span className="text-[10px] font-black tracking-wider text-white">{book.rating > 0 ? book.rating.toFixed(1) : 'NEW'}</span>
              </div>
              <div className="w-px h-3 bg-white/20"></div>
              <span className="text-[10px] font-mono text-gray-400">{book.size}</span>
            </div>
            <h3 className="text-white font-black text-lg leading-tight line-clamp-2 drop-shadow-xl mb-1 group-hover:text-primary transition-colors">{book.cleanTitle || book.title}</h3>
            <p className="text-gray-400 text-xs font-bold uppercase tracking-wider line-clamp-1">{book.author}</p>
          </div>
        )}
      </div>

      <div className="p-0 hidden"></div>
      {/* We are moving towards a cover-only card design for maximum impact, 
          but keeping the code structure if we want to revert to text-below later. 
          For now, overlay is cleaner. */}
    </div>
  );
});

BookCard.displayName = 'BookCard';
