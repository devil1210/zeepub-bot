import React from 'react';

const SearchBar = ({ onSearch }) => {
    return (
        <div className="w-full max-w-sm px-6 mb-6">
            <div className="relative flex items-center group">
                <div className="absolute left-4 text-gray-500 group-focus-within:text-blue-500 transition-colors pointer-events-none">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
                <input
                    type="text"
                    placeholder="Search"
                    onChange={(e) => onSearch(e.target.value)}
                    className="w-full bg-[#242f3d] text-white text-[15px] pl-11 pr-4 py-2.5 rounded-xl border border-transparent focus:border-[#2481cc]/30 outline-none transition-all placeholder-[#7f8c99]"
                />
            </div>
        </div>
    );
};

export default SearchBar;
