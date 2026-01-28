import React from 'react';

export const LibraryHeader: React.FC = () => {
    return (
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between mb-12">
            <div>
                <h1 className="text-5xl font-black tracking-tighter text-white mb-3">Mi Biblioteca</h1>
                <p className="text-gray-500 font-medium tracking-wide">Gestiona tu colección y sigue tus lecturas.</p>
            </div>
        </div>
    );
};
