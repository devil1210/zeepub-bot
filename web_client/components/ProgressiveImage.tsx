import React, { useState, useEffect, useRef } from 'react';

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

    return (
        <div
            ref={containerRef}
            className={`relative overflow-hidden ${containerClassName}`}
            style={{ backgroundColor: placeholderColor }}
        >
            {/* Loading Skeleton / Pulse */}
            {!isLoaded && (
                <div className="absolute inset-0 animate-pulse bg-white/5" />
            )}

            {isInView && (
                <img
                    src={src}
                    alt={alt}
                    className={`transition-opacity duration-700 ease-in-out ${isLoaded ? 'opacity-100 blur-0 scale-100' : 'opacity-0 blur-sm scale-105'
                        } ${className}`}
                    onLoad={() => setIsLoaded(true)}
                    {...props}
                />
            )}
        </div>
    );
};
