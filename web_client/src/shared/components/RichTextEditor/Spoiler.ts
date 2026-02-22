import { Mark, mergeAttributes } from '@tiptap/core';

export interface SpoilerOptions {
    HTMLAttributes: Record<string, any>;
}

declare module '@tiptap/core' {
    interface Commands<ReturnType> {
        spoiler: {
            /**
             * Set a spoiler mark
             */
            setSpoiler: () => ReturnType;
            /**
             * Toggle a spoiler mark
             */
            toggleSpoiler: () => ReturnType;
            /**
             * Unset a spoiler mark
             */
            unsetSpoiler: () => ReturnType;
        };
    }
}

export const Spoiler = Mark.create<SpoilerOptions>({
    name: 'spoiler',

    addOptions() {
        return {
            HTMLAttributes: {
                class: 'tg-spoiler',
            },
        };
    },

    parseHTML() {
        return [
            {
                tag: 'span',
                getAttrs: element => (element as HTMLElement).classList.contains('tg-spoiler') && null,
            },
            {
                tag: 'tg-spoiler',
            },
        ];
    },

    renderHTML({ HTMLAttributes }) {
        return ['tg-spoiler', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), 0];
    },

    addCommands() {
        return {
            setSpoiler: () => ({ commands }) => {
                return commands.setMark(this.name);
            },
            toggleSpoiler: () => ({ commands }) => {
                return commands.toggleMark(this.name);
            },
            unsetSpoiler: () => ({ commands }) => {
                return commands.unsetMark(this.name);
            },
        };
    },
});
