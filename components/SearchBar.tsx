
import React, { useState } from 'react';
import { SearchIcon, LoaderIcon } from './Icons';

interface SearchBarProps {
  onSearch: (term: string) => void;
  isLoading: boolean;
}

export const SearchBar: React.FC<SearchBarProps> = ({ onSearch, isLoading }) => {
  const [term, setTerm] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLoading) {
      onSearch(term);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex-grow">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400">
          <SearchIcon />
        </div>
        <input
          type="text"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          placeholder="Enter a URL to browse, or a target (domain, email, IP) to investigate..."
          className="w-full p-3 pl-12 pr-12 bg-gray-700 border border-gray-600 rounded-full text-gray-200 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 transition duration-300"
          disabled={isLoading}
        />
        {isLoading && (
          <div className="absolute inset-y-0 right-0 pr-4 flex items-center">
            <LoaderIcon />
          </div>
        )}
      </div>
    </form>
  );
};
