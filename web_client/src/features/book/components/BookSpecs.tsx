import React from 'react';
import { Database, Library } from 'lucide-react';

interface SpecItem {
    label: string;
    value: string | number;
    highlight?: boolean;
    clickable?: boolean;
    type?: string;
    color?: string;
    font?: 'mono' | 'sans';
}

interface BookSpecsProps {
    details: SpecItem[];
    specs: SpecItem[];
    onSearch: (term: string, type?: string) => void;
}

export const BookSpecs: React.FC<BookSpecsProps> = ({ details, specs, onSearch }) => {
    const renderItem = (item: SpecItem, idx: number) => (
        <div key={idx} className="flex justify-between py-3 border-b border-white/5 last:border-0 hover:bg-white/[0.02] px-2 -mx-2 rounded-premium-md transition-colors">
            <span className="text-sm text-gray-500 font-medium">{item.label}</span>
            {item.clickable ? (
                <button
                    onClick={() => onSearch(String(item.value), item.type)}
                    className={`text-sm text-right ${item.color || (item.highlight ? 'text-white font-bold' : 'text-gray-400')} ${item.font === 'mono' ? 'font-mono' : ''} truncate max-w-[200px] hover:underline hover:text-primary transition-colors`}
                >
                    {item.value}
                </button>
            ) : (
                <span className={`text-sm text-right ${item.color || (item.highlight ? 'text-white font-bold' : 'text-gray-400')} ${item.font === 'mono' ? 'font-mono' : ''} truncate max-w-[200px]`}>
                    {item.value}
                </span>
            )}
        </div>
    );

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Book Details */}
            <div className="glass-panel border border-white/5 rounded-premium-lg p-6 shadow-premium h-full">
                <div className="flex items-center gap-2 mb-6 text-primary">
                    <Library className="w-5 h-5" />
                    <h3 className="text-xs font-black uppercase tracking-widest">Detalles del Libro</h3>
                </div>
                <div className="space-y-0.5">
                    {details.map(renderItem)}
                </div>
            </div>

            {/* Tech Specs */}
            <div className="glass-panel border border-white/5 rounded-premium-lg p-6 shadow-premium h-full">
                <div className="flex items-center gap-2 mb-6 text-primary">
                    <Database className="w-5 h-5" />
                    <h3 className="text-xs font-black uppercase tracking-widest">Ficha Técnica</h3>
                </div>
                <div className="space-y-0.5">
                    {specs.map(renderItem)}
                </div>
            </div>
        </div>
    );
};
