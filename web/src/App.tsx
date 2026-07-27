import React, { useState } from 'react';
import HomePage from './pages/HomePage';
import OWCoachPage from './pages/OWCoachPage';

export default function App() {
  const isCoachSubdomain = window.location.hostname === 'coach.alphaqwq.xyz';
  const [page, setPage] = useState<string>(isCoachSubdomain ? 'ow-coach' : 'home');

  switch (page) {
    case 'ow-coach':
      return <OWCoachPage onBack={() => isCoachSubdomain ? window.location.href = 'https://alphaqwq.xyz' : setPage('home')} />;
    default:
      return <HomePage onNavigate={setPage} />;
  }
}
