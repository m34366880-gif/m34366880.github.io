
import React, { useState, useCallback, useRef } from 'react';
import { SearchBar } from './components/SearchBar';
import { Sidebar } from './components/Sidebar';
import { GraphView } from './components/GraphView';
import { AnalyticsPanel } from './components/AnalyticsPanel';
import { Tabs } from './components/Tabs';
import { runInvestigation, generateReport, expandEntityAnalysis, performDeepAnalysisOnEntity } from './services/geminiService';
import { encrypt, decrypt } from './services/cryptoService';
import type { Tab, InvestigationData, Entity } from './types';
import { AppState, ViewMode, EntityType } from './types';
import { LogoIcon, InfoIcon, BrowserIcon, GraphIcon, SaveIcon, LoadIcon, ExportIcon } from './components/Icons';

const createNewTab = (id: string, title: string = "New Tab"): Tab => ({
    id,
    title,
    url: '',
    viewMode: ViewMode.Browser,
    appState: AppState.Idle,
    investigationData: null,
    report: '',
    error: null,
});

const App: React.FC = () => {
  const [tabs, setTabs] = useState<Tab[]>([createNewTab('tab-1')]);
  const [activeTabId, setActiveTabId] = useState<string>('tab-1');
  const [highlightedEntity, setHighlightedEntity] = useState<Entity | null>(null);
  const loadCaseInputRef = useRef<HTMLInputElement>(null);

  const activeTab = tabs.find(t => t.id === activeTabId) || tabs[0];
  
  const updateActiveTab = useCallback((update: Partial<Tab>) => {
      setTabs(prevTabs =>
          prevTabs.map(tab => (tab.id === activeTabId ? { ...tab, ...update } : tab))
      );
  }, [activeTabId]);

  const handleSearch = useCallback(async (searchTerm: string) => {
    if (!searchTerm || !activeTabId) return;
    
    let isUrl = searchTerm.startsWith('http://') || searchTerm.startsWith('https://') || searchTerm.startsWith('www.');
    if (isUrl && !searchTerm.startsWith('http')) {
        searchTerm = 'https://' + searchTerm;
    }

    if (isUrl) {
        updateActiveTab({ url: searchTerm, viewMode: ViewMode.Browser, title: searchTerm.split('/')[2] || "Web Page" });
    } else {
        updateActiveTab({ 
            appState: AppState.FetchingData,
            investigationData: null,
            report: '',
            error: null,
            viewMode: ViewMode.Analysis,
            title: `Analysis: ${searchTerm}`,
        });
        setHighlightedEntity(null);

        try {
            const data = await runInvestigation(searchTerm);
            updateActiveTab({ investigationData: data, appState: AppState.GeneratingReport });
            
            const generatedReport = await generateReport(data);
            updateActiveTab({ report: generatedReport, appState: AppState.Done });

        } catch (err) {
            console.error(err);
            updateActiveTab({
                error: 'An error occurred during the investigation. Please check the console and your API key.',
                appState: AppState.Error,
            });
        }
    }
  }, [activeTabId, updateActiveTab]);

  const handleNodeClick = async (entity: Entity) => {
    if (!activeTab.investigationData) return;

    updateActiveTab({ appState: AppState.ExpandingAnalysis });
    
    try {
        const currentData = activeTab.investigationData;
        let expansionData: InvestigationData;

        // Check if the entity is a file, breach, or source file for deep analysis
        if ([EntityType.File, EntityType.Breach, EntityType.SourceFile].includes(entity.type)) {
            expansionData = await performDeepAnalysisOnEntity(entity, currentData);
        } else {
            expansionData = await expandEntityAnalysis(entity, currentData);
        }
        
        // Merge new data with existing data
        const entityMap = new Map<string, Entity>();
        currentData.entities.forEach(e => entityMap.set(`${e.type}:${e.label}`, e));
        expansionData.entities.forEach(e => entityMap.set(`${e.type}:${e.label}`, e));

        const finalEntities = Array.from(entityMap.values());
        const finalEntityIds = new Set(finalEntities.map(e => e.id));

        const relationSet = new Set<string>();
        const allRelations = [...currentData.relations, ...expansionData.relations];
        const finalRelations = allRelations.filter(r => {
            if (finalEntityIds.has(r.from) && finalEntityIds.has(r.to)) {
                const key = `${r.from}-${r.to}-${r.label}`;
                if (!relationSet.has(key)) {
                    relationSet.add(key);
                    return true;
                }
            }
            return false;
        });
        
        const mergedData = { entities: finalEntities, relations: finalRelations };
        updateActiveTab({ investigationData: mergedData, appState: AppState.GeneratingReport });
        
        // Generate new report based on merged data
        const newReport = await generateReport(mergedData);
        updateActiveTab({ report: newReport, appState: AppState.Done });

    } catch (err) {
        console.error("Failed to expand entity analysis:", err);
        updateActiveTab({
            error: 'Failed to expand analysis for the selected entity.',
            appState: AppState.Error
        });
    }
  };

  const handleSaveCase = async () => {
    if (!activeTab.investigationData) {
        alert("No investigation data to save.");
        return;
    }
    const password = prompt("Enter a password to encrypt this case:");
    if (!password) return;

    try {
        const encryptedData = await encrypt(JSON.stringify(activeTab.investigationData), password);
        const blob = new Blob([encryptedData], { type: 'text/plain' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `nexus-osint-case-${activeTab.title.replace(/[^a-z0-9]/gi, '_')}.enc`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (e) {
        console.error("Encryption failed:", e);
        alert("Failed to encrypt and save the case.");
    }
  };

  const handleLoadCase = () => {
    loadCaseInputRef.current?.click();
  };

  const handleLoadCaseFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const password = prompt("Enter the password to decrypt this case:");
    if (!password) return;
    
    const reader = new FileReader();
    reader.onload = async (e) => {
        try {
            const encryptedData = e.target?.result as string;
            const decryptedJson = await decrypt(encryptedData, password);
            const data: InvestigationData = JSON.parse(decryptedJson);

            const newTabId = `tab-${Date.now()}`;
            const newTab: Tab = {
                ...createNewTab(newTabId, `Loaded: ${file.name.replace('.enc','')}`),
                investigationData: data,
                appState: AppState.GeneratingReport,
                viewMode: ViewMode.Analysis,
            };
            
            setTabs(prevTabs => [...prevTabs, newTab]);
            setActiveTabId(newTabId);

            const report = await generateReport(data);
            setTabs(prevTabs => prevTabs.map(t => t.id === newTabId ? {...t, report, appState: AppState.Done} : t));

        } catch (error) {
            console.error("Decryption failed:", error);
            alert("Failed to decrypt case. Incorrect password or corrupted file.");
        }
    };
    reader.readAsText(file);
    if (loadCaseInputRef.current) {
      loadCaseInputRef.current.value = "";
    }
  };
  
  const handleExportReport = () => {
    if (!activeTab.report) {
        alert("No report to export.");
        return;
    }
    const blob = new Blob([activeTab.report], { type: 'text/markdown;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `nexus-osint-report-${activeTab.title.replace(/[^a-z0-9]/gi, '_')}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const renderTabContent = () => {
    if (activeTab.viewMode === ViewMode.Browser) {
        if (!activeTab.url) {
            return (
                <div className="text-center text-gray-400 flex flex-col items-center justify-center h-full">
                    <div className="w-24 h-24 mb-6 text-gray-600"> <LogoIcon /> </div>
                    <h2 className="text-2xl font-bold text-gray-300">NexusOSINT Analysis Platform</h2>
                    <p className="mt-2 max-w-2xl"> Enter a URL to browse or a target to investigate. Use the toolbar to save or load an encrypted case. </p>
                </div>
            )
        }
        return <iframe src={activeTab.url} className="w-full h-full border-0 bg-white" title="Browser View"></iframe>;
    }

    if (activeTab.appState === AppState.Idle) return null;
     if (activeTab.appState === AppState.Error) {
        return (
            <div className="text-center text-red-400 flex flex-col items-center justify-center h-full p-4">
                <div className="w-16 h-16 mb-4 text-red-500"> <InfoIcon /> </div>
                <h2 className="text-2xl font-bold text-red-300">Operation Failed</h2>
                <p className="mt-2 max-w-2xl bg-red-900/50 p-3 rounded-lg"> {activeTab.error} </p>
            </div>
        );
    }
    
    return (
        <div className="flex-grow flex overflow-hidden">
            <div className="flex-none w-64 bg-gray-900/70 border-r border-gray-700 overflow-y-auto">
                <Sidebar 
                    data={activeTab.investigationData} 
                    onEntityHover={setHighlightedEntity}
                    onEntityLeave={() => setHighlightedEntity(null)}
                />
            </div>
            <div className="flex-grow flex flex-col">
                <div className="flex-grow p-4 relative">
                    <GraphView data={activeTab.investigationData} highlightedEntity={highlightedEntity} onNodeClick={handleNodeClick} />
                </div>
                <div className="flex-none h-1/2 border-t border-gray-700 overflow-y-auto">
                    <AnalyticsPanel 
                        report={activeTab.report} 
                        state={activeTab.appState}
                    />
                </div>
            </div>
        </div>
    )
  }
  
  const isLoading = [
        AppState.FetchingData, 
        AppState.GeneratingReport, 
        AppState.ExpandingAnalysis,
    ].includes(activeTab.appState);

  return (
    <div className="h-screen w-screen bg-gray-900 text-gray-200 flex flex-col font-sans">
        <Tabs tabs={tabs} activeTabId={activeTabId} onSelectTab={setActiveTabId} onNewTab={() => setTabs(prev => [...prev, createNewTab(`tab-${Date.now()}`)])} onCloseTab={(id) => {
            if (tabs.length === 1) return; // Prevent closing the last tab
            const tabIndex = tabs.findIndex(t => t.id === id);
            const newTabs = tabs.filter(t => t.id !== id);
            setTabs(newTabs);
            if (activeTabId === id) {
                const newActiveIndex = Math.max(0, tabIndex - 1);
                setActiveTabId(newTabs[newActiveIndex].id);
            }
        }} />
      <header className="flex-none p-3 border-b border-gray-700 bg-gray-800/50 shadow-lg flex items-center space-x-3">
        <SearchBar onSearch={handleSearch} isLoading={isLoading} />
        <div className="flex items-center space-x-2">
            <button onClick={() => updateActiveTab({ viewMode: ViewMode.Browser })} disabled={activeTab.viewMode === ViewMode.Browser} className="p-2 rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors" title="Browser View"><BrowserIcon /></button>
            <button onClick={() => updateActiveTab({ viewMode: ViewMode.Analysis })} disabled={activeTab.viewMode === ViewMode.Analysis || !activeTab.investigationData} className="p-2 rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors" title="Analysis View"><GraphIcon /></button>
            <div className="w-px h-6 bg-gray-600"></div>
            <button onClick={handleSaveCase} disabled={!activeTab.investigationData} className="p-2 rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors" title="Save Encrypted Case"><SaveIcon /></button>
            <button onClick={handleLoadCase} className="p-2 rounded-md hover:bg-gray-700 transition-colors" title="Load Encrypted Case"><LoadIcon /></button>
            <div className="w-px h-6 bg-gray-600"></div>
            <button onClick={handleExportReport} disabled={!activeTab.report} className="p-2 rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors" title="Export Report"><ExportIcon /></button>
            <input type="file" ref={loadCaseInputRef} onChange={handleLoadCaseFileChange} accept=".enc" className="hidden" />
        </div>
      </header>
      <main className="flex-grow flex overflow-hidden">
        {renderTabContent()}
      </main>
    </div>
  );
};

export default App;