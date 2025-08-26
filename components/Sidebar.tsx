
import React, { useMemo } from 'react';
import type { InvestigationData, Entity } from '../types';
import { EntityType } from '../types';
import { DomainIcon, EmailIcon, IPIcon, UserIcon, BreachIcon, FileIcon, OrgIcon, PersonIcon, UnknownIcon, SourceFileIcon, PasswordIcon, HashIcon, SessionIcon, APIKeyIcon, CookieIcon } from './Icons';

interface SidebarProps {
  data: InvestigationData | null;
  onEntityHover: (entity: Entity) => void;
  onEntityLeave: (entity: Entity) => void;
}

const getIconForType = (type: EntityType) => {
    switch (type) {
        case EntityType.Domain: return <DomainIcon />;
        case EntityType.Email: return <EmailIcon />;
        case EntityType.IP: return <IPIcon />;
        case EntityType.Username: return <UserIcon />;
        case EntityType.Breach: return <BreachIcon />;
        case EntityType.File: return <FileIcon />;
        case EntityType.Organization: return <OrgIcon />;
        case EntityType.Person: return <PersonIcon />;
        case EntityType.SourceFile: return <SourceFileIcon />;
        case EntityType.Password: return <PasswordIcon />;
        case EntityType.PasswordHash: return <HashIcon />;
        case EntityType.SessionInfo: return <SessionIcon />;
        case EntityType.APIKey: return <APIKeyIcon />;
        case EntityType.Cookie: return <CookieIcon />;
        default: return <UnknownIcon />;
    }
}

export const Sidebar: React.FC<SidebarProps> = ({ data, onEntityHover, onEntityLeave }) => {
  // FIX: Explicitly type the return value of useMemo and the accumulator in reduce.
  // This ensures `groupedEntities` has a consistent type (`Record<string, Entity[]>`),
  // which resolves downstream TypeScript errors where `entities` was inferred as `unknown`.
  const groupedEntities = useMemo((): Record<string, Entity[]> => {
    if (!data?.entities) return {};
    return data.entities.reduce((acc: Record<string, Entity[]>, entity) => {
      (acc[entity.type] = acc[entity.type] || []).push(entity);
      return acc;
    }, {});
  }, [data]);

  return (
    <div className="p-4 h-full text-gray-300">
      <h2 className="text-xl font-bold mb-4 text-cyan-400 border-b border-gray-700 pb-2">Discovered Entities</h2>
      {data && data.entities.length > 0 ? (
        <div className="space-y-4">
          {Object.entries(groupedEntities).sort(([typeA], [typeB]) => { // Sort to show Source File first
            if (typeA === EntityType.SourceFile) return -1;
            if (typeB === EntityType.SourceFile) return 1;
            return typeA.localeCompare(typeB);
          }).map(([type, entities]) => (
            <div key={type}>
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">{type} ({entities.length})</h3>
              <ul className="space-y-1">
                {entities.map(entity => (
                  <li 
                    key={entity.id} 
                    className="flex items-center space-x-2 text-sm p-1.5 rounded-md hover:bg-gray-700/50 transition-colors cursor-pointer"
                    onMouseEnter={() => onEntityHover(entity)}
                    onMouseLeave={() => onEntityLeave(entity)}
                  >
                    <span className="w-5 h-5 text-cyan-500 flex-shrink-0">{getIconForType(entity.type as EntityType)}</span>
                    <span className="truncate" title={entity.label}>{entity.label}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-500 italic">No entities found yet. Start an investigation or analyze a data dump.</p>
      )}
    </div>
  );
};