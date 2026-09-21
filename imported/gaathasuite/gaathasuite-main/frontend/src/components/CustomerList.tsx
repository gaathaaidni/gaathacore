import React from 'react';
import { DashboardLayout } from '../../../DashboardLayout';
import { Text } from '../../../Text';
import { Button } from '../../../Button';
import { Users, Mail, Phone, MoreHorizontal, UserPlus, Filter } from 'lucide-react';

interface Customer {
  id: number;
  name: string;
  email: string;
  phone: string;
  status: 'Active' | 'Lead' | 'Inactive';
  lastOrder: string;
}



const StatusBadge = ({ status }: { status: Customer['status'] }) => {
  const styles = {
    Active: 'bg-gaatha-success/10 text-gaatha-success',
    Lead: 'bg-gaatha-blue-50 text-gaatha-blue-600',
    Inactive: 'bg-gaatha-gray-100 text-gaatha-gray-500',
  };
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${styles[status]}`}>
      {status}
    </span>
  );
};

export const CustomerList: React.FC = () => {
  const [customers] = React.useState<Customer[]>([]);

  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <Text variant="h2">Customers</Text>
            <Text variant="caption">Manage your organization's contacts and leads.</Text>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" size="md" className="gap-2">
              <Filter size={18} /> Filter
            </Button>
            <Button variant="primary" size="md" className="gap-2" onClick={() => window.alert('Add Customer is coming soon.') }>
              <UserPlus size={18} /> Add Customer
            </Button>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gaatha-gray-100 overflow-hidden shadow-sm">
          <table className="min-w-full divide-y divide-gaatha-gray-100 text-left">
            <thead className="bg-gaatha-gray-50">
              <tr>
                <th className="px-6 py-4 text-xs font-bold text-gaatha-gray-600 uppercase tracking-wider">Customer</th>
                <th className="px-6 py-4 text-xs font-bold text-gaatha-gray-600 uppercase tracking-wider">Contact</th>
                <th className="px-6 py-4 text-xs font-bold text-gaatha-gray-600 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-bold text-gaatha-gray-600 uppercase tracking-wider">Last Order</th>
                <th className="px-6 py-4"></th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gaatha-gray-100">
              {customers.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-10 text-center text-gaatha-gray-500">No customer records yet.</td>
                </tr>
              ) : customers.map((customer) => (
                <tr key={customer.id} className="hover:bg-gaatha-gray-50/50 transition-colors cursor-pointer group">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-gaatha-blue-100 text-gaatha-blue-600 flex items-center justify-center font-bold text-xs">
                        {customer.name.charAt(0)}
                      </div>
                      <Text variant="body" className="font-semibold text-gaatha-gray-900">{customer.name}</Text>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-1.5 text-gaatha-gray-500">
                        <Mail size={14} />
                        <span className="text-sm">{customer.email}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-gaatha-gray-500">
                        <Phone size={14} />
                        <span className="text-sm">{customer.phone}</span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={customer.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Text variant="small" className="text-gaatha-gray-600">{customer.lastOrder}</Text>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <MoreHorizontal className="text-gaatha-gray-400 group-hover:text-gaatha-gray-600 transition-colors" size={20} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </DashboardLayout>
  );
};