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
    Tag
} from 'lucide-react';
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
        { icon: <LinkIcon className="w-4 h-4" />, action: setLink, active: editor.isActive('link'), title: 'Insertar Link' },
        { icon: <List className="w-4 h-4" />, action: () => editor.chain().focus().toggleBulletList().run(), active: editor.isActive('bulletList'), title: 'Lista' },
        { icon: <ListOrdered className="w-4 h-4" />, action: () => editor.chain().focus().toggleOrderedList().run(), active: editor.isActive('orderedList'), title: 'Lista numerada' },
        { icon: <Undo className="w-4 h-4" />, action: () => editor.chain().focus().undo().run(), active: false, title: 'Deshacer' },
        { icon: <Redo className="w-4 h-4" />, action: () => editor.chain().focus().redo().run(), active: false, title: 'Rehacer' },
    ];

    const placeholders = [
        { icon: <Type className="w-3.5 h-3.5" />, label: 'Título', value: 'title' },
        { icon: <User className="w-3.5 h-3.5" />, label: 'Autor', value: 'author' },
        { icon: <Book className="w-3.5 h-3.5" />, label: 'Serie', value: 'series' },
        { icon: <Layers className="w-3.5 h-3.5" />, label: 'Volumen', value: 'volume' },
        { icon: <Tag className="w-3.5 h-3.5" />, label: 'Etiquetas', value: 'tags' },
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
            StarterKit,
            Underline,
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
