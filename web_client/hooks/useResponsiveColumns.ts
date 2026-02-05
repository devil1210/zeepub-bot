import { useState, useEffect } from 'react';

export const useResponsiveColumns = () => {
    const [columns, setColumns] = useState(2);

    useEffect(() => {
        const handleResize = () => {
            const width = window.innerWidth;
            // sm: 640px -> 3 cols
            // md: 768px -> 4 cols
            // lg: 1024px -> 5 cols
            if (width >= 1024) {
                setColumns(5);
            } else if (width >= 768) {
                setColumns(4);
            } else if (width >= 640) {
                setColumns(3);
            } else {
                setColumns(2);
            }
        };

        // Initial call
        handleResize();

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return columns;
};
