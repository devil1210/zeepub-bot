import React, { useState } from 'react';
import { Star, X } from 'lucide-react';

interface RatingModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (rating: number) => void;
    title: string;
}

export const RatingModal: React.FC<RatingModalProps> = ({ isOpen, onClose, onSubmit, title }) => {
    const [rating, setRating] = useState(0);
    const [hover, setHover] = useState(0);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div
                className="glass-panel border border-white/10 rounded-3xl w-full max-w-sm flex flex-col shadow-2xl overflow-hidden animate-in slide-in-from-bottom-4 sm:zoom-in-95 duration-200 bg-[#12171c]/95"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Handle for mobile bottom sheet look */}
                <div className="w-12 h-1.5 bg-white/10 rounded-full mx-auto mt-3 mb-1 sm:hidden"></div>

                <div className="p-8 flex flex-col items-center text-center">
                    <h3 className="text-xl font-bold text-white mb-2 leading-tight">Califica este libro</h3>
                    <p className="text-gray-400 text-sm mb-8">Comparte tu opinión sobre este libro</p>

                    {/* Star Rating System */}
                    <div className="flex items-center gap-3 mb-10">
                        {[1, 2, 3, 4, 5].map((star) => (
                            <button
                                key={star}
                                onMouseEnter={() => setHover(star)}
                                onMouseLeave={() => setHover(0)}
                                onClick={() => setRating(star)}
                                className="transition-transform active:scale-90"
                            >
                                <Star
                                    className={`w-10 h-10 ${(hover || rating) >= star
                                            ? 'fill-yellow-500 text-yellow-500 drop-shadow-[0_0_10px_rgba(234,179,8,0.3)]'
                                            : 'text-gray-700'
                                        } transition-all duration-200`}
                                    strokeWidth={1.5}
                                />
                            </button>
                        ))}
                    </div>

                    <div className="flex flex-col w-full gap-3">
                        <button
                            onClick={() => rating > 0 && onSubmit(rating)}
                            disabled={rating === 0}
                            className={`w-full py-4 rounded-2xl text-sm font-black uppercase tracking-widest transition-all ${rating > 0
                                    ? 'bg-primary text-white shadow-lg shadow-primary/20 active:scale-[0.98]'
                                    : 'bg-white/5 text-gray-500 cursor-not-allowed border border-white/5'
                                }`}
                        >
                            Enviar Valoración
                        </button>
                        <button
                            onClick={onClose}
                            className="w-full py-4 rounded-2xl text-xs font-black uppercase tracking-widest text-gray-400 hover:text-white hover:bg-white/5 transition-all"
                        >
                            Cancelar
                        </button>
                    </div>
                </div>
            </div>
            {/* Overlay click to close */}
            <div className="absolute inset-0 -z-10" onClick={onClose}></div>
        </div>
    );
};
