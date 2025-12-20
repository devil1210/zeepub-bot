import React from 'react';

const SearchBar = ({ onSearch }) => {
    return (
        <div className="w-full mb-4">
            <div className="relative flex items-center group">
                <div style={{ position: 'absolute', left: '16px', color: '#546675', pointerEvents: 'none' }}>
                    <svg style={{ width: '18px', height: '18px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
                <input
                    type="text"
                    placeholder="Search"
                    onChange={(e) => onSearch(e.target.value)}
                    style={{ width: '100%', backgroundColor: '#1c2732', color: '#ffffff', fontSize: '17px', padding: '12px 16px 12px 48px', borderRadius: '12px', border: '1px solid transparent', outline: 'none' }}
                    className="focus:border-[#2481cc]/30 transition-all shadow-inner"
                />
            </div>
        </div>
    );
};

export default SearchBar;
