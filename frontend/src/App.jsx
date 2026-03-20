import React from 'react';
import Chat from './components/Chat.jsx';

export default function App() {
  return (
    <div className="app-root">
      <header className="top-bar">
        <div>
          <h1 className="app-title">AI Agent Chat</h1>
          <p className="app-subtitle">Chat with your GitHub-aware AI agent</p>
        </div>
      </header>
      <main className="app-main">
        <Chat />
      </main>
    </div>
  );
}

