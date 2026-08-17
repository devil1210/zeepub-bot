import React from 'react';
import { Database, Library } from 'lucide-react';

interface SpecItem {
    label: string;
    value: string | number;
    highlight?: boolean;
    clickable?: boolean;
    isMulti?: boolean;
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
        <div key={idx} className="flex justify-between items-start py-3 border-b border-black/5 dark:border-white/5 last:border-0 hover:bg-black/5 dark:hover:bg-white/[0.02] px-2 -mx-2 rounded transition-colors gap-3">
            <span className="text-sm text-gray-500 font-medium shrink-0">{item.label}</span>
            {item.isMulti && item.value && String(item.value) !== 'N/A' ? (
                <div className="flex flex-wrap gap-1.5 justify-end">
                    {String(item.value).split(',').map((v, i) => (
                        <span
                            key={i}
                            onClick={() => item.clickable && onSearch(v.trim(), item.type)}
                            className="text-xs font-semibold px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20 cursor-pointer hover:bg-primary/20 transition-colors"
                        >
                            {v.trim()}
                        </span>
                    ))}
                </div>
            ) : item.clickable ? (
                <button
                    onClick={() => onSearch(String(item.value), item.type)}
                    className={`text-sm text-right ${item.color || (item.highlight ? 'text-gray-900 dark:text-gray-200 font-bold' : 'text-gray-600 dark:text-gray-400')} ${item.font === 'mono' ? 'font-mono' : ''} truncate max-w-[200px] hover:underline hover:text-primary transition-colors`}
                >
                    {item.value}
                </button>
            ) : (
                <span className={`text-sm text-right ${item.color || (item.highlight ? 'text-gray-900 dark:text-gray-200 font-bold' : 'text-gray-600 dark:text-gray-400')} ${item.font === 'mono' ? 'font-mono' : ''} truncate max-w-[200px]`}>
                    {item.value}
                </span>
            )}
        </div>
    );

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Book Details */}
            <div className="glass-panel border border-black/5 dark:border-white/5 rounded-premium-sm p-6 shadow-sm dark:shadow-xl h-full">
                <div className="flex items-center gap-2 mb-6 text-primary">
                    <Library className="w-5 h-5" />
                    <h3 className="text-xs font-black uppercase tracking-widest">Detalles del Libro</h3>
                </div>
                <div className="space-y-0.5">
                    {details.map(renderItem)}
                </div>
            </div>

            {/* Tech Specs */}
            <div className="glass-panel border border-black/5 dark:border-white/5 rounded-premium-sm p-6 shadow-sm dark:shadow-xl h-full">
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
