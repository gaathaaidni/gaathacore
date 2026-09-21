import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Chart, registerables } from 'chart.js';
import { Link } from 'react-router-dom';

const CouponCreator = ({ onCouponCreated }) => {
  const [code, setCode] = useState('');
  const [value, setValue] = useState('');
  const [description, setDescription] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('/api/superadmin/coupons', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          code,
          value: parseFloat(value),
          description,
          discount_type: 'fixed', // Assuming fixed amount for subscription
        }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create coupon');
      }
      setMessage(`Successfully created coupon: ${code}`);
      setCode('');
      setValue('');
      setDescription('');
      if (onCouponCreated) onCouponCreated(); // Trigger refresh
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    }
  };

  return (
    <div>
      <h4>Create Subscription Voucher</h4>
      <form onSubmit={handleSubmit}>
        <input type="text" value={code} onChange={(e) => setCode(e.target.value)} placeholder="Voucher Code" required />
        <input type="number" value={value} onChange={(e) => setValue(e.target.value)} placeholder="Subscription Value (e.g., 999)" required />
        <input type="text" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description (optional)" />
        <button type="submit">Create Voucher</button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
};

const CouponList = ({ coupons, onCouponUpdated, searchTerm }) => {
  const [couponToDeactivate, setCouponToDeactivate] = useState(null);

  const handleToggle = (coupon) => {
    if (coupon.is_active) {
      // Show confirmation modal before deactivating
      setCouponToDeactivate(coupon);
    } else {
      // Activate immediately without confirmation
      toggleCouponStatus(coupon.id);
    }
  };

  const toggleCouponStatus = async (couponId) => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`/api/superadmin/coupons/${couponId}/toggle`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to update coupon status');
      if (onCouponUpdated) onCouponUpdated();
    } catch (err) {
      console.error(err);
      alert(err.message);
    }
  };

  const filteredCoupons = useMemo(() => {
    if (!searchTerm) return coupons;
    return coupons.filter(c =>
      c.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.description?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [coupons, searchTerm]);

  const confirmDeactivation = () => {
    if (couponToDeactivate) {
      toggleCouponStatus(couponToDeactivate.id);
      setCouponToDeactivate(null);
    }
  };

  return (
  <div className="bg-white p-6 rounded-lg shadow-md">
    <h4 className="text-lg font-semibold">Created Vouchers</h4>
    <table className="min-w-full divide-y divide-gray-200 mt-4">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Code</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Active</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usage</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
        </tr>
      </thead>
      <tbody className="bg-white divide-y divide-gray-200">
        {filteredCoupons.map((coupon) => (
          <tr key={coupon.id}>
            <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900">{coupon.code}</td>
            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{coupon.value}</td>
            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{coupon.description}</td>
            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{coupon.is_active ? 'Yes' : 'No'}</td>
            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{coupon.used_count} / {coupon.usage_limit}</td>
            <td className="px-4 py-2 whitespace-nowrap text-sm font-medium">
              <button onClick={() => handleToggle(coupon)} className={`px-3 py-1 text-xs rounded-full ${coupon.is_active ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                {coupon.is_active ? 'Deactivate' : 'Activate'}
              </button>
            </td>
          </tr>
        ))}
        {filteredCoupons.length === 0 && <tr><td colSpan="6" className="text-center py-4 text-sm text-gray-500">No coupons found.</td></tr>}
      </tbody>
    </table>

    {couponToDeactivate && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg shadow-xl max-w-sm w-full">
          <h3 className="text-lg font-bold text-slate-800">Confirm Deactivation</h3>
          <p className="text-slate-600 my-4">
            Are you sure you want to deactivate the coupon "<strong>{couponToDeactivate.code}</strong>"? This will prevent it from being used for new registrations.
          </p>
          <div className="flex justify-end gap-3">
            <button onClick={() => setCouponToDeactivate(null)} className="px-4 py-2 text-slate-700 border border-slate-300 rounded-lg hover:bg-slate-50">Cancel</button>
            <button onClick={confirmDeactivation} className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium">Deactivate</button>
          </div>
        </div>
      </div>
    )}
  </div>
  );
};

const PaginationControls = ({ currentPage, totalItems, itemsPerPage, onPageChange }) => {
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  if (totalPages <= 1) return null;

  return (
    <div className="flex justify-end items-center gap-4 mt-4">
      <button onClick={() => onPageChange(currentPage - 1)} disabled={currentPage === 1} className="px-3 py-1 border rounded disabled:opacity-50">
        Previous
      </button>
      <span>Page {currentPage} of {totalPages}</span>
      <button onClick={() => onPageChange(currentPage + 1)} disabled={currentPage === totalPages} className="px-3 py-1 border rounded disabled:opacity-50">
        Next
      </button>
    </div>
  );
};

const UserSignupsChart = () => {
  const chartRef = React.useRef(null);
  const chartInstanceRef = React.useRef(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    Chart.register(...registerables);

    const fetchDataAndRenderChart = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        const url = new URL(window.location.origin + '/api/superadmin/charts/user-signups');
        if (startDate) url.searchParams.append('start_date', startDate);
        if (endDate) url.searchParams.append('end_date', endDate);

        const response = await fetch(url.toString(), {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await response.json();

        if (chartInstanceRef.current) {
          chartInstanceRef.current.destroy();
        }

        const ctx = chartRef.current.getContext('2d');
        chartInstanceRef.current = new Chart(ctx, {
          type: 'line',
          data: {
            labels: data.map(d => d.date),
            datasets: [{
              label: 'User Signups',
              data: data.map(d => d.count),
              borderColor: 'rgb(75, 192, 192)',
              tension: 0.1,
              fill: false,
            }]
          }
        });
      } catch (error) {
        console.error("Failed to fetch chart data:", error);
      }
    };
    fetchDataAndRenderChart();

    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
      }
    };
  }, [startDate, endDate]);

  return (
    <div>
      <div className="flex gap-4 mb-4">
        <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} className="p-2 border rounded" />
        <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} className="p-2 border rounded" />
      </div>
      <canvas ref={chartRef}></canvas>
    </div>
  );
};

const SuperadminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [coupons, setCoupons] = useState([]);
  const [orgPage, setOrgPage] = useState(1);
  const [couponPage, setCouponPage] = useState(1);
  const [totalOrgs, setTotalOrgs] = useState(0);
  const [totalCoupons, setTotalCoupons] = useState(0);
  const [orgSearch, setOrgSearch] = useState('');
  const [couponSearch, setCouponSearch] = useState('');
  const [orgSort, setOrgSort] = useState({ column: 'created_at', order: 'desc' });
  const [orgToDeactivate, setOrgToDeactivate] = useState(null);
  const [couponSort, setCouponSort] = useState({ column: 'created_at', order: 'desc' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('accessToken');
      const headers = { Authorization: `Bearer ${token}` };

      const orgsUrl = new URL(window.location.origin + `/api/superadmin/organizations`);
      orgsUrl.searchParams.append('page', orgPage);
      orgsUrl.searchParams.append('per_page', 10);
      orgsUrl.searchParams.append('sort_by', orgSort.column);
      orgsUrl.searchParams.append('sort_order', orgSort.order);
      if (orgSearch) orgsUrl.searchParams.append('search', orgSearch);

      const couponsUrl = `/api/superadmin/coupons?page=${couponPage}&per_page=5&sort_by=${couponSort.column}&sort_order=${couponSort.order}`;

      const [statsResponse, orgsResponse, couponsResponse] = await Promise.all([
        fetch('/api/superadmin/dashboard-stats', { headers }),
        fetch(orgsUrl.toString(), { headers }),
        fetch(couponsUrl, { headers }),
      ]);

      if (!statsResponse.ok) throw new Error('Failed to fetch dashboard stats');
      const statsData = await statsResponse.json();
      setStats(statsData);

      if (!orgsResponse.ok) throw new Error('Failed to fetch organizations');
      const orgsData = await orgsResponse.json();
      setOrganizations(orgsData.items);
      setTotalOrgs(orgsData.total);

      if (!couponsResponse.ok) throw new Error('Failed to fetch coupons');
      const couponsData = await couponsResponse.json();
      setCoupons(couponsData.items);
      setTotalCoupons(couponsData.total);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [orgPage, couponPage, orgSort, couponSort, orgSearch]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSort = (column, type) => {
    const sortState = type === 'org' ? orgSort : couponSort;
    const setSortState = type === 'org' ? setOrgSort : setCouponSort;
    const order = sortState.column === column && sortState.order === 'asc' ? 'desc' : 'asc';
    setSortState({ column, order });
  };

  const handleOrgToggle = (org) => {
    if (org.is_active) {
      setOrgToDeactivate(org);
    } else {
      toggleOrgStatus(org.id);
    }
  };

  const toggleOrgStatus = async (orgId) => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`/api/superadmin/organizations/${orgId}/toggle`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) {
        throw new Error('Failed to update organization status');
      }
      fetchData(); // Refresh data
    } catch (err) {
      console.error(err);
      alert(err.message);
    }
  };

  const confirmOrgDeactivation = () => {
    if (orgToDeactivate) {
      toggleOrgStatus(orgToDeactivate.id);
      setOrgToDeactivate(null);
    }
  };

  if (loading) return <div>Loading Superadmin Dashboard...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="p-8 bg-gray-100 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">God-Level Superadmin Dashboard</h1>
        <Link to="/superadmin/settings" className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">System Settings</Link>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {stats && (
          <>
            <div className="bg-white p-6 rounded-lg shadow-md"><h3 className="text-gray-500">Total Orgs</h3><p className="text-2xl font-bold">{stats.total_organizations}</p></div>
            <div className="bg-white p-6 rounded-lg shadow-md"><h3 className="text-gray-500">Total Users</h3><p className="text-2xl font-bold">{stats.total_users}</p></div>
            <div className="bg-white p-6 rounded-lg shadow-md"><h3 className="text-gray-500">Active Subs</h3><p className="text-2xl font-bold">{stats.active_subscriptions}</p></div>
          </>
        )}
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-4">User Signups</h3>
            <UserSignupsChart />
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold">Organizations</h3>
              <input type="text" placeholder="Search organizations..." value={orgSearch} onChange={e => setOrgSearch(e.target.value)} className="p-2 border rounded" />
            </div>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th onClick={() => handleSort('id', 'org')} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer">ID</th>
                  <th onClick={() => handleSort('name', 'org')} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer">Name</th>
                  <th onClick={() => handleSort('is_active', 'org')} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer">Status</th>
                  <th onClick={() => handleSort('created_at', 'org')} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer">Created At</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payment Status</th>
                  <th onClick={() => handleSort('last_login_at', 'org')} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer">Last Admin Login</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {organizations.map((org) => (
                  <tr key={org.id}>
                    <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900">{org.id}</td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{org.name}</td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        org.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {org.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{new Date(org.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{org.payment_status}</td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                      {org.last_admin_login ? new Date(org.last_admin_login).toLocaleString() : 'Never'}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm font-medium">
                      <button onClick={() => handleOrgToggle(org)} className={`px-3 py-1 text-xs rounded-full ${org.is_active ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                        {org.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
                {organizations.length === 0 && <tr><td colSpan="7" className="text-center py-4 text-sm text-gray-500">No organizations found.</td></tr>}
              </tbody>
            </table>
            <PaginationControls
              currentPage={orgPage}
              totalItems={totalOrgs}
              itemsPerPage={10}
              onPageChange={setOrgPage}
            />
            {orgToDeactivate && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white p-6 rounded-lg shadow-xl max-w-sm w-full">
                  <h3 className="text-lg font-bold text-slate-800">Confirm Deactivation</h3>
                  <p className="text-slate-600 my-4">
                    Are you sure you want to deactivate the organization "<strong>{orgToDeactivate.name}</strong>"? This will prevent all its users from logging in.
                  </p>
                  <div className="flex justify-end gap-3">
                    <button onClick={() => setOrgToDeactivate(null)} className="px-4 py-2 text-slate-700 border border-slate-300 rounded-lg hover:bg-slate-50">Cancel</button>
                    <button onClick={confirmOrgDeactivation} className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium">Deactivate</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
        <div className="space-y-8">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <CouponCreator onCouponCreated={fetchData} />
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <input type="text" placeholder="Search coupons..." value={couponSearch} onChange={e => setCouponSearch(e.target.value)} className="p-2 border rounded w-full mb-4" />
            <CouponList coupons={coupons} onCouponUpdated={fetchData} searchTerm={couponSearch} />
            <PaginationControls
              currentPage={couponPage}
              totalItems={totalCoupons}
              itemsPerPage={5}
              onPageChange={setCouponPage}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SuperadminDashboard;