import React from 'react';

const SearchBar = ({ onSearch }) => {
    return (
        <div className="w-full max-w-md mx-auto mb-6 px-2">
            <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-gray-500 group-focus-within:text-blue-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 70 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
                <input
                    type="text"
                    className="block w-full h-11 pl-12 pr-4 border-none rounded-full leading-tight bg-[#242f3d] text-white placeholder-gray-500 focus:ring-1 focus:ring-blue-500/50 outline-none transition-all duration-200 text-base"
                    placeholder="Search"
                    onChange={(e) => onSearch(e.target.value)}
                />
            </div>
        </div>
    );
};

export default SearchBar;
