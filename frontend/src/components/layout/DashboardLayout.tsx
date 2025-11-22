import React from 'react';
import { Activity, BarChart2, Terminal, Settings, Zap, Shield } from 'lucide-react';

interface DashboardLayoutProps {
    children: React.ReactNode;
    activeView?: string;
    onNavigate?: (view: string) => void;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
    children,
    activeView = 'dashboard',
    onNavigate = () => { }
}) => {
    return (
        <div className="min-h-screen bg-background text-text-primary flex">
            {/* Sidebar */}
            <aside className="w-20 lg:w-64 border-r border-glass-border bg-surface/50 backdrop-blur-sm flex flex-col fixed h-full z-50 transition-all duration-300">
                <div className="h-16 flex items-center justify-center lg:justify-start lg:px-6 border-b border-glass-border">
                    <div className="w-8 h-8 bg-gradient-to-br from-primary to-secondary rounded-lg flex items-center justify-center shadow-lg shadow-primary/20">
                        <Activity className="w-5 h-5 text-white" />
                    </div>
                    <span className="hidden lg:block ml-3 font-bold text-lg tracking-tight text-white">
                        DayTrader<span className="text-primary">AI</span>
                    </span>
                </div>

                <nav className="flex-1 py-6 flex flex-col gap-2 px-3">
                    <NavItem
                        icon={<BarChart2 />}
                        label="Dashboard"
                        active={activeView === 'dashboard'}
                        onClick={() => onNavigate('dashboard')}
                    />
                    <NavItem
                        icon={<Zap />}
                        label="Opportunities"
                        active={activeView === 'opportunities'}
                        onClick={() => onNavigate('opportunities')}
                    />
                    <NavItem
                        icon={<Terminal />}
                        label="Terminal"
                        active={activeView === 'terminal'}
                        onClick={() => onNavigate('terminal')}
                    />
                    <NavItem
                        icon={<Shield />}
                        label="Risk"
                        active={activeView === 'risk'}
                        onClick={() => onNavigate('risk')}
                    />
                    <div className="flex-1" />
                    <NavItem
                        icon={<Settings />}
                        label="Settings"
                        active={activeView === 'settings'}
                        onClick={() => onNavigate('settings')}
                    />
                </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 ml-20 lg:ml-64 min-h-screen flex flex-col relative">
                {/* Background Gradients */}
                <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
                    <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/10 rounded-full blur-[120px]" />
                    <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-secondary/10 rounded-full blur-[120px]" />
                </div>

                {/* Header */}
                <header className="h-16 border-b border-glass-border bg-surface/30 backdrop-blur-md sticky top-0 z-40 px-6 flex items-center justify-between">
                    <h1 className="text-xl font-semibold text-white capitalize">{activeView}</h1>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-success/10 border border-success/20">
                            <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
                            <span className="text-xs font-medium text-success">System Online</span>
                        </div>
                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-slate-700 to-slate-600 border border-slate-500" />
                    </div>
                </header>

                {/* Content Area */}
                <div className="flex-1 p-6 relative z-10 overflow-y-auto">
                    <div className="max-w-7xl mx-auto">
                        {children}
                    </div>
                </div>
            </main>
        </div>
    );
};

const NavItem = ({ icon, label, active = false, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }) => (
    <button
        onClick={onClick}
        className={`
    flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group w-full
    ${active
                ? 'bg-primary/10 text-primary shadow-lg shadow-primary/5'
                : 'text-text-secondary hover:bg-white/5 hover:text-white'}
  `}>
        <span className={`transition-transform duration-200 ${active ? 'scale-110' : 'group-hover:scale-110'}`}>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {React.cloneElement(icon as any, { size: 20 })}
        </span>
        <span className="hidden lg:block font-medium text-sm">{label}</span>
        {active && (
            <div className="hidden lg:block ml-auto w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
        )}
    </button>
);
