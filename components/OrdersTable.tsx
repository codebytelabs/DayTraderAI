
import React from 'react';
import { Order, OrderStatus } from '../types';
import { MinusCircleIcon } from './icons/MinusCircleIcon';

interface OrdersTableProps {
  orders: Order[];
  cancelOrder: (orderId: string) => void;
}

export const OrdersTable: React.FC<OrdersTableProps> = ({ orders, cancelOrder }) => {
    const statusColor = (status: string) => {
        switch (status) {
            case 'open': return 'text-blue-400 bg-blue-500/10';
            case 'filled': return 'text-emerald-400 bg-emerald-500/10';
            case 'canceled': return 'text-slate-400 bg-slate-500/10';
            default: return 'text-slate-400 bg-slate-500/10';
        }
    }

    const recentOrders = orders.slice(-10).reverse();

    return (
        <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-slate-700/50 overflow-hidden">
            <div className="flex items-center justify-between mb-5">
                <h3 className="text-xl font-bold text-white">Recent Orders</h3>
                <span className="px-3 py-1 bg-purple-500/20 text-purple-400 rounded-full text-sm font-semibold">
                    {recentOrders.length}
                </span>
            </div>
            <div className="overflow-x-auto">
                <div className="max-h-[400px] overflow-y-auto">
                    <table className="w-full text-sm">
                        <thead className="text-xs text-slate-400 uppercase tracking-wider border-b border-slate-700/50 sticky top-0 bg-slate-900/90 backdrop-blur-sm">
                            <tr>
                                <th scope="col" className="px-4 py-4 text-left font-semibold">Symbol</th>
                                <th scope="col" className="px-4 py-4 text-left font-semibold">Side</th>
                                <th scope="col" className="px-4 py-4 text-right font-semibold">Qty</th>
                                <th scope="col" className="px-4 py-4 text-center font-semibold">Status</th>
                                <th scope="col" className="px-4 py-4 text-center font-semibold">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {recentOrders.length > 0 ? recentOrders.map((order) => (
                                <tr key={order.id} className="hover:bg-slate-800/30 transition-colors">
                                    <td className="px-4 py-4 font-bold text-white">{order.symbol}</td>
                                    <td className="px-4 py-4">
                                        <span className={`inline-flex px-2.5 py-1 rounded-md text-xs font-bold ${
                                            order.side === 'buy' 
                                                ? 'bg-emerald-500/20 text-emerald-400' 
                                                : 'bg-rose-500/20 text-rose-400'
                                        }`}>
                                            {order.side.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="px-4 py-4 text-right text-slate-300">{order.qty}</td>
                                    <td className="px-4 py-4 text-center">
                                        <span className={`inline-flex px-2.5 py-1 rounded-md text-xs font-bold ${statusColor(order.status)}`}>
                                            {order.status.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="px-4 py-4 text-center">
                                        {order.status === OrderStatus.OPEN && (
                                            <button 
                                                onClick={() => cancelOrder(order.id)} 
                                                className="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 p-1.5 rounded-lg transition-all" 
                                                aria-label={`Cancel order for ${order.symbol}`}
                                            >
                                                <MinusCircleIcon className="w-5 h-5" />
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            )) : (
                                <tr>
                                    <td colSpan={5} className="text-center py-12 text-slate-500">
                                        <div className="flex flex-col items-center gap-2">
                                            <span className="text-2xl">📝</span>
                                            <span>No recent orders</span>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
