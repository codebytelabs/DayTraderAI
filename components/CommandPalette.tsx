import React, { useState, useEffect, useRef } from 'react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectCommand: (command: Command) => void;
  onSelectAction: (action: string) => void;
  filter: string;
  positions: any[];
  orders: any[];
}

interface Command {
  id: string;
  category: string;
  label: string;
  description: string;
  prompt: string;
  icon: string;
}

interface PortfolioAction {
  id: string;
  type: 'position' | 'order' | 'quick';
  symbol?: string;
  label: string;
  description: string;
  action: string;
  requiresConfirmation: boolean;
}

// Slash Commands Registry
const SLASH_COMMANDS: Command[] = [
  // Market & Analysis
  {
    id: 'market-summary',
    category: '📊 Market & Analysis',
    label: '/market-summary',
    description: "Today's market overview",
    prompt: 'Give me a comprehensive market summary including major indices, sector performance, VIX, key movers, and how this affects my portfolio',
    icon: '📊'
  },
  {
    id: 'news',
    category: '📊 Market & Analysis',
    label: '/news',
    description: 'Latest market news',
    prompt: 'Latest market news affecting my portfolio including breaking news, earnings, economic data, and impact on my positions',
    icon: '📰'
  },
  // Portfolio Analysis
  {
    id: 'portfolio-summary',
    category: '💼 Portfolio Analysis',
    label: '/portfolio-summary',
    description: 'Complete portfolio view',
    prompt: 'Complete portfolio analysis: current positions, P/L, sector exposure, risk metrics, performance vs benchmarks',
    icon: '💼'
  },
  {
    id: 'performance',
    category: '💼 Portfolio Analysis',
    label: '/performance',
    description: 'Performance metrics',
    prompt: 'Portfolio performance analysis: daily/weekly/monthly returns, win rate, best/worst performers, comparison to SPY/QQQ',
    icon: '📈'
  },
  {
    id: 'risk-analysis',
    category: '💼 Portfolio Analysis',
    label: '/risk-analysis',
    description: 'Risk assessment',
    prompt: 'Comprehensive risk analysis: position sizing, sector concentration, correlation risk, drawdown analysis, recommendations',
    icon: '⚠️'
  },
  // Recommendations
  {
    id: 'opportunities',
    category: '🎯 Recommendations',
    label: '/opportunities',
    description: 'Trading opportunities',
    prompt: 'Show me trading opportunities: new position ideas, strong signals, ML-validated opportunities, risk/reward analysis',
    icon: '🎯'
  },
  {
    id: 'what-to-do',
    category: '🎯 Recommendations',
    label: '/what-to-do',
    description: 'Actionable recommendations',
    prompt: 'What should I do with my portfolio right now? Immediate actions, profit-taking, loss-cutting, rebalancing, risk management',
    icon: '🎯'
  },
  {
    id: 'take-profits',
    category: '🎯 Recommendations',
    label: '/take-profits',
    description: 'Profit-taking suggestions',
    prompt: 'Which positions should I take profits on? Positions near targets, at resistance, overextended positions',
    icon: '💰'
  },
  // Analysis
  {
    id: 'analyze',
    category: '🔬 Deep Analysis',
    label: '/analyze SYMBOL',
    description: 'Comprehensive stock analysis',
    prompt: '/analyze ',
    icon: '🔬'
  },
  // Help
  {
    id: 'help',
    category: '📚 Help',
    label: '/help',
    description: 'All available commands',
    prompt: 'Show all available commands and features',
    icon: '❓'
  },
];

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onSelectCommand,
  onSelectAction,
  filter,
  positions,
  orders
}) => {
  const [filteredCommands, setFilteredCommands] = useState<Command[]>([]);
  const [portfolioActions, setPortfolioActions] = useState<PortfolioAction[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const isSlashCommand = filter.startsWith('/');
  const isPortfolioAction = filter.startsWith('#');

  // Filter commands based on input
  useEffect(() => {
    if (isSlashCommand) {
      const query = filter.slice(1).toLowerCase();
      const filtered = SLASH_COMMANDS.filter(cmd => 
        cmd.label.toLowerCase().includes(query) ||
        cmd.description.toLowerCase().includes(query) ||
        cmd.category.toLowerCase().includes(query)
      );
      setFilteredCommands(filtered);
      setSelectedIndex(0);
    } else if (isPortfolioAction) {
      const actions = generatePortfolioActions(positions, orders, filter);
      setPortfolioActions(actions);
      setSelectedIndex(0);
    }
  }, [filter, positions, orders, isSlashCommand, isPortfolioAction]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      const items = isSlashCommand ? filteredCommands : portfolioActions;
      
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => Math.min(prev + 1, items.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => Math.max(prev - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (items[selectedIndex]) {
            if (isSlashCommand) {
              onSelectCommand(items[selectedIndex] as Command);
            } else {
              onSelectAction((items[selectedIndex] as PortfolioAction).action);
            }
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, filteredCommands, portfolioActions, isSlashCommand, onSelectCommand, onSelectAction, onClose]);

  if (!isOpen || (!isSlashCommand && !isPortfolioAction)) {
    return null;
  }

  return (
    <div 
      ref={containerRef}
      className="absolute bottom-full left-0 right-0 mb-2 bg-slate-800/95 backdrop-blur-sm border border-slate-700 rounded-xl shadow-2xl max-h-96 overflow-hidden z-50"
    >
      {isSlashCommand && (
        <div className="p-2">
          <div className="text-xs text-slate-400 px-3 py-2 border-b border-slate-700">
            💡 Slash Commands - Discover all features
          </div>
          <div className="max-h-80 overflow-y-auto">
            {filteredCommands.length === 0 ? (
              <div className="p-4 text-center text-slate-500">
                No commands found for "{filter}"
              </div>
            ) : (
              renderCommandsByCategory(filteredCommands, selectedIndex, onSelectCommand)
            )}
          </div>
        </div>
      )}

      {isPortfolioAction && (
        <div className="p-2">
          <div className="text-xs text-slate-400 px-3 py-2 border-b border-slate-700">
            ⚡ Portfolio Actions - Direct commands
          </div>
          <div className="max-h-80 overflow-y-auto">
            {portfolioActions.length === 0 ? (
              <div className="p-4 text-center text-slate-500">
                No actions available
              </div>
            ) : (
              renderPortfolioActions(portfolioActions, selectedIndex, onSelectAction)
            )}
          </div>
        </div>
      )}
    </div>
  );
};

function renderCommandsByCategory(
  commands: Command[], 
  selectedIndex: number, 
  onSelect: (command: Command) => void
) {
  const categories = [...new Set(commands.map(cmd => cmd.category))];
  let currentIndex = 0;

  return (
    <div className="space-y-1">
      {categories.map(category => {
        const categoryCommands = commands.filter(cmd => cmd.category === category);
        const categoryStart = currentIndex;
        
        const categoryElement = (
          <div key={category}>
            <div className="px-3 py-1 text-xs font-semibold text-slate-300 bg-slate-900/50">
              {category}
            </div>
            {categoryCommands.map((cmd, idx) => {
              const itemIndex = categoryStart + idx;
              const isSelected = itemIndex === selectedIndex;
              
              return (
                <div
                  key={cmd.id}
                  className={`px-3 py-2 cursor-pointer transition-colors ${
                    isSelected 
                      ? 'bg-blue-600/20 border-l-2 border-blue-500' 
                      : 'hover:bg-slate-700/50'
                  }`}
                  onClick={() => onSelect(cmd)}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{cmd.icon}</span>
                    <span className="font-medium text-white">{cmd.label}</span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {cmd.description}
                  </div>
                </div>
              );
            })}
          </div>
        );
        
        currentIndex += categoryCommands.length;
        return categoryElement;
      })}
    </div>
  );
}

function renderPortfolioActions(
  actions: PortfolioAction[], 
  selectedIndex: number, 
  onSelect: (action: string) => void
) {
  return (
    <div className="space-y-1">
      {actions.map((action, idx) => {
        const isSelected = idx === selectedIndex;
        
        return (
          <div
            key={action.id}
            className={`px-3 py-2 cursor-pointer transition-colors ${
              isSelected 
                ? 'bg-blue-600/20 border-l-2 border-blue-500' 
                : 'hover:bg-slate-700/50'
            }`}
            onClick={() => onSelect(action.action)}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium text-white">{action.label}</span>
              {action.requiresConfirmation && (
                <span className="text-xs text-yellow-400">⚠️</span>
              )}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              {action.description}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function generatePortfolioActions(
  positions: any[], 
  orders: any[], 
  filter: string
): PortfolioAction[] {
  const actions: PortfolioAction[] = [];
  
  // If just # typed, show all categories
  if (filter === '#') {
    // Show positions
    positions.forEach(pos => {
      const pnl = pos.unrealized_pl || 0;
      const pnlPct = pos.unrealized_plpc || 0;
      const pnlDisplay = pnl >= 0 ? `+$${pnl.toFixed(0)}` : `-$${Math.abs(pnl).toFixed(0)}`;
      
      actions.push({
        id: `pos-${pos.symbol}`,
        type: 'position',
        symbol: pos.symbol,
        label: `#${pos.symbol}`,
        description: `${pos.qty} shares, ${pnlDisplay}`,
        action: `#${pos.symbol}`,
        requiresConfirmation: false
      });
    });
    
    // Show quick actions
    actions.push(
      {
        id: 'close-all',
        type: 'quick',
        label: '#close-all',
        description: `Close all ${positions.length} positions`,
        action: '#close-all',
        requiresConfirmation: true
      },
      {
        id: 'cancel-all',
        type: 'quick',
        label: '#cancel-all',
        description: `Cancel all ${orders.length} orders`,
        action: '#cancel-all',
        requiresConfirmation: true
      }
    );
  } else {
    // Filter by symbol
    const symbol = filter.slice(1).toUpperCase();
    const position = positions.find(p => p.symbol.includes(symbol));
    
    if (position) {
      actions.push(
        {
          id: `${position.symbol}-close`,
          type: 'position',
          symbol: position.symbol,
          label: `#${position.symbol} close`,
          description: 'Close entire position',
          action: `#${position.symbol} close`,
          requiresConfirmation: true
        }
      );
    }
  }
  
  return actions;
}
