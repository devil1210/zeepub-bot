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

// Datos falsos para mostrar en la previsualización
const DUMMY_DATA: Record<string, string> = {
    '{titulo}': 'Demon Slayer: Kimetsu no Yaiba',
    '{romaji_title}': 'Kimetsu no Yaiba',
    '{english_title}': 'Demon Slayer',
    '{spanish_title}': 'Guardianes de la Noche',
    '{jap_title}': '鬼滅の刃',
    '{autor}': 'Koyoharu Gotouge',
    '{illustrator}': 'Koyoharu Gotouge',
    '{serie}': 'Demon Slayer [NL]',
    '{series_spanish}': 'Guardianes de la Noche [NL]',
    '{series_english}': 'Demon Slayer [NL]',
    '{volumen}': 'Volumen 01',
    '{sinopsis}': 'Tanjiro Kamado es un chico inteligente y de buen corazón que vive con su familia y gana dinero vendiendo carbón. Todo cambia cuando su familia es atacada y asesinada por un demonio (oni).',
    '{tipo}': 'Novela Ligera',
    '{traductor}': 'Demon Fansub',
    '{layout_by}': 'Demon Fansub',
    '{editorial}': 'Shueisha',
    '{isbn}': '978-4-08-880723-2',
    '{rating}': '⭐ 4.9',
    '{tamaño}': '5.2 MB',
    '{cover_high}': '',
    '{cover_low}': '',
    '{cover_original}': '',
    '{published_at}': '2016-02-15',
    '{edition}': 'Digital',
    '{is_uncensored}': 'Sí',
    '{color_mode}': 'Color',
    '{language}': 'es',
    '{archivo}': 'Demon_Slayer_v01.epub',
    '{hash}': 'DS_KNY_01',
    '{demography}': 'Shounen',
    '{genres}': 'Acción, Fantasía, Demonios'
};


export const TelegramMessagePreview: React.FC<TelegramMessagePreviewProps> = ({ content, templateName, coverQuality, sampleBook }) => {

    // Parsear el contenido para generar las burbujas simuladas
    const messages = useMemo(() => {
        if (!content) return [];

        // Map DUMMY_DATA optionally extended with sampleBook properties
        const mapping = { ...DUMMY_DATA };
        if (sampleBook) {
            mapping['{titulo}'] = sampleBook.title || mapping['{titulo}'];
            mapping['{romaji_title}'] = sampleBook.romaji_title || mapping['{romaji_title}'];
            mapping['{english_title}'] = sampleBook.english_title || mapping['{english_title}'];
            mapping['{spanish_title}'] = sampleBook.spanish_title || mapping['{spanish_title}'];
            mapping['{jap_title}'] = sampleBook.jap_title || mapping['{jap_title}'];
            mapping['{autor}'] = sampleBook.author || mapping['{autor}'];
            mapping['{illustrator}'] = sampleBook.illustrator || mapping['{illustrator}'];
            mapping['{serie}'] = sampleBook.series || mapping['{serie}'];
            mapping['{series_spanish}'] = sampleBook.series_spanish || mapping['{series_spanish}'];
            mapping['{series_english}'] = sampleBook.series_english || mapping['{series_english}'];
            mapping['{volumen}'] = sampleBook.volumeNumber ? `Vol. ${sampleBook.volumeNumber}` : mapping['{volumen}'];
            mapping['{tamaño}'] = sampleBook.size || mapping['{tamaño}'];
            mapping['{is_uncensored}'] = sampleBook.is_uncensored ? 'Sí' : 'No';
            mapping['{traductor}'] = sampleBook.translator || 'Desconocido';
            mapping['{layout_by}'] = sampleBook.layout_by || 'Desconocido';
            mapping['{tipo}'] = sampleBook.bookType || mapping['{tipo}'];
            mapping['{isbn}'] = sampleBook.isbn || mapping['{isbn}'];
            mapping['{archivo}'] = sampleBook.title ? `${sampleBook.title.replace(/\s+/g, '_')}.epub` : mapping['{archivo}'];
            mapping['{hash}'] = (sampleBook as any).book_hash || mapping['{hash}'];

            // Handle arrays like genres
            const tags = (sampleBook as any).tags;
            if (tags && Array.isArray(tags)) {
                mapping['{genres}'] = tags.join(', ');
                mapping['{demography}'] = tags.includes('Seinen') ? 'Seinen' : (tags.includes('Shounen') ? 'Shounen' : mapping['{demography}']);
            }
        }

        // 1. Evaluar condicionales: [?variable]...[/?]
        const evaluateConditional = (match: string, varName: string, innerContent: string) => {
            const key = `{${varName.toLowerCase()}}`;
            const value = mapping[key] || "";
            // Considerar vacío si es Desconocido, 0.0, 0 MB, False o string vacío
            const lowerVal = value.toString().trim().toLowerCase();
            if (!lowerVal || lowerVal === "desconocido" || lowerVal === "0.0" || lowerVal === "0" || lowerVal === "0 mb" || lowerVal === "false" || lowerVal === "no") {
                return "";
            }
            return innerContent;
        };

        let resultStr = content.replace(/\[\?(\w+)\](.*?)\[\/?\]/gis, evaluateConditional);

        // Telegram parser: reemplazar variables
        Object.entries(mapping).forEach(([key, value]) => {
            // Regex case insensitive global para las variables
            const regex = new RegExp(key.replace('{', '\\{').replace('}', '\\}'), 'gi');
            resultStr = resultStr.replace(regex, value);
        });

        // Simular el comportamiento del backend: dividir por ---next--- o <hr>
        const parts = resultStr.split(/&lt;hr\s*\/?&gt;|<hr\s*\/?>|---next---|---/i);

        return parts.map(p => p.trim()).filter(p => p.length > 0);
    }, [content, sampleBook]);

    return (
        <div className="flex flex-col h-full rounded-premium overflow-hidden border border-white/10 bg-[#0e1621] font-sans">
            {/* Cabecera simulada de Telegram */}
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

            {/* Panel de mensajes (scrollable) */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[url('https://telegram.org/file/464001088/2/5B5g3M1b0D8.127411/56c739199a5e4d2ebf')] bg-cover bg-center">

                {messages.length === 0 && (
                    <div className="flex justify-center mt-10">
                        <span className="bg-[#182533]/80 text-[#7f91a4] text-xs px-3 py-1 rounded-full backdrop-blur-sm">
                            El contenido aparecerá aquí...
                        </span>
                    </div>
                )}

                {messages.map((msg, idx) => {
                    // Validar la URL de la imagen (de prueba o del libro)
                    let coverUrl = 'https://m.media-amazon.com/images/I/81Y1u+L4kRL._SL1500_.jpg'; // Fallback
                    if (sampleBook) {
                        coverUrl = getCoverUrl(('cover' in sampleBook ? (sampleBook as any).cover : sampleBook.coverUrl) as string, ('cover_thumb' in sampleBook ? (sampleBook as any).cover_thumb : sampleBook.coverThumbUrl) as string, coverQuality as any || 'mediana');
                    }

                    return (
                        <div key={idx} className="flex flex-col items-start w-full animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <div className="relative max-w-[85%] bg-[#182533] text-white rounded-2xl rounded-tl-none text-[15px] leading-relaxed shadow-sm flex flex-col overflow-hidden">
                                {/* Tail SVG */}
                                <svg className="absolute w-[11px] h-[20px] -left-[11px] top-0 text-[#182533] fill-current" viewBox="0 0 11 20">
                                    <path d="M11 20C11 20 11 0 11 0C11 0 5 0 2 0C-0.9 0 -0.1 3 1.5 4.5C3.1 6 11 20 11 20Z"></path>
                                </svg>

                                {/* Imagen de Portada (Telegram Caption Style) */}
                                <div className="w-full relative">
                                    <img src={coverUrl} alt="Cover Preview" className="w-full h-auto object-cover max-h-[350px] bg-[#101924]" />
                                </div>

                                <div className="px-3 pt-2 pb-2">
                                    <div
                                        className="html-preview-content space-y-2 [&>p]:m-0 [&>a]:text-[#53a6e4] [&>a]:underline-offset-2 [&>strong]:font-bold [&>em]:italic break-words"
                                        dangerouslySetInnerHTML={{ __html: msg }}
                                    />

                                    <div className="flex justify-end items-center gap-1 mt-1 -mb-1 float-right clear-both ml-3">
                                        <span className="text-[11px] text-[#768c9e]">12:00</span>
                                        <CheckCheck className="w-3.5 h-3.5 text-[#53a6e4]" />
                                    </div>
                                </div>
                            </div>

                            {/* Botones inline simulados */}
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
                        </div>
                    )
                })}

            </div>

            {/* Input simulado */}
            <div className="bg-[#17212b] p-3 flex shrink-0">
                <div className="bg-[#242f3d] rounded-full w-full h-10 px-4 flex items-center text-[#7f91a4] text-sm">
                    Mensaje...
                </div>
            </div>
        </div>
    );
};
