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
    Layers
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
    { tag: '{genres}', label: 'Géneros', icon: '🎭' },
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
        <div className="space-y-4">
            {/* Telegram Rich Toolbar */}
            <div className="p-2.5 rounded-2xl bg-slate-900/80 border border-white/10 backdrop-blur-xl shadow-lg space-y-2.5">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/5 pb-2">
                    <div className="flex flex-wrap items-center gap-1">
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
                            className="px-2 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-cyan-300 text-xs font-medium flex items-center gap-1"
                            title="Cita <blockquote>"
                        >
                            <Quote className="w-3.5 h-3.5" /> Cita
                        </button>
                        <button
                            type="button"
                            onClick={() => handleFormat('quote_expandable')}
                            className="px-2 py-1 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/20 text-xs font-medium flex items-center gap-1"
                            title="Cita Expandible <blockquote expandable>"
                        >
                            <Quote className="w-3.5 h-3.5" /> Expandible
                        </button>
                        <button
                            type="button"
                            onClick={() => handleFormat('code')}
                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-200 hover:text-white transition-all"
                            title="Código en línea <code>"
                        >
                            <Code className="w-4 h-4" />
                        </button>
                        <button
                            type="button"
                            onClick={() => handleFormat('link')}
                            className="px-2 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-blue-400 text-xs font-medium flex items-center gap-1"
                            title="Enlace URL <a>"
                        >
                            <Link className="w-3.5 h-3.5" /> Enlace
                        </button>
                        <button
                            type="button"
                            onClick={() => handleFormat('hr')}
                            className="px-2 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-purple-300 text-xs font-medium flex items-center gap-1"
                            title="Divisor de Mensaje <hr/>"
                        >
                            <Split className="w-3.5 h-3.5" /> Dividir
                        </button>
                    </div>

                    <div className="flex items-center gap-1">
                        <button
                            type="button"
                            onClick={() => handleFormat('conditional')}
                            className="px-2.5 py-1 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/30 text-xs font-bold flex items-center gap-1.5 transition-all shadow-sm"
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
                    <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto pr-1">
                        {TEMPLATE_VARIABLES.map((v) => (
                            <button
                                key={v.tag}
                                type="button"
                                onClick={() => insertTextAtCursor(v.tag)}
                                className="px-2 py-0.5 rounded-md bg-slate-800 hover:bg-indigo-600/30 hover:border-indigo-500/40 text-gray-300 hover:text-indigo-200 border border-white/5 text-[11px] font-mono transition-all flex items-center gap-1 active:scale-95"
                                title={v.label}
                            >
                                <span>{v.icon}</span>
                                <span>{v.tag}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Code / Text Area */}
            <div className="relative">
                <textarea
                    ref={textareaRef}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    rows={12}
                    placeholder="Escribe aquí la plantilla usando etiquetas HTML de Telegram y variables..."
                    className="w-full p-4 rounded-2xl bg-slate-900/90 border border-white/10 text-xs font-mono text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 shadow-inner leading-relaxed select-text"
                />
            </div>
        </div>
    );
};
