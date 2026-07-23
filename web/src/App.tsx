import React, { useState } from 'react';
import HomePage from './pages/HomePage';
import OWCoachPage from './pages/OWCoachPage';

export default function App() {
  const [page, setPage] = useState<string>('home');

  switch (page) {
    case 'ow-coach':
      return <OWCoachPage onBack={() => setPage('home')} />;
    default:
      return <HomePage onNavigate={setPage} />;
  }
}
