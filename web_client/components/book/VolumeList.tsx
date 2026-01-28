import React from 'react';
import { Download, Star } from 'lucide-react';
import { Volume, Series } from '../../types';
import { getCoverUrl } from '../../src/utils/imageUtils';

interface VolumeListProps {
    volumes: Volume[];
    viewMode: 'list' | 'grid';
    onSelectVolume: (volume: Volume, series: Series) => void;
    series: Series;
    settings: any;
}

export const VolumeList: React.FC<VolumeListProps> = ({ volumes, viewMode, onSelectVolume, series, settings }) => {
    return (
        <div className={viewMode === 'list' ? "flex flex-col gap-4" : "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-6"}>
            {volumes.map((vol) => (
                viewMode === 'list' ? (
                    <div
                        key={vol.id}
                        onClick={() => {
                            onSelectVolume(vol, series);
                        }}
                        className="group relative flex gap-5 p-4 rounded-[2rem] glass-panel hover:bg-white/[0.07] hover:border-white/20 hover:shadow-[0_20px_40px_-10px_rgba(0,0,0,0.4)] transition-all duration-500 cursor-pointer overflow-hidden mb-4"
                    >
                        {/* Premium Backdrop Glow */}
                        <div className="absolute -inset-20 bg-primary/5 blur-[100px] opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none"></div>

                        {/* Left Section: Image with Space-Saving Badges */}
                        <div className="relative shrink-0 w-[100px] sm:w-[120px] aspect-[2/3] rounded-premium-sm overflow-hidden shadow-2xl border border-white/10 group-hover:scale-[1.03] transition-transform duration-700">
                            <img
                                alt={vol.title}
                                className="w-full h-full object-cover transition-all duration-1000 group-hover:scale-110"
                                src={getCoverUrl(vol.coverUrl, vol.coverThumbUrl, settings.coverQuality)}
                            />
                            <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/60 to-transparent"></div>

                            {/* Floating Quality Badges on Cover */}
                            <div className="absolute bottom-2 right-2 flex flex-col items-end gap-1.5">
                                {vol.color_mode === 'color' && (
                                    <div className="bg-gradient-to-br from-orange-400 to-pink-500 text-white text-[7px] font-black px-1.5 py-0.5 rounded-md shadow-2xl border border-white/20 uppercase tracking-widest">
                                        COLOR
                                    </div>
                                )}
                                {vol.is_uncensored && (
                                    <div className="bg-red-600 text-white text-[7px] font-black px-1.5 py-0.5 rounded-md shadow-2xl border border-white/20 uppercase tracking-widest">
                                        S/C
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Middle Section: Detailed Content */}
                        <div className="flex-1 min-w-0 flex flex-col py-1 z-10">
                            {/* Clean Header Info */}
                            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mb-1 text-[10px] font-black uppercase tracking-widest">
                                <span className="text-primary opacity-90">VOLUMEN {vol.volumeNumber}</span>
                                {vol.group && (
                                    <>
                                        <span className="w-1 h-1 rounded-full bg-white/10"></span>
                                        <span className="text-emerald-400 opacity-80 truncate max-w-[150px]">{vol.group}</span>
                                    </>
                                )}
                            </div>

                            <h3 className="text-white font-black text-base sm:text-lg leading-tight line-clamp-2 tracking-tight group-hover:text-primary transition-colors mb-1">
                                {vol.cleanTitle || vol.title}
                            </h3>

                            {vol.romajiTitle && (
                                <p className="text-gray-500 text-[10px] sm:text-xs font-medium italic mb-2 line-clamp-2 opacity-70">
                                    {vol.romajiTitle}
                                </p>
                            )}

                            {/* Author Info */}
                            <div className="flex items-center gap-2 mb-3 text-gray-400 text-[10px] font-bold uppercase tracking-widest">
                                <span className="text-gray-600">Por</span>
                                <span className="text-white/70 group-hover:text-white truncate">{series.author}</span>
                            </div>

                            {/* Metrics Footer - Simplified */}
                            <div className="mt-auto flex items-center gap-5 pt-3 border-t border-white/5">
                                <div className="flex items-center gap-1.5 text-yellow-500">
                                    <Star className="w-3.5 h-3.5 fill-current" />
                                    <span className="text-[11px] font-black text-white">{vol.rating > 0 ? vol.rating.toFixed(1) : 'NEW'}</span>
                                </div>

                                <div className="flex items-center gap-1.5 text-primary">
                                    <Download className="w-3.5 h-3.5" />
                                    <span className="text-[11px] font-black text-white">{vol.downloadCount}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div
                        key={vol.id}
                        onClick={() => {
                            onSelectVolume(vol, series);
                        }}
                        className="group relative glass-panel rounded-[2.5rem] overflow-hidden hover:border-primary/40 shadow-2xl hover:shadow-primary/20 hover:-translate-y-2 transition-all duration-700 flex flex-col h-full cursor-pointer"
                    >
                        <div className="relative aspect-[2/3] w-full overflow-hidden bg-white/5 shadow-2xl">
                            <img
                                alt={vol.title}
                                className="absolute inset-0 w-full h-full object-cover transition-all duration-1000 group-hover:scale-110"
                                src={getCoverUrl(vol.coverUrl, vol.coverThumbUrl, settings.coverQuality)}
                            />

                            {/* Floating Badges */}
                            <div className="absolute top-4 left-4 flex flex-col gap-2">
                                <span className="bg-primary text-white text-[10px] font-black px-4 py-2 rounded-premium-sm uppercase tracking-widest shadow-2xl border border-white/10">
                                    Vol {vol.volumeNumber}
                                </span>
                                {vol.color_mode === 'color' && (
                                    <span className="bg-gradient-to-br from-orange-400 to-pink-500 text-white text-[9px] font-black px-3 py-1.5 rounded-premium-sm uppercase tracking-widest shadow-2xl border border-white/10">
                                        Color
                                    </span>
                                )}
                                {vol.is_uncensored && (
                                    <span className="bg-red-500 text-white text-[9px] font-black px-3 py-1.5 rounded-premium-sm uppercase tracking-widest shadow-2xl border border-white/10">
                                        S/C
                                    </span>
                                )}
                            </div>

                            {/* Gradient Overlay */}
                            <div className="absolute inset-x-0 bottom-0 p-6 bg-gradient-to-t from-black via-black/40 to-transparent">
                                <div className="flex items-center gap-2 text-yellow-400 mb-2">
                                    <Star className="w-4 h-4 fill-current" />
                                    <span className="text-[12px] font-black">{vol.rating > 0 ? vol.rating.toFixed(1) : '—'}</span>
                                </div>
                                <h3 className="text-white font-black text-sm sm:text-lg leading-tight line-clamp-2 drop-shadow-2xl group-hover:text-primary transition-colors tracking-tight">
                                    {vol.cleanTitle || vol.title}
                                </h3>
                            </div>
                        </div>

                        {/* Hover Accent Glow */}
                        <div className="absolute -inset-20 bg-primary/5 blur-[80px] opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
                    </div>
                )
            ))}
        </div>
    );
};
