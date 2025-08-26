
import React from 'react';
import type { Tab } from '../types';
import { PlusIcon, CloseIcon } from './Icons';

interface TabsProps {
    tabs: Tab[];
    activeTabId: string;
    onSelectTab: (id: string) => void;
    onNewTab: () => void;
    onCloseTab: (id: string) => void;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, activeTabId, onSelectTab, onNewTab, onCloseTab }) => {
    return (
        <div className="flex-none bg-gray-800 border-b border-gray-700 flex items-center">
            <div className="flex items-center overflow-x-auto">
                {tabs.map(tab => (
                    <div
                        key={tab.id}
                        onClick={() => onSelectTab(tab.id)}
                        className={`flex items-center space-x-2 py-2 px-4 border-r border-gray-700 cursor-pointer transition-colors ${
                            activeTabId === tab.id
                                ? 'bg-gray-900 text-cyan-400'
                                : 'text-gray-400 hover:bg-gray-700/50'
                        }`}
                    >
                        <span className="truncate max-w-xs text-sm">{tab.title}</span>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onCloseTab(tab.id);
                            }}
                            className="p-1 rounded-full hover:bg-gray-600"
                        >
                            <CloseIcon />
                        </button>
                    </div>
                ))}
            </div>
            <button onClick={onNewTab} className="p-2 text-gray-400 hover:bg-gray-700/50">
                <PlusIcon />
            </button>
        </div>
    );
};
