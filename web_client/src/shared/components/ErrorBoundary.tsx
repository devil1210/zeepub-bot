
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
    children?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
        errorInfo: null
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error, errorInfo: null };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("Uncaught error:", error, errorInfo);

        // Auto-reload to clear Vite chunk cache if an old asset is requested
        if (error.message?.includes('Failed to fetch dynamically imported module')) {
            window.location.reload();
            return;
        }

        this.setState({ error, errorInfo });
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div style={{
                    padding: '20px',
                    color: '#ff4444',
                    backgroundColor: '#1a1a1a',
                    height: '100vh',
                    overflow: 'auto',
                    fontFamily: 'monospace'
                }}>
                    <h1 style={{ fontSize: '20px', marginBottom: '10px' }}>⚠️ Application Crashed</h1>
                    <h2 style={{ fontSize: '16px', color: '#fff' }}>{this.state.error?.message}</h2>
                    <details style={{ whiteSpace: 'pre-wrap', marginTop: '10px', color: '#888' }}>
                        {this.state.errorInfo?.componentStack}
                    </details>
                    <button
                        onClick={() => window.location.href = '/'}
                        style={{
                            marginTop: '20px',
                            padding: '10px 20px',
                            backgroundColor: '#333',
                            color: 'white',
                            border: '1px solid #555',
                            borderRadius: '5px',
                            cursor: 'pointer'
                        }}
                    >
                        Reload Home
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}
