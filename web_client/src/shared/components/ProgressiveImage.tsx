import React, { useState, useEffect, useRef } from 'react';
import { ImageOff } from 'lucide-react';

interface ProgressiveImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
    src: string;
    placeholderColor?: string;
    className?: string; // Class for the IMG element
    containerClassName?: string; // Class for the wrapper div
}

export const ProgressiveImage: React.FC<ProgressiveImageProps> = ({
    src,
    placeholderColor = '#1f2937', // gray-800
    className = '',
    containerClassName = '',
    alt,
    ...props
}) => {
    const [isLoaded, setIsLoaded] = useState(false);
    const [hasError, setHasError] = useState(false);
    const [isInView, setIsInView] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setIsInView(true);
                        observer.disconnect();
                    }
                });
            },
            {
                rootMargin: '200px', // Start loading 200px before appearing
                threshold: 0.01,
            }
        );

        if (containerRef.current) {
            observer.observe(containerRef.current);
        }

        return () => {
            observer.disconnect();
        };
    }, []);

    const [currentSrc, setCurrentSrc] = useState(src);

    useEffect(() => {
        setCurrentSrc(src);
        setHasError(!src);
        setIsLoaded(false);
    }, [src]);

    return (
        <div
            ref={containerRef}
            className={`relative overflow-hidden flex items-center justify-center ${containerClassName || 'w-full h-full'}`}
            style={{ backgroundColor: placeholderColor }}
        >
            {/* Loading Skeleton / Pulse */}
            {!isLoaded && !hasError && (
                <div className="absolute inset-0 animate-pulse bg-white/5" />
            )}

            {hasError ? (
                <div className="flex flex-col items-center justify-center p-2 text-gray-500 text-center select-none">
                    <ImageOff className="w-6 h-6 mb-1 opacity-40" />
                    <span className="text-[9px] font-bold uppercase tracking-widest opacity-40">Sin Portada</span>
                </div>
            ) : (
                isInView && (
                    <img
                        src={currentSrc}
                        alt={alt}
                        loading="lazy"
                        className={`transition-all duration-700 ease-out ${isLoaded ? 'opacity-100 blur-0 scale-100' : 'opacity-0 blur-md scale-105'
                            } ${className}`}
                        onLoad={() => setIsLoaded(true)}
                        onError={() => {
                            if (currentSrc.includes('_medium.jpg') || currentSrc.includes('_high.jpg')) {
                                setCurrentSrc(currentSrc.replace(/_(medium|high)\.jpg$/, '_low.jpg'));
                            } else {
                                setHasError(true);
                                setIsLoaded(true);
                            }
                        }}
                        {...props}
                    />
                )
            )}
        </div>
    );
};
