
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
            case 'open': return 'text-blue-400';
            case 'filled': return 'text-brand-success';
            case 'canceled': return 'text-brand-text-secondary';
            default: return '';
        }
    }

    const recentOrders = orders.slice(-10).reverse();

    return (
        <div className="bg-brand-surface p-4 rounded-lg shadow-lg border border-brand-surface-2 overflow-x-auto">
            <h3 className="text-lg font-semibold text-brand-text mb-4">Recent Orders</h3>
            <div className="max-h-[340px] overflow-y-auto">
                <table className="w-full text-sm text-left">
                    <thead className="text-xs text-brand-text-secondary uppercase border-b border-brand-surface-2 sticky top-0 bg-brand-surface">
                        <tr>
                            <th scope="col" className="px-4 py-3">Symbol</th>
                            <th scope="col" className="px-4 py-3">Side</th>
                            <th scope="col" className="px-4 py-3">Qty</th>
                            <th scope="col" className="px-4 py-3">Status</th>
                            <th scope="col" className="px-4 py-3">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {recentOrders.length > 0 ? recentOrders.map((order) => (
                            <tr key={order.id} className="hover:bg-brand-surface-2 border-b border-brand-surface-2">
                                <td className="px-4 py-3 font-medium">{order.symbol}</td>
                                <td className={`px-4 py-3 font-semibold ${order.side === 'buy' ? 'text-brand-success' : 'text-brand-danger'}`}>
                                    {order.side.toUpperCase()}
                                </td>
                                <td className="px-4 py-3">{order.qty}</td>
                                <td className={`px-4 py-3 font-semibold ${statusColor(order.status)}`}>
                                    {order.status.toUpperCase()}
                                </td>
                                <td className="px-4 py-3">
                                  {order.status === OrderStatus.OPEN && (
                                     <button onClick={() => cancelOrder(order.id)} className="text-brand-danger hover:text-red-400 transition-colors" aria-label={`Cancel order for ${order.symbol}`}>
                                       <MinusCircleIcon className="w-5 h-5" />
                                     </button>
                                  )}
                                </td>
                            </tr>
                        )) : (
                          <tr>
                            <td colSpan={5} className="text-center py-4 text-brand-text-secondary">No recent orders.</td>
                          </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
