import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AssessmentProvider } from './context/AssessmentContext';

import { LoginPage } from './pages/auth/LoginPage';
import { ChangePasswordPage } from './pages/auth/ChangePasswordPage';

import { AuthorityLayout } from './components/authority/AuthorityLayout';
import { CommandCentrePage } from './pages/authority/CommandCentrePage';
import { FloodIntelligencePage } from './pages/authority/FloodIntelligencePage';
import { ImpactAnalysisPage } from './pages/authority/ImpactAnalysisPage';
import { NeighbourhoodPage } from './pages/authority/NeighbourhoodPage';
import { CriticalFacilitiesPage } from './pages/authority/CriticalFacilitiesPage';
import { EvacuationPlanningPage } from './pages/authority/EvacuationPlanningPage';
import { ShelterManagementPage } from './pages/authority/ShelterManagementPage';
import { RescueOperationsPage } from './pages/authority/RescueOperationsPage';
import { ScenarioSimulatorPage } from './pages/authority/ScenarioSimulatorPage';
import { RoadIntelligencePage } from './pages/authority/RoadIntelligencePage';
import { SituationReportsPage } from './pages/authority/SituationReportsPage';
import { DataOperationsPage } from './pages/authority/DataOperationsPage';
import { AIAssistantPage } from './pages/authority/AIAssistantPage';
import { SystemMonitorPage } from './pages/authority/SystemMonitorPage';

const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading, mustChangePassword } = useAuth();
  const location = useLocation();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-pravah-slate">
        <Loader2 className="w-5 h-5 animate-spin" aria-label="Loading" />
      </div>
    );
  }
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (mustChangePassword) return <ChangePasswordPage />;
  return <>{children}</>;
};

export default function App() {
  return (
    <AuthProvider>
      <AssessmentProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/authority" element={<RequireAuth><AuthorityLayout /></RequireAuth>}>
            <Route index element={<Navigate to="/authority/command" replace />} />
            <Route path="command" element={<CommandCentrePage />} />
            <Route path="flood" element={<FloodIntelligencePage />} />
            <Route path="impact" element={<ImpactAnalysisPage />} />
            <Route path="neighbourhoods" element={<NeighbourhoodPage />} />
            <Route path="facilities" element={<CriticalFacilitiesPage />} />
            <Route path="evacuation" element={<EvacuationPlanningPage />} />
            <Route path="shelters" element={<ShelterManagementPage />} />
            <Route path="rescue" element={<RescueOperationsPage />} />
            <Route path="scenario" element={<ScenarioSimulatorPage />} />
            <Route path="roads" element={<RoadIntelligencePage />} />
            <Route path="sitrep" element={<SituationReportsPage />} />
            <Route path="ai" element={<AIAssistantPage />} />
            <Route path="monitor" element={<SystemMonitorPage />} />
            <Route path="data-operations" element={<DataOperationsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/authority/command" replace />} />
        </Routes>
      </BrowserRouter>
      </AssessmentProvider>
    </AuthProvider>
  );
}
