import React from 'react';
import { Download, Star } from 'lucide-react';
import { Book } from '../types';

interface BookCardProps {
  book: Book;
  onDownload: (book: Book) => void;
  compact?: boolean;
}

export const BookCard: React.FC<BookCardProps> = ({ book, onDownload, compact = false }) => {
  return (
    <div className="group relative glass-panel rounded-xl overflow-hidden border border-white/5 hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 transition-all duration-300 flex flex-col h-full">
      <div className="absolute top-3 right-3 z-10">
        <span className="bg-black/70 backdrop-blur text-white text-[10px] font-bold px-2 py-1 rounded-md uppercase tracking-wider border border-white/10">
          {book.format}
        </span>
      </div>
      
      <div className={`relative overflow-hidden bg-gray-800 ${compact ? 'aspect-[3/4]' : 'aspect-[2/3]'}`}>
        <img 
          alt={book.title} 
          className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500 opacity-90 group-hover:opacity-100" 
          src={book.coverUrl} 
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent opacity-60"></div>
        {!compact && (
          <div className="absolute bottom-4 left-4 right-4">
            <h3 className="text-white font-bold text-lg leading-tight line-clamp-2 drop-shadow-md">{book.title}</h3>
            <p className="text-gray-300 text-sm font-medium mt-1 truncate">{book.author}</p>
          </div>
        )}
      </div>

      <div className="p-4 flex flex-col flex-1">
        {compact && (
          <div className="mb-3">
             <h3 className="text-white font-bold text-base leading-tight line-clamp-1">{book.title}</h3>
             <p className="text-gray-400 text-xs mt-1 truncate">{book.author}</p>
          </div>
        )}

        <div className="flex items-center gap-2 mb-3">
          <div className="flex items-center gap-1 text-yellow-500 text-xs bg-yellow-500/10 px-2 py-0.5 rounded border border-yellow-500/20">
            <Star className="w-3 h-3 fill-current" />
            <span className="font-bold">{book.rating}</span>
          </div>
          <span className="text-[10px] text-gray-500 font-mono px-2 py-0.5 bg-white/5 rounded">{book.size}</span>
        </div>

        <div className="mt-auto pt-3 border-t border-white/5 flex items-center justify-between">
          <span className="text-[10px] text-gray-500 uppercase tracking-wider">
            {compact ? book.format : 'Available'}
          </span>
          <button 
            onClick={() => onDownload(book)}
            className="p-2 rounded-lg bg-white/5 text-gray-300 hover:bg-primary hover:text-white transition-colors"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};