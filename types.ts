
export enum EntityType {
    Domain = 'Domain',
    Email = 'Email',
    IP = 'IP Address',
    Username = 'Username',
    Breach = 'Data Breach',
    File = 'File',
    Organization = 'Organization',
    Person = 'Person',
    Unknown = 'Unknown',
    SourceFile = 'Source File',
    Password = 'Password',
    PasswordHash = 'Password Hash',
    SessionInfo = 'Session Info',
    APIKey = 'API Key',
    Cookie = 'Cookie'
}

export interface Entity {
    id: number;
    type: EntityType;
    label: string;
}

export interface Relation {
    from: number;
    to: number;
    label: string;
}

export interface InvestigationData {
    entities: Entity[];
    relations: Relation[];
}

export enum AppState {
    Idle = 'IDLE',
    FetchingData = 'FETCHING_DATA',
    GeneratingReport = 'GENERATING_REPORT',
    ExpandingAnalysis = 'EXPANDING_ANALYSIS',
    Done = 'DONE',
    Error = 'ERROR'
}

export enum ViewMode {
    Browser = 'BROWSER',
    Analysis = 'ANALYSIS'
}

export interface Tab {
    id: string;
    title: string;
    url: string;
    viewMode: ViewMode;
    appState: AppState;
    investigationData: InvestigationData | null;
    report: string;
    error: string | null;
}