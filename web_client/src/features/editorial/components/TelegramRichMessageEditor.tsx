import React, { useRef } from 'react';
import {
    Bold,
    Italic,
    Underline,
    Strikethrough,
    EyeOff,
    Quote,
    Code,
    Terminal,
    Link,
    Split,
    HelpCircle,
    Sparkles,
    Tag,
    Layers,
    Table,
    Heading,
    Image as ImageIcon
} from 'lucide-react';

interface TelegramRichMessageEditorProps {
    value: string;
    onChange: (val: string) => void;
    platform?: 'telegram' | 'facebook';
}

const TEMPLATE_VARIABLES = [
    { tag: '{serie}', label: 'Serie (Inglés/Español)', icon: '📚' },
    { tag: '{volumen}', label: 'Volumen', icon: '📖' },
    { tag: '{titulo}', label: 'Título del Tomo', icon: '🏷️' },
    { tag: '{autor}', label: 'Autor', icon: '✍️' },
    { tag: '{illustrator}', label: 'Ilustrador', icon: '🎨' },
    { tag: '{traductor}', label: 'Traductor', icon: '🌐' },
    { tag: '{editorial}', label: 'Editorial / Grupo', icon: '🏢' },
    { tag: '{sinopsis}', label: 'Sinopsis Completa', icon: '📝' },
    { tag: '{demography}', label: 'Demografía', icon: '👥' },
    { tag: '{genres}', label: 'Géneros (#Hashtags)', icon: '🎭' },
    { tag: '{tamaño}', label: 'Tamaño (MB)', icon: '📦' },
    { tag: '{fecha}', label: 'Fecha de Actualización', icon: '📅' },
    { tag: '{published_at}', label: 'Fecha de Publicación', icon: '📆' },
    { tag: '{slug}', label: 'Slug Hashtag', icon: '🏷️' },
    { tag: '{download_link}', label: 'Enlace de Descarga / WebApp', icon: '🔗' },
    { tag: '{layout_by}', label: 'Maquetador', icon: '🖌️' },
];

export const TelegramRichMessageEditor: React.FC<TelegramRichMessageEditorProps> = ({
    value,
    onChange,
    platform = 'telegram',
}) => {
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const insertTextAtCursor = (prefix: string, suffix: string = '', defaultText: string = '') => {
        const textarea = textareaRef.current;
        if (!textarea) return;

        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = value.substring(start, end) || defaultText;
        const before = value.substring(0, start);
        const after = value.substring(end);

        const replacement = `${prefix}${selectedText}${suffix}`;
        const newValue = `${before}${replacement}${after}`;
        onChange(newValue);

        setTimeout(() => {
            textarea.focus();
            const newCursor = start + prefix.length + selectedText.length;
            textarea.setSelectionRange(newCursor, newCursor);
        }, 50);
    };

    const handleFormat = (tag: string) => {
        switch (tag) {
            case 'bold':
                insertTextAtCursor('<b>', '</b>', 'texto en negrita');
                break;
            case 'italic':
                insertTextAtCursor('<i>', '</i>', 'texto en cursiva');
                break;
            case 'underline':
                insertTextAtCursor('<u>', '</u>', 'texto subrayado');
                break;
            case 'strike':
                insertTextAtCursor('<s>', '</s>', 'texto tachado');
                break;
            case 'spoiler':
                insertTextAtCursor('<tg-spoiler>', '</tg-spoiler>', 'texto spoiler');
                break;
            case 'quote':
                insertTextAtCursor('<blockquote>', '</blockquote>', 'Cita o sinopsis aquí');
                break;
            case 'quote_expandable':
                insertTextAtCursor('<blockquote expandable>', '</blockquote>', 'Texto largo colapsable');
                break;
            case 'code':
                insertTextAtCursor('<code>', '</code>', 'código_en_linea');
                break;
            case 'pre':
                insertTextAtCursor('<pre>', '</pre>', 'bloque de código multilínea');
                break;
            case 'link':
                insertTextAtCursor('<a href="{download_link}">', '</a>', 'Haz clic aquí');
                break;
            case 'img':
                insertTextAtCursor('<img src="tg://photo?id=cover" />\n', '', '');
                break;
            case 'table':
                insertTextAtCursor(
                    '<table bordered striped>\n[?autor]<tr><td>👤 <b>Autor</b></td><td>{autor}</td></tr>[/?]\n[?illustrator]<tr><td>🎨 <b>Ilustrador</b></td><td>{illustrator}</td></tr>[/?]\n[?tipo]<tr><td>🏷 <b>Categoría</b></td><td>{tipo}</td></tr>[/?]\n[?demography]<tr><td>👥 <b>Demografía</b></td><td>{demography}</td></tr>[/?]\n</table>\n',
                    '',
                    ''
                );
                break;
            case 'h3':
                insertTextAtCursor('<h3>', '</h3>', 'Título de la Serie');
                break;
            case 'hr':
                insertTextAtCursor('\n<hr/>\n', '', '');
                break;
            case 'conditional': {
                const textarea = textareaRef.current;
                const start = textarea ? textarea.selectionStart : 0;
                const end = textarea ? textarea.selectionEnd : 0;
                const selected = value.substring(start, end) || '{autor}';
                insertTextAtCursor(`[?autor]✍️ <b>Autor:</b> `, `[/?]\n`, selected);
                break;
            }
            default:
                break;
        }
    };

    return (
        <div className="space-y-4 flex flex-col h-full">
            {/* Telegram Rich Toolbar */}
            <div className="p-3 rounded-2xl bg-slate-900/90 border border-white/10 backdrop-blur-xl shadow-lg space-y-3 shrink-0">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/5 pb-2.5">
                    <div className="flex flex-wrap items-center gap-1.5">
                        <button
                            type="button"
                            onClick={() => handleFormat('bold')}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-200 hover:text-white transition-all text-xs font-bold"
                            title="Negrita <b>"
                        >
                            <Bold className="w-4 h-4" />
                        </button>
                        <button
                            type="button"
                            onClick={() => handleFormat('italic')}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-200 hover:text-white transition-all"
                            title="Cursiva <i>"
                        >
                            <Italic className="w-4 h-4" />
                        </button>
                        <button
                            type="button"
                            onClick={() => handleFormat('underline')}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-200 hover:text-white transition-all"
                            title="Subrayado <u>"
                        >
                            <Underline className="w-4 h-4" />
                        </button>
                        <button
                            type="button"
                            onClick={() => handleFormat('strike')}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-200 hover:text-white transition-all"
                            title="Tachado <s>"
                        >
                            <Strikethrough className="w-4 h-4" />
                        </button>
                        <button
                            type="button"
                            onClick={() => handleFormat('spoiler')}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-amber-300 hover:text-amber-200 transition-all flex items-center gap-1 text-xs"
                            title="Spoiler <tg-spoiler>"
                        >
                            <EyeOff className="w-4 h-4" />
                        </button>

                        <div className="w-px h-5 bg-white/10 mx-1" />

                        <button
                            type="button"
                            onClick={() => handleFormat('quote')}
                            className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-cyan-300 text-xs font-medium flex items-center gap-1"
                            title="Cita <blockquote>"
                        >
                            <Quote className="w-3.5 h-3.5" /> Cita
                        </button>
                        <button
                            type="button"
                            onClick={() => handleFormat('quote_expandable')}
                            className="px-2.5 py-1 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/20 text-xs font-medium flex items-center gap-1"
                            title="Cita Expandible <blockquote expandable>"
                        >
                            <Quote className="w-3.5 h-3.5" /> Expandible
                        </button>
                        <button
                            type="button"
                            onClick={() => handleFormat('h3')}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-200 hover:text-white transition-all"
                            title="Encabezado <h3>"
                        >
                            <Heading className="w-4 h-4" />
                        </button>
                        <button
                            type="button"
                            onClick={() => handleFormat('table')}
                            className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-indigo-300 text-xs font-medium flex items-center gap-1"
                            title="Tabla de Ficha Técnica <table>"
                        >
                            <Table className="w-3.5 h-3.5" /> Tabla
                        </button>
                        <button
                            type="button"
                            onClick={() => handleFormat('img')}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-emerald-300 hover:text-emerald-200 transition-all"
                            title="Insertar Foto / Portada <img>"
                        >
                            <ImageIcon className="w-4 h-4" />
                        </button>
                        <button
                            type="button"
                            onClick={() => handleFormat('link')}
                            className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-blue-400 text-xs font-medium flex items-center gap-1"
                            title="Enlace URL <a>"
                        >
                            <Link className="w-3.5 h-3.5" /> Enlace
                        </button>
                    </div>

                    <div className="flex items-center gap-1">
                        <button
                            type="button"
                            onClick={() => handleFormat('conditional')}
                            className="px-3 py-1 rounded-xl bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/30 text-xs font-bold flex items-center gap-1.5 transition-all shadow-sm"
                            title="Insertar bloque condicional [?tag]...[/?]"
                        >
                            <Layers className="w-3.5 h-3.5" /> Condicional [?tag]
                        </button>
                    </div>
                </div>

                {/* Variable chips palette */}
                <div className="space-y-1.5">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1">
                        <Tag className="w-3 h-3 text-indigo-400" /> Variables Disponibles (Haz clic para insertar):
                    </div>
                    <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto pr-1">
                        {TEMPLATE_VARIABLES.map((v) => (
                            <button
                                key={v.tag}
                                type="button"
                                onClick={() => insertTextAtCursor(v.tag)}
                                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-indigo-600/30 hover:border-indigo-500/40 text-gray-300 hover:text-indigo-200 border border-white/5 text-[11px] font-mono transition-all flex items-center gap-1 active:scale-95"
                                title={v.label}
                            >
                                <span>{v.icon}</span>
                                <span>{v.tag}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Code / Text Area - Full Height Widescreen */}
            <div className="relative flex-1 min-h-[560px] 2xl:min-h-[640px]">
                <textarea
                    ref={textareaRef}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder="Escribe aquí la plantilla usando etiquetas HTML de Telegram y variables..."
                    className="w-full h-full min-h-[560px] 2xl:min-h-[640px] p-5 rounded-3xl bg-slate-900/90 border border-white/10 text-xs sm:text-sm font-mono text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 shadow-inner leading-relaxed select-text resize-y"
                />
            </div>
        </div>
    );
};
