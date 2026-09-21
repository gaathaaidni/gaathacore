import React, { useState } from 'react';
import { Text } from './Text';
import { Button } from './Button';
import { X, AlertCircle } from 'lucide-react';
import axios from 'axios';

interface StockAdjustmentModalProps {
  item: { id: number; name: string; sku: string };
  onClose: () => void;
  onSuccess: () => void;
}

export const StockAdjustmentModal: React.FC<StockAdjustmentModalProps> = ({ item, onClose, onSuccess }) => {
  const [qty, setQty] = useState<number>(0);
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await axios.post('/api/v2/inventory/adjust', {
        item_id: item.id,
        warehouse_id: 1, // Defaulting to primary warehouse for now
        adjustment_qty: qty,
        note: note
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <div>
            <Text variant="body" className="font-bold">Adjust Stock</Text>
            <Text variant="caption">{item.name} ({item.sku})</Text>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-4">
          {error && (
            <div className="p-3 bg-red-50 text-red-600 rounded-lg flex gap-2 items-center text-sm">
              <AlertCircle size={16} /> {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Adjustment Quantity</label>
            <input 
              type="number" 
              required
              value={qty}
              onChange={(e) => setQty(parseFloat(e.target.value))}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-600 outline-none"
              placeholder="e.g. 10 or -5"
            />
            <p className="text-[10px] text-slate-400 mt-1">Positive to add to stock, negative to remove.</p>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Reason / Note</label>
            <textarea 
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-600 outline-none h-20 resize-none"
              placeholder="Reason for adjustment..."
            />
          </div>

          <div className="flex gap-3 mt-2">
            <Button 
              type="button" 
              variant="outline" 
              className="flex-1" 
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" className="flex-1" disabled={loading}>
              {loading ? 'Processing...' : 'Apply Adjustment'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};