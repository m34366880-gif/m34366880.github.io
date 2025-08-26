
import React from 'react';
import { AppState } from '../types';
import { LoaderIcon } from './Icons';

interface AnalyticsPanelProps {
  report: string;
  state: AppState;
}

const formatReport = (rawReport: string): React.ReactNode[] => {
    const nodes: React.ReactNode[] = [];
    let currentListItems: React.ReactNode[] = [];

    const flushList = () => {
        if (currentListItems.length > 0) {
            nodes.push(<ul key={`ul-${nodes.length}`} className="list-disc ml-5 space-y-1 my-2">{currentListItems}</ul>);
            currentListItems = [];
        }
    };

    rawReport.split('\n').forEach((line, index) => {
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith('* ')) {
            const itemHtml = trimmedLine.substring(2).replace(/\*\*(.*?)\*\*/g, '<strong class="text-amber-400 font-semibold">$1</strong>');
            currentListItems.push(<li key={`li-${index}`} dangerouslySetInnerHTML={{ __html: itemHtml }} />);
        } else {
            flushList();
            if (line.startsWith('### ')) {
                nodes.push(<h3 key={index} className="text-lg font-semibold text-cyan-400 mt-4 mb-2">{line.substring(4)}</h3>);
            } else if (line.startsWith('## ')) {
                nodes.push(<h2 key={index} className="text-xl font-bold text-cyan-300 mt-6 mb-3 border-b border-gray-600 pb-1">{line.substring(3)}</h2>);
            } else if (line.startsWith('# ')) {
                nodes.push(<h1 key={index} className="text-2xl font-bold text-cyan-200 mt-4 mb-4">{line.substring(2)}</h1>);
            } else if (trimmedLine !== '') {
                const p_html = line.replace(/\*\*(.*?)\*\*/g, '<strong class="text-amber-400 font-semibold">$1</strong>');
                nodes.push(<p key={index} className="text-gray-300 mb-2 leading-relaxed" dangerouslySetInnerHTML={{ __html: p_html }} />);
            }
        }
    });
    
    flushList();

    return nodes;
};


export const AnalyticsPanel: React.FC<AnalyticsPanelProps> = ({ report, state }) => {

  const renderContent = () => {
    switch (state) {
      case AppState.GeneratingReport:
        return (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <LoaderIcon />
            <p className="mt-4 text-lg">AI is analyzing data and generating the report...</p>
            <p className="text-sm text-gray-500">This may take a moment.</p>
          </div>
        );
      case AppState.ExpandingAnalysis:
        return (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <LoaderIcon />
            <p className="mt-4 text-lg">Performing deeper analysis on selected entity...</p>
            <p className="text-sm text-gray-500">Expanding the investigation graph.</p>
          </div>
        );
      case AppState.Done:
        return (
            <div className="relative h-full">
                <div className="prose prose-invert prose-sm max-w-none p-6">{formatReport(report)}</div>
            </div>
        );
      default:
        return (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>Analytical report will appear here once data is processed.</p>
          </div>
        );
    }
  };

  return (
    <div className="h-full bg-gray-800/60 overflow-y-auto">
      {renderContent()}
    </div>
  );
};
