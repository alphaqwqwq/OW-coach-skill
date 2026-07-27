import React, { useState, useCallback } from 'react';
import HomePage from './pages/HomePage';
import OWCoachPage from './pages/OWCoachPage';

export default function App() {
  const isCoach = window.location.hostname === 'coach.alphaqwq.xyz';
  const [page, setPage] = useState(isCoach ? 'ow-coach' : 'home');

  const goHome = useCallback(() => {
    if (isCoach) {
      window.location.href = 'https://alphaqwq.xyz';
    } else {
      setPage('home');
    }
  }, [isCoach]);

  if (page === 'ow-coach') {
    return <OWCoachPage onBack={goHome} />;
  }
  return <HomePage onNavigate={setPage} />;
}
