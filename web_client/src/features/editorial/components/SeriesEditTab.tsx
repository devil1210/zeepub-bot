import React from 'react';
import {
    FileSpreadsheet,
    GitMerge,
    Loader2,
    Save,
    Tag,
    X,
    BookOpen,
    Plus,
    Trash2
} from 'lucide-react';

interface SeriesEditTabProps {
    seriesEnglish: string;
    setSeriesEnglish: (val: string) => void;
    seriesSpanish: string;
    setSeriesSpanish: (val: string) => void;
    name: string;
    setName: (val: string) => void;
    author: string;
    setAuthor: (val: string) => void;
    illustrator: string;
    setIllustrator: (val: string) => void;
    bookType: string;
    setBookType: (val: string) => void;
    demography: string;
    setDemography: (val: string) => void;
    coverUrl: string;
    setCoverUrl: (val: string) => void;
    description: string;
    setDescription: (val: string) => void;
    isSaving: boolean;
    onSaveMetadata: (e: React.FormEvent) => void;
    onOpenMergeModal: () => void;
    // Aliases
    aliases: Array<{ id: number; alias: string }>;
    newAliasInput: string;
    setNewAliasInput: (val: string) => void;
    addingAlias: boolean;
    onAddAlias: () => void;
    onRemoveAlias: (id: number) => void;
    // Linked Books
    books: any[];
    onOpenAttachModal: () => void;
    onUnlinkBook: (id: string, title: string) => void;
}

export const SeriesEditTab: React.FC<SeriesEditTabProps> = ({
    seriesEnglish,
    setSeriesEnglish,
    seriesSpanish,
    setSeriesSpanish,
    name,
    setName,
    author,
    setAuthor,
    illustrator,
    setIllustrator,
    bookType,
    setBookType,
    demography,
    setDemography,
    coverUrl,
    setCoverUrl,
    description,
    setDescription,
    isSaving,
    onSaveMetadata,
    onOpenMergeModal,
    aliases,
    newAliasInput,
    setNewAliasInput,
    addingAlias,
    onAddAlias,
    onRemoveAlias,
    books,
    onOpenAttachModal,
    onUnlinkBook,
}) => {
    return (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Form: Series Metadata (6 cols) */}
            <form
                onSubmit={onSaveMetadata}
                className="lg:col-span-6 bg-slate-900/50 border border-white/10 rounded-3xl p-6 sm:p-7 space-y-5 backdrop-blur-xl shadow-xl"
            >
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <FileSpreadsheet className="w-4 h-4 text-indigo-400" /> Metadatos Principales de la Serie
                    </h3>
                    <button
                        type="button"
                        onClick={onOpenMergeModal}
                        className="px-3 py-1.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 text-xs font-bold border border-purple-500/30 flex items-center gap-1.5 transition-all"
                    >
                        <GitMerge className="w-3.5 h-3.5" /> Fusionar Serie
                    </button>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                            Título en Inglés (Oficial Internacional)
                        </label>
                        <input
                            type="text"
                            value={seriesEnglish}
                            onChange={(e) => setSeriesEnglish(e.target.value)}
                            className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-bold"
                        />
                    </div>

                    <div>
                        <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                            Título en Español
                        </label>
                        <input
                            type="text"
                            value={seriesSpanish}
                            onChange={(e) => setSeriesSpanish(e.target.value)}
                            className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-bold text-amber-300"
                        />
                    </div>

                    <div>
                        <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                            Título en Japonés / Romaji
                        </label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                        />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Autor</label>
                            <input
                                type="text"
                                value={author}
                                onChange={(e) => setAuthor(e.target.value)}
                                className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                            />
                        </div>
                        <div>
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Ilustrador</label>
                            <input
                                type="text"
                                value={illustrator}
                                onChange={(e) => setIllustrator(e.target.value)}
                                className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Tipo de Obra</label>
                            <select
                                value={bookType}
                                onChange={(e) => setBookType(e.target.value)}
                                className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-bold"
                            >
                                <option value="Novela Ligera">Novela Ligera</option>
                                <option value="Web Novel">Web Novel</option>
                                <option value="Manga">Manga</option>
                                <option value="Novela Visual">Novela Visual</option>
                                <option value="Libro General">Libro General</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Demografía</label>
                            <select
                                value={demography}
                                onChange={(e) => setDemography(e.target.value)}
                                className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-bold"
                            >
                                <option value="Seinen">Seinen</option>
                                <option value="Shounen">Shounen</option>
                                <option value="Josei">Josei</option>
                                <option value="Shoujo">Shoujo</option>
                                <option value="General">General</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">URL Portada</label>
                        <input
                            type="text"
                            value={coverUrl}
                            onChange={(e) => setCoverUrl(e.target.value)}
                            placeholder="https://... o /api/library/covers/..."
                            className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white font-mono"
                        />
                    </div>

                    <div>
                        <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Sinopsis de la Serie</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={4}
                            className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white leading-relaxed"
                        />
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={isSaving}
                    className="w-full py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 shadow-xl shadow-indigo-600/30 transition-all active:scale-95 disabled:opacity-50"
                >
                    {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    <span>Guardar Metadatos</span>
                </button>
            </form>

            {/* Right Column: Aliases + Volume Linking (6 cols) */}
            <div className="lg:col-span-6 space-y-6">
                {/* Aliases Card */}
                <div className="bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-4 backdrop-blur-xl shadow-xl">
                    <div className="flex items-center justify-between border-b border-white/10 pb-3">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <Tag className="w-4 h-4 text-cyan-400" /> Siglas y Títulos Alias ({aliases.length})
                        </h3>
                    </div>

                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={newAliasInput}
                            onChange={(e) => setNewAliasInput(e.target.value)}
                            placeholder="Ej. Toaru Majutsu no Index, Index..."
                            className="flex-1 px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white"
                        />
                        <button
                            type="button"
                            onClick={onAddAlias}
                            disabled={addingAlias}
                            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md"
                        >
                            + Añadir
                        </button>
                    </div>

                    <div className="flex flex-wrap gap-2 pt-2">
                        {aliases.map((al) => (
                            <span
                                key={al.id}
                                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white/5 border border-white/10 text-xs text-gray-200"
                            >
                                <span>{al.alias}</span>
                                <button
                                    type="button"
                                    onClick={() => onRemoveAlias(al.id)}
                                    className="text-gray-500 hover:text-red-400 transition-colors"
                                >
                                    <X className="w-3.5 h-3.5" />
                                </button>
                            </span>
                        ))}
                    </div>
                </div>

                {/* Linked Books Management Card */}
                <div className="bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-4 backdrop-blur-xl shadow-xl">
                    <div className="flex items-center justify-between border-b border-white/10 pb-3">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <BookOpen className="w-4 h-4 text-indigo-400" /> Gestión de Volúmenes Vinculados ({books.length})
                        </h3>
                        <button
                            type="button"
                            onClick={onOpenAttachModal}
                            className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-md"
                        >
                            <Plus className="w-3.5 h-3.5" /> Vincular Tomo
                        </button>
                    </div>

                    <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                        {books.map((b) => (
                            <div
                                key={b.id}
                                className="p-3 rounded-2xl bg-slate-950/70 border border-white/5 flex items-center justify-between gap-3 text-xs"
                            >
                                <div className="flex items-center gap-3 min-w-0">
                                    <span className="px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 font-mono font-bold shrink-0">
                                        Vol. {b.volume}
                                    </span>
                                    <span className="text-white truncate font-medium">{b.spanish_title || b.title}</span>
                                </div>

                                <button
                                    type="button"
                                    onClick={() => onUnlinkBook(b.id, b.title)}
                                    className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors shrink-0"
                                    title="Desvincular volumen"
                                >
                                    <Trash2 className="w-3.5 h-3.5" />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};
