
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

console.log('🚀 Starting DayTraderAI Frontend...');

const rootElement = document.getElementById('root');
if (!rootElement) {
  console.error('❌ Root element not found!');
  throw new Error("Could not find root element to mount to");
}

console.log('✅ Root element found, mounting React app...');

try {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
  console.log('✅ React app mounted successfully!');
} catch (error) {
  console.error('❌ Failed to mount React app:', error);
  rootElement.innerHTML = `
    <div style="padding: 20px; color: white; background: #1a1a2e;">
      <h1>Failed to Load App</h1>
      <pre style="color: red;">${error}</pre>
    </div>
  `;
}
