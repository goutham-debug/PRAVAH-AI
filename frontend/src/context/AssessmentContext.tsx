import React, { createContext, useContext, useState } from 'react';

/** One shared assessment context for every module:
 *  - Same closures and rainfall assumption
 *  - Shared assessment ID, dataset version, and generation timestamp
 *  - Persisted for the browser session
 */
interface AssessmentState {
  closedRoads: string[];
  rainfall: string;
  assessmentId: string;
  datasetVersion: string;
  assessmentTimestamp: string;
  apply: (closedRoads: string[], rainfall: string) => void;
  reset: () => void;
  regenerateId: () => void;
}

const KEY = 'pravah_assessment';
const Ctx = createContext<AssessmentState | undefined>(undefined);

function makeAssessmentId(): string {
  const now = new Date();
  const d = now.toISOString().slice(0, 10).replace(/-/g, '');
  const t = now.toISOString().slice(11, 19).replace(/:/g, '');
  return `ASSESS-${d}-${t}`;
}

function load(): { closedRoads: string[]; rainfall: string; assessmentId: string; assessmentTimestamp: string } {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (raw) {
      const p = JSON.parse(raw);
      if (Array.isArray(p.closedRoads) && typeof p.rainfall === 'string') {
        return {
          closedRoads: p.closedRoads,
          rainfall: p.rainfall,
          assessmentId: p.assessmentId || makeAssessmentId(),
          assessmentTimestamp: p.assessmentTimestamp || new Date().toISOString(),
        };
      }
    }
  } catch { /* ignore */ }
  return {
    closedRoads: [],
    rainfall: 'HEAVY',
    assessmentId: makeAssessmentId(),
    assessmentTimestamp: new Date().toISOString(),
  };
}

export const AssessmentProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState(load);
  const datasetVersion = 'v2.4-mahadevapura-pilot';

  const apply = (closedRoads: string[], rainfall: string) => {
    const next = {
      closedRoads,
      rainfall,
      assessmentId: makeAssessmentId(),
      assessmentTimestamp: new Date().toISOString(),
    };
    setState(next);
    try { sessionStorage.setItem(KEY, JSON.stringify(next)); } catch { /* ignore */ }
  };

  const regenerateId = () => {
    const next = {
      ...state,
      assessmentId: makeAssessmentId(),
      assessmentTimestamp: new Date().toISOString(),
    };
    setState(next);
    try { sessionStorage.setItem(KEY, JSON.stringify(next)); } catch { /* ignore */ }
  };

  return (
    <Ctx.Provider
      value={{
        ...state,
        datasetVersion,
        apply,
        reset: () => apply([], 'HEAVY'),
        regenerateId,
      }}
    >
      {children}
    </Ctx.Provider>
  );
};

export const useAssessment = () => {
  const c = useContext(Ctx);
  if (!c) throw new Error('useAssessment must be used within AssessmentProvider');
  return c;
};
