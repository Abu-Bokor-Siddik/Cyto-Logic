/*
Core responsibility
------------------------------------------------------
Catch unexpected React rendering errors and show
a fallback screen instead of leaving the application
blank or crashing completely.

Design note
------------------------------------------------
I kept the recovery UI inside this component so
the rest of the application stays focused on its
own responsibilities. Wrapping the app once is
enough to protect every child component.
*/
import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  // React calls this automatically after a rendering error.
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  // Keeping the error in the console makes debugging much easier during development.
  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          background: '#1c222e',
          color: '#fff',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          padding: 20
        }}>
          <h1 style={{ color: '#ff5f5f' }}>Something went wrong</h1>
          <p style={{ color: '#aaa', marginBottom: 20 }}>
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>
          <button
            // Reloading is the simplest recovery path for unexpected UI failures.
            onClick={() => window.location.reload()}
            style={{
              padding: '10px 24px',
              background: '#1D9E75',
              color: '#fff',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 14
            }}
          >
            Reload Application
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
