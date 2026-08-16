import React, { useEffect } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Underline from '@tiptap/extension-underline';
import Placeholder from '@tiptap/extension-placeholder';
import Link from '@tiptap/extension-link';
import {
    Bold,
    Italic,
    Underline as UnderlineIcon,
    Link as LinkIcon,
    List,
    ListOrdered,
    Undo,
    Redo,
    Type,
    User,
    Book,
    Layers,
    Tag,
    Globe,
    Building2,
    Users,
    FileText,
    Monitor,
    Star,
    HardDrive,
    Image as ImageIcon,
    MessageSquarePlus,
    Calendar,
    BookOpen,
    ShieldCheck,
    Palette,
    Languages,
    FileArchive,
    Strikethrough,
    Code,
    Terminal,
    Quote,
    EyeOff,
    SeparatorHorizontal,
} from 'lucide-react';
import { Spoiler } from './Spoiler';
import './RichTextEditor.css';

interface RichTextEditorProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
}

const MenuBar = ({ editor }: { editor: any }) => {
    if (!editor) {
        return null;
    }

    const setLink = () => {
        const previousUrl = editor.getAttributes('link').href;
        const url = window.prompt('URL', previousUrl);

        if (url === null) {
            return;
        }

        if (url === '') {
            editor.chain().focus().extendMarkRange('link').unsetLink().run();
            return;
        }

        editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
    };

    const insertPlaceholder = (text: string) => {
        editor.chain().focus().insertContent(`{${text}}`).run();
    };

    const buttons = [
        { icon: <Bold className="w-4 h-4" />, action: () => editor.chain().focus().toggleBold().run(), active: editor.isActive('bold'), title: 'Negrita' },
        { icon: <Italic className="w-4 h-4" />, action: () => editor.chain().focus().toggleItalic().run(), active: editor.isActive('italic'), title: 'Cursiva' },
        { icon: <UnderlineIcon className="w-4 h-4" />, action: () => editor.chain().focus().toggleUnderline().run(), active: editor.isActive('underline'), title: 'Subrayado' },
        { icon: <Strikethrough className="w-4 h-4" />, action: () => editor.chain().focus().toggleStrike().run(), active: editor.isActive('strike'), title: 'Tachado' },
        { icon: <EyeOff className="w-4 h-4" />, action: () => editor.chain().focus().toggleSpoiler().run(), active: editor.isActive('spoiler'), title: 'Spoiler' },
        { icon: <LinkIcon className="w-4 h-4" />, action: setLink, active: editor.isActive('link'), title: 'Insertar Link' },
        { icon: <Code className="w-4 h-4" />, action: () => editor.chain().focus().toggleCode().run(), active: editor.isActive('code'), title: 'Código' },
        { icon: <Terminal className="w-4 h-4" />, action: () => editor.chain().focus().toggleCodeBlock().run(), active: editor.isActive('codeBlock'), title: 'Bloque de código' },
        { icon: <Quote className="w-4 h-4" />, action: () => editor.chain().focus().toggleBlockquote().run(), active: editor.isActive('blockquote'), title: 'Cita' },
        { icon: <List className="w-4 h-4" />, action: () => editor.chain().focus().toggleBulletList().run(), active: editor.isActive('bulletList'), title: 'Lista' },
        { icon: <ListOrdered className="w-4 h-4" />, action: () => editor.chain().focus().toggleOrderedList().run(), active: editor.isActive('orderedList'), title: 'Lista numerada' },
        { icon: <SeparatorHorizontal className="w-4 h-4" />, action: () => editor.chain().focus().setHorizontalRule().run(), active: false, title: 'Separador' },
        { icon: <Undo className="w-4 h-4" />, action: () => editor.chain().focus().undo().run(), active: false, title: 'Deshacer' },
        { icon: <Redo className="w-4 h-4" />, action: () => editor.chain().focus().redo().run(), active: false, title: 'Rehacer' },
        {
            icon: <MessageSquarePlus className="w-4 h-4 text-primary" />,
            action: () => editor.chain().focus().insertContent('\n\n---next---\n\n').run(),
            active: false,
            title: 'Siguiente Mensaje (Divide la publicación)'
        },
    ];

    const placeholders = [
        { icon: <Type className="w-3 h-3" />, label: 'Título', value: 'titulo' },
        { icon: <Type className="w-3 h-3" />, label: 'Romaji', value: 'romaji_title' },
        { icon: <Type className="w-3 h-3" />, label: 'Japonés', value: 'jap_title' },
        { icon: <User className="w-3 h-3" />, label: 'Autor', value: 'autor' },
        { icon: <User className="w-3 h-3" />, label: 'Ilustrador', value: 'illustrator' },
        { icon: <Book className="w-3 h-3" />, label: 'Serie', value: 'serie' },
        { icon: <Layers className="w-3 h-3" />, label: 'Volumen', value: 'volumen' },
        { icon: <FileText className="w-3 h-3" />, label: 'Sinopsis', value: 'sinopsis' },
        { icon: <FileText className="w-3 h-3" />, label: 'Resumen', value: 'resumen' },
        { icon: <Monitor className="w-3 h-3" />, label: 'Tipo', value: 'tipo' },
        { icon: <Users className="w-3 h-3" />, label: 'Traductor', value: 'traductor' },
        { icon: <Users className="w-3 h-3" />, label: 'Maquetador', value: 'layout_by' },
        { icon: <Building2 className="w-3 h-3" />, label: 'Editorial', value: 'editorial' },
        { icon: <Tag className="w-3 h-3" />, label: 'ISBN/ID', value: 'isbn' },
        { icon: <Star className="w-3 h-3" />, label: 'Rating', value: 'rating' },
        { icon: <Star className="w-3 h-3" />, label: 'Votos', value: 'votes' },
        { icon: <HardDrive className="w-3 h-3" />, label: 'Tamaño', value: 'tamaño' },
        { icon: <Tag className="w-3 h-3" />, label: 'Hash', value: 'hash' },
        { icon: <Tag className="w-3 h-3" />, label: 'Versión', value: 'version' },
        { icon: <Tag className="w-3 h-3" />, label: 'Demografía', value: 'demography' },
        { icon: <Tag className="w-3 h-3" />, label: 'Géneros', value: 'genres' },
        { icon: <Tag className="w-3 h-3" />, label: 'Tags', value: 'tags' },
        { icon: <ImageIcon className="w-3 h-3" />, label: 'Portada HD', value: 'cover_high' },
        { icon: <ImageIcon className="w-3 h-3" />, label: 'Portada SD', value: 'cover_low' },
        { icon: <Calendar className="w-3 h-3 text-amber-400" />, label: 'Actualizado', value: 'fecha' },
        { icon: <Calendar className="w-3 h-3" />, label: 'Fecha Publ.', value: 'published_at' },
        { icon: <Users className="w-3 h-3 text-blue-400" />, label: 'Fansub', value: 'grupo_traductor' },
        { icon: <LinkIcon className="w-3 h-3 text-blue-300" />, label: 'Links Fansub', value: 'grupo_links' },
        { icon: <User className="w-3 h-3 text-purple-400" />, label: 'Editor', value: 'editor' },
        { icon: <LinkIcon className="w-3 h-3 text-purple-300" />, label: 'Links Editor', value: 'editor_links' },
        { icon: <LinkIcon className="w-3 h-3 text-green-300" />, label: 'Links Maquet.', value: 'maquetador_links' },
        { icon: <FileText className="w-3 h-3" />, label: 'Palabras', value: 'palabras' },
        { icon: <FileText className="w-3 h-3" />, label: 'Páginas', value: 'paginas' },
        { icon: <Tag className="w-3 h-3" />, label: 'ASIN', value: 'asin' },
        { icon: <BookOpen className="w-3 h-3" />, label: 'Edición', value: 'edition' },
        { icon: <ShieldCheck className="w-3 h-3" />, label: 'Sin Censura', value: 'is_uncensored' },
        { icon: <Palette className="w-3 h-3" />, label: 'Color/B&N', value: 'color_mode' },
        { icon: <Languages className="w-3 h-3" />, label: 'Idioma', value: 'language' },
        { icon: <FileArchive className="w-3 h-3" />, label: 'Archivo', value: 'archivo' },
        { icon: <LinkIcon className="w-3 h-3 border-primary text-primary" />, label: 'Descarga', value: 'download_link' }
    ];

    return (
        <div className="flex flex-col gap-2 border-b border-white/10 p-2 bg-white/5">
            <div className="flex flex-wrap gap-1">
                {buttons.map((btn, i) => (
                    <button
                        key={i}
                        type="button"
                        onClick={btn.action}
                        title={btn.title}
                        className={`p-1.5 rounded-lg transition-all ${btn.active ? 'bg-primary text-white shadow-lg' : 'text-gray-400 hover:text-white hover:bg-white/10'}`}
                    >
                        {btn.icon}
                    </button>
                ))}
            </div>
            <div className="flex flex-wrap gap-1.5 pt-1 border-t border-white/5">
                <span className="text-[9px] font-black uppercase tracking-widest text-gray-500 flex items-center mr-1">Variables:</span>
                {placeholders.map((p, i) => (
                    <button
                        key={i}
                        type="button"
                        onClick={() => insertPlaceholder(p.value)}
                        className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-white/5 hover:bg-white/10 text-gray-400 hover:text-primary transition-all group border border-white/5"
                    >
                        {p.icon}
                        <span className="text-[9px] font-bold uppercase tracking-wider">{p.label}</span>
                    </button>
                ))}
            </div>
        </div>
    );
};

export const RichTextEditor: React.FC<RichTextEditorProps> = ({ value, onChange, placeholder }) => {
    const editor = useEditor({
        extensions: [
            StarterKit.configure({
                codeBlock: {
                    HTMLAttributes: {
                        class: 'bg-black/40 rounded-lg p-3 font-mono text-sm border border-white/5 my-2',
                    },
                },
                blockquote: {
                    HTMLAttributes: {
                        class: 'border-l-4 border-primary/50 pl-4 py-1 my-2 italic text-gray-400 bg-white/5 rounded-r-lg',
                    },
                },
            }),
            Underline,
            Spoiler,
            Link.configure({
                openOnClick: false,
                HTMLAttributes: {
                    class: 'text-primary underline cursor-pointer',
                },
            }),
            Placeholder.configure({
                placeholder: placeholder || 'Escribe algo increíble...',
            }),
        ],
        content: value,
        onUpdate: ({ editor }) => {
            onChange(editor.getHTML());
        },
    });

    // Sincronizar valor externo (ej. al cargar)
    useEffect(() => {
        if (editor && value !== editor.getHTML()) {
            editor.commands.setContent(value);
        }
    }, [value, editor]);

    return (
        <div className="rich-text-editor-container glass-panel !bg-black/20 border border-white/10 rounded-premium overflow-hidden focus-within:border-primary/50 transition-all">
            <MenuBar editor={editor} />
            <EditorContent editor={editor} className="min-h-[150px] p-4 text-sm text-gray-200 focus:outline-none" />
        </div>
    );
};
