import React, { useState, useRef, useEffect } from 'react';
import './chat.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function Message({ role, content }) {
  return (
    <div className={`message ${role}`}>
      <div className="role">{role}</div>
      <div className="content">{content}</div>
    </div>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [githubMenuOpen, setGithubMenuOpen] = useState(false);
  const containerRef = useRef(null);
  const githubWrapperRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.scrollTop = containerRef.current.scrollHeight;
  }, [messages, loading]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (githubWrapperRef.current && !githubWrapperRef.current.contains(e.target)) {
        setGithubMenuOpen(false);
      }
    }
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  async function send(text) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setInput('');
    setError(null);
    setLoading(true);

    const newMessages = [...messages, { role: 'user', content: trimmed }];
    setMessages(newMessages);

    try {
      const res = await fetch(`${API_BASE_URL}/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          model: 'deepseek-r1:1.5b',
          history: newMessages.map(m => ({ role: m.role, content: m.content })),
          stream: false,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        const detail = data?.detail || 'Something went wrong';
        setError(detail);
        setMessages(msgs => [...msgs, { role: 'assistant', content: detail }]);
      } else {
        setMessages(msgs => [...msgs, { role: 'assistant', content: data.message }]);
      }
    } catch (err) {
      const msg =
        'Network error. Make sure FastAPI and Ollama are running.\nTry: uvicorn app:app --reload and ollama serve';
      setError(msg);
      setMessages(msgs => [...msgs, { role: 'assistant', content: msg }]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    send(input);
  }

  function handleGithubAction(action) {
    setGithubMenuOpen(false);
    if (action === 'show-all-repos') {
      send('show me all my github repos');
    } else if (action === 'show-repo-details') {
      send('show repo details of FAQ-AGENt');
    } else if (action === 'show-branch-details') {
      send('show the main branch of FAQ-AGENt repo');
    } else if (action === 'create-pr') {
      send('create pull request from dev to main of repo FAQ-AGENt');
    }
  }

  return (
    <div className="chat-root">
      <div className="chat-container" ref={containerRef}>
        {messages.map((m, idx) => (
          <Message key={idx} role={m.role} content={m.content} />
        ))}
        {loading && <Message role="assistant" content="…" />}
      </div>

      <div className="input-area">
        <form className="input-form" onSubmit={handleSubmit}>
          <div className="input-row">
            <div className="github-feature-wrapper" ref={githubWrapperRef}>
              <button
                type="button"
                className="github-feature-btn"
                onClick={() => setGithubMenuOpen(open => !open)}
              >
                GitHub Feature
              </button>
              {githubMenuOpen && (
                <div className="github-dropdown">
                  <button
                    type="button"
                    className="github-dropdown-item"
                    onClick={() => handleGithubAction('show-all-repos')}
                  >
                    Show all github repository
                  </button>
                  <button
                    type="button"
                    className="github-dropdown-item"
                    onClick={() => handleGithubAction('show-repo-details')}
                  >
                    show repo details
                  </button>
                  <button
                    type="button"
                    className="github-dropdown-item"
                    onClick={() => handleGithubAction('show-branch-details')}
                  >
                    show branch details
                  </button>
                  <button
                    type="button"
                    className="github-dropdown-item"
                    onClick={() => handleGithubAction('create-pr')}
                  >
                    Create Pull Request
                  </button>
                </div>
              )}
            </div>

            <textarea
              className="message-input"
              placeholder="Type your message..."
              rows={1}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  send(input);
                }
              }}
            />
            <button type="submit" className="send-btn" disabled={loading}>
              Send
            </button>
          </div>
        </form>
        {error && <div className="error-banner">{error}</div>}
      </div>
    </div>
  );
}

