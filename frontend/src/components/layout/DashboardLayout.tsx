import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    Activity, BarChart2, Terminal, Settings, Zap, Shield, 
    Menu, X, ChevronRight, Bell, User
} from 'lucide-react';

interface DashboardLayoutProps {
    children: React.ReactNode;
    activeView?: string;
    onNavigate?: (view: string) => void;
}

const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart2 },
    { id: 'opportunities', label: 'Opportunities', icon: Zap },
    { id: 'terminal', label: 'Terminal', icon: Terminal },
    { id: 'risk', label: 'Risk', icon: Shield },
];

export function DashboardLayout({
    children,
    activeView = 'dashboard',
    onNavigate = () => {}
}: DashboardLayoutProps) {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    return (
        <div className="min-h-screen bg-background text-text-primary flex">
            {/* Mobile Menu Overlay */}
            <AnimatePresence>
                {mobileMenuOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
                        onClick={() => setMobileMenuOpen(false)}
                    />
                )}
            </AnimatePresence>

            {/* Sidebar */}
            <motion.aside
                className={`fixed lg:relative inset-y-0 left-0 z-50 flex flex-col border-r border-glass-border bg-surface/80 backdrop-blur-xl transition-all duration-300 ${
                    mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
                } ${sidebarCollapsed ? 'w-20' : 'w-64'}`}
                initial={false}
            >
                {/* Logo */}
                <div className="h-16 flex items-center justify-between px-4 border-b border-glass-border">
                    <div className="flex items-center gap-3">
                        <motion.div
                            className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-lg shadow-primary/25"
                            whileHover={{ scale: 1.05, rotate: 5 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <Activity className="w-5 h-5 text-white" />
                        </motion.div>
                        <AnimatePresence>
                            {!sidebarCollapsed && (
                                <motion.span
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -10 }}
                                    className="font-bold text-lg tracking-tight text-white"
                                >
                                    DayTrader<span className="text-primary">AI</span>
                                </motion.span>
                            )}
                        </AnimatePresence>
                    </div>
                    <button
                        className="lg:hidden p-2 hover:bg-surface rounded-lg text-text-secondary"
                        onClick={() => setMobileMenuOpen(false)}
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 py-6 px-3 space-y-1">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = activeView === item.id;
                        
                        return (
                            <motion.button
                                key={item.id}
                                onClick={() => {
                                    onNavigate(item.id);
                                    setMobileMenuOpen(false);
                                }}
                                className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group relative ${
                                    isActive
                                        ? 'bg-primary/10 text-primary'
                                        : 'text-text-secondary hover:bg-surface hover:text-white'
                                }`}
                                whileHover={{ x: 4 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                {isActive && (
                                    <motion.div
                                        layoutId="activeNav"
                                        className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary rounded-r-full"
                                        transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                                    />
                                )}
                                <Icon className={`w-5 h-5 ${isActive ? 'text-primary' : ''}`} />
                                <AnimatePresence>
                                    {!sidebarCollapsed && (
                                        <motion.span
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            exit={{ opacity: 0 }}
                                            className="font-medium text-sm"
                                        >
                                            {item.label}
                                        </motion.span>
                                    )}
                                </AnimatePresence>
                                {isActive && !sidebarCollapsed && (
                                    <motion.div
                                        className="ml-auto w-2 h-2 rounded-full bg-primary shadow-lg shadow-primary/50"
                                        layoutId="activeDot"
                                    />
                                )}
                            </motion.button>
                        );
                    })}
                </nav>

                {/* Bottom Section */}
                <div className="p-3 border-t border-glass-border">
                    <motion.button
                        onClick={() => onNavigate('settings')}
                        className="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-text-secondary hover:bg-surface hover:text-white transition-colors"
                        whileHover={{ x: 4 }}
                    >
                        <Settings className="w-5 h-5" />
                        {!sidebarCollapsed && <span className="font-medium text-sm">Settings</span>}
                    </motion.button>
                    
                    {/* Collapse Toggle - Desktop Only */}
                    <button
                        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                        className="hidden lg:flex w-full items-center justify-center gap-2 mt-2 py-2 text-text-muted hover:text-text-secondary transition-colors"
                    >
                        <ChevronRight className={`w-4 h-4 transition-transform ${sidebarCollapsed ? '' : 'rotate-180'}`} />
                    </button>
                </div>
            </motion.aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Header */}
                <header className="h-16 border-b border-glass-border bg-surface/50 backdrop-blur-xl sticky top-0 z-30 px-4 lg:px-6 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button
                            className="lg:hidden p-2 hover:bg-surface rounded-lg text-text-secondary"
                            onClick={() => setMobileMenuOpen(true)}
                        >
                            <Menu className="w-5 h-5" />
                        </button>
                        <div>
                            <h1 className="text-xl font-semibold text-white capitalize">{activeView}</h1>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {/* System Status Badge */}
                        <motion.div
                            className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-success/10 border border-success/20"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                        >
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-success" />
                            </span>
                            <span className="text-xs font-semibold text-success">System Online</span>
                        </motion.div>

                        {/* Notifications */}
                        <button className="p-2 hover:bg-surface rounded-lg text-text-secondary hover:text-white transition-colors relative">
                            <Bell className="w-5 h-5" />
                            <span className="absolute top-1 right-1 w-2 h-2 bg-primary rounded-full" />
                        </button>

                        {/* User Avatar */}
                        <button className="w-9 h-9 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 border border-glass-border flex items-center justify-center hover:border-primary/30 transition-colors">
                            <User className="w-4 h-4 text-text-secondary" />
                        </button>
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 p-4 lg:p-6 overflow-y-auto relative">
                    {/* Background Gradients */}
                    <div className="fixed inset-0 pointer-events-none overflow-hidden">
                        <div className="absolute top-[-30%] left-[-20%] w-[60%] h-[60%] bg-primary/5 rounded-full blur-[150px]" />
                        <div className="absolute bottom-[-30%] right-[-20%] w-[60%] h-[60%] bg-secondary/5 rounded-full blur-[150px]" />
                    </div>

                    <div className="relative z-10 max-w-7xl mx-auto">
                        <motion.div
                            key={activeView}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            {children}
                        </motion.div>
                    </div>
                </main>
            </div>
        </div>
    );
}
