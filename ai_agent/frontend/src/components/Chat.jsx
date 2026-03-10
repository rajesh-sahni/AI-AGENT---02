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
  const [repoDetailsDialogOpen, setRepoDetailsDialogOpen] = useState(false);
  const [reposList, setReposList] = useState([]);
  const [selectedRepoForDetails, setSelectedRepoForDetails] = useState('');
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [repoSelectOpen, setRepoSelectOpen] = useState(false);
  const containerRef = useRef(null);
  const githubWrapperRef = useRef(null);
  const repoSelectRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.scrollTop = containerRef.current.scrollHeight;
  }, [messages, loading]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (githubWrapperRef.current && !githubWrapperRef.current.contains(e.target)) {
        setGithubMenuOpen(false);
      }
      if (repoSelectOpen && repoSelectRef.current && !repoSelectRef.current.contains(e.target)) {
        setRepoSelectOpen(false);
      }
    }
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [repoSelectOpen]);

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

  async function openRepoDetailsDialog() {
    setGithubMenuOpen(false);
    setRepoDetailsDialogOpen(true);
    setSelectedRepoForDetails('');
    setRepoSelectOpen(false);
    setLoadingRepos(true);
    setReposList([]);
    try {
      const res = await fetch(`${API_BASE_URL}/github/repos?per_page=100`);
      const data = await res.json();
      if (res.ok && data.nodes && data.nodes.length) {
        setReposList(data.nodes);
        setSelectedRepoForDetails(data.nodes[0].name || '');
      } else {
        setReposList([]);
      }
    } catch (err) {
      setReposList([]);
    } finally {
      setLoadingRepos(false);
    }
  }

  function handleRepoDetailsOk() {
    if (!selectedRepoForDetails.trim()) return;
    send(`show details of repo ${selectedRepoForDetails}`);
    setRepoDetailsDialogOpen(false);
  }

  function handleGithubAction(action) {
    setGithubMenuOpen(false);
    if (action === 'show-all-repos') {
      send('show me all my github repos');
    } else if (action === 'show-repo-details') {
      openRepoDetailsDialog();
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

      {repoDetailsDialogOpen && (
        <div className="dialog-backdrop" onClick={() => setRepoDetailsDialogOpen(false)}>
          <div className="dialog-box" onClick={e => e.stopPropagation()}>
            <h3 className="dialog-title">Show repository details</h3>
            <p className="dialog-label">Select repository</p>
            {loadingRepos ? (
              <p className="dialog-loading">Loading repositories…</p>
            ) : (
              <div className="dialog-select-wrapper" ref={repoSelectRef}>
                <button
                  type="button"
                  className="dialog-select-trigger"
                  onClick={() => setRepoSelectOpen(o => !o)}
                  aria-expanded={repoSelectOpen}
                  aria-haspopup="listbox"
                >
                  {selectedRepoForDetails
                    ? reposList.find(r => r.name === selectedRepoForDetails)?.full_name || selectedRepoForDetails
                    : '-- Select repo --'}
                </button>
                {repoSelectOpen && (
                  <ul className="dialog-select-list" role="listbox">
                    {reposList.map(repo => (
                      <li
                        key={repo.id}
                        role="option"
                        aria-selected={selectedRepoForDetails === repo.name}
                        className={`dialog-select-option ${selectedRepoForDetails === repo.name ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedRepoForDetails(repo.name);
                          setRepoSelectOpen(false);
                        }}
                      >
                        {repo.full_name || repo.name}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
            <div className="dialog-actions">
              <button type="button" className="dialog-btn dialog-cancel" onClick={() => setRepoDetailsDialogOpen(false)}>
                Cancel
              </button>
              <button
                type="button"
                className="dialog-btn dialog-ok"
                onClick={handleRepoDetailsOk}
                disabled={loadingRepos || !selectedRepoForDetails}
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

