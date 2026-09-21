import React, { useState, useEffect } from 'react';
import { DashboardLayout } from './DashboardLayout';
import { Text } from './Text';
import { Button } from './Button';
import { Package, Search, Filter, AlertTriangle, Plus, Edit3, Loader2 } from 'lucide-react';
import { StockAdjustmentModal } from './StockAdjustmentModal';
import axios from 'axios'; // Or import your axiosInstance

interface InventoryItem {
  id: number;
  name: string;
  sku: string;
  category: string;
  current_stock?: number;
  min_stock_level: number;
  sale_price: number;
}


export const InventoryList: React.FC = () => {
  const [search, setSearch] = useState('');
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchInventory = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/v2/inventory/items');
      setItems(response.data);
    } catch (error) {
      console.error("Failed to fetch inventory", error);
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, []);

  const filteredItems = items.filter(item => 
    item.name?.toLowerCase()?.includes(search.toLowerCase()) || 
    item.sku?.toLowerCase()?.includes(search.toLowerCase())
  );

  const handleRefresh = () => {
    fetchInventory();
  };

  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <Text variant="h2">Inventory Management</Text>
            <Text variant="caption">Track stock levels, SKUs, and warehouse distribution.</Text>
          </div>
          <Button variant="primary" className="gap-2" onClick={() => window.alert('Add Item is coming soon.')}>
            <Plus size={18} /> Add Item
          </Button>
        </div>

        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gaatha-gray-400" size={18} />
            <input 
              type="text" 
              placeholder="Search by SKU or Item Name..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white border border-gaatha-gray-100 rounded-lg text-sm focus:ring-2 focus:ring-gaatha-blue-600 outline-none transition-all"
            />
          </div>
          <Button variant="outline" className="gap-2">
            <Filter size={18} /> Filters
          </Button>
        </div>

        <div className="bg-white rounded-xl border border-gaatha-gray-100 overflow-hidden shadow-sm">
          <table className="min-w-full divide-y divide-gaatha-gray-100">
            <thead className="bg-gaatha-gray-50 text-left">
              <tr>
                <th className="px-6 py-4 text-xs font-bold text-gaatha-gray-600 uppercase">Item Details</th>
                <th className="px-6 py-4 text-xs font-bold text-gaatha-gray-600 uppercase">Category</th>
                <th className="px-6 py-4 text-xs font-bold text-gaatha-gray-600 uppercase">Stock Level</th>
                <th className="px-6 py-4 text-xs font-bold text-gaatha-gray-600 uppercase text-right">Unit Price</th>
                <th className="px-6 py-4 text-xs font-bold text-gaatha-gray-600 uppercase text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gaatha-gray-100">
              {loading ? (
                <tr><td colSpan={5} className="py-10 text-center"><Loader2 className="animate-spin mx-auto text-blue-600" /></td></tr>
              ) : filteredItems.map((item) => {
                const stock = item.current_stock ?? 0;
                const isLowStock = stock > 0 && stock <= item.min_stock_level;
                const isOutOfStock = stock === 0;

                return (
                  <tr key={item.id} className="hover:bg-gaatha-gray-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-gaatha-gray-50 rounded-lg">
                          <Package size={20} className="text-gaatha-gray-400" />
                        </div>
                        <div>
                          <Text variant="body" className="font-semibold">{item.name}</Text>
                          <Text variant="small" className="text-gaatha-gray-500 font-mono uppercase">{item.sku}</Text>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <Text variant="small" className="bg-gaatha-gray-100 text-gaatha-gray-600 px-2 py-1 rounded-md">{item.category}</Text>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="flex-1 h-2 bg-gaatha-gray-100 rounded-full overflow-hidden max-w-[80px]">
                          <div className={`h-full rounded-full ${isOutOfStock ? 'bg-gaatha-danger w-0' : isLowStock ? 'bg-gaatha-warning w-1/3' : 'bg-gaatha-success w-full'}`} />
                        </div>
                        <Text variant="small" className={`font-bold ${isOutOfStock ? 'text-gaatha-danger' : isLowStock ? 'text-gaatha-warning' : 'text-gaatha-success'}`}>
                          {stock} Units
                        </Text>
                        {(isLowStock || isOutOfStock) && <AlertTriangle size={14} className={isOutOfStock ? 'text-gaatha-danger' : 'text-gaatha-warning'} />}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Text variant="body" className="font-mono">${item.sale_price.toFixed(2)}</Text>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Button 
                        variant="outline" 
                        className="p-2 h-auto"
                        onClick={() => setSelectedItem(item)}
                      >
                        <Edit3 size={16} />
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {selectedItem && (
          <StockAdjustmentModal 
            item={selectedItem}
            onClose={() => setSelectedItem(null)}
            onSuccess={handleRefresh}
          />
        )}
      </div>
    </DashboardLayout>
  );
};