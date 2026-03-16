import React from 'react';

export const LibraryHeader: React.FC = () => {
    return (
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between mb-12 px-2">
            <div>
                <h1 className="text-5xl font-black tracking-tighter text-white mb-2">Mi Biblioteca</h1>
                <p className="text-gray-500 font-medium tracking-wide text-sm">Gestiona tu colección y sigue tus lecturas.</p>
            </div>
        </div>
    );
};
