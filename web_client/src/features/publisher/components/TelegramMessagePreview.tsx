import React, { useMemo } from 'react';
import { CheckCheck } from 'lucide-react';

import { Book } from '@shared/types';

interface TelegramMessagePreviewProps {
    content: string;
    templateName?: string;
    coverQuality?: string;
    sampleBook?: Book | null;
}

import { getCoverUrl } from '@shared/utils/imageUtils';

const DUMMY_DATA: Record<string, string> = {
    '{titulo}': 'Demon Slayer: Kimetsu no Yaiba',
    '{titulo_volumen}': 'Demon Slayer: Kimetsu no Yaiba - Volumen 01',
    '{romaji_title}': 'Kimetsu no Yaiba',
    '{english_title}': 'Demon Slayer',
    '{spanish_title}': 'Guardianes de la Noche',
    '{jap_title}': '鬼滅の刃',
    '{slug}': 'demon_slayer_kimetsu_no_yaiba',
    '{autor}': 'Koyoharu Gotouge',
    '{author_jap}': '吾峠 呼世晴',
    '{illustrator}': 'Koyoharu Gotouge',
    '{illustrator_jap}': '吾峠 呼世晴',
    '{serie}': 'Demon Slayer [NL]',
    '{series_spanish}': 'Guardianes de la Noche [NL]',
    '{series_english}': 'Demon Slayer [NL]',
    '{volumen}': 'Volumen 01',
    '{sinopsis}': 'Tanjiro Kamado es un chico inteligente y de buen corazón que vive con su familia y gana dinero vendiendo carbón. Todo cambia cuando su familia es atacada y asesinada por un demonio (oni).',
    '{resumen}': 'Una historia épica sobre un joven que se convierte en cazador de demonios para vengar a su familia.',
    '{etiquetas}': 'Acción, Fantasía, Demonios',
    '{idioma}': 'es',
    '{editorial}': 'Shueisha',
    '{traductor}': 'Demon Fansub',
    '{maquetador}': 'Demon Fansub',
    '{layout_by}': 'Demon Fansub',
    '{tipo}': 'Novela Ligera',
    '{tamaño}': '5.2 MB',
    '{rating}': '4.9',
    '{votes}': '128',
    '{hash}': 'DS_KNY_01',
    '{version}': '2.0',
    '{tags}': 'Acción, Fantasía, Demonios',
    '{genres}': 'Acción, Fantasía, Demonios',
    '{demography}': 'Shounen',
    '{published_at}': '2016-02-15',
    '{edition}': 'Digital',
    '{color_mode}': 'Color',
    '{is_uncensored}': 'Sí',
    '{archivo}': 'Demon_Slayer_v01.epub',
    '{isbn}': '978-4-08-880723-2',
    '{asin}': 'B01AXHUEPU',
    '{description}': 'Tanjiro Kamado es un chico inteligente y de buen corazón que vive con su familia y gana dinero vendiendo carbón.',
    '{fecha_actualizacion}': '2024-05-20',
    '{descargas_globales}': '1,234'
};

function convertHtmlToTelegramVisual(html: string): string {
    let result = html;

    result = result.replace(/<tg-spoiler>([\s\S]*?)<\/tg-spoiler>/gi, '<span class="tg-spoiler-preview">$1</span>');
    result = result.replace(/<span class="tg-spoiler[^"]*">([\s\S]*?)<\/span>/gi, '<span class="tg-spoiler-preview">$1</span>');

    result = result.replace(/<blockquote>([\s\S]*?)<\/blockquote>/gi, '<div class="tg-quote">$1</div>');

    result = result.replace(/<pre>([\s\S]*?)<\/pre>/gi, '<div class="tg-code-block"><code>$1</code></div>');

    result = result.replace(/<code>([\s\S]*?)<\/code>/gi, '<span class="tg-inline-code">$1</span>');

    result = result.replace(/<p>([\s\S]*?)<\/p>/gi, '$1\n');
    result = result.replace(/<br\s*\/?>/gi, '\n');
    result = result.replace(/<div>([\s\S]*?)<\/div>/gi, '$1\n');

    result = result.replace(/<hr\s*\/?>/gi, '\n---MSG_SPLIT---\n');

    return result;
}

export const TelegramMessagePreview: React.FC<TelegramMessagePreviewProps> = ({ content, templateName, coverQuality, sampleBook }) => {

    const messages = useMemo(() => {
        if (!content) return [];

        const mapping = { ...DUMMY_DATA };

        if (sampleBook) {
            mapping['{titulo}'] = sampleBook.title || mapping['{titulo}'];
            mapping['{slug}'] = sampleBook.title
                ? sampleBook.title.toLowerCase().replace(/[^a-z0-9\s-]/g, '').replace(/[\s_]+/g, '_').substring(0, 50)
                : mapping['{slug}'];
            mapping['{romaji_title}'] = sampleBook.romaji_title || mapping['{romaji_title}'];
            mapping['{english_title}'] = sampleBook.english_title || mapping['{english_title}'];
            mapping['{spanish_title}'] = sampleBook.spanish_title || mapping['{spanish_title}'];
            mapping['{jap_title}'] = sampleBook.jap_title || mapping['{jap_title}'];
            mapping['{autor}'] = sampleBook.author || mapping['{autor}'];
            mapping['{illustrator}'] = sampleBook.illustrator || mapping['{illustrator}'];
            mapping['{serie}'] = sampleBook.series || mapping['{serie}'];
            mapping['{series_spanish}'] = sampleBook.series_spanish || mapping['{series_spanish}'];
            mapping['{series_english}'] = sampleBook.series_english || mapping['{series_english}'];

            const volNum = sampleBook.volumeNumber || (sampleBook as any).volume || (sampleBook as any).series_index;
            mapping['{volumen}'] = volNum ? String(Math.floor(parseFloat(String(volNum)))) : mapping['{volumen}'];

            mapping['{tamaño}'] = sampleBook.size || mapping['{tamaño}'];
            mapping['{is_uncensored}'] = sampleBook.is_uncensored ? 'Sí' : 'No';
            mapping['{traductor}'] = sampleBook.translator || 'Desconocido';
            mapping['{maquetador}'] = sampleBook.layout_by || 'Desconocido';
            mapping['{layout_by}'] = sampleBook.layout_by || 'Desconocido';
            mapping['{tipo}'] = sampleBook.bookType || sampleBook.book_type || mapping['{tipo}'];
            mapping['{isbn}'] = sampleBook.isbn || mapping['{isbn}'];
            mapping['{archivo}'] = sampleBook.title ? `${sampleBook.title.replace(/\s+/g, '_')}.epub` : mapping['{archivo}'];
            mapping['{hash}'] = (sampleBook as any).book_hash || mapping['{hash}'];
            mapping['{rating}'] = sampleBook.rating ? String(sampleBook.rating) : mapping['{rating}'];
            mapping['{votes}'] = (sampleBook as any).rating_count ? String((sampleBook as any).rating_count) : mapping['{votes}'];
            mapping['{description}'] = (sampleBook as any).description || (sampleBook as any).summary || mapping['{description}'];
            mapping['{sinopsis}'] = (sampleBook as any).description || (sampleBook as any).summary || (sampleBook as any).sinopsis || mapping['{sinopsis}'];
            mapping['{resumen}'] = (sampleBook as any).summary || (sampleBook as any).description || (sampleBook as any).resumen || mapping['{resumen}'];
            mapping['{version}'] = (sampleBook as any).epub_version || mapping['{version}'];

            const pubDate = (sampleBook as any).published_at || '';
            if (pubDate && pubDate.includes('T')) {
                try {
                    const d = new Date(pubDate);
                    mapping['{published_at}'] = d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
                } catch {
                    mapping['{published_at}'] = pubDate.substring(0, 10);
                }
            } else {
                mapping['{published_at}'] = pubDate || mapping['{published_at}'];
            }

            mapping['{edition}'] = (sampleBook as any).edition || mapping['{edition}'];
            mapping['{color_mode}'] = (sampleBook as any).color_mode || mapping['{color_mode}'];
            mapping['{idioma}'] = (sampleBook as any).language || mapping['{idioma}'];
            mapping['{editorial}'] = (sampleBook as any).publisher || mapping['{editorial}'];
            mapping['{asin}'] = (sampleBook as any).asin || mapping['{asin}'];
            mapping['{titulo_volumen}'] = (sampleBook as any).title_volumen || sampleBook.title || mapping['{titulo_volumen}'];
            mapping['{author_jap}'] = (sampleBook as any).author_jap || mapping['{author_jap}'];
            mapping['{illustrator_jap}'] = (sampleBook as any).illustrator_jap || mapping['{illustrator_jap}'];
            mapping['{fecha_actualizacion}'] = (sampleBook as any).updated_at || (sampleBook as any).fecha_modificacion || mapping['{fecha_actualizacion}'];
            mapping['{descargas_globales}'] = (sampleBook as any).download_count || (sampleBook as any).total_downloads || '0';

            const tags = (sampleBook as any).tags || (sampleBook as any).genres || (sampleBook as any).etiquetas;
            if (tags && Array.isArray(tags)) {
                const tagsStr = tags.join(', ');
                mapping['{genres}'] = tagsStr;
                mapping['{tags}'] = tagsStr;
                mapping['{etiquetas}'] = tagsStr;
                mapping['{demography}'] = (sampleBook as any).demography ||
                    (tags.includes('Seinen') ? 'Seinen' :
                        tags.includes('Shounen') ? 'Shounen' :
                            tags.includes('Shoujo') ? 'Shoujo' :
                                tags.includes('Josei') ? 'Josei' : mapping['{demography}']);
            }
        }

        const evaluateConditional = (match: string, varName: string, innerContent: string) => {
            const key = `{${varName.toLowerCase()}}`;
            const value = mapping[key] || "";
            const lowerVal = value.toString().trim().toLowerCase();
            const emptyValues = ["", "desconocido", "desconocida", "0.0", "0", "0.00 mb", "0 mb", "false", "none", "no"];
            if (!lowerVal || emptyValues.includes(lowerVal)) {
                return "";
            }
            return innerContent;
        };

        let resultStr = content.replace(/\[\?(\w+)\](.*?)\[\/\?\]/gis, evaluateConditional);

        Object.entries(mapping).forEach(([key, value]) => {
            const regex = new RegExp(key.replace('{', '\\{').replace('}', '\\}'), 'gi');
            resultStr = resultStr.replace(regex, value);
        });

        resultStr = convertHtmlToTelegramVisual(resultStr);

        const parts = resultStr.split(/---MSG_SPLIT---|---next---|---/i);

        return parts.map(p => p.trim()).filter(p => p.length > 0);
    }, [content, sampleBook]);

    return (
        <div className="flex flex-col h-full rounded-premium overflow-hidden border border-white/10 bg-[#0e1621] font-sans">
            <div className="flex items-center gap-3 px-4 py-2 bg-[#17212b] border-b border-black/20 shrink-0">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-bold shadow-sm">
                    {templateName ? templateName.charAt(0).toUpperCase() : 'Z'}
                </div>
                <div className="flex flex-col">
                    <span className="text-white font-semibold text-sm">
                        {templateName || 'Vista Previa'}
                    </span>
                    <span className="text-[#7f91a4] text-xs">bot</span>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[url('https://telegram.org/file/464001088/2/5B5g3M1b0D8.127411/56c739199a5e4d2ebf')] bg-cover bg-center">
                <style>{`
                    .tg-spoiler-preview {
                        background: rgba(255, 255, 255, 0.15);
                        color: rgba(255, 255, 255, 0.15);
                        border-radius: 4px;
                        padding: 0 4px;
                        cursor: pointer;
                        transition: all 0.2s;
                    }
                    .tg-spoiler-preview:hover {
                        background: rgba(255, 255, 255, 0.25);
                        color: rgba(255, 255, 255, 0.25);
                    }
                    .tg-quote {
                        border-left: 4px solid rgba(96, 172, 248, 0.6);
                        padding: 8px 12px;
                        margin: 8px 0;
                        background: rgba(96, 172, 248, 0.1);
                        border-radius: 0 8px 8px 0;
                        color: rgba(255, 255, 255, 0.85);
                        font-style: italic;
                    }
                    .tg-code-block {
                        background: rgba(0, 0, 0, 0.4);
                        border-radius: 8px;
                        padding: 12px;
                        margin: 8px 0;
                        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                        font-size: 13px;
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        overflow-x: auto;
                    }
                    .tg-code-block code {
                        background: transparent;
                        padding: 0;
                        color: #e2e8f0;
                    }
                    .tg-inline-code {
                        background: rgba(0, 0, 0, 0.4);
                        padding: 2px 6px;
                        border-radius: 4px;
                        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                        font-size: 13px;
                        color: #e2e8f0;
                    }
                    .html-preview-content strong { font-weight: 700; }
                    .html-preview-content em, .html-preview-content i { font-style: italic; }
                    .html-preview-content u { text-decoration: underline; }
                    .html-preview-content s, .html-preview-content del { text-decoration: line-through; }
                    .html-preview-content a { color: #53a6e4; text-decoration: underline; }
                    .html-preview-content hr { 
                        border: none; 
                        border-top: 1px solid rgba(255,255,255,0.1); 
                        margin: 8px 0; 
                    }
                `}</style>

                {messages.length === 0 && (
                    <div className="flex justify-center mt-10">
                        <span className="bg-[#182533]/80 text-[#7f91a4] text-xs px-3 py-1 rounded-full backdrop-blur-sm">
                            El contenido aparecerá aquí...
                        </span>
                    </div>
                )}

                {messages.map((msg, idx) => {
                    let coverUrl = 'https://m.media-amazon.com/images/I/81Y1u+L4kRL._SL1500_.jpg';
                    if (sampleBook) {
                        coverUrl = getCoverUrl(
                            ('cover' in sampleBook ? (sampleBook as any).cover : sampleBook.coverUrl) as string,
                            ('cover_thumb' in sampleBook ? (sampleBook as any).cover_thumb : sampleBook.coverThumbUrl) as string,
                            coverQuality as any || 'mediana'
                        );
                    }

                    const showCover = idx === 0;
                    // Detectar si el mensaje contiene el archivo (buscando el nombre del dummy o la variable)
                    const hasFile = msg.includes('Demon_Slayer_v01.epub') || msg.includes('.epub') || msg.includes('.mobi') || msg.includes('.pdf');

                    return (
                        <div key={idx} className="flex flex-col items-start w-full animate-in fade-in slide-in-from-bottom-2 duration-300 relative">
                            {/* Indicadores de Tipo de Mensaje */}
                            <div className="flex gap-2 mb-1 pl-1">
                                {showCover && (
                                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-500/20 text-blue-400 text-[10px] font-bold uppercase tracking-wider border border-blue-500/30">
                                        🖼️ Foto + Caption
                                    </span>
                                )}
                                {hasFile && (
                                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-400 text-[10px] font-bold uppercase tracking-wider border border-amber-500/30">
                                        📎 Con Archivo EPUB
                                    </span>
                                )}
                                {!showCover && !hasFile && (
                                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-white/10 text-white/40 text-[10px] font-bold uppercase tracking-wider border border-white/5">
                                        📝 Mensaje de Texto
                                    </span>
                                )}
                            </div>

                            <div className="relative max-w-[85%] bg-[#182533] text-white rounded-2xl rounded-tl-none text-[15px] leading-relaxed shadow-sm flex flex-col overflow-hidden">
                                <svg className="absolute w-[11px] h-[20px] -left-[11px] top-0 text-[#182533] fill-current" viewBox="0 0 11 20">
                                    <path d="M11 20C11 20 11 0 11 0C11 0 5 0 2 0C-0.9 0 -0.1 3 1.5 4.5C3.1 6 11 20 11 20Z"></path>
                                </svg>

                                {showCover && (
                                    <div className="w-full relative group">
                                        <img src={coverUrl} alt="Cover Preview" className="w-full h-auto object-cover max-h-[350px] bg-[#101924]" />
                                        <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                            <span className="bg-black/60 px-2 py-1 rounded text-xs">Vista de Portada</span>
                                        </div>
                                    </div>
                                )}

                                <div className="px-3 pt-2 pb-2">
                                    <div
                                        className="html-preview-content space-y-2 [&>p]:m-0 break-words whitespace-pre-wrap"
                                        dangerouslySetInnerHTML={{ __html: msg }}
                                    />

                                    {/* Simulación de archivo adjunto si el tag está presente */}
                                    {hasFile && (
                                        <div className="mt-3 mb-1 p-2 bg-[#242f3d] rounded-xl border border-white/5 flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-lg bg-blue-500 flex items-center justify-center shrink-0 shadow-lg">
                                                <span className="text-white font-bold text-[10px]">EPUB</span>
                                            </div>
                                            <div className="flex flex-col min-w-0">
                                                <span className="text-sm font-medium truncate text-blue-400">
                                                    {sampleBook?.title || 'Demon_Slayer_v01'}.epub
                                                </span>
                                                <span className="text-[11px] text-[#768c9e]">
                                                    {sampleBook?.size || '5.2 MB'} • Documento
                                                </span>
                                            </div>
                                        </div>
                                    )}

                                    <div className="flex justify-end items-center gap-1 mt-1 -mb-1 float-right clear-both ml-3">
                                        <span className="text-[11px] text-[#768c9e]">12:00</span>
                                        <CheckCheck className="w-3.5 h-3.5 text-[#53a6e4]" />
                                    </div>
                                </div>
                            </div>

                            {showCover && (
                                <div className="mt-1 flex flex-col max-w-[85%] space-y-1 w-full pl-[2px]">
                                    <div className="flex gap-1 w-full">
                                        <button className="flex-1 bg-[#182533] text-[#53a6e4] hover:bg-[#202e3f] transition-colors py-2 px-3 rounded-xl text-sm font-semibold text-center border border-transparent">
                                            📖 Leer Online
                                        </button>
                                        <button className="flex-1 bg-[#182533] text-[#53a6e4] hover:bg-[#202e3f] transition-colors py-2 px-3 rounded-xl text-sm font-semibold text-center border border-transparent">
                                            🔽 Descargar
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )
                })}

            </div>

            <div className="bg-[#17212b] p-3 flex shrink-0">
                <div className="bg-[#242f3d] rounded-full w-full h-10 px-4 flex items-center text-[#7f91a4] text-sm">
                    Mensaje...
                </div>
            </div>
        </div>
    );
};
