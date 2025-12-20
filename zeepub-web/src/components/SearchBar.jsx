import React from 'react';

const SearchBar = ({ onSearch }) => {
    return (
        <div className="w-full mb-4">
            <div className="relative flex items-center group">
                <div className="absolute left-4 text-[#546675] group-focus-within:text-telegram-link transition-colors pointer-events-none">
                    <svg className="w-4.5 h-4.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
                <input
                    type="text"
                    placeholder="Search"
                    onChange={(e) => onSearch(e.target.value)}
                    className="w-full bg-[#1c2732] text-white text-[17px] pl-12 pr-4 py-3 rounded-xl border border-transparent focus:border-telegram-link/30 outline-none transition-all placeholder-[#546675] shadow-inner"
                />
            </div>
        </div>
    );
};

export default SearchBar;
