import React, { useState } from 'react';
import { ArrowLeft, Settings, List, Search, Bookmark } from 'lucide-react';

export const Reader: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [progress, setProgress] = useState(32);

  return (
    <div className="fixed inset-0 z-50 bg-background text-gray-300 flex flex-col font-serif">
      {/* HUD Header */}
      <header className="fixed top-0 w-full z-50 px-6 h-16 flex items-center justify-between glass-panel border-b border-white/10 transition-transform duration-300">
        <div className="flex items-center gap-4">
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-white/10">
            <ArrowLeft className="w-6 h-6" />
          </button>
          <div className="hidden sm:block">
            <h1 className="text-sm font-semibold text-white tracking-wide font-sans">Atomic Habits</h1>
            <p className="text-xs text-gray-400 font-sans">James Clear • Chapter 3</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="text-gray-400 hover:text-white p-2 rounded-lg hover:bg-white/10"><List className="w-5 h-5"/></button>
          <button className="text-gray-400 hover:text-white p-2 rounded-lg hover:bg-white/10"><Settings className="w-5 h-5"/></button>
          <button className="text-gray-400 hover:text-white p-2 rounded-lg hover:bg-white/10"><Search className="w-5 h-5"/></button>
          <button className="text-gray-400 hover:text-white p-2 rounded-lg hover:bg-white/10"><Bookmark className="w-5 h-5"/></button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto w-full h-full pt-24 pb-24 px-4 sm:px-8 max-w-3xl mx-auto">
        <div className="prose prose-invert prose-lg max-w-none prose-p:text-gray-300 prose-headings:text-white">
          <h2 className="text-3xl font-bold text-white mb-8">How to Build Better Habits in 4 Simple Steps</h2>
          
          <p className="mb-6 leading-loose text-lg">
            In 1898, a psychologist named Edward Thorndike conducted an experiment that would lay the foundation for our understanding of how habits form and the rules that guide our behavior. Thorndike was interested in the study of animal behavior, and he started by working with cats.
          </p>
          
          <p className="mb-6 leading-loose text-lg">
            He would place each cat inside a device known as a "puzzle box." The box was designed so that the cat could escape through a door by some simple act, such as pulling on a loop of cord, pressing a lever, or stepping on a platform. For example, one box contained a lever that, when pressed, would open the door on the side of the box. Once the door had been opened, the cat could dart out and run over to a bowl of food.
          </p>

          <div className="my-8 p-6 bg-white/5 rounded-xl border-l-4 border-primary italic text-gray-400">
            "Habits are the compound interest of self-improvement."
          </div>

          <p className="mb-6 leading-loose text-lg">
            Thorndike tracked the behavior of each cat across many trials. In the beginning, the animals moved around the box at random. But as soon as the lever was pressed and the door opened, the process of learning began. Gradually, each cat learned to associate the action of pressing the lever with the reward of escaping the box and getting food.
          </p>
          
          <p className="mb-6 leading-loose text-lg">
            From his studies, Thorndike described the learning process by stating, "behaviors followed by satisfying consequences tend to be repeated and those that produce unpleasant consequences are less likely to be repeated."
          </p>
        </div>
      </main>

      {/* HUD Footer */}
      <footer className="fixed bottom-0 w-full z-50 px-6 py-4 glass-panel border-t border-white/10 font-sans">
        <div className="max-w-4xl mx-auto flex flex-col gap-4">
          <div className="w-full flex items-center gap-4 text-xs font-medium text-gray-400">
            <span>0%</span>
            <div className="relative flex-1 h-1.5 bg-gray-700/50 rounded-full cursor-pointer group">
              <div className="absolute top-0 left-0 h-full bg-primary rounded-full transition-all" style={{ width: `${progress}%` }}></div>
              <input 
                type="range" 
                min="0" 
                max="100" 
                value={progress} 
                onChange={(e) => setProgress(Number(e.target.value))}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
            </div>
            <span>{progress}%</span>
          </div>
          <div className="flex justify-center text-xs text-gray-500 font-mono">
            Page 45 of 210
          </div>
        </div>
      </footer>
    </div>
  );
};