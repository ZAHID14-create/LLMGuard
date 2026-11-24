import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Overview } from './pages/Overview';
import { Playground } from './pages/Playground';
import { Evaluation } from './pages/Evaluation';
import { Guardrails } from './pages/Guardrails';
import { Observability } from './pages/Observability';
import { Reports } from './pages/Reports';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<Overview />} />
          <Route path="/playground" element={<Playground />} />
          <Route path="/evaluation" element={<Evaluation />} />
          <Route path="/guardrails" element={<Guardrails />} />
          <Route path="/observability" element={<Observability />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
