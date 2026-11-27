import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  error: Error | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('Dashboard render error', error.message, info.componentStack)
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-[#070c1c] px-6 text-slate-100">
          <div className="max-w-lg rounded-3xl border border-rose-400/20 bg-rose-500/10 p-8 text-sm">
            <h1 className="text-lg font-semibold text-white">Dashboard error</h1>
            <p className="mt-3 text-rose-200">{this.state.error.message}</p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-5 rounded-full border border-rose-300/30 px-4 py-2 text-xs font-medium text-rose-100 transition hover:bg-rose-400/10"
            >
              Reload dashboard
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
