import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useLocation, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import { User, Users, Settings, LogOut, LayoutDashboard, Briefcase, BookOpen, Package, CreditCard, Headphones, ShieldCheck, Mail, Phone, MapPin, CheckCircle2, ArrowRight, Bell, Trash2, X, Building2, Clock, Star } from 'lucide-react';

import CustomFieldsPage from './CustomFieldsPage';
// Placeholder for module icons - in a real app, these would be proper components or SVGs
const ModuleIcon = ({ iconClass }) => <i className={`${iconClass} text-blue-600 mb-2 block text-xl group-hover:scale-110 transition`}></i>;

/**
 * ErrorBoundary: Catches JavaScript errors anywhere in their child component tree.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
          <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-lg border border-red-100 text-center">
            <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <i className="bi bi-exclamation-triangle-fill text-2xl"></i>
            </div>

            <h2 className="text-xl font-bold text-slate-800 mb-2">Something went wrong</h2>
            <p className="text-slate-600 mb-6 text-sm">We've encountered an unexpected error. Please try refreshing the page.</p>
            <button onClick={() => window.location.reload()} className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition font-medium">
              Refresh Application
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

/**
 * ActivitySkeleton: Provides a shimmer effect for loading lists.
 */
const ActivitySkeleton = () => (
  <div className="animate-pulse space-y-4">
    {[1, 2, 3].map((i) => (
      <div key={i} className="flex items-center gap-3 border-b border-slate-50 pb-3">
        <div className="w-2 h-2 bg-slate-200 rounded-full"></div>
        <div className="h-4 bg-slate-200 rounded w-3/4"></div>
      </div>
    ))}
  </div>
);

/**
 * LoadingSpinner: A reusable Tailwind-based spinner for API calls.
 */
const LoadingSpinner = ({ size = "md", label = "Loading..." }) => {
  const sizes = { sm: "h-4 w-4", md: "h-8 w-8", lg: "h-12 w-12" };
  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className={`${sizes[size]} animate-spin rounded-full border-b-2 border-blue-600`}></div>
      {label && <p className="mt-2 text-sm text-slate-500 font-medium">{label}</p>}
    </div>
  );
};

const showFeatureComingSoon = (feature = 'This feature') => {
  window.alert(`${feature} is coming soon. Please check back later or contact your administrator for access.`);
};

const moduleCatalog = [
  { title: 'Accounting', route: '/books', iconClass: 'bi bi-journal-bookmark', description: 'Record transactions, manage books, and keep finance workflows organized.' },
  { title: 'CRM', route: '/crm', iconClass: 'bi bi-people', description: 'Track customers, leads, deals, and sales activities from one place.' },
  { title: 'Inventory', route: '/inventory', iconClass: 'bi bi-box-seam', description: 'Monitor stock levels, warehouse movement, and inventory health.' },
  { title: 'Payroll', route: '/payroll', iconClass: 'bi bi-cash-stack', description: 'Process payslips, approvals, and payroll compliance with ease.' },
  { title: 'Payments', route: '/pay', iconClass: 'bi bi-credit-card', description: 'Handle invoices, receipts, collections, and payment follow-ups.' },
  { title: 'Helpdesk', route: '/desk', iconClass: 'bi bi-headset', description: 'Resolve tickets, support customers, and keep service response organized.' },
  { title: 'Invoices', route: '/invoices', iconClass: 'bi bi-receipt', description: 'Create, send, and track customer invoices and billing activity.' },
  { title: 'Vendors', route: '/vendors', iconClass: 'bi bi-building', description: 'Manage supplier records, purchase relationships, and vendor performance.' },
  { title: 'Employees', route: '/employees', iconClass: 'bi bi-person-badge', description: 'Maintain employee profiles, roles, and workforce records.' },
  { title: 'Attendance', route: '/attendance', iconClass: 'bi bi-clock-history', description: 'Track daily attendance, clock-ins, and timekeeping workflows.' },
  { title: 'Projects', route: '/projects', iconClass: 'bi bi-kanban', description: 'Plan work, follow milestones, and manage delivery across teams.' },
  { title: 'Performance', route: '/performance', iconClass: 'bi bi-bar-chart-line', description: 'Review goals, evaluations, and team performance insights.' },
];

/**
 * BetaBanner: Displays a prominent "Beta Version - In Testing" banner on all pages.
 */
const BetaBanner = () => {
  return (
    <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-200 px-4 py-3 shadow-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 text-center">
        <span className="inline-flex items-center gap-2">
          <span className="inline-block w-2 h-2 bg-amber-500 rounded-full animate-pulse"></span>
          <span className="text-sm font-semibold text-amber-900">
            <span className="inline-block px-2.5 py-0.5 bg-amber-200 text-amber-900 rounded-full text-xs font-bold mr-2">BETA</span>
            This version is in testing. Features and functionality may change.
          </span>
        </span>
      </div>
    </div>
  );
};

const LandingPage = () => {
  const { isAuthenticated, user } = useAuth();
  const role = user?.role;

  if (isAuthenticated) {
    const dashboardPath = role === 'superadmin' || role === 'super_admin'
      ? '/superadmin/dashboard'
      : '/dashboard';
    return <Navigate to={dashboardPath} replace />;
  }

  return (
    <>
      <nav className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <img src="/static/dist/logo.png" alt="Gaatha Suite" className="h-8 w-8 object-contain rounded" />
          <span className="text-xl font-bold tracking-tight text-slate-800">Gaatha Suite</span>
        </div>
        <div className="flex gap-4">
          <Link to="/auth/login" className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-blue-600 transition">Sign In</Link>
          <Link to="/auth/register" className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 shadow-sm transition">Sign Up</Link>
        </div>
      </nav>

      <main>
        {/* Hero Section */}
        <section className="max-w-6xl mx-auto px-6 py-20 text-center">
          <h1 className="text-5xl font-extrabold text-slate-900 mb-6 tracking-tight">
            The Operating System for <span className="text-blue-600">Your Enterprise</span>
          </h1>
          <p className="text-xl text-slate-600 mb-10 max-w-2xl mx-auto leading-relaxed">
            Unify your Sales, HR, Accounting, and AI-driven analytics in one seamless ecosystem. Built for modern SMEs.
          </p>
          <div className="flex justify-center gap-4">
            <Link to="/modules" className="px-8 py-3 bg-slate-900 text-white font-semibold rounded-lg hover:bg-slate-800 transition shadow-lg">
              Explore Modules
            </Link>
            <button
              type="button"
              onClick={() => document.getElementById('demo-section')?.scrollIntoView({ behavior: 'smooth' })}
              className="px-8 py-3 bg-white border border-slate-200 text-slate-700 font-semibold rounded-lg hover:bg-slate-50 transition shadow-sm"
            >
              Watch Demo
            </button>
          </div>
        </section>

        {/* Module Grid */}
        <section id="modules-section" className="bg-white py-20 border-y border-slate-200">
          <div className="max-w-6xl mx-auto px-6">
            <div className="flex items-center gap-2 mb-12">
              <div className="h-1 w-12 bg-blue-600 rounded"></div>
              <h2 className="text-2xl font-bold text-slate-800">Gaatha Business Suite</h2>
            </div>
            <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
              {moduleCatalog.map((module) => (
                <Link
                  key={module.title}
                  to={module.route}
                  className="group block rounded-3xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-lg"
                >
                  <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                    <ModuleIcon iconClass={module.iconClass} />
                  </div>
                  <h3 className="mt-5 text-lg font-semibold text-slate-900">{module.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{module.description}</p>
                  <div className="mt-5 inline-flex items-center text-sm font-semibold text-blue-600 transition group-hover:translate-x-1">
                    Explore module <span className="ml-2">→</span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* Demo Section */}
        <section id="demo-section" className="bg-slate-50 py-20">
          <div className="max-w-6xl mx-auto px-6">
            <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
              <div>
                <span className="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-blue-700">
                  Watch Demo
                </span>
                <h2 className="mt-6 text-3xl font-bold text-slate-900">See how Gaatha brings your organization together</h2>
                <p className="mt-4 text-slate-600 text-lg leading-8">
                  Preview the core workflows that support Sales, HR, Finance, Inventory, and Support teams from a single platform built for growing enterprises.
                </p>
                <ul className="mt-8 space-y-3 text-slate-600">
                  <li className="flex items-start gap-3"><span className="mt-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-blue-700">✓</span>Unified dashboard for organization-wide operations.</li>
                  <li className="flex items-start gap-3"><span className="mt-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-blue-700">✓</span>Role-based access for finance, sales, HR and support teams.</li>
                  <li className="flex items-start gap-3"><span className="mt-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-blue-700">✓</span>Fast access to business-critical modules from one place.</li>
                </ul>
              </div>
              <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
                <div className="h-64 rounded-3xl bg-slate-100 flex items-center justify-center text-slate-500 text-sm font-medium">
                  Demo preview coming soon
                </div>
                <div className="mt-6 grid gap-3">
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm font-semibold text-slate-900">Org-level insights</p>
                    <p className="mt-2 text-slate-600 text-sm">Monitor team performance, revenue, and operational health in one place.</p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm font-semibold text-slate-900">Secure collaboration</p>
                    <p className="mt-2 text-slate-600 text-sm">Keep sensitive business data protected while sharing access across departments.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="bg-slate-50 py-12 text-center text-slate-500 text-sm">
        <p>© 2026 Aidni Global LLP. All rights reserved.</p>
        <div className="mt-4 flex justify-center gap-6">
          <Link to="/privacy" className="hover:text-blue-600">Privacy Policy</Link>
          <Link to="/terms" className="hover:text-blue-600">Terms of Service</Link>
        </div>
      </footer>
    </>
  );
};

/**
 * LeadConversionModal: Handles the atomic conversion of a Lead to a Customer.
 */
const LeadConversionModal = ({ lead, isOpen, onClose, onConverted }) => {
  const { authFetch } = useAuth();
  const [step, setStep] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);

  if (!isOpen || !lead) return null;

  const handleConvert = async () => {
    setIsProcessing(true);
    setStep(2); // Show progress
    
    try {
      const response = await authFetch(`/crm/api/convert-lead/${lead.id}`, { method: 'POST' });
      if (response && response.ok) {
        setTimeout(() => {
          setStep(3); // Completed
          setIsProcessing(false);
          if (onConverted) onConverted();
        }, 1500);
      }
    } catch (err) {
      console.error("Conversion failed", err);
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden border border-slate-200">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <h3 className="text-xl font-bold text-slate-800">Convert Lead to Customer</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>
        
        <div className="p-8">
          {step === 1 && (
            <div className="space-y-6">
              <div className="flex items-center gap-4 p-4 bg-blue-50 rounded-xl">
                <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">{lead.name[0]}</div>
                <div>
                  <div className="font-bold text-slate-900">{lead.name}</div>
                  <div className="text-sm text-slate-500">{lead.company}</div>
                </div>
              </div>
              <p className="text-slate-600 text-sm">Converting this lead will create a new Customer record and allow you to generate their first invoice automatically.</p>
              <button onClick={handleConvert} className="w-full bg-blue-600 text-white py-3 rounded-xl font-bold hover:bg-blue-700 transition flex items-center justify-center gap-2">
                Start Conversion <ArrowRight size={18} />
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="text-center py-10">
              <LoadingSpinner label="Migrating data & generating accounts..." />
              <div className="mt-4 w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div className="bg-blue-600 h-full animate-[progress_2s_ease-in-out]"></div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="text-center py-6 space-y-4">
              <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 size={40} />
              </div>
              <h4 className="text-2xl font-bold text-slate-900">Conversion Successful!</h4>
              <p className="text-slate-600">Lead has been graduated to a Customer. Chart of accounts synchronized.</p>
              <button onClick={onClose} className="w-full bg-slate-900 text-white py-3 rounded-xl font-bold">Done</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const AddLeadModal = ({ isOpen, onClose, onAdded }) => {
  const { authFetch } = useAuth();
  const [name, setName] = useState('');
  const [company, setCompany] = useState('');
  const [email, setEmail] = useState('');
  const [source, setSource] = useState('Website');
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setName('');
      setCompany('');
      setEmail('');
      setSource('Website');
      setError('');
      setIsSaving(false);
    }
  }, [isOpen]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Lead name is required.');
      return;
    }

    setIsSaving(true);

    try {
      const payload = {
        name: name.trim(),
        company: company.trim() || undefined,
        contact_email: email.trim() || undefined,
        source: source.trim() || 'Website'
      };
      const response = await authFetch('/crm/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response) return;
      if (!response.ok) {
        const responseBody = await response.json().catch(() => ({}));
        setError(responseBody.detail || responseBody.message || 'Unable to create lead.');
        return;
      }

      const created = await response.json();
      if (onAdded) {
        onAdded({
          id: created.id,
          name: created.name,
          company: created.company,
          status: created.status || 'new',
          email: created.email,
          source: created.source
        });
      }
      onClose();
    } catch (err) {
      console.error('Failed to create lead', err);
      setError('Unable to create lead. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-xl w-full overflow-hidden border border-slate-200">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <div>
            <h3 className="text-xl font-bold text-slate-800">Add New Lead</h3>
            <p className="text-slate-500 text-sm">Create a new lead and add it to your sales pipeline.</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Lead Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              placeholder="Enter lead name"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Company</label>
            <input
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              placeholder="Enter company name"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              placeholder="Enter email address"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Lead Source</label>
            <input
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              placeholder="e.g. Website, Referral, Event"
            />
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
          <div className="flex gap-3 mt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="flex-1 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
            >
              {isSaving ? 'Saving...' : 'Create Lead'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const EditCustomerModal = ({ customer, isOpen, onClose, onSaved }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [status, setStatus] = useState('Active');
  const [totalValue, setTotalValue] = useState(0);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && customer) {
      setName(customer.name || '');
      setEmail(customer.email || '');
      setPhone(customer.phone || '');
      setStatus(customer.status || 'Active');
      setTotalValue(customer.totalValue || 0);
      setError('');
    }
  }, [isOpen, customer]);

  if (!isOpen || !customer) return null;

  const handleSubmit = (event) => {
    event.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Customer name is required.');
      return;
    }

    if (onSaved) {
      onSaved({
        ...customer,
        name: name.trim(),
        email: email.trim(),
        phone: phone.trim(),
        status,
        totalValue: Number(totalValue) || 0,
      });
    }

    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-xl w-full overflow-hidden border border-slate-200">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <div>
            <h3 className="text-xl font-bold text-slate-800">Manage Customer</h3>
            <p className="text-slate-500 text-sm">Update customer details and account status.</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Customer Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Phone</label>
            <input value={phone} onChange={(e) => setPhone(e.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">Status</label>
              <select value={status} onChange={(e) => setStatus(e.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500">
                <option value="Active">Active</option>
                <option value="Inactive">Inactive</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Total Value</label>
              <input type="number" min="0" value={totalValue} onChange={(e) => setTotalValue(e.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500" />
            </div>
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
          <div className="flex gap-3 mt-4">
            <button type="button" onClick={onClose} className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">Cancel</button>
            <button type="submit" className="flex-1 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700">Save Changes</button>
          </div>
        </form>
      </div>
    </div>
  );
};

const CRMPage = () => {
  const { authFetch } = useAuth();
  const [leads, setLeads] = useState([]);
  const [selectedLead, setSelectedLead] = useState(null);
  const [isAddLeadOpen, setIsAddLeadOpen] = useState(false);

  useEffect(() => {
    const loadLeads = async () => {
      try {
        const response = await authFetch('/crm/api/leads');
        if (!response) return;
        if (response.ok) {
          const data = await response.json();
          setLeads(data);
        }
      } catch (err) {
        console.error('Failed to load CRM leads', err);
      }
    };
    loadLeads();
  }, [authFetch]);

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Users className="text-blue-600" /> Sales Pipeline
          </h2>
          <p className="text-slate-500 text-sm">Manage your leads and convert them to long-term partners.</p>
        </div>
        <button onClick={() => setIsAddLeadOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition">
          + Add New Lead
        </button>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="p-4 text-sm font-semibold text-slate-600">Lead Name</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Company</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
              <th className="p-4 text-sm font-semibold text-slate-600 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {leads.map(lead => (
              <tr key={lead.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                <td className="p-4 font-medium text-slate-900">{lead.name}</td>
                <td className="p-4 text-slate-600 text-sm">{lead.company}</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase ${
                    lead.status === 'Hot' ? 'bg-orange-100 text-orange-600' : 'bg-blue-100 text-blue-600'
                  }`}>
                    {lead.status}
                  </span>
                </td>
                <td className="p-4 text-right">
                  <button 
                    onClick={() => setSelectedLead(lead)}
                    className="text-blue-600 hover:text-blue-800 text-sm font-bold flex items-center gap-1 ml-auto"
                  >
                    Convert <ArrowRight size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <LeadConversionModal 
        lead={selectedLead} 
        isOpen={!!selectedLead} 
        onClose={() => setSelectedLead(null)}
        onConverted={() => setLeads(leads.filter(l => l.id !== selectedLead.id))}
      />
      <AddLeadModal
        isOpen={isAddLeadOpen}
        onClose={() => setIsAddLeadOpen(false)}
        onAdded={(newLead) => setLeads((prevLeads) => [newLead, ...prevLeads])}
      />
    </div>
  );
};

const CustomersPage = () => {
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Users className="text-blue-600" /> Customers
          </h2>
          <p className="text-slate-500 text-sm">Manage your customer relationships and account information.</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="p-4 text-sm font-semibold text-slate-600">Customer Name</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Email</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Phone</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Total Value</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
              <th className="p-4 text-sm font-semibold text-slate-600 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {customers.map(customer => (
              <tr key={customer.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                <td className="p-4 font-medium text-slate-900">{customer.name}</td>
                <td className="p-4 text-slate-600 text-sm">{customer.email}</td>
                <td className="p-4 text-slate-600 text-sm">{customer.phone}</td>
                <td className="p-4 font-semibold text-slate-900">${customer.totalValue.toLocaleString()}</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase ${
                    customer.status === 'Active' ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {customer.status}
                  </span>
                </td>
                <td className="p-4 text-right">
                  <button
                    onClick={() => setSelectedCustomer(customer)}
                    className="text-blue-600 hover:text-blue-800 text-sm font-bold"
                  >
                    Manage
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <EditCustomerModal
        customer={selectedCustomer}
        isOpen={!!selectedCustomer}
        onClose={() => setSelectedCustomer(null)}
        onSaved={(updatedCustomer) => {
          setCustomers((prevCustomers) =>
            prevCustomers.map((customer) => customer.id === updatedCustomer.id ? updatedCustomer : customer)
          );
        }}
      />
    </div>
  );
};

const DealsPage = () => {
  const [deals, setDeals] = useState([]);
  const [isAddDealOpen, setIsAddDealOpen] = useState(false);

  const stageColors = {
    'Lead': 'bg-blue-100 text-blue-600',
    'Proposal': 'bg-yellow-100 text-yellow-600',
    'Negotiation': 'bg-orange-100 text-orange-600',
    'Won': 'bg-green-100 text-green-600',
    'Lost': 'bg-red-100 text-red-600'
  };

  const handleAddDeal = (deal) => {
    const nextId = deals.length ? Math.max(...deals.map(d => d.id)) + 1 : 1;
    setDeals((prevDeals) => [{ id: nextId, ...deal }, ...prevDeals]);
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Briefcase className="text-blue-600" /> Deals & Opportunities
          </h2>
          <p className="text-slate-500 text-sm">Track your sales pipeline and deal progress.</p>
        </div>
        <button onClick={() => setIsAddDealOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition">
          + New Deal
        </button>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="p-4 text-sm font-semibold text-slate-600">Deal Name</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Customer</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Amount</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Stage</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Close Date</th>
            </tr>
          </thead>
          <tbody>
            {deals.map(deal => (
              <tr key={deal.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                <td className="p-4 font-medium text-blue-600 cursor-pointer hover:underline">{deal.name}</td>
                <td className="p-4 text-slate-600 text-sm">{deal.customer}</td>
                <td className="p-4 font-semibold text-slate-900">${deal.amount.toLocaleString()}</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase ${stageColors[deal.stage]}`}>
                    {deal.stage}
                  </span>
                </td>
                <td className="p-4 text-slate-600 text-sm">{deal.closeDate}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <AddDealModal
        isOpen={isAddDealOpen}
        onClose={() => setIsAddDealOpen(false)}
        onAdded={handleAddDeal}
      />
    </div>
  );
};

const AddDealModal = ({ isOpen, onClose, onAdded }) => {
  const [name, setName] = useState('');
  const [customer, setCustomer] = useState('');
  const [amount, setAmount] = useState('');
  const [stage, setStage] = useState('Lead');
  const [closeDate, setCloseDate] = useState('');
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setName('');
      setCustomer('');
      setAmount('');
      setStage('Lead');
      setCloseDate('');
      setError('');
      setIsSaving(false);
    }
  }, [isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !customer || !amount || !closeDate) {
      setError('Deal name, customer, amount, and close date are required.');
      return;
    }
    setIsSaving(true);
    onAdded({
      name,
      customer,
      amount: parseFloat(amount),
      stage,
      closeDate
    });
    onClose();
    setIsSaving(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h3 className="text-xl font-bold mb-4">Create New Deal</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Deal Name *</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Deal name" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Customer *</label>
            <input type="text" value={customer} onChange={(e) => setCustomer(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Customer name" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Amount *</label>
            <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="0.00" step="0.01" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Stage *</label>
            <select value={stage} onChange={(e) => setStage(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="Lead">Lead</option>
              <option value="Proposal">Proposal</option>
              <option value="Negotiation">Negotiation</option>
              <option value="Won">Won</option>
              <option value="Lost">Lost</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Expected Close Date *</label>
            <input type="date" value={closeDate} onChange={(e) => setCloseDate(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          {error && <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">{error}</div>}
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={onClose} className="px-4 py-2 text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50">Cancel</button>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
              {isSaving ? 'Creating...' : 'Create Deal'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const CRMHub = () => {
  const [activeTab, setActiveTab] = useState('leads');

  return (
    <div className="flex-1 min-h-screen">
      {/* Tab Navigation */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="p-6">
          <h1 className="text-3xl font-bold text-slate-900 mb-4">CRM</h1>
          <div className="flex gap-1 border-b border-slate-200">
            <button
              onClick={() => setActiveTab('leads')}
              className={`px-4 py-3 font-medium transition ${activeTab === 'leads' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
            >
              Leads
            </button>
            <button
              onClick={() => setActiveTab('customers')}
              className={`px-4 py-3 font-medium transition ${activeTab === 'customers' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
            >
              Customers
            </button>
            <button
              onClick={() => setActiveTab('deals')}
              className={`px-4 py-3 font-medium transition ${activeTab === 'deals' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
            >
              Deals & Opportunities
            </button>
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'leads' && <CRMPage />}
        {activeTab === 'customers' && <CustomersPage />}
        {activeTab === 'deals' && <DealsPage />}
      </div>
    </div>
  );
};

const ProfilePage = () => {
  const { authFetch } = useAuth();
  const [profile, setProfile] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    authFetch('/auth/users/me')
      .then((res) => {
        if (!res || !res.ok) {
          throw new Error('Failed to load profile');
        }
        return res.json();
      })
      .then((data) => setProfile(data))
      .catch((err) => {
        console.error('Profile load error:', err);
        setError('Unable to load profile. Please try again later.');
      });
  }, []);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const payload = {
        username: profile.username,
        email: profile.email,
        first_name: profile.first_name,
        last_name: profile.last_name,
        phone: profile.phone,
        department: profile.department,
      };

      if (password) {
        payload.password = password;
      }

      const response = await authFetch('/auth/users/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response || !response.ok) {
        throw new Error('Unable to save profile.');
      }

      const updatedProfile = await response.json();
      setProfile(updatedProfile);
      setPassword('');
    } catch (err) {
      console.error('Profile update error:', err);
      alert('Unable to save profile. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (error) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
          {error}
        </div>
      </div>
    );
  }

  if (!profile) return <div className="p-8"><LoadingSpinner /></div>;

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
        <User className="text-blue-600" /> User Profile
      </h2>
      <form onSubmit={handleUpdate} className="bg-white p-8 rounded-xl shadow-sm border border-slate-200 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">First Name</label>
            <input
              type="text"
              className="mt-1 block w-full border border-slate-300 rounded-md p-2"
              value={profile.first_name || ''}
              onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Last Name</label>
            <input
              type="text"
              className="mt-1 block w-full border border-slate-300 rounded-md p-2"
              value={profile.last_name || ''}
              onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Email</label>
            <input
              type="email"
              className="mt-1 block w-full border border-slate-300 rounded-md p-2 bg-slate-50"
              value={profile.email || ''}
              disabled
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Username</label>
            <input
              type="text"
              className="mt-1 block w-full border border-slate-300 rounded-md p-2"
              value={profile.username || ''}
              onChange={(e) => setProfile({ ...profile, username: e.target.value })}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Phone</label>
            <input
              type="text"
              className="mt-1 block w-full border border-slate-300 rounded-md p-2"
              value={profile.phone || ''}
              onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Designation</label>
            <input
              type="text"
              className="mt-1 block w-full border border-slate-300 rounded-md p-2"
              value={profile.department || ''}
              onChange={(e) => setProfile({ ...profile, department: e.target.value })}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">New Password (optional)</label>
          <input
            type="password"
            className="mt-1 block w-full border border-slate-300 rounded-md p-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Leave blank to keep current password"
          />
        </div>

        <button type="submit" disabled={isSaving} className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:opacity-50">
          {isSaving ? 'Updating...' : 'Save Changes'}
        </button>
      </form>
    </div>
  );
};

const OrganizationSettingsPage = () => {
  const { authFetch, user } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    logo_url: '',
    website: '',
    email: '',
    phone: '',
    address: '',
    currency: 'USD',
    tax_id: '',
    invoice_notes: '',
    invoice_terms: '',
    invoice_template: 'classic',
  });
  const [isSaving, setIsSaving] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState({ type: '', message: '' });

  const invoiceTemplates = [
    { id: 'classic', title: 'Classic', description: 'Bold header with a traditional invoice layout.' },
    { id: 'modern', title: 'Modern', description: 'Clean, structured blocks with accent color.' },
    { id: 'minimal', title: 'Minimal', description: 'Simple white layout for fast, elegant invoicing.' },
  ];

  useEffect(() => {
    if (!user) return;
    authFetch('/api/v2/settings/')
      .then(res => res?.ok ? res.json() : null)
      .then(data => {
        if (data) {
          setFormData({
            name: data.name || '',
            logo_url: data.logo_url || '',
            website: data.website || '',
            email: data.email || '',
            phone: data.phone || '',
            address: data.address || '',
            currency: data.currency || 'USD',
            tax_id: data.tax_id || '',
            invoice_notes: data.invoice_notes || '',
            invoice_terms: data.invoice_terms || '',
            invoice_template: data.invoice_template || 'classic',
          });
        }
      })
      .catch(() => {});
  }, [user]);

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setStatus({ type: 'info', message: 'Saving organization settings...' });

    const response = await authFetch('/api/v2/settings/', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });

    if (!response || !response.ok) {
      setStatus({ type: 'error', message: 'Unable to save settings. Please try again.' });
      setIsSaving(false);
      return;
    }

    const data = await response.json();
    setFormData({
      name: data.name || '',
      logo_url: data.logo_url || '',
      website: data.website || '',
      email: data.email || '',
      phone: data.phone || '',
      address: data.address || '',
      currency: data.currency || 'USD',
      tax_id: data.tax_id || '',
      invoice_notes: data.invoice_notes || '',
      invoice_terms: data.invoice_terms || '',
      invoice_template: data.invoice_template || 'classic',
    });
    setStatus({ type: 'success', message: 'Organization settings saved successfully.' });
    setIsSaving(false);
  };

  const isAdmin = user?.role === 'admin' || user?.role === 'orgadmin' || user?.role === 'superadmin' || user?.role === 'super_admin';

  const handleLogoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setStatus({ type: 'info', message: 'Uploading logo...' });

    const uploadFormData = new FormData();
    uploadFormData.append('file', file);

    try {
      const response = await authFetch('/api/v2/books/logo', {
        method: 'POST',
        body: uploadFormData,
        headers: {}, // Let browser set Content-Type for FormData
      });
      const data = await response.json();
      setFormData({ ...formData, logo_url: data.path });
      setStatus({ type: 'success', message: 'Logo uploaded successfully.' });
    } catch (err) {
      setStatus({ type: 'error', message: 'Logo upload failed.' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDragEvents = (e, dragging) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(dragging);
  };

  const handleDrop = (e) => {
    handleDragEvents(e, false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      // Create a synthetic event to reuse the existing upload handler
      handleLogoUpload({ target: { files } });
      // It's good practice to clear the data transfer
      e.dataTransfer.clearData();
    }
  };

  if (!isAdmin) {
    return (
      <div className="p-8 max-w-3xl mx-auto">
        <h2 className="text-2xl font-bold text-slate-800 mb-4">Organization Settings</h2>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 text-slate-700">
          <p className="text-sm">Only organization administrators can update company branding, invoice templates, and invoice footer settings.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Organization Settings</h2>
          <p className="text-slate-500">Update company branding, invoice footers, and invoice template selection.</p>
        </div>
        <button onClick={handleSave} disabled={isSaving} className="bg-blue-600 text-white px-5 py-2 rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50">
          {isSaving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>

      {status.message && (
        <div className={`mb-6 p-4 rounded-lg text-sm ${status.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : status.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-blue-50 text-blue-700 border border-blue-200'}`}>
          {status.message}
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-700">Company Name</label>
            <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="mt-1 block w-full border border-slate-300 rounded-md p-3" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Upload Logo</label>
            <div
              onDragEnter={(e) => handleDragEvents(e, true)}
              onDragLeave={(e) => handleDragEvents(e, false)}
              onDragOver={(e) => handleDragEvents(e, true)}
              onDrop={handleDrop}
              className={`mt-1 flex justify-center rounded-lg border-2 border-dashed px-6 py-10 transition ${isDragging ? 'border-blue-600 bg-blue-50' : 'border-slate-300'}`}
            >
              <div className="text-center">
                <p className="text-sm text-slate-600">{isUploading ? 'Uploading...' : 'Drag & drop a logo, or click to select'}</p>
                <input id="logo-upload" type="file" onChange={handleLogoUpload} accept="image/png, image/jpeg" className="sr-only" />
                <label htmlFor="logo-upload" className="cursor-pointer text-sm font-semibold text-blue-600 hover:text-blue-500">
                  <span>Upload a file</span>
                </label>
              </div>
            </div>
            {formData.logo_url && (
              <img src={formData.logo_url} alt="Logo preview" className="mt-4 h-16 object-contain rounded-md border border-slate-200 p-2" />
            )}
          </div>
        </div>

        {formData.logo_url && (
          <div className="rounded-xl overflow-hidden border border-slate-200 p-4 bg-slate-50">
            <p className="text-sm text-slate-600 mb-2">Logo preview</p>
            <img src={formData.logo_url} alt="Company logo preview" className="h-20 object-contain" />
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-700">Website</label>
            <input type="url" value={formData.website} onChange={(e) => setFormData({ ...formData, website: e.target.value })} className="mt-1 block w-full border border-slate-300 rounded-md p-3" placeholder="https://yourcompany.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Email</label>
            <input type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} className="mt-1 block w-full border border-slate-300 rounded-md p-3" placeholder="contact@company.com" />
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-700">Phone</label>
            <input type="tel" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} className="mt-1 block w-full border border-slate-300 rounded-md p-3" placeholder="+91 98765 43210" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Address</label>
            <input type="text" value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} className="mt-1 block w-full border border-slate-300 rounded-md p-3" placeholder="123 Main St, City, Country" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Company Tax ID</label>
          <input type="text" value={formData.tax_id} onChange={(e) => setFormData({ ...formData, tax_id: e.target.value })} className="mt-1 block w-full border border-slate-300 rounded-md p-3" placeholder="e.g., GSTIN, EIN" />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-700">Default Currency</label>
            <select value={formData.currency || 'USD'} onChange={(e) => setFormData({ ...formData, currency: e.target.value })} className="mt-1 block w-full border border-slate-300 rounded-md p-3 bg-white">
              <option value="USD">USD (US Dollar)</option>
              <option value="EUR">EUR (Euro)</option>
              <option value="GBP">GBP (British Pound)</option>
              <option value="INR">INR (Indian Rupee)</option>
              <option value="AUD">AUD (Australian Dollar)</option>
              <option value="CAD">CAD (Canadian Dollar)</option>
              <option value="JPY">JPY (Japanese Yen)</option>
            </select>
          </div>
          <div className="rounded-xl border border-blue-100 bg-blue-50 p-3 text-sm text-blue-800">
            Org admins can now set the default currency used for invoices and finance reports.
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Invoice Note</label>
          <textarea value={formData.invoice_notes} onChange={(e) => setFormData({ ...formData, invoice_notes: e.target.value })} rows={4} className="mt-1 block w-full border border-slate-300 rounded-md p-3" placeholder="Add a note to appear on invoices, such as payment reminders or thank-you messages." />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Invoice Conditions</label>
          <textarea value={formData.invoice_terms} onChange={(e) => setFormData({ ...formData, invoice_terms: e.target.value })} rows={4} className="mt-1 block w-full border border-slate-300 rounded-md p-3" placeholder="Payment terms, conditions, or legal notes that appear on invoices." />
        </div>

        <div>
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-lg font-semibold text-slate-800">Invoice Template</h3>
              <p className="text-sm text-slate-500">Choose the invoice design used for outgoing invoices.</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {invoiceTemplates.map((template) => (
              <button
                key={template.id}
                type="button"
                onClick={() => setFormData({ ...formData, invoice_template: template.id })}
                className={`rounded-2xl border p-4 text-left transition ${formData.invoice_template === template.id ? 'border-blue-600 bg-blue-50 shadow-sm' : 'border-slate-200 bg-white hover:border-slate-400'}`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-semibold text-slate-900">{template.title}</h4>
                    <p className="text-sm text-slate-500">{template.description}</p>
                  </div>
                  {formData.invoice_template === template.id && <span className="text-xs font-semibold uppercase text-blue-600">Selected</span>}
                </div>
                <div className="h-24 rounded-xl bg-slate-100 p-3">
                  <div className="h-3 rounded-full bg-slate-300 mb-2 w-3/4"></div>
                  <div className="h-3 rounded-full bg-slate-300 mb-2 w-1/2"></div>
                  <div className="h-3 rounded-full bg-slate-300 w-5/6"></div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </form>
    </div>
  );
};

const UsersListPage = () => {
  const { authFetch } = useAuth();
  const [users, setUsers] = useState([]);
  const [departments, setDepartments] = useState([]);

  const { user } = useAuth();
  const [newUser, setNewUser] = useState({ username: '', email: '', password: '', role: 'user', department: '' });
  const [isCreating, setIsCreating] = useState(false);
  const [editingUser, setEditingUser] = useState(null);

  useEffect(() => {
    authFetch('/auth/users')
      .then(res => res?.json())
      .then(data => setUsers(data));

    authFetch('/departments')
      .then(r => r?.json())
      .then(d => setDepartments(Array.isArray(d) ? d : []))
      .catch(() => setDepartments([]));
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      const method = editingUser ? 'PUT' : 'POST';
      const url = editingUser ? `/auth/users/${editingUser.id}` : '/auth/users';
      const res = await authFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newUser)
      });
      const created = await res.json();
      if (editingUser) {
        setUsers(prev => prev.map(u => u.id === created.id ? created : u));
        setEditingUser(null);
      } else {
        setUsers(prev => [created, ...prev]);
      }
      setNewUser({ username: '', email: '', password: '', role: 'user', department: '' });
    } catch (err) {
      console.error('Create user failed', err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleEdit = (u) => {
    setEditingUser(u);
    setNewUser({ username: u.username, email: u.email, password: '', role: u.role || 'user', department: u.department || '' });
  }

  const handleDelete = async (u) => {
    if (!confirm(`Delete user ${u.username}?`)) return;
    try {
      const res = await authFetch(`/auth/users/${u.id}`, { method: 'DELETE' });
      const body = await res.json();
      if (body.deleted) setUsers(prev => prev.filter(x => x.id !== u.id));
    } catch (err) {
      console.error('Delete failed', err);
    }
  }

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
        <Users className="text-blue-600" /> System Users
      </h2>
      {(user?.role === 'superadmin' || user?.role === 'orgadmin') && (
        <form onSubmit={handleCreate} className="mb-6 bg-white p-4 rounded-md shadow-sm border border-slate-200 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <input required placeholder="Username" className="p-2 border rounded" value={newUser.username} onChange={e=>setNewUser({...newUser, username: e.target.value})} />
            <input required type="email" placeholder="Email" className="p-2 border rounded" value={newUser.email} onChange={e=>setNewUser({...newUser, email: e.target.value})} />
            <input required type="password" placeholder="Password" className="p-2 border rounded" value={newUser.password} onChange={e=>setNewUser({...newUser, password: e.target.value})} />
            <select className="p-2 border rounded" value={newUser.department} onChange={e=>setNewUser({...newUser, department: e.target.value})}>
              <option value="">Select Department</option>
              {departments.map(d => (
                <option key={d.id} value={d.name}>{d.name}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-3">
            <select className="p-2 border rounded" value={newUser.role} onChange={e=>setNewUser({...newUser, role: e.target.value})}>
              <option value="user">User</option>
              <option value="manager">Manager</option>
              <option value="orgadmin">Org Admin</option>
            </select>
            <button disabled={isCreating} className="bg-blue-600 text-white px-4 py-2 rounded">{isCreating? 'Creating...':'Create User'}</button>
          </div>
        </form>
      )}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="p-4 text-sm font-semibold text-slate-700">Username</th>
              <th className="p-4 text-sm font-semibold text-slate-700">Email</th>
              <th className="p-4 text-sm font-semibold text-slate-700">Role</th>
              <th className="p-4 text-sm font-semibold text-slate-700">Department</th>
              <th className="p-4 text-sm font-semibold text-slate-700 text-right">Status</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} className="border-b border-slate-100 hover:bg-slate-50 transition">
                <td className="p-4 text-sm font-medium text-slate-900">{u.username}</td>
                <td className="p-4 text-sm text-slate-600">{u.email}</td>
                <td className="p-4">
                  <span className="px-2 py-1 text-xs font-bold rounded-full bg-blue-100 text-blue-700 uppercase">
                    {u.role.replace('_', ' ')}
                  </span>
                </td>
                <td className="p-4 text-sm text-slate-600">{u.department || 'Unassigned'}</td>
                <td className="p-4 text-right">
                  <div className="flex justify-end gap-2 items-center">
                    <button onClick={()=>handleEdit(u)} className="text-sm text-blue-600">Edit</button>
                    <button onClick={()=>handleDelete(u)} className="text-sm text-red-500">Delete</button>
                    {u.is_admin ? <ShieldCheck className="inline text-green-500 w-5 h-5" /> : null}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};


const DepartmentsPage = () => {
  const { authFetch } = useAuth();
  const [departments, setDepartments] = useState([]);
  const [name, setName] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(()=>{
    authFetch('/departments').then(r=>r.json()).then(d=>setDepartments(d)).catch(()=>setDepartments([]));
  },[]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const res = await authFetch('/departments', { method: 'POST', body: JSON.stringify({ name }), headers: { 'Content-Type': 'application/json' } });
      const created = await res.json();
      setDepartments(prev=>[created,...prev]);
      setName('');
    } catch (err) { console.error(err) }
    setIsSaving(false);
  }

  const handleDelete = async (dept) => {
    if (!confirm(`Delete department ${dept.name}?`)) return;
    try {
      const res = await authFetch(`/departments/${dept.id}`, { method: 'DELETE' });
      const body = await res.json();
      if (body.deleted) setDepartments(prev => prev.filter(x => x.id !== dept.id));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">Departments</h2>
      <form onSubmit={handleCreate} className="mb-6 flex gap-2">
        <input required className="p-2 border rounded" placeholder="Department name" value={name} onChange={e=>setName(e.target.value)} />
        <button className="bg-blue-600 text-white px-4 py-2 rounded">{isSaving? 'Saving...':'Add'}</button>
      </form>
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <ul>
          {departments.map(d=> (
            <li key={d.id} className="p-4 border-b flex items-center justify-between gap-4">
              <span>{d.name}</span>
              <button onClick={() => handleDelete(d)} className="text-sm text-red-500">Delete</button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

const EmployeesPage = () => {
  const { authFetch } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [form, setForm] = useState({
    employee_code: '',
    name: '',
    email: '',
    phone: '',
    department_id: '',
    position: '',
    hired_date: '',
    salary: ''
  });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    authFetch('/api/v2/hr/employees')
      .then(res => res.ok ? res.json() : [])
      .then(data => setEmployees(Array.isArray(data) ? data : []))
      .catch(() => setEmployees([]));
    authFetch('/departments')
      .then(res => res.ok ? res.json() : [])
      .then(data => setDepartments(Array.isArray(data) ? data : []))
      .catch(() => setDepartments([]));
  }, [authFetch]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setIsSaving(true);

    try {
      const payload = {
        employee_code: form.employee_code,
        name: form.name,
        email: form.email,
        phone: form.phone,
        department_id: form.department_id ? Number(form.department_id) : null,
        position: form.position,
        hired_date: form.hired_date || null,
        salary: form.salary ? Number(form.salary) : 0
      };
      const res = await authFetch('/api/v2/hr/employees', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const created = await res.json();
      setEmployees(prev => [created, ...prev]);
      setForm({ employee_code: '', name: '', email: '', phone: '', department_id: '', position: '', hired_date: '', salary: '' });
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (employee) => {
    if (!confirm(`Delete employee ${employee.name}?`)) return;
    try {
      await authFetch(`/api/v2/hr/employees/${employee.id}`, { method: 'DELETE' });
      setEmployees(prev => prev.filter(e => e.id !== employee.id));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-8">
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Employee Information</h2>
          <p className="text-slate-500 text-sm">Centralized personnel records and organizational profiles.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full lg:w-auto">
          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <div className="text-xs uppercase text-slate-400 mb-2">Employees</div>
            <div className="text-3xl font-bold text-slate-900">{employees.length}</div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <div className="text-xs uppercase text-slate-400 mb-2">Departments</div>
            <div className="text-3xl font-bold text-slate-900">{departments.length}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-1 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="font-semibold mb-4">Add New Employee</h3>
          <form onSubmit={handleCreate} className="space-y-3">
            <input className="w-full p-3 border rounded" placeholder="Employee Code" value={form.employee_code} onChange={e=>setForm({...form, employee_code: e.target.value})} required />
            <input className="w-full p-3 border rounded" placeholder="Name" value={form.name} onChange={e=>setForm({...form, name: e.target.value})} required />
            <input className="w-full p-3 border rounded" placeholder="Email" value={form.email} onChange={e=>setForm({...form, email: e.target.value})} />
            <input className="w-full p-3 border rounded" placeholder="Phone" value={form.phone} onChange={e=>setForm({...form, phone: e.target.value})} />
            <select className="w-full p-3 border rounded" value={form.department_id} onChange={e=>setForm({...form, department_id: e.target.value})}>
              <option value="">Select Department</option>
              {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
            <input className="w-full p-3 border rounded" placeholder="Position" value={form.position} onChange={e=>setForm({...form, position: e.target.value})} />
            <input type="date" className="w-full p-3 border rounded" value={form.hired_date} onChange={e=>setForm({...form, hired_date: e.target.value})} />
            <input type="number" className="w-full p-3 border rounded" placeholder="Salary" value={form.salary} onChange={e=>setForm({...form, salary: e.target.value})} />
            <button disabled={isSaving} className="w-full bg-blue-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-blue-700 transition">{isSaving ? 'Saving...' : 'Add Employee'}</button>
          </form>
        </div>
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-200">
            <h3 className="text-lg font-semibold">Employee Directory</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="p-4 text-sm font-semibold text-slate-600">Code</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Name</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Department</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Role</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Salary</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {employees.map(emp => (
                  <tr key={emp.id} className="border-b border-slate-100 hover:bg-slate-50 transition">
                    <td className="p-4 font-medium text-slate-900">{emp.employee_code}</td>
                    <td className="p-4 text-slate-600">{emp.name}</td>
                    <td className="p-4 text-slate-600">{emp.department_name || 'N/A'}</td>
                    <td className="p-4 text-slate-600">{emp.position || '—'}</td>
                    <td className="p-4 font-semibold text-slate-900">${(emp.salary || 0).toLocaleString()}</td>
                    <td className="p-4 text-right">
                      <button onClick={() => handleDelete(emp)} className="text-sm text-red-500">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

const AttendancePage = () => {
  const { authFetch } = useAuth();
  const [records, setRecords] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadRecords = async () => {
    setIsLoading(true);
    try {
      const res = await authFetch('/api/v2/hr/attendance/today');
      setRecords(await res.json());
    } catch (err) {
      console.error(err);
      setRecords([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadRecords();
  }, [authFetch]);

  const handleClockIn = async () => {
    try {
      await authFetch('/api/v2/hr/attendance/clock-in', { method: 'POST' });
      loadRecords();
    } catch (err) {
      console.error(err);
    }
  };

  const handleClockOut = async () => {
    try {
      await authFetch('/api/v2/hr/attendance/clock-out', { method: 'POST' });
      loadRecords();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-8">
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Time & Attendance</h2>
          <p className="text-slate-500 text-sm">Track employee check-ins, hours, and attendance status.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={handleClockIn} className="bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700 transition">Clock In</button>
          <button onClick={handleClockOut} className="bg-slate-800 text-white px-4 py-2 rounded-lg hover:bg-slate-900 transition">Clock Out</button>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Today&apos;s Attendance</h3>
            <p className="text-slate-500 text-sm">Latest clock in/out records for your organization.</p>
          </div>
          {isLoading ? <span className="text-slate-500">Loading...</span> : null}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="p-4 text-sm font-semibold text-slate-600">Employee</th>
                <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
                <th className="p-4 text-sm font-semibold text-slate-600">Clock In</th>
                <th className="p-4 text-sm font-semibold text-slate-600">Clock Out</th>
                <th className="p-4 text-sm font-semibold text-slate-600">Hours</th>
              </tr>
            </thead>
            <tbody>
              {records.length === 0 ? (
                <tr>
                  <td colSpan="5" className="p-4 text-slate-500">No attendance records for today.</td>
                </tr>
              ) : records.map(rec => (
                <tr key={rec.id} className="border-b border-slate-100 hover:bg-slate-50 transition">
                  <td className="p-4 font-medium text-slate-900">{rec.employee_name || 'Unknown'}</td>
                  <td className="p-4 text-slate-600">{rec.status}</td>
                  <td className="p-4 text-slate-600">{rec.check_in ? new Date(rec.check_in).toLocaleTimeString() : '—'}</td>
                  <td className="p-4 text-slate-600">{rec.check_out ? new Date(rec.check_out).toLocaleTimeString() : '—'}</td>
                  <td className="p-4 text-slate-600">{rec.hours_worked ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

/**
 * NotificationCenter: Manages and displays a history of WebSocket alerts.
 */
const NotificationCenter = ({ notifications, onClear, onRemove }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-slate-400 hover:text-blue-600 transition"
      >
        <Bell size={20} />
        {notifications.length > 0 && (
          <span className="absolute top-0 right-0 w-4 h-4 bg-red-500 text-white text-[10px] flex items-center justify-center rounded-full animate-pulse">
            {notifications.length}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-2xl border border-slate-200 z-[110] overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <h4 className="font-bold text-slate-800 text-sm">Notifications</h4>
            {notifications.length > 0 && (
              <button onClick={onClear} className="text-[10px] text-red-500 hover:underline flex items-center gap-1">
                <Trash2 size={10} /> Clear All
              </button>
            )}
          </div>
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-sm italic">No recent alerts</div>
            ) : (
              notifications.map((n, idx) => (
                <div key={idx} className="p-4 border-b border-slate-50 last:border-0 hover:bg-slate-50 transition group flex justify-between gap-2">
                  <div className="text-xs text-slate-600 leading-relaxed">{n.msg}</div>
                  <button onClick={() => onRemove(idx)} className="text-slate-300 hover:text-slate-500 opacity-0 group-hover:opacity-100 transition">
                    <X size={12} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
      {/* CreatePayslipModal intentionally rendered in PayrollPage only. */}
    </div>
  );
};


const SuperadminDashboard = () => {
  const { authFetch, user } = useAuth();
  const [stats, setStats] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [coupons, setCoupons] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const [statsResponse, organizationsResponse, couponsResponse] = await Promise.all([
          authFetch('/api/superadmin/dashboard-stats'),
          authFetch('/api/superadmin/organizations'),
          authFetch('/api/superadmin/coupons'),
        ]);

        if (!statsResponse.ok) throw new Error('Unable to load superadmin statistics.');
        if (!organizationsResponse.ok) throw new Error('Unable to load organizations.');
        if (!couponsResponse.ok) throw new Error('Unable to load coupons.');

        const [statsData, organizationsData, couponsData] = await Promise.all([
          statsResponse.json(),
          organizationsResponse.json(),
          couponsResponse.json(),
        ]);

        setStats(statsData);
        setOrganizations(organizationsData.items || []);
        setCoupons(couponsData.items || []);
      } catch (err) {
        console.error('Failed to load superadmin dashboard', err);
        setError(err.message || 'Unable to load superadmin dashboard.');
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, [authFetch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" label="Preparing superadmin dashboard..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-6">
          <h1 className="text-xl font-bold mb-2">Superadmin dashboard could not load</h1>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 bg-slate-50 min-h-screen">
      <header className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">Superadmin</p>
        <h1 className="text-3xl font-bold text-slate-900">Welcome back, {user?.username || 'Superadmin'}</h1>
        <p className="text-slate-500">Platform-wide overview for organizations, users, subscriptions, and vouchers.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-slate-500 text-sm font-medium mb-1">Total Organizations</div>
          <div className="text-3xl font-bold text-slate-900">{stats?.total_organizations ?? 0}</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-slate-500 text-sm font-medium mb-1">Total Users</div>
          <div className="text-3xl font-bold text-slate-900">{stats?.total_users ?? 0}</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-slate-500 text-sm font-medium mb-1">Active Subscriptions</div>
          <div className="text-3xl font-bold text-green-600">{stats?.active_subscriptions ?? 0}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <section className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-900">Organizations</h2>
            <span className="text-sm text-slate-500">{organizations.length} shown</span>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-slate-500 uppercase text-xs">
                <tr>
                  <th className="px-4 py-3 text-left">ID</th>
                  <th className="px-4 py-3 text-left">Name</th>
                  <th className="px-4 py-3 text-left">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {organizations.map((org) => (
                  <tr key={org.id}>
                    <td className="px-4 py-3 font-medium text-slate-900">{org.id}</td>
                    <td className="px-4 py-3 text-slate-700">{org.name}</td>
                    <td className="px-4 py-3 text-slate-600">{org.payment_status || 'Unknown'}</td>
                  </tr>
                ))}
                {organizations.length === 0 && (
                  <tr><td colSpan="3" className="px-4 py-8 text-center text-slate-500">No organizations found.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-900">Vouchers</h2>
            <span className="text-sm text-slate-500">{coupons.length} shown</span>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-slate-500 uppercase text-xs">
                <tr>
                  <th className="px-4 py-3 text-left">Code</th>
                  <th className="px-4 py-3 text-left">Value</th>
                  <th className="px-4 py-3 text-left">Active</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {coupons.map((coupon) => (
                  <tr key={coupon.id}>
                    <td className="px-4 py-3 font-medium text-slate-900">{coupon.code}</td>
                    <td className="px-4 py-3 text-slate-700">{coupon.value}</td>
                    <td className="px-4 py-3 text-slate-600">{coupon.is_active ? 'Yes' : 'No'}</td>
                  </tr>
                ))}
                {coupons.length === 0 && (
                  <tr><td colSpan="3" className="px-4 py-8 text-center text-slate-500">No vouchers found.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
};


const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();

  // Extract 'next' parameter from URL. Default to dashboard after successful login.
  const queryParams = new URLSearchParams(location.search);
  const nextUrl = queryParams.get('next') || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest', // Indicate AJAX request
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
        // Store the access token in localStorage
        localStorage.setItem('token', data.access_token);
        // Global State Update
        login(data.user);
        navigate(data.redirect || nextUrl);
      } else {
        setError(data.detail || data.message || 'Login failed');
      }
    } catch (err) {
      setError('Network error or server unreachable.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-100">
      <div className="p-8 bg-white shadow-lg rounded-lg w-96">
        <h2 className="text-2xl font-bold mb-4 text-center">Sign In to Gaatha</h2>
        {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">Username</label>
            <input
              type="text"
              id="username"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">Password</label>
            <input
              type="password"
              id="password"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Login
          </button>
        </form>
        <div className="mt-6 text-center">
          <Link to="/auth/register" className="font-medium text-blue-600 hover:text-blue-500">
            Don't have an account? Sign Up
          </Link>
        </div>
      </div>
    </div>
  );
};

// Accounting (Books) Page
const AddAccountModal = ({ isOpen, onClose, onAdded }) => {
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [type, setType] = useState('Asset');
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!code.trim()) {
      setError('Account code is required');
      return;
    }
    if (!name.trim()) {
      setError('Account name is required');
      return;
    }

    setIsSaving(true);
    try {
      if (onAdded) {
        onAdded({ code, name, type, balance: 0 });
      }
      setCode('');
      setName('');
      setType('Asset');
      onClose();
    } catch (err) {
      console.error('Failed to create account', err);
      setError('Unable to create account. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-200">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <h3 className="text-xl font-bold text-slate-800">Create New Account</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Account Code</label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              placeholder="e.g., 1500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Account Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              placeholder="e.g., Prepaid Expenses"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Account Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
            >
              <option>Asset</option>
              <option>Liability</option>
              <option>Equity</option>
              <option>Revenue</option>
              <option>Expense</option>
            </select>
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
          <div className="flex gap-3 mt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:bg-blue-300"
            >
              {isSaving ? 'Creating...' : 'Create Account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const JournalEntryModal = ({ isOpen, onClose, onAdded }) => {
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [accountCode, setAccountCode] = useState('');
  const [description, setDescription] = useState('');
  const [debit, setDebit] = useState('');
  const [credit, setCredit] = useState('');
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!accountCode.trim()) {
      setError('Account code is required');
      return;
    }
    if (!description.trim()) {
      setError('Description is required');
      return;
    }

    const debitVal = parseFloat(debit) || 0;
    const creditVal = parseFloat(credit) || 0;

    if (debitVal === 0 && creditVal === 0) {
      setError('Either debit or credit amount must be entered');
      return;
    }

    if (debitVal > 0 && creditVal > 0) {
      setError('Cannot have both debit and credit amounts');
      return;
    }

    setIsSaving(true);
    try {
      if (onAdded) {
        onAdded({
          date,
          account: accountCode,
          description,
          debit: debitVal,
          credit: creditVal
        });
      }
      setDate(new Date().toISOString().split('T')[0]);
      setAccountCode('');
      setDescription('');
      setDebit('');
      setCredit('');
      onClose();
    } catch (err) {
      console.error('Failed to create entry', err);
      setError('Unable to create entry. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-200">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <h3 className="text-xl font-bold text-slate-800">Journal Entry</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Date</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Account Code</label>
            <input
              type="text"
              value={accountCode}
              onChange={(e) => setAccountCode(e.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              placeholder="e.g., 1000"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Description</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              placeholder="e.g., Client payment received"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">Debit</label>
              <input
                type="number"
                value={debit}
                onChange={(e) => { setDebit(e.target.value); setCredit(''); }}
                className="mt-2 w-full rounded-lg border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
                placeholder="0.00"
                step="0.01"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Credit</label>
              <input
                type="number"
                value={credit}
                onChange={(e) => { setCredit(e.target.value); setDebit(''); }}
                className="mt-2 w-full rounded-lg border border-slate-200 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
                placeholder="0.00"
                step="0.01"
              />
            </div>
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
          <div className="flex gap-3 mt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:bg-blue-300"
            >
              {isSaving ? 'Recording...' : 'Record Entry'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Add Bill Modal (Accounts Payable)
const AddBillModal = ({ isOpen, onClose, onAdded }) => {
  const [billNumber, setBillNumber] = useState('');
  const [vendor, setVendor] = useState('');
  const [amount, setAmount] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setBillNumber('');
      setVendor('');
      setAmount('');
      setDueDate('');
      setDescription('');
      setError('');
    }
  }, [isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!billNumber || !vendor || !amount || !dueDate) {
      setError('Bill number, vendor, amount, and due date are required');
      return;
    }
    setIsSaving(true);
    try {
      onAdded({
        vendor,
        amount: parseFloat(amount),
        dueDate,
        description,
        status: 'Pending'
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to add bill');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h3 className="text-xl font-bold mb-4">Add New Bill</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Vendor *</label>
            <input type="text" value={vendor} onChange={(e) => setVendor(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Vendor name" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Amount *</label>
            <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="0.00" step="0.01" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Due Date *</label>
            <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Bill description" rows="3"></textarea>
          </div>
          {error && <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">{error}</div>}
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={onClose} className="px-4 py-2 text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50">Cancel</button>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
              {isSaving ? 'Adding...' : 'Add Bill'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Add Invoice Modal (Accounts Receivable)
const AddInvoiceModal = ({ isOpen, onClose, onAdded }) => {
  const [customer, setCustomer] = useState('');
  const [amount, setAmount] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setCustomer('');
      setAmount('');
      setDueDate('');
      setDescription('');
      setError('');
    }
  }, [isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!customer || !amount || !dueDate) {
      setError('Customer, amount, and due date are required');
      return;
    }
    setIsSaving(true);
    try {
      onAdded({
        customer,
        amount: parseFloat(amount),
        dueDate,
        description,
        status: 'Pending'
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to add invoice');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h3 className="text-xl font-bold mb-4">Add New Invoice</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Customer *</label>
            <input type="text" value={customer} onChange={(e) => setCustomer(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Customer name" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Amount *</label>
            <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="0.00" step="0.01" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Due Date *</label>
            <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Invoice description" rows="3"></textarea>
          </div>
          {error && <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">{error}</div>}
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={onClose} className="px-4 py-2 text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50">Cancel</button>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
              {isSaving ? 'Adding...' : 'Add Invoice'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Add Asset Modal (Fixed Asset Management)
const AddAssetModal = ({ isOpen, onClose, onAdded }) => {
  const [assetName, setAssetName] = useState('');
  const [category, setCategory] = useState('');
  const [purchasePrice, setPurchasePrice] = useState('');
  const [purchaseDate, setPurchaseDate] = useState('');
  const [depreciationRate, setDepreciationRate] = useState('');
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setAssetName('');
      setCategory('');
      setPurchasePrice('');
      setPurchaseDate('');
      setDepreciationRate('');
      setError('');
    }
  }, [isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!assetName || !category || !purchasePrice || !purchaseDate || !depreciationRate) {
      setError('All fields are required');
      return;
    }
    setIsSaving(true);
    try {
      onAdded({
        name: assetName,
        category,
        purchasePrice: parseFloat(purchasePrice),
        currentValue: parseFloat(purchasePrice),
        purchaseDate,
        depreciationRate: parseFloat(depreciationRate),
        status: 'Active'
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to add asset');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h3 className="text-xl font-bold mb-4">Add New Asset</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Asset Name *</label>
            <input type="text" value={assetName} onChange={(e) => setAssetName(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Asset name" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Category *</label>
            <select value={category} onChange={(e) => setCategory(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">Select category</option>
              <option value="Real Estate">Real Estate</option>
              <option value="Machinery">Machinery</option>
              <option value="Vehicles">Vehicles</option>
              <option value="Technology">Technology</option>
              <option value="Furniture">Furniture</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Purchase Price *</label>
            <input type="number" value={purchasePrice} onChange={(e) => setPurchasePrice(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="0.00" step="0.01" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Purchase Date *</label>
            <input type="date" value={purchaseDate} onChange={(e) => setPurchaseDate(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Annual Depreciation Rate (%) *</label>
            <input type="number" value={depreciationRate} onChange={(e) => setDepreciationRate(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="0.00" step="0.01" />
          </div>
          {error && <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">{error}</div>}
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={onClose} className="px-4 py-2 text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50">Cancel</button>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
              {isSaving ? 'Adding...' : 'Add Asset'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Advanced Reporting Modal
const ReportConfigModal = ({ isOpen, onClose, onAdded }) => {
  const [reportName, setReportName] = useState('');
  const [reportType, setReportType] = useState('');
  const [dimensions, setDimensions] = useState([]);
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setReportName('');
      setReportType('');
      setDimensions([]);
      setError('');
    }
  }, [isOpen]);

  const toggleDimension = (dimension) => {
    setDimensions(prev => 
      prev.includes(dimension) 
        ? prev.filter(d => d !== dimension)
        : [...prev, dimension]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reportName || !reportType) {
      setError('Report name and type are required');
      return;
    }
    setIsSaving(true);
    try {
      onAdded({
        reportName,
        reportType,
        dimensions,
        createdDate: new Date().toISOString().split('T')[0],
        status: 'Active'
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create report');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md max-h-96 overflow-y-auto">
        <h3 className="text-xl font-bold mb-4">Create Advanced Report</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Report Name *</label>
            <input type="text" value={reportName} onChange={(e) => setReportName(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g., Q2 Product Profitability" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Report Type *</label>
            <select value={reportType} onChange={(e) => setReportType(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">Select type</option>
              <option value="Profitability">Profitability Analysis</option>
              <option value="Regional">Regional Performance</option>
              <option value="Product">Product Analysis</option>
              <option value="Project">Project Analysis</option>
              <option value="Custom">Custom Report</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Analysis Dimensions</label>
            <div className="space-y-2">
              {['Product', 'Region', 'Project', 'Department', 'Customer'].map(dim => (
                <label key={dim} className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={dimensions.includes(dim)} onChange={() => toggleDimension(dim)} className="w-4 h-4 border border-slate-300 rounded" />
                  <span className="text-sm text-slate-700">{dim}</span>
                </label>
              ))}
            </div>
          </div>
          {error && <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">{error}</div>}
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={onClose} className="px-4 py-2 text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50">Cancel</button>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
              {isSaving ? 'Creating...' : 'Create Report'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Compliance & Audit Modal
const ComplianceAuditModal = ({ isOpen, onClose, onAdded }) => {
  const [complianceStandard, setComplianceStandard] = useState('GAAP');
  const [auditFrequency, setAuditFrequency] = useState('Monthly');
  const [enableAutoValidation, setEnableAutoValidation] = useState(true);
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setComplianceStandard('GAAP');
      setAuditFrequency('Monthly');
      setEnableAutoValidation(true);
      setError('');
    }
  }, [isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      onAdded({
        complianceStandard,
        auditFrequency,
        enableAutoValidation,
        appliedDate: new Date().toISOString().split('T')[0],
        status: 'Active'
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to configure compliance');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h3 className="text-xl font-bold mb-4">Configure Compliance & Audit</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Accounting Standard *</label>
            <select value={complianceStandard} onChange={(e) => setComplianceStandard(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="GAAP">GAAP (US Generally Accepted)</option>
              <option value="IFRS">IFRS (International Standards)</option>
              <option value="Both">Both GAAP & IFRS</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Audit Frequency *</label>
            <select value={auditFrequency} onChange={(e) => setAuditFrequency(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="Weekly">Weekly</option>
              <option value="Monthly">Monthly</option>
              <option value="Quarterly">Quarterly</option>
              <option value="Annually">Annually</option>
            </select>
          </div>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" checked={enableAutoValidation} onChange={(e) => setEnableAutoValidation(e.target.checked)} className="w-4 h-4 border border-slate-300 rounded" />
            <span className="text-sm text-slate-700">Enable Automatic Validation & Error Detection</span>
          </label>
          {error && <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">{error}</div>}
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={onClose} className="px-4 py-2 text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50">Cancel</button>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
              {isSaving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Multi-Entity & Multi-Currency Modal
const MultiEntityModal = ({ isOpen, onClose, onAdded }) => {
  const [entityName, setEntityName] = useState('');
  const [entityType, setEntityType] = useState('Subsidiary');
  const [baseCurrency, setBaseCurrency] = useState('USD');
  const [supportedCurrencies, setSupportedCurrencies] = useState(['USD']);
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setEntityName('');
      setEntityType('Subsidiary');
      setBaseCurrency('USD');
      setSupportedCurrencies(['USD']);
      setError('');
    }
  }, [isOpen]);

  const toggleCurrency = (currency) => {
    setSupportedCurrencies(prev =>
      prev.includes(currency)
        ? prev.filter(c => c !== currency)
        : [...prev, currency]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!entityName) {
      setError('Entity name is required');
      return;
    }
    setIsSaving(true);
    try {
      onAdded({
        entityName,
        entityType,
        baseCurrency,
        supportedCurrencies,
        createdDate: new Date().toISOString().split('T')[0],
        status: 'Active'
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to add entity');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md my-8">
        <h3 className="text-xl font-bold mb-4">Add Multi-Entity & Currency</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Entity Name *</label>
            <input type="text" value={entityName} onChange={(e) => setEntityName(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g., EMEA Region HQ" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Entity Type *</label>
            <select value={entityType} onChange={(e) => setEntityType(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="Headquarters">Headquarters</option>
              <option value="Subsidiary">Subsidiary</option>
              <option value="Branch">Branch</option>
              <option value="Division">Division</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Base Currency *</label>
            <select value={baseCurrency} onChange={(e) => setBaseCurrency(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="USD">USD (US Dollar)</option>
              <option value="EUR">EUR (Euro)</option>
              <option value="GBP">GBP (British Pound)</option>
              <option value="JPY">JPY (Japanese Yen)</option>
              <option value="AUD">AUD (Australian Dollar)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Supported Currencies</label>
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY'].map(curr => (
                <label key={curr} className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={supportedCurrencies.includes(curr)} onChange={() => toggleCurrency(curr)} className="w-4 h-4 border border-slate-300 rounded" />
                  <span className="text-sm text-slate-700">{curr}</span>
                </label>
              ))}
            </div>
          </div>
          {error && <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">{error}</div>}
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={onClose} className="px-4 py-2 text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50">Cancel</button>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
              {isSaving ? 'Adding...' : 'Add Entity'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const AccountingPage = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [isAddAccountOpen, setIsAddAccountOpen] = useState(false);
  const [isAddEntryOpen, setIsAddEntryOpen] = useState(false);
  const [isAddBillOpen, setIsAddBillOpen] = useState(false);
  const [isAddInvoiceOpen, setIsAddInvoiceOpen] = useState(false);
  const [isAddAssetOpen, setIsAddAssetOpen] = useState(false);
  
  const [chartOfAccounts, setChartOfAccounts] = useState([]);

  const [glEntries, setGlEntries] = useState([]);

  const [payableBills, setPayableBills] = useState([]);

  const [receivableInvoices, setReceivableInvoices] = useState([]);

  const [fixedAssets, setFixedAssets] = useState([]);

  const [automatedWorkflows] = useState([]);

  const financialSummary = {
    totalAssets: 0,
    totalLiabilities: 0,
    totalEquity: 0,
    revenue: 0,
    expenses: 0,
    netIncome: 0,
    currentRatio: 0
  };

  const handleAddAccount = (newAccount) => {
    setChartOfAccounts([...chartOfAccounts, { ...newAccount, balance: 0 }]);
  };

  const handleAddEntry = (newEntry) => {
    setGlEntries([newEntry, ...glEntries]);
  };

  const handleAddBill = (newBill) => {
    setPayableBills([{ ...newBill, id: `PO-${Date.now()}` }, ...payableBills]);
  };

  const handleAddInvoice = (newInvoice) => {
    setReceivableInvoices([{ ...newInvoice, id: `INV-${Date.now()}` }, ...receivableInvoices]);
  };

  const handleAddAsset = (newAsset) => {
    setFixedAssets([{ ...newAsset, id: `FA-${Date.now()}` }, ...fixedAssets]);
  };


  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2 mb-2">
          <BookOpen className="text-blue-600" /> General Accounting
        </h2>
        <p className="text-slate-500 text-sm">Manage chart of accounts, general ledger, and financial statements.</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-slate-200 overflow-x-auto">
        <button 
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 font-medium transition whitespace-nowrap ${activeTab === 'overview' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-800'}`}
        >
          Financial Overview
        </button>
        <button 
          onClick={() => setActiveTab('coa')}
          className={`px-4 py-2 font-medium transition whitespace-nowrap ${activeTab === 'coa' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-800'}`}
        >
          Chart of Accounts
        </button>
        <button 
          onClick={() => setActiveTab('ledger')}
          className={`px-4 py-2 font-medium transition whitespace-nowrap ${activeTab === 'ledger' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-800'}`}
        >
          General Ledger
        </button>
        <button 
          onClick={() => setActiveTab('ap')}
          className={`px-4 py-2 font-medium transition whitespace-nowrap ${activeTab === 'ap' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-800'}`}
        >
          Accounts Payable
        </button>
        <button 
          onClick={() => setActiveTab('ar')}
          className={`px-4 py-2 font-medium transition whitespace-nowrap ${activeTab === 'ar' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-800'}`}
        >
          Accounts Receivable
        </button>
        <button 
          onClick={() => setActiveTab('assets')}
          className={`px-4 py-2 font-medium transition whitespace-nowrap ${activeTab === 'assets' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-800'}`}
        >
          Fixed Assets
        </button>
        <button 
          onClick={() => setActiveTab('workflows')}
          className={`px-4 py-2 font-medium transition whitespace-nowrap ${activeTab === 'workflows' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-800'}`}
        >
          Automated Workflows
        </button>
      </div>

      {/* Financial Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-sm font-medium mb-2">Total Assets</div>
              <div className="text-3xl font-bold text-slate-900">${financialSummary.totalAssets.toLocaleString()}</div>
              <div className="mt-2 text-xs text-green-600">↑ 8.5% from last month</div>
            </div>
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-sm font-medium mb-2">Total Liabilities</div>
              <div className="text-3xl font-bold text-slate-900">${financialSummary.totalLiabilities.toLocaleString()}</div>
              <div className="mt-2 text-xs text-green-600">↓ 5% from last month</div>
            </div>
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-sm font-medium mb-2">Net Income</div>
              <div className="text-3xl font-bold text-green-600">${financialSummary.netIncome.toLocaleString()}</div>
              <div className="mt-2 text-xs text-green-600">↑ 12% from last month</div>
            </div>
          </div>

          {/* Income Statement */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-bold mb-4">Income Statement</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center py-2 border-b border-slate-100">
                <span className="font-semibold text-slate-900">Revenue</span>
                <span className="font-semibold text-green-600">${financialSummary.revenue.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center py-2 pl-4 border-b border-slate-100">
                <span className="text-slate-600">COGS</span>
                <span className="text-red-600">-$250,000</span>
              </div>
              <div className="flex justify-between items-center py-2 pl-4 border-b border-slate-100">
                <span className="text-slate-600">Operating Expenses</span>
                <span className="text-red-600">-$100,000</span>
              </div>
              <div className="flex justify-between items-center py-3 font-bold text-lg bg-blue-50 px-4 rounded">
                <span>Net Income</span>
                <span className="text-green-600">${financialSummary.netIncome.toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Financial Ratios */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-bold mb-4">Financial Ratios</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{financialSummary.currentRatio}</div>
                <div className="text-xs text-slate-600 mt-1">Current Ratio</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">3.5x</div>
                <div className="text-xs text-slate-600 mt-1">Debt to Equity</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">30%</div>
                <div className="text-xs text-slate-600 mt-1">Profit Margin</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">1.79x</div>
                <div className="text-xs text-slate-600 mt-1">ROA</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chart of Accounts Tab */}
      {activeTab === 'coa' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold">Chart of Accounts</h3>
            <button 
              onClick={() => setIsAddAccountOpen(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition"
            >
              + New Account
            </button>
          </div>
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="p-4 text-sm font-semibold text-slate-600">Code</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Account Name</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Type</th>
                  <th className="p-4 text-sm font-semibold text-slate-600 text-right">Balance</th>
                </tr>
              </thead>
              <tbody>
                {chartOfAccounts.map(account => (
                  <tr key={account.code} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                    <td className="p-4 font-mono font-medium text-slate-900">{account.code}</td>
                    <td className="p-4 text-slate-900">{account.name}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        account.type === 'Asset' ? 'bg-blue-100 text-blue-700' :
                        account.type === 'Liability' ? 'bg-red-100 text-red-700' :
                        account.type === 'Equity' ? 'bg-purple-100 text-purple-700' :
                        account.type === 'Revenue' ? 'bg-green-100 text-green-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {account.type}
                      </span>
                    </td>
                    <td className={`p-4 text-right font-semibold ${account.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${Math.abs(account.balance).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* General Ledger Tab */}
      {activeTab === 'ledger' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold">General Ledger</h3>
            <button 
              onClick={() => setIsAddEntryOpen(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition"
            >
              + New Entry
            </button>
          </div>
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="p-4 text-sm font-semibold text-slate-600">Date</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Account Code</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Description</th>
                  <th className="p-4 text-sm font-semibold text-slate-600 text-right">Debit</th>
                  <th className="p-4 text-sm font-semibold text-slate-600 text-right">Credit</th>
                </tr>
              </thead>
              <tbody>
                {glEntries.map((entry, idx) => (
                  <tr key={idx} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                    <td className="p-4 text-slate-900 text-sm">{entry.date}</td>
                    <td className="p-4 font-mono font-medium text-slate-900">{entry.account}</td>
                    <td className="p-4 text-slate-600 text-sm">{entry.description}</td>
                    <td className="p-4 text-right font-semibold text-green-600">{entry.debit > 0 ? `$${entry.debit.toLocaleString()}` : '—'}</td>
                    <td className="p-4 text-right font-semibold text-red-600">{entry.credit > 0 ? `$${entry.credit.toLocaleString()}` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Accounts Payable Tab */}
      {activeTab === 'ap' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-lg font-bold">Accounts Payable</h3>
              <p className="text-slate-600 text-sm">Manage vendor bills, track payment schedules, and automate disbursements.</p>
            </div>
            <button 
              onClick={() => setIsAddBillOpen(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition"
            >
              + New Bill
            </button>
          </div>

          {/* AP Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Total Payable</div>
              <div className="text-2xl font-bold text-red-600">$25,500</div>
              <div className="text-xs text-slate-500 mt-1">3 vendors</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Pending</div>
              <div className="text-2xl font-bold text-orange-600">$17,000</div>
              <div className="text-xs text-slate-500 mt-1">2 bills</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Approved</div>
              <div className="text-2xl font-bold text-blue-600">$12,000</div>
              <div className="text-xs text-slate-500 mt-1">1 bill</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Paid This Month</div>
              <div className="text-2xl font-bold text-green-600">$8,500</div>
              <div className="text-xs text-slate-500 mt-1">Settled</div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="p-4 text-sm font-semibold text-slate-600">PO #</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Vendor</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Description</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Amount</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Due Date</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
                </tr>
              </thead>
              <tbody>
                {payableBills.map(bill => (
                  <tr key={bill.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                    <td className="p-4 font-mono font-medium text-slate-900">{bill.id}</td>
                    <td className="p-4 text-slate-900">{bill.vendor}</td>
                    <td className="p-4 text-slate-600 text-sm">{bill.description}</td>
                    <td className="p-4 font-semibold text-slate-900">${bill.amount.toLocaleString()}</td>
                    <td className="p-4 text-slate-600 text-sm">{bill.dueDate}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        bill.status === 'Pending' ? 'bg-orange-100 text-orange-700' :
                        bill.status === 'Approved' ? 'bg-blue-100 text-blue-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {bill.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Accounts Receivable Tab */}
      {activeTab === 'ar' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-lg font-bold">Accounts Receivable</h3>
              <p className="text-slate-600 text-sm">Manage customer invoicing, payment receipts, and track outstanding balances.</p>
            </div>
            <button 
              onClick={() => setIsAddInvoiceOpen(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition"
            >
              + New Invoice
            </button>
          </div>

          {/* AR Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Total Receivable</div>
              <div className="text-2xl font-bold text-green-600">$32,500</div>
              <div className="text-xs text-slate-500 mt-1">3 customers</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Pending</div>
              <div className="text-2xl font-bold text-orange-600">$22,500</div>
              <div className="text-xs text-slate-500 mt-1">2 invoices</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Overdue</div>
              <div className="text-2xl font-bold text-red-600">$15,000</div>
              <div className="text-xs text-slate-500 mt-1">1 invoice</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Paid This Month</div>
              <div className="text-2xl font-bold text-green-600">$10,000</div>
              <div className="text-xs text-slate-500 mt-1">Collected</div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="p-4 text-sm font-semibold text-slate-600">Invoice #</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Customer</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Description</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Amount</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Due Date</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
                </tr>
              </thead>
              <tbody>
                {receivableInvoices.map(invoice => (
                  <tr key={invoice.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                    <td className="p-4 font-mono font-medium text-slate-900">{invoice.id}</td>
                    <td className="p-4 text-slate-900">{invoice.customer}</td>
                    <td className="p-4 text-slate-600 text-sm">{invoice.description}</td>
                    <td className="p-4 font-semibold text-slate-900">${invoice.amount.toLocaleString()}</td>
                    <td className="p-4 text-slate-600 text-sm">{invoice.dueDate}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        invoice.status === 'Pending' ? 'bg-orange-100 text-orange-700' :
                        invoice.status === 'Overdue' ? 'bg-red-100 text-red-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {invoice.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Fixed Asset Management Tab */}
      {activeTab === 'assets' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-lg font-bold">Fixed Asset Management</h3>
              <p className="text-slate-600 text-sm">Track lifecycle, depreciation, and valuation of company assets.</p>
            </div>
            <button 
              onClick={() => setIsAddAssetOpen(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition"
            >
              + New Asset
            </button>
          </div>

          {/* Asset Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Total Assets Value</div>
              <div className="text-2xl font-bold text-slate-900">${fixedAssets.reduce((sum, a) => sum + a.purchasePrice, 0).toLocaleString()}</div>
              <div className="text-xs text-slate-500 mt-1">{fixedAssets.length} assets</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Current Book Value</div>
              <div className="text-2xl font-bold text-blue-600">${fixedAssets.reduce((sum, a) => sum + a.currentValue, 0).toLocaleString()}</div>
              <div className="text-xs text-slate-500 mt-1">After depreciation</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Total Depreciation</div>
              <div className="text-2xl font-bold text-orange-600">${(fixedAssets.reduce((sum, a) => sum + a.purchasePrice, 0) - fixedAssets.reduce((sum, a) => sum + a.currentValue, 0)).toLocaleString()}</div>
              <div className="text-xs text-slate-500 mt-1">Accumulated</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Active Assets</div>
              <div className="text-2xl font-bold text-green-600">{fixedAssets.filter(a => a.status === 'Active').length}</div>
              <div className="text-xs text-slate-500 mt-1">In use</div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="p-4 text-sm font-semibold text-slate-600">Asset ID</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Name</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Category</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Purchase Price</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Current Value</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Depreciation %</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
                </tr>
              </thead>
              <tbody>
                {fixedAssets.map(asset => {
                  const totalDepreciation = asset.purchasePrice - asset.currentValue;
                  const depreciationPercent = ((totalDepreciation / asset.purchasePrice) * 100).toFixed(1);
                  return (
                    <tr key={asset.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                      <td className="p-4 font-mono font-medium text-slate-900">{asset.id}</td>
                      <td className="p-4 text-slate-900">{asset.name}</td>
                      <td className="p-4 text-slate-600 text-sm">{asset.category}</td>
                      <td className="p-4 font-semibold text-slate-900">${asset.purchasePrice.toLocaleString()}</td>
                      <td className="p-4 font-semibold text-blue-600">${asset.currentValue.toLocaleString()}</td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div className="bg-orange-500 h-2 rounded-full" style={{width: `${depreciationPercent}%`}}></div>
                          </div>
                          <span className="text-xs font-semibold text-slate-600">{depreciationPercent}%</span>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className="px-2 py-1 rounded text-xs font-bold bg-green-100 text-green-700">
                          {asset.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Automated Workflows Tab */}
      {activeTab === 'workflows' && (
        <div className="space-y-6">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-bold text-slate-900 mb-2">Real-Time Data Flow & Automation</h3>
            <p className="text-slate-600">Operational actions automatically flow to the general ledger without manual reentry.</p>
          </div>

          {/* Active Workflows */}
          <div>
            <h4 className="text-lg font-bold mb-4">Active Workflows</h4>
            <div className="grid gap-4">
              {automatedWorkflows.map((workflow) => (
                <div key={workflow.id} className={`bg-white rounded-lg border p-4 shadow-sm ${workflow.status === 'Active' ? 'border-green-200' : 'border-yellow-200'}`}>
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h5 className="font-bold text-slate-900">{workflow.name}</h5>
                      <p className="text-sm text-slate-600">{workflow.description}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      workflow.status === 'Active' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {workflow.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                      <span className="text-slate-600">Processed today: <span className="font-bold text-slate-900">{workflow.processedToday}</span></span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Data Sync Status */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-sm font-medium text-slate-600 mb-2">Ledger Entries Today</div>
              <div className="text-3xl font-bold text-slate-900">247</div>
              <div className="text-xs text-green-600 mt-2">↑ 18% from yesterday</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-sm font-medium text-slate-600 mb-2">Pending Approvals</div>
              <div className="text-3xl font-bold text-orange-600">8</div>
              <div className="text-xs text-slate-600 mt-2">Awaiting review</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-sm font-medium text-slate-600 mb-2">Last Sync</div>
              <div className="text-lg font-bold text-slate-900">2 min ago</div>
              <div className="text-xs text-green-600 mt-2">All systems synchronized</div>
            </div>
          </div>

          {/* Centralized Database Info */}
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6">
            <h4 className="font-bold text-slate-900 mb-3">Centralized Database</h4>
            <ul className="space-y-2 text-slate-700 text-sm">
              <li className="flex items-start gap-2">
                <span className="text-indigo-600 font-bold">✓</span>
                <span>Single source of truth for all financial data</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-600 font-bold">✓</span>
                <span>Real-time synchronization across all departments</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-600 font-bold">✓</span>
                <span>Eliminates data silos and discrepancies</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-600 font-bold">✓</span>
                <span>Operational actions (shipping, approvals) immediately reflected in GL</span>
              </li>
            </ul>
          </div>
        </div>
      )}

      {/* Modals */}
      <AddAccountModal 
        isOpen={isAddAccountOpen} 
        onClose={() => setIsAddAccountOpen(false)}
        onAdded={handleAddAccount}
      />
      <JournalEntryModal 
        isOpen={isAddEntryOpen} 
        onClose={() => setIsAddEntryOpen(false)}
        onAdded={handleAddEntry}
      />
      <AddBillModal 
        isOpen={isAddBillOpen} 
        onClose={() => setIsAddBillOpen(false)}
        onAdded={handleAddBill}
      />
      <AddInvoiceModal 
        isOpen={isAddInvoiceOpen} 
        onClose={() => setIsAddInvoiceOpen(false)}
        onAdded={handleAddInvoice}
      />
      <AddAssetModal 
        isOpen={isAddAssetOpen} 
        onClose={() => setIsAddAssetOpen(false)}
        onAdded={handleAddAsset}
      />
    </div>
  );
};

// Invoices Page
const InvoicesPage = () => {
  const { authFetch } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [isCreateInvoiceOpen, setIsCreateInvoiceOpen] = useState(false);
  const [orgSettings, setOrgSettings] = useState({
    name: 'Your Company',
    logo_url: '',
    email: '',
    phone: '',
    address: '',
    currency: 'USD',
    invoice_notes: '',
    invoice_terms: '',
    invoice_template: 'classic'
  });
  const [scannedVendorInvoices, setScannedVendorInvoices] = useState([]);
  const [isVendorInvoicesLoading, setIsVendorInvoicesLoading] = useState(false);

  const approvedSalesOrders = [];

  const approvedDeliveryNotes = [];

  useEffect(() => {
    authFetch('/api/v2/settings')
      .then(res => res?.ok ? res.json() : null)
      .then(data => {
        if (data) {
          setOrgSettings({
            name: data.name || 'Your Company',
            logo_url: data.logo_url || '',
            email: data.email || '',
            phone: data.phone || '',
            address: data.address || '',
            currency: data.currency || 'USD',
            invoice_notes: data.invoice_notes || '',
            invoice_terms: data.invoice_terms || '',
            invoice_template: data.invoice_template || 'classic'
          });
        }
      })
      .catch(() => {});
  }, [authFetch]);

  useEffect(() => {
    setIsVendorInvoicesLoading(true);
    authFetch('/api/v2/vendor-invoices')
      .then(res => res?.ok ? res.json() : [])
      .then(data => setScannedVendorInvoices(Array.isArray(data) ? data : []))
      .catch(() => setScannedVendorInvoices([]))
      .finally(() => setIsVendorInvoicesLoading(false));
  }, [authFetch]);

  const totalInvoices = invoices.length;
  const totalAmount = invoices.reduce((sum, invoice) => sum + invoice.amount, 0);
  const openInvoices = invoices.filter(inv => inv.status !== 'Paid');
  const openAmount = openInvoices.reduce((sum, invoice) => sum + invoice.amount, 0);
  const formatCurrency = (amount, currency = orgSettings.currency || 'USD') => {
    const value = Number(amount || 0);
    return `${currency} ${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const handleConfirmVendorInvoice = async (invoiceId) => {
    const response = await authFetch(`/api/v2/vendor-invoices/${invoiceId}/approve`, {
      method: 'POST'
    });

    if (!response || !response.ok) {
      return;
    }

    const updatedInvoice = await response.json();
    setScannedVendorInvoices(prev => prev.map(inv => inv.id === invoiceId ? updatedInvoice : inv));
  };

  const handleCreateInvoice = (invoice) => {
    const nextId = Date.now();
    const nextNumber = `INV-${String(invoices.length + 1).padStart(3, '0')}`;
    setInvoices((prevInvoices) => [
      {
        id: nextId,
        number: nextNumber,
        createdDate: new Date().toISOString().slice(0, 10),
        ...invoice
      },
      ...prevInvoices
    ]);
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2"><Mail className="text-blue-600" /> Invoices</h2>
          <p className="text-slate-500 text-sm">Create, track, and manage customer invoices.</p>
        </div>
        <button onClick={() => setIsCreateInvoiceOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition">+ Create Invoice</button>
      </div>

      {/* Invoice Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Total Invoices</div>
          <div className="text-2xl font-bold text-slate-900">{totalInvoices}</div>
          <div className="text-xs text-slate-500 mt-1">Recorded invoices</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Total Amount</div>
          <div className="text-2xl font-bold text-slate-900">{formatCurrency(totalAmount)}</div>
          <div className="text-xs text-slate-500 mt-1">Invoice portfolio</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Open Invoices</div>
          <div className="text-2xl font-bold text-blue-600">{openInvoices.length}</div>
          <div className="text-xs text-slate-500 mt-1">Awaiting payment</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Open Amount</div>
          <div className="text-2xl font-bold text-red-600">{formatCurrency(openAmount)}</div>
          <div className="text-xs text-slate-500 mt-1">To collect</div>
        </div>
      </div>

      {/* Invoice processing workflow */}
      <div className="grid gap-4 mb-8 md:grid-cols-3">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Receipt & Extraction</h3>
              <p className="text-sm text-slate-500">Upload vendor PDFs and scanned receipts for OCR extraction.</p>
            </div>
            <span className="text-xs uppercase font-semibold text-slate-500">AI-assisted</span>
          </div>
          <div className="space-y-3">
            {scannedVendorInvoices.map(invoice => (
              <div key={invoice.id} className="rounded-xl border border-slate-200 p-3 bg-slate-50">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-slate-900">{invoice.vendor}</div>
                    <div className="text-xs text-slate-500">{invoice.date} • {invoice.id}</div>
                  </div>
                  <div className="text-sm font-semibold text-slate-700">{formatCurrency(invoice.amount)}</div>
                </div>
                <div className="mt-2 text-xs text-slate-600">
                  PO: {invoice.extractedFields.po_number} • Invoice: {invoice.extractedFields.invoice_number}
                </div>
                <div className="mt-2 flex items-center justify-between gap-2">
                  <div className="text-xs font-medium uppercase text-slate-500">{invoice.status}</div>
                  <button type="button" onClick={() => handleConfirmVendorInvoice(invoice.id)} className="rounded-md bg-blue-600 text-white px-3 py-1 text-xs hover:bg-blue-700 transition">
                    Approve
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Purchase Order Matching</h3>
              <p className="text-sm text-slate-500">Automatically compare invoice amounts to original purchase orders.</p>
            </div>
            <span className="text-xs uppercase font-semibold text-slate-500">3-way</span>
          </div>
          <div className="text-sm text-slate-600 space-y-2">
            <p>When scanned invoice totals match purchase order lines and delivery receipts, the system flags the invoice as ready for approval.</p>
            <div className="rounded-xl border border-slate-200 p-3 bg-slate-50">
              <div className="text-xs uppercase text-slate-500 mb-2">Matched Invoice</div>
              <div className="text-sm font-semibold text-slate-900">VI-002</div>
              <div className="text-xs text-slate-500">Matched to PO-300</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Approval Workflows</h3>
              <p className="text-sm text-slate-500">Route approved invoices for payment based on vendor terms.</p>
            </div>
            <span className="text-xs uppercase font-semibold text-slate-500">Automated</span>
          </div>
          <div className="text-sm text-slate-600 space-y-2">
            <p>Invoices that pass quantity and price checks are scheduled for payment and recorded automatically.</p>
            <div className="rounded-xl border border-slate-200 p-3 bg-slate-50">
              <div className="text-xs uppercase text-slate-500 mb-2">Next action</div>
              <div className="text-sm font-semibold text-slate-900">Approve payment for vendor invoice VI-001</div>
            </div>
          </div>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="p-4 text-sm font-semibold text-slate-600">Invoice #</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Customer</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Amount</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Source</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Created Date</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Due Date</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Actions</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map(inv => (
              <tr key={inv.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                <td className="p-4 font-medium text-blue-600 cursor-pointer hover:underline">{inv.number}</td>
                <td className="p-4 text-slate-600 text-sm">{inv.customer}</td>
                <td className="p-4 font-semibold text-slate-900">{formatCurrency(inv.amount)}</td>
                <td className="p-4 text-slate-600 text-sm">{inv.sourceType ? `${inv.sourceType} (${inv.sourceRef})` : 'Manual'}</td>
                <td className="p-4 text-slate-600 text-sm">{inv.createdDate}</td>
                <td className="p-4 text-slate-600 text-sm">{inv.dueDate}</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase ${
                    inv.status === 'Paid' ? 'bg-green-100 text-green-600' :
                    inv.status === 'Pending' ? 'bg-yellow-100 text-yellow-600' :
                    'bg-red-100 text-red-600'
                  }`}>
                    {inv.status}
                  </span>
                </td>
                <td className="p-4 text-sm">
                  <button className="text-blue-600 hover:text-blue-800 font-medium">View</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <CreateInvoiceModal
        isOpen={isCreateInvoiceOpen}
        onClose={() => setIsCreateInvoiceOpen(false)}
        onAdded={handleCreateInvoice}
        salesOrders={approvedSalesOrders}
        deliveryNotes={approvedDeliveryNotes}
        orgSettings={orgSettings}
      />
    </div>
  );
};

const CreateInvoiceModal = ({ isOpen, onClose, onAdded, salesOrders, deliveryNotes, orgSettings }) => {
  const { user } = useAuth();
  const [sourceId, setSourceId] = useState('');
  const [customer, setCustomer] = useState('');
  const [amount, setAmount] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('Pending');
  const [customFields, setCustomFields] = useState({});
  const [sourceType, setSourceType] = useState('Manual');
  const [sourceRef, setSourceRef] = useState('');
  const [template, setTemplate] = useState(orgSettings?.invoice_template || 'classic');
  const [error, setError] = useState('');

  const getVisibleCustomFields = () => {
    if (!orgSettings?.custom_fields) return {};
    return Object.entries(orgSettings.custom_fields).reduce((acc, [key, fieldData]) => {
      if (!fieldData.roles || fieldData.roles.length === 0 || fieldData.roles.includes(user?.role)) {
        acc[key] = fieldData.value || '';
      }
      return acc;
    }, {});
  };

  useEffect(() => {
    if (isOpen) {
      setSourceCategory('Manual');
      setSourceId('');
      setCustomer('');
      setAmount('');
      setDueDate('');
      setDescription('');
      setStatus('Pending');
      setCustomFields(getVisibleCustomFields());
      setSourceType('Manual');
      setSourceRef('');
      setTemplate(orgSettings?.invoice_template || 'classic');
      setError('');
    }
  }, [isOpen, orgSettings]);

  useEffect(() => {
    if (!sourceId) return;

    if (sourceCategory === 'Sales Order') {
      const order = salesOrders.find(order => order.id === sourceId);
      if (order) {
        setCustomer(order.customer);
        setAmount(order.amount.toString());
        setDueDate(order.dueDate);
        setDescription(order.description);
        setSourceType('Sales Order');
        setSourceRef(order.orderNumber);
      }
    }

    if (sourceCategory === 'Delivery Note') {
      const note = deliveryNotes.find(note => note.id === sourceId);
      if (note) {
        setCustomer(note.customer);
        setAmount(note.amount.toString());
        setDueDate(note.dueDate);
        setDescription(note.description);
        setSourceType('Delivery Note');
        setSourceRef(note.deliveryNumber);
      }
    }
  }, [sourceCategory, sourceId, salesOrders, deliveryNotes]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!customer || !amount || !dueDate) {
      setError('Customer, amount, and due date are required.');
      return;
    }

    onAdded({
      customer,
      amount: parseFloat(amount),
      dueDate,
      description,
      status,
      sourceType,
      sourceRef,
      custom_fields: customFields,
      invoice_template: template
    });
    onClose();
  };

  if (!isOpen) return null;

  const selectedOptions = sourceCategory === 'Sales Order' ? salesOrders : sourceCategory === 'Delivery Note' ? deliveryNotes : [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-lg">
        <h3 className="text-xl font-bold mb-4">Create Invoice</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Invoice Source</label>
            <select value={sourceCategory} onChange={(e) => { setSourceCategory(e.target.value); setSourceId(''); setSourceType(e.target.value); setSourceRef(''); }} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="Manual">Manual Entry</option>
              <option value="Sales Order">Approved Sales Order</option>
              <option value="Delivery Note">Approved Delivery Note</option>
            </select>
          </div>
          {sourceCategory !== 'Manual' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Select {sourceCategory}</label>
              <select value={sourceId} onChange={(e) => setSourceId(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Choose a source</option>
                {selectedOptions.map(source => (
                  <option key={source.id} value={source.id}>{`${source.orderNumber || source.deliveryNumber} • ${source.customer} • $${source.amount.toLocaleString()}`}</option>
                ))}
              </select>
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Customer *</label>
            <input type="text" value={customer} onChange={(e) => setCustomer(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Customer name" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Amount *</label>
              <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="0.00" step="0.01" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Due Date *</label>
              <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Invoice description" rows="3"></textarea>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Invoice Template</label>
            <select value={template} onChange={(e) => setTemplate(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="classic">Classic</option>
              <option value="modern">Modern</option>
              <option value="minimal">Minimal</option>
            </select>
            <p className="mt-2 text-xs text-slate-500">Default template loaded from organization settings.</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Custom Fields</label>
            <div className="space-y-2">
              {Object.entries(customFields).map(([key, value]) => (
                <div key={key} className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    value={key}
                    className="w-full px-2 py-1 border border-slate-300 rounded-md text-sm bg-slate-50"
                    readOnly
                  />
                  <input type="text" value={value} onChange={(e) => setCustomFields(prev => ({ ...prev, [key]: e.target.value }))} className="w-full px-2 py-1 border border-slate-300 rounded-md text-sm" />
                </div>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Invoice Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="Pending">Pending</option>
              <option value="Paid">Paid</option>
              <option value="Overdue">Overdue</option>
            </select>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-sm uppercase tracking-wide text-slate-500">Preview</div>
                <div className="text-lg font-semibold text-slate-900">{orgSettings?.name || 'Your Company'}</div>
              </div>
              {orgSettings?.logo_url && <img src={orgSettings.logo_url} alt="Logo preview" className="h-10 object-contain" />}
            </div>
            <div className="grid gap-2 md:grid-cols-2 text-sm text-slate-600">
              <div>
                <div className="font-semibold text-slate-800">Customer</div>
                <div>{customer || 'Customer name'}</div>
              </div>
              <div>
                <div className="font-semibold text-slate-800">Invoice Template</div>
                <div>{template}</div>
              </div>
              <div>
                <div className="font-semibold text-slate-800">Amount</div>
                <div>${amount ? parseFloat(amount).toFixed(2) : '0.00'}</div>
              </div>
              <div>
                <div className="font-semibold text-slate-800">Tax ID</div>
                <div>{orgSettings?.tax_id || 'Not set'}</div>
              </div>
              <div>
                <div className="font-semibold text-slate-800">Due Date</div>
                <div>{dueDate || 'YYYY-MM-DD'}</div>
              </div>
              {customFields && Object.entries(customFields).filter(([key, value]) => value).map(([key, value]) => (
                <div key={key}>
                  <div className="font-semibold text-slate-800">{key}</div>
                  <div>{value}</div>
                </div>
              ))}
            </div>
            <div className="mt-4 text-xs text-slate-500">
              {template === 'classic' ? 'Classic layout with strong headers.' : template === 'modern' ? 'Modern layout with clean section blocks.' : 'Minimal layout with lightweight spacing.'}
            </div>
            <div className="mt-4 text-xs text-slate-600 border-t border-slate-200 pt-3">
              <div className="font-semibold text-slate-800">Notes</div>
              <div>{orgSettings?.invoice_notes || 'Add invoice note in organization settings.'}</div>
            </div>
            <div className="mt-3 text-xs text-slate-600 border-t border-slate-200 pt-3">
              <div className="font-semibold text-slate-800">Terms</div>
              <div>{orgSettings?.invoice_terms || 'Add invoice terms in organization settings.'}</div>
            </div>
          </div>
          {error && <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">{error}</div>}
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={onClose} className="px-4 py-2 text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50">Cancel</button>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">Create Invoice</button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Inventory Page
const InventoryPage = () => {
  const [items, setItems] = useState([
    { id: 1, name: "Laptop Pro", sku: "SKU-001", quantity: 45, reorderLevel: 20, category: "Electronics" },
    { id: 2, name: "Office Chair", sku: "SKU-002", quantity: 12, reorderLevel: 10, category: "Furniture" },
    { id: 3, name: "Desk Lamp", sku: "SKU-003", quantity: 5, reorderLevel: 15, category: "Accessories" }
  ]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newItem, setNewItem] = useState({ name: '', sku: '', category: 'Electronics', quantity: 0, reorderLevel: 0 });

  const handleCreateItem = (event) => {
    event.preventDefault();
    if (!newItem.name.trim() || !newItem.sku.trim()) return;

    setItems((prev) => [
      {
        id: Date.now(),
        name: newItem.name.trim(),
        sku: newItem.sku.trim().toUpperCase(),
        quantity: Number(newItem.quantity) || 0,
        reorderLevel: Number(newItem.reorderLevel) || 0,
        category: newItem.category || 'General',
      },
      ...prev,
    ]);
    setNewItem({ name: '', sku: '', category: 'Electronics', quantity: 0, reorderLevel: 0 });
    setIsCreateOpen(false);
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2"><Package className="text-blue-600" /> Inventory Management</h2>
          <p className="text-slate-500 text-sm">Monitor stock levels and warehouse operations.</p>
        </div>
        <button onClick={() => setIsCreateOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition">+ Add Item</button>
      </div>

      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-slate-200">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xl font-semibold text-slate-900">Add Inventory Item</h3>
              <button type="button" onClick={() => setIsCreateOpen(false)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>
            <form onSubmit={handleCreateItem} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-sm text-slate-700">Name<input value={newItem.name} onChange={(e) => setNewItem({ ...newItem, name: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" required /></label>
                <label className="text-sm text-slate-700">SKU<input value={newItem.sku} onChange={(e) => setNewItem({ ...newItem, sku: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" required /></label>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-sm text-slate-700">Category<input value={newItem.category} onChange={(e) => setNewItem({ ...newItem, category: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" /></label>
                <label className="text-sm text-slate-700">Quantity<input type="number" min="0" value={newItem.quantity} onChange={(e) => setNewItem({ ...newItem, quantity: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" /></label>
              </div>
              <label className="block text-sm text-slate-700">Reorder Level<input type="number" min="0" value={newItem.reorderLevel} onChange={(e) => setNewItem({ ...newItem, reorderLevel: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" /></label>
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => setIsCreateOpen(false)} className="rounded-lg border border-slate-200 px-4 py-2 text-slate-600">Cancel</button>
                <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">Save Item</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="p-4 text-sm font-semibold text-slate-600">Item Name</th>
              <th className="p-4 text-sm font-semibold text-slate-600">SKU</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Quantity</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Reorder Level</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Category</th>
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <tr key={item.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                <td className="p-4 font-medium text-slate-900">{item.name}</td>
                <td className="p-4 text-slate-600 text-sm font-mono">{item.sku}</td>
                <td className="p-4 font-semibold text-slate-900">{item.quantity}</td>
                <td className="p-4 text-slate-600 text-sm">{item.reorderLevel}</td>
                <td className="p-4"><span className="px-2 py-1 bg-blue-100 text-blue-700 text-[10px] font-bold rounded">{item.category}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Payroll Page
const PayrollPage = () => {
  const { authFetch } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [payslips, setPayslips] = useState([]);
  const [payrollSummary, setPayrollSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isCreatePayslipOpen, setIsCreatePayslipOpen] = useState(false);
  const [isCreatingPayslip, setIsCreatingPayslip] = useState(false);

  useEffect(() => {
    const loadPayrollData = async () => {
      setIsLoading(true);
      try {
        const [employeesRes, payslipsRes, summaryRes] = await Promise.all([
          authFetch('/api/v2/hr/employees'),
          authFetch('/api/v2/hr/payslips'),
          authFetch('/api/v2/hr/payroll/summary'),
        ]);
        const employeesData = employeesRes.ok ? await employeesRes.json() : [];
        const payslipsData = payslipsRes.ok ? await payslipsRes.json() : [];
        const summaryData = summaryRes.ok ? await summaryRes.json() : null;

        setEmployees(Array.isArray(employeesData) ? employeesData : []);
        setPayslips(Array.isArray(payslipsData) ? payslipsData : []);
        setPayrollSummary(summaryData);
      } catch (err) {
        console.error(err);
        setEmployees([]);
        setPayslips([]);
        setPayrollSummary(null);
      } finally {
        setIsLoading(false);
      }
    };
    loadPayrollData();
  }, [authFetch]);

  const handleCreatePayslip = async (payload) => {
    setIsCreatingPayslip(true);
    try {
      const res = await authFetch('/api/v2/hr/payslips/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorBody = await res.json().catch(() => null);
        throw new Error(errorBody?.detail || 'Unable to generate payslip');
      }

      const created = await res.json();
      setPayslips((prev) => [created, ...prev]);
      setIsCreatePayslipOpen(false);
    } catch (err) {
      console.error(err);
      alert(err.message || 'Failed to generate payslip');
    } finally {
      setIsCreatingPayslip(false);
    }
  };

  const handleProcessPayslip = async (payslipId) => {
    setIsProcessing(true);
    try {
      const res = await authFetch(`/api/v2/hr/payslips/${payslipId}/process`, { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        setPayslips(prev => prev.map(p => p.id === updated.id ? updated : p));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="p-8">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2"><Users className="text-blue-600" /> Payroll Management</h2>
          <p className="text-slate-500 text-sm">Track salary, pay slips, and payroll approvals from one HR dashboard.</p>
        </div>
        <button onClick={() => setIsCreatePayslipOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition">+ Create Payslip</button>
      </div>

      <div className="grid gap-6 mb-8 lg:grid-cols-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="text-xs uppercase text-slate-400 mb-2">Employees</div>
          <div className="text-3xl font-bold text-slate-900">{employees.length}</div>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="text-xs uppercase text-slate-400 mb-2">Payslips</div>
          <div className="text-3xl font-bold text-slate-900">{payslips.length}</div>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="text-xs uppercase text-slate-400 mb-2">Pending processing</div>
          <div className="text-3xl font-bold text-slate-900">{payslips.filter(p => p.status === 'draft').length}</div>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="text-xs uppercase text-slate-400 mb-2">Attendance Hours</div>
          <div className="text-3xl font-bold text-slate-900">{payrollSummary?.attendance_hours?.toLocaleString() ?? '0'}</div>
        </div>
      </div>

      <CreatePayslipModal
        open={isCreatePayslipOpen}
        employees={employees}
        onClose={() => setIsCreatePayslipOpen(false)}
        onCreate={handleCreatePayslip}
        isSubmitting={isCreatingPayslip}
      />

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Payslip Ledger</h3>
            <p className="text-slate-500 text-sm">Approve draft payslips and keep payroll in sync with HR records.</p>
          </div>
          {isLoading ? <span className="text-slate-500">Loading payslips…</span> : null}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="p-4 text-sm font-semibold text-slate-600">Employee</th>
                <th className="p-4 text-sm font-semibold text-slate-600">Period</th>
                <th className="p-4 text-sm font-semibold text-slate-600">Gross</th>
                <th className="p-4 text-sm font-semibold text-slate-600">Net</th>
                <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
                <th className="p-4 text-sm font-semibold text-slate-600">Action</th>
              </tr>
            </thead>
            <tbody>
              {payslips.length === 0 ? (
                <tr>
                  <td colSpan="6" className="p-4 text-slate-500">No payslips available.</td>
                </tr>
              ) : payslips.map(payslip => (
                <tr key={payslip.id} className="border-b border-slate-100 hover:bg-slate-50 transition">
                  <td className="p-4 font-medium text-slate-900">{payslip.employee_name || 'Unknown'}</td>
                  <td className="p-4 text-slate-600">{payslip.period_start || '—'} to {payslip.period_end || '—'}</td>
                  <td className="p-4 text-slate-600">${(payslip.gross || 0).toLocaleString()}</td>
                  <td className="p-4 text-slate-600">${(payslip.net || 0).toLocaleString()}</td>
                  <td className="p-4 text-slate-600">{payslip.status}</td>
                  <td className="p-4 text-right">
                    {payslip.status === 'draft' ? (
                      <button onClick={() => handleProcessPayslip(payslip.id)} disabled={isProcessing} className="text-sm text-blue-600 hover:underline">
                        {isProcessing ? 'Processing…' : 'Process'}
                      </button>
                    ) : (
                      <span className="text-sm text-slate-500">Processed</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const PerformancePage = () => {
  const { authFetch } = useAuth();
  const [reviews, setReviews] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [newReview, setNewReview] = useState({ employee_id: '', rating: 0, goals: '', summary: '', status: 'pending' });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      try {
        const [reviewsRes, employeesRes] = await Promise.all([
          authFetch('/api/v2/hr/reviews'),
          authFetch('/api/v2/hr/employees'),
        ]);
        const reviewsData = await reviewsRes.json();
        const employeesData = await employeesRes.json();
        setReviews(Array.isArray(reviewsData) ? reviewsData : []);
        setEmployees(Array.isArray(employeesData) ? employeesData : []);
      } catch (err) {
        console.error(err);
        setReviews([]);
        setEmployees([]);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, [authFetch]);

  const handleCreateReview = async (event) => {
    event.preventDefault();
    setIsSaving(true);
    try {
      const payload = {
        employee_id: Number(newReview.employee_id),
        rating: Number(newReview.rating) || 0,
        goals: newReview.goals || '',
        summary: newReview.summary || '',
        status: newReview.status || 'pending',
      };
      const res = await authFetch('/api/v2/hr/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const created = await res.json();
        setReviews((prev) => [created, ...prev]);
        setNewReview({ employee_id: '', rating: 0, goals: '', summary: '', status: 'pending' });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-8">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2"><Star className="text-blue-600" /> Performance Reviews</h2>
          <p className="text-slate-500 text-sm">Capture employee performance feedback, review scores, and next-step coaching notes.</p>
        </div>
      </div>

      <div className="grid gap-6 mb-8 lg:grid-cols-3">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="text-xs uppercase text-slate-400 mb-2">Reviews</div>
          <div className="text-3xl font-bold text-slate-900">{reviews.length}</div>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="text-xs uppercase text-slate-400 mb-2">Top score</div>
          <div className="text-3xl font-bold text-slate-900">{reviews.reduce((max, review) => Math.max(max, review.score || 0), 0)}</div>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="text-xs uppercase text-slate-400 mb-2">Average score</div>
          <div className="text-3xl font-bold text-slate-900">{reviews.length ? (reviews.reduce((sum, review) => sum + (review.score || 0), 0) / reviews.length).toFixed(1) : '—'}</div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">New Review</h3>
          <form className="space-y-4" onSubmit={handleCreateReview}>
            <div>
              <label className="block text-sm font-medium text-slate-700">Employee</label>
              <select value={newReview.employee_id} onChange={(e) => setNewReview({ ...newReview, employee_id: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm">
                <option value="">Select an employee</option>
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>{employee.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Rating</label>
              <input type="number" min="0" max="5" step="0.1" value={newReview.rating} onChange={(e) => setNewReview({ ...newReview, rating: Number(e.target.value) })} className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Goals</label>
              <textarea value={newReview.goals} onChange={(e) => setNewReview({ ...newReview, goals: e.target.value })} rows={3} className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Summary</label>
              <textarea value={newReview.summary} onChange={(e) => setNewReview({ ...newReview, summary: e.target.value })} rows={4} className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Status</label>
              <select value={newReview.status} onChange={(e) => setNewReview({ ...newReview, status: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm">
                <option value="pending">Pending</option>
                <option value="completed">Completed</option>
              </select>
            </div>
            <button type="submit" disabled={isSaving} className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition">
              {isSaving ? 'Saving…' : 'Add Review'}
            </button>
          </form>
        </div>

        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm overflow-x-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Recent Reviews</h3>
            {isLoading ? <span className="text-slate-500">Loading reviews…</span> : null}
          </div>
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="p-4 text-sm font-semibold text-slate-600">Employee</th>
                <th className="p-4 text-sm font-semibold text-slate-600">Score</th>
                <th className="p-4 text-sm font-semibold text-slate-600">Comments</th>
                <th className="p-4 text-sm font-semibold text-slate-600">Date</th>
              </tr>
            </thead>
            <tbody>
              {reviews.length === 0 ? (
                <tr>
                  <td colSpan="4" className="p-4 text-slate-500">No performance reviews yet.</td>
                </tr>
              ) : reviews.map((review) => (
                <tr key={review.id} className="border-b border-slate-100 hover:bg-slate-50 transition">
                  <td className="p-4 font-medium text-slate-900">{review.employee_name || review.employee_id || 'Unknown'}</td>
                  <td className="p-4 text-slate-600">{review.rating ?? review.score ?? '—'}</td>
                  <td className="p-4 text-slate-600 max-w-xl break-words">{review.summary || review.goals || review.comments || '—'}</td>
                  <td className="p-4 text-slate-600">{review.reviewed_at ? new Date(review.reviewed_at).toLocaleDateString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Payments Page
const PaymentsPage = () => {
  const { authFetch } = useAuth();
  const [payments, setPayments] = useState([]);
  const [orgSettings, setOrgSettings] = useState({ currency: 'USD' });
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newPayment, setNewPayment] = useState({ reference: '', customer: '', amount: '0', method: 'Bank Transfer', date: new Date().toISOString().slice(0, 10) });

  useEffect(() => {
    authFetch('/api/v2/settings')
      .then(res => res?.ok ? res.json() : null)
      .then(data => {
        if (data) {
          setOrgSettings({ currency: data.currency || 'USD' });
        }
      })
      .catch(() => {});
  }, [authFetch]);

  const formatCurrency = (amount, currency = orgSettings.currency || 'USD') => {
    const value = Number(amount || 0);
    return `${currency} ${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const handleCreatePayment = (event) => {
    event.preventDefault();
    if (!newPayment.reference.trim() || !newPayment.customer.trim()) return;

    setPayments((prev) => [
      {
        id: Date.now(),
        reference: newPayment.reference.trim(),
        customer: newPayment.customer.trim(),
        amount: Number(newPayment.amount) || 0,
        method: newPayment.method,
        date: newPayment.date,
      },
      ...prev,
    ]);
    setNewPayment({ reference: '', customer: '', amount: '0', method: 'Bank Transfer', date: new Date().toISOString().slice(0, 10) });
    setIsCreateOpen(false);
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2"><CreditCard className="text-blue-600" /> Payments & Collections</h2>
          <p className="text-slate-500 text-sm">Track incoming and outgoing payments.</p>
        </div>
        <button onClick={() => setIsCreateOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition">+ Record Payment</button>
      </div>

      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-slate-200">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xl font-semibold text-slate-900">Record Payment</h3>
              <button type="button" onClick={() => setIsCreateOpen(false)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>
            <form onSubmit={handleCreatePayment} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-sm text-slate-700">Reference<input value={newPayment.reference} onChange={(e) => setNewPayment({ ...newPayment, reference: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" required /></label>
                <label className="text-sm text-slate-700">Customer<input value={newPayment.customer} onChange={(e) => setNewPayment({ ...newPayment, customer: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" required /></label>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-sm text-slate-700">Amount<input type="number" min="0" step="0.01" value={newPayment.amount} onChange={(e) => setNewPayment({ ...newPayment, amount: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" required /></label>
                <label className="text-sm text-slate-700">Method<select value={newPayment.method} onChange={(e) => setNewPayment({ ...newPayment, method: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"><option>Bank Transfer</option><option>Cash</option><option>Card</option><option>UPI</option></select></label>
              </div>
              <label className="block text-sm text-slate-700">Date<input type="date" value={newPayment.date} onChange={(e) => setNewPayment({ ...newPayment, date: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" /></label>
              <div className="flex justify-end gap-3 pt-2"><button type="button" onClick={() => setIsCreateOpen(false)} className="rounded-lg border border-slate-200 px-4 py-2 text-slate-600">Cancel</button><button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">Save Payment</button></div>
            </form>
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="p-4 text-sm font-semibold text-slate-600">Reference</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Customer</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Amount</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Method</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Date</th>
            </tr>
          </thead>
          <tbody>
            {payments.map(pay => (
              <tr key={pay.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                <td className="p-4 font-medium text-slate-900">{pay.reference}</td>
                <td className="p-4 text-slate-600 text-sm">{pay.customer}</td>
                <td className="p-4 font-semibold text-green-600">{formatCurrency(pay.amount)}</td>
                <td className="p-4 text-slate-600 text-sm">{pay.method}</td>
                <td className="p-4 text-slate-600 text-sm">{pay.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Projects Page
const ProjectsPage = () => {
  const [projects, setProjects] = useState([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newProject, setNewProject] = useState({ name: '', client: '', status: 'In Progress', progress: 10, dueDate: new Date().toISOString().slice(0, 10) });

  const handleCreateProject = (event) => {
    event.preventDefault();
    if (!newProject.name.trim()) return;

    setProjects((prev) => [
      {
        id: Date.now(),
        name: newProject.name.trim(),
        client: newProject.client.trim() || 'Internal',
        status: newProject.status,
        progress: Number(newProject.progress) || 0,
        dueDate: newProject.dueDate,
      },
      ...prev,
    ]);
    setNewProject({ name: '', client: '', status: 'In Progress', progress: 10, dueDate: new Date().toISOString().slice(0, 10) });
    setIsCreateOpen(false);
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2"><Briefcase className="text-blue-600" /> Project Management</h2>
          <p className="text-slate-500 text-sm">Track projects, milestones and deliverables.</p>
        </div>
        <button onClick={() => setIsCreateOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition">+ New Project</button>
      </div>

      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-slate-200">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xl font-semibold text-slate-900">Create Project</h3>
              <button type="button" onClick={() => setIsCreateOpen(false)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>
            <form onSubmit={handleCreateProject} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-sm text-slate-700">Project Name<input value={newProject.name} onChange={(e) => setNewProject({ ...newProject, name: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" required /></label>
                <label className="text-sm text-slate-700">Client<input value={newProject.client} onChange={(e) => setNewProject({ ...newProject, client: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" /></label>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-sm text-slate-700">Status<select value={newProject.status} onChange={(e) => setNewProject({ ...newProject, status: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"><option>In Progress</option><option>Planned</option><option>On Hold</option></select></label>
                <label className="text-sm text-slate-700">Progress<input type="number" min="0" max="100" value={newProject.progress} onChange={(e) => setNewProject({ ...newProject, progress: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" /></label>
              </div>
              <label className="block text-sm text-slate-700">Due Date<input type="date" value={newProject.dueDate} onChange={(e) => setNewProject({ ...newProject, dueDate: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" /></label>
              <div className="flex justify-end gap-3 pt-2"><button type="button" onClick={() => setIsCreateOpen(false)} className="rounded-lg border border-slate-200 px-4 py-2 text-slate-600">Cancel</button><button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">Create Project</button></div>
            </form>
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="p-4 text-sm font-semibold text-slate-600">Project Name</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Client</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Progress</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Due Date</th>
            </tr>
          </thead>
          <tbody>
            {projects.map(proj => (
              <tr key={proj.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                <td className="p-4 font-medium text-slate-900">{proj.name}</td>
                <td className="p-4 text-slate-600 text-sm">{proj.client}</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase ${
                    proj.status === 'In Progress' ? 'bg-blue-100 text-blue-600' : 'bg-yellow-100 text-yellow-600'
                  }`}>
                    {proj.status}
                  </span>
                </td>
                <td className="p-4">
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${proj.progress}%` }}></div>
                  </div>
                  <span className="text-xs text-slate-600">{proj.progress}%</span>
                </td>
                <td className="p-4 text-slate-600 text-sm">{proj.dueDate}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Helpdesk Page
const HelpdeskPage = () => {
  const [tickets, setTickets] = useState([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newTicket, setNewTicket] = useState({ subject: '', customer: '', priority: 'Medium', status: 'Open' });

  const handleCreateTicket = (event) => {
    event.preventDefault();
    if (!newTicket.subject.trim() || !newTicket.customer.trim()) return;

    setTickets((prev) => [
      {
        id: Date.now(),
        ticketId: `T-${String(Date.now()).slice(-5)}`,
        subject: newTicket.subject.trim(),
        customer: newTicket.customer.trim(),
        priority: newTicket.priority,
        status: newTicket.status,
      },
      ...prev,
    ]);
    setNewTicket({ subject: '', customer: '', priority: 'Medium', status: 'Open' });
    setIsCreateOpen(false);
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2"><Headphones className="text-blue-600" /> Helpdesk & Support</h2>
          <p className="text-slate-500 text-sm">Manage customer support tickets and inquiries.</p>
        </div>
        <button onClick={() => setIsCreateOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition">+ New Ticket</button>
      </div>

      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-slate-200">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xl font-semibold text-slate-900">Create Ticket</h3>
              <button type="button" onClick={() => setIsCreateOpen(false)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>
            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-sm text-slate-700">Subject<input value={newTicket.subject} onChange={(e) => setNewTicket({ ...newTicket, subject: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" required /></label>
                <label className="text-sm text-slate-700">Customer<input value={newTicket.customer} onChange={(e) => setNewTicket({ ...newTicket, customer: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2" required /></label>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <label className="text-sm text-slate-700">Priority<select value={newTicket.priority} onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"><option>Low</option><option>Medium</option><option>High</option></select></label>
                <label className="text-sm text-slate-700">Status<select value={newTicket.status} onChange={(e) => setNewTicket({ ...newTicket, status: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"><option>Open</option><option>In Progress</option><option>Resolved</option></select></label>
              </div>
              <div className="flex justify-end gap-3 pt-2"><button type="button" onClick={() => setIsCreateOpen(false)} className="rounded-lg border border-slate-200 px-4 py-2 text-slate-600">Cancel</button><button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">Create Ticket</button></div>
            </form>
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="p-4 text-sm font-semibold text-slate-600">Ticket ID</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Subject</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Customer</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Priority</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map(ticket => (
              <tr key={ticket.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                <td className="p-4 font-medium text-slate-900 font-mono">{ticket.ticketId}</td>
                <td className="p-4 text-slate-600 text-sm">{ticket.subject}</td>
                <td className="p-4 text-slate-600 text-sm">{ticket.customer}</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase ${
                    ticket.priority === 'High' ? 'bg-red-100 text-red-600' :
                    ticket.priority === 'Medium' ? 'bg-yellow-100 text-yellow-600' :
                    'bg-green-100 text-green-600'
                  }`}>
                    {ticket.priority}
                  </span>
                </td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase ${
                    ticket.status === 'Open' ? 'bg-blue-100 text-blue-600' :
                    ticket.status === 'In Progress' ? 'bg-yellow-100 text-yellow-600' :
                    'bg-green-100 text-green-600'
                  }`}>
                    {ticket.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Vendor Management Page
const VendorManagementPage = () => {
  const { authFetch } = useAuth();
  const [activeTab, setActiveTab] = useState('vendors');
  const [vendors, setVendors] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [vendorPerformance, setVendorPerformance] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isVendorCreateOpen, setIsVendorCreateOpen] = useState(false);

  useEffect(() => {
    const loadVendorModule = async () => {
      setIsLoading(true);
      try {
        const [vendorRes, poRes, perfRes] = await Promise.all([
          authFetch('/api/v2/vendors'),
          authFetch('/api/v2/purchase-orders'),
          authFetch('/api/v2/vendors/performance'),
        ]);
        const [vendorData, poData, perfData] = await Promise.all([
          vendorRes.ok ? vendorRes.json() : [],
          poRes.ok ? poRes.json() : [],
          perfRes.ok ? perfRes.json() : [],
        ]);

        setVendors(Array.isArray(vendorData) ? vendorData : []);
        setPurchaseOrders(Array.isArray(poData) ? poData : []);
        setVendorPerformance(Array.isArray(perfData) ? perfData : []);
      } catch (error) {
        console.error('Failed to load vendor data:', error);
        setVendors([]);
        setPurchaseOrders([]);
        setVendorPerformance([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadVendorModule();
  }, [authFetch]);

  const handleAddVendor = (vendor) => {
    setVendors((prev) => [vendor, ...prev]);
  };

  const totalSpend = purchaseOrders.reduce((sum, po) => sum + (po.total_amount || 0), 0);
  const pendingPOs = purchaseOrders.filter(po => ['draft', 'pending', 'pending_approval'].includes((po.status || '').toLowerCase())).length;
  const inTransitPOs = purchaseOrders.filter(po => ['in transit', 'ordered'].includes((po.status || '').toLowerCase())).length;
  const averageQuality = vendorPerformance.length ? (vendorPerformance.reduce((sum, perf) => sum + (perf.quality_score || 0), 0) / vendorPerformance.length).toFixed(1) : '—';

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2 mb-2">
          <Package className="text-blue-600" /> Vendor Management
        </h2>
        <p className="text-slate-500 text-sm">Manage suppliers, purchase orders, and vendor performance.</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-slate-200 overflow-x-auto">
        <button 
          onClick={() => setActiveTab('vendors')}
          className={`px-4 py-2 font-medium transition whitespace-nowrap ${activeTab === 'vendors' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-800'}`}
        >
          Vendors
        </button>
        <button 
          onClick={() => setActiveTab('po')}
          className={`px-4 py-2 font-medium transition whitespace-nowrap ${activeTab === 'po' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-800'}`}
        >
          Purchase Orders
        </button>
        <button 
          onClick={() => setActiveTab('performance')}
          className={`px-4 py-2 font-medium transition whitespace-nowrap ${activeTab === 'performance' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-600 hover:text-slate-800'}`}
        >
          Performance
        </button>
      </div>

      {/* Vendors Tab */}
      {activeTab === 'vendors' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-bold">Vendors List</h3>
            <button onClick={() => setIsVendorCreateOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition">+ Add Vendor</button>
          </div>

          {/* Vendor Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Total Vendors</div>
              <div className="text-2xl font-bold text-slate-900">{vendors.length}</div>
              <div className="text-xs text-slate-500 mt-1">Supplier profiles in the network</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Active Vendors</div>
              <div className="text-2xl font-bold text-green-600">{vendors.length}</div>
              <div className="text-xs text-slate-500 mt-1">Ready for procurement</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Total Spend</div>
              <div className="text-2xl font-bold text-slate-900">${totalSpend.toLocaleString()}</div>
              <div className="text-xs text-slate-500 mt-1">Across approved purchase orders</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Avg Quality</div>
              <div className="text-2xl font-bold text-blue-600">{averageQuality}%</div>
              <div className="text-xs text-slate-500 mt-1">Metric from vendor performance</div>
            </div>
          </div>

          {/* Vendors Table */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="p-4 text-sm font-semibold text-slate-600">Vendor Name</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Category</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Email</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
                </tr>
              </thead>
              <tbody>
                {vendors.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="p-4 text-slate-500">No vendors found yet.</td>
                  </tr>
                ) : vendors.map(vendor => (
                  <tr key={vendor.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                    <td className="p-4 font-medium text-blue-600 cursor-pointer hover:underline">{vendor.name}</td>
                    <td className="p-4 text-slate-600 text-sm">{vendor.category || 'General'}</td>
                    <td className="p-4 text-slate-600 text-sm">{vendor.email || '—'}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase ${
                        'bg-green-100 text-green-600'
                      }`}>
                        Active
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Purchase Orders Tab */}
      {activeTab === 'po' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-bold">Purchase Orders</h3>
            <button onClick={() => showFeatureComingSoon('Create PO')} className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm transition">+ Create PO</button>
          </div>

          {/* PO Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Total POs</div>
              <div className="text-2xl font-bold text-slate-900">{purchaseOrders.length}</div>
              <div className="text-xs text-slate-500 mt-1">Across all vendors</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Pending</div>
              <div className="text-2xl font-bold text-yellow-600">{pendingPOs}</div>
              <div className="text-xs text-slate-500 mt-1">Need approval</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">In Transit</div>
              <div className="text-2xl font-bold text-blue-600">{inTransitPOs}</div>
              <div className="text-xs text-slate-500 mt-1">Shipping or receiving</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
              <div className="text-slate-600 text-xs font-semibold uppercase mb-1">Total Value</div>
              <div className="text-2xl font-bold text-slate-900">${totalSpend.toLocaleString()}</div>
              <div className="text-xs text-slate-500 mt-1">Committed spend</div>
            </div>
          </div>

          {/* PO Table */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="p-4 text-sm font-semibold text-slate-600">PO Number</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Vendor</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Amount</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Created Date</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Last Updated</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
                </tr>
              </thead>
              <tbody>
                {purchaseOrders.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="p-4 text-slate-500">No purchase orders found.</td>
                  </tr>
                ) : purchaseOrders.map(po => (
                  <tr key={po.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                    <td className="p-4 font-medium text-blue-600 cursor-pointer hover:underline">{po.reference_number}</td>
                    <td className="p-4 text-slate-600 text-sm">{po.vendor_name || 'Unknown'}</td>
                    <td className="p-4 font-semibold text-slate-900">${(po.total_amount || 0).toLocaleString()}</td>
                    <td className="p-4 text-slate-600 text-sm">{po.created_at ? new Date(po.created_at).toLocaleDateString() : '—'}</td>
                    <td className="p-4 text-slate-600 text-sm">{po.updated_at ? new Date(po.updated_at).toLocaleDateString() : '—'}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase ${
                        po.status === 'Delivered' ? 'bg-green-100 text-green-600' :
                        po.status === 'In Transit' ? 'bg-blue-100 text-blue-600' :
                        'bg-yellow-100 text-yellow-600'
                      }`}>
                        {po.status || 'Draft'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Performance Tab */}
      {activeTab === 'performance' && (
        <div className="space-y-6">
          <h3 className="text-lg font-bold">Vendor Performance Metrics</h3>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="p-4 text-sm font-semibold text-slate-600">Vendor Name</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">On-Time Delivery</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Quality Score</th>
                  <th className="p-4 text-sm font-semibold text-slate-600">Response Time</th>
                </tr>
              </thead>
              <tbody>
                {vendorPerformance.map((perf, idx) => (
                  <tr key={idx} className="border-b border-slate-50 hover:bg-slate-50/50 transition">
                    <td className="p-4 font-medium text-slate-900">{perf.vendor_name || perf.vendor || 'Unknown'}</td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <div className="w-20 bg-slate-200 rounded-full h-2">
                          <div className="bg-green-500 h-2 rounded-full" style={{ width: `${(perf.on_time_delivery_rate ?? perf.onTimeDelivery) || 0}%` }}></div>
                        </div>
                        <span className="text-sm font-semibold text-slate-900">{(perf.on_time_delivery_rate ?? perf.onTimeDelivery) || 0}%</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <div className="w-20 bg-slate-200 rounded-full h-2">
                          <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${(perf.quality_score ?? perf.quality) || 0}%` }}></div>
                        </div>
                        <span className="text-sm font-semibold text-slate-900">{(perf.quality_score ?? perf.quality) || 0}%</span>
                      </div>
                    </td>
                    <td className="p-4 text-slate-600 text-sm font-semibold">{perf.response_time || perf.responseTime || 'TBD'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      <CreateVendorModal
        open={isVendorCreateOpen}
        onClose={() => setIsVendorCreateOpen(false)}
        onSave={handleAddVendor}
      />
    </div>
  );
};

const CreateVendorModal = ({ open, onClose, onSave }) => {
  const { authFetch } = useAuth();
  const [name, setName] = useState('');
  const [category, setCategory] = useState('');
  const [email, setEmail] = useState('');
  const [notes, setNotes] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setName('');
      setCategory('');
      setEmail('');
      setNotes('');
      setIsSaving(false);
    }
  }, [open]);

  const handleSave = async () => {
    if (!name.trim()) {
      alert('Vendor name is required.');
      return;
    }

    setIsSaving(true);
    try {
      const response = await authFetch('/api/v2/vendors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, category, email, notes }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail || 'Unable to create vendor');
      }

      const vendor = await response.json();
      onSave(vendor);
      onClose();
    } catch (error) {
      console.error('Create vendor error:', error);
      alert(`Create vendor failed: ${error.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 py-6">
      <div className="w-full max-w-xl rounded-3xl bg-white p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-semibold text-slate-900">Add New Vendor</h3>
            <p className="text-sm text-slate-500">Create a vendor profile for your procurement workflows.</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">✕</button>
        </div>
        <div className="grid gap-4">
          <label className="block text-sm font-medium text-slate-700">Vendor Name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-blue-500" placeholder="Acme Supplies" />
          <label className="block text-sm font-medium text-slate-700">Category</label>
          <input value={category} onChange={(e) => setCategory(e.target.value)} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-blue-500" placeholder="Raw Materials" />
          <label className="block text-sm font-medium text-slate-700">Email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-blue-500" placeholder="vendor@example.com" />
          <label className="block text-sm font-medium text-slate-700">Notes</label>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-blue-500" rows={4} placeholder="Optional notes about this supplier."></textarea>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button onClick={onClose} className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">Cancel</button>
          <button onClick={handleSave} disabled={isSaving} className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50">
            {isSaving ? 'Saving...' : 'Create Vendor'}
          </button>
        </div>
      </div>
    </div>
  );
};

const CreatePayslipModal = ({ open, employees, onClose, onCreate, isSubmitting }) => {
  const [employeeId, setEmployeeId] = useState('');
  const [periodStart, setPeriodStart] = useState('');
  const [periodEnd, setPeriodEnd] = useState('');
  const [payType, setPayType] = useState('monthly');
  const [hourlyRate, setHourlyRate] = useState('');
  const [pieces, setPieces] = useState('');
  const [ratePerPiece, setRatePerPiece] = useState('');
  const [loanRepayment, setLoanRepayment] = useState('0');
  const [extraDeductions, setExtraDeductions] = useState('0');

  useEffect(() => {
    if (!open) {
      setEmployeeId('');
      setPeriodStart('');
      setPeriodEnd('');
      setPayType('monthly');
      setHourlyRate('');
      setPieces('');
      setRatePerPiece('');
      setLoanRepayment('0');
      setExtraDeductions('0');
    }
  }, [open]);

  const handleSubmit = async () => {
    if (!employeeId || !periodStart || !periodEnd) {
      alert('Employee and payroll period are required.');
      return;
    }

    await onCreate({
      employee_id: Number(employeeId),
      period_start: periodStart,
      period_end: periodEnd,
      pay_type: payType,
      hourly_rate: hourlyRate ? Number(hourlyRate) : undefined,
      pieces: pieces ? Number(pieces) : undefined,
      rate_per_piece: ratePerPiece ? Number(ratePerPiece) : undefined,
      loan_repayment: Number(loanRepayment || 0),
      extra_deductions: Number(extraDeductions || 0),
    });
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 py-6">
      <div className="w-full max-w-2xl rounded-3xl bg-white p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-semibold text-slate-900">Create Payslip</h3>
            <p className="text-sm text-slate-500">Use attendance or salary structure to generate payroll accurately.</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">✕</button>
        </div>
        <div className="grid gap-4">
          <label className="block text-sm font-medium text-slate-700">Employee</label>
          <select value={employeeId} onChange={(e) => setEmployeeId(e.target.value)} className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-blue-500">
            <option value="">Select employee</option>
            {employees.map(emp => (
              <option key={emp.id} value={emp.id}>{emp.name} ({emp.employee_code})</option>
            ))}
          </select>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-700">Period Start</label>
              <input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Period End</label>
              <input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-blue-500" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Pay Type</label>
            <select value={payType} onChange={(e) => setPayType(e.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-blue-500">
              <option value="monthly">Monthly salary</option>
              <option value="hourly">Hourly wage</option>
              <option value="piece-rate">Piece-rate</option>
            </select>
          </div>
          {payType === 'hourly' && (
            <div>
              <label className="block text-sm font-medium text-slate-700">Hourly Rate</label>
              <input type="number" value={hourlyRate} onChange={(e) => setHourlyRate(e.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-blue-500" placeholder="Leave blank to use employee salary as hourly rate" />
            </div>
          )}
          {payType === 'piece-rate' && (
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-slate-700">Units / Pieces</label>
                <input type="number" value={pieces} onChange={(e) => setPieces(e.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">Rate per Piece</label>
                <input type="number" value={ratePerPiece} onChange={(e) => setRatePerPiece(e.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-blue-500" />
              </div>
            </div>
          )}
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-700">Loan Repayment</label>
              <input type="number" value={loanRepayment} onChange={(e) => setLoanRepayment(e.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Extra Deductions</label>
              <input type="number" value={extraDeductions} onChange={(e) => setExtraDeductions(e.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-blue-500" />
            </div>
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button onClick={onClose} className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">Cancel</button>
          <button onClick={handleSubmit} disabled={isSubmitting} className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50">
            {isSubmitting ? 'Calculating...' : 'Generate Payslip'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Generic component for module pages
const ModulePage = ({ moduleName }) => {
  return (
    <div className="p-10 text-center">
      <h1 className="text-4xl font-bold">{moduleName} Module</h1>
      <p className="text-lg text-slate-600 mt-4">Welcome to the {moduleName} section. More content coming soon!</p>
      <Link to="/" className="mt-8 inline-block px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Back to Home</Link>
    </div>
  );
};

const ModulesPage = () => {
  return (
    <div className="max-w-6xl mx-auto px-6 py-20">
      <div className="text-center mb-12">
        <p className="text-sm uppercase tracking-[0.3em] text-blue-600 font-semibold">Gaatha Modules</p>
        <h1 className="mt-4 text-4xl font-bold text-slate-900">Built for every part of your business</h1>
        <p className="mt-4 text-slate-600 max-w-2xl mx-auto">Browse the capabilities that make Gaatha the single window platform for finance, operations, people management, and customer engagement.</p>
      </div>
      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {moduleCatalog.map((module) => (
          <Link
            key={module.title}
            to={module.route}
            className="group block rounded-3xl border border-slate-200 bg-white p-6 transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-xl"
          >
            <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 text-xl">
              <i className={`${module.iconClass} text-blue-700`}></i>
            </div>
            <h2 className="text-xl font-semibold text-slate-900">{module.title}</h2>
            <p className="mt-3 text-slate-600">{module.description}</p>
          </Link>
        ))}
      </div>
      <div className="mt-12 text-center">
        <Link to="/auth/login" className="inline-flex items-center justify-center rounded-full bg-blue-600 px-8 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition">
          Sign in to access your Gaatha workspace
        </Link>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const { user, authFetch } = useAuth();

  useEffect(() => {
    authFetch('/api/dashboard-stats')
      .then((res) => {
        if (!res || !res.ok) {
          throw new Error(`Dashboard stats request failed with status ${res ? res.status : 'unknown'}`);
        }
        return res.json();
      })
      .then((data) => setStats(data))
      .catch((err) => {
        console.error('Failed to fetch stats', err);
        setStats({
          customers: 0,
          invoices: 0,
          products: 0,
          employees: 0,
          total_revenue: 0,
          low_stock_count: 0,
          recent_activity: [],
        });
      });
  }, [authFetch]);

  if (!stats) return (
    <div className="flex items-center justify-center min-h-[400px]">
      <LoadingSpinner size="lg" label="Preparing your dashboard metrics..." />
    </div>
  );

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-800">Welcome back, {user?.username || 'User'}</h1>
        <p className="text-slate-500">Here's what's happening in your enterprise today.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-slate-500 text-sm font-medium mb-1">Total Customers</div>
          <div className="text-3xl font-bold text-slate-900">{stats.customers}</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-slate-500 text-sm font-medium mb-1">Open Invoices</div>
          <div className="text-3xl font-bold text-slate-900">{stats.invoices}</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-slate-500 text-sm font-medium mb-1">Products in Stock</div>
          <div className="text-3xl font-bold text-slate-900">{stats.products}</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-slate-500 text-sm font-medium mb-1">Active Employees</div>
          <div className="text-3xl font-bold text-slate-900">{stats.employees}</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-slate-500 text-sm font-medium mb-1">Total Revenue</div>
          <div className="text-3xl font-bold text-green-600">${stats.total_revenue.toLocaleString()}</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-slate-500 text-sm font-medium mb-1">Low Stock Alerts</div>
          <div className="text-3xl font-bold text-red-600">{stats.low_stock_count}</div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-lg font-bold mb-4">Recent Activity</h3>
        {!stats.recent_activity ? <ActivitySkeleton /> : (
          <ul className="space-y-4">
                {stats.recent_activity.map(act => (
                  <li key={act.id} className="flex items-center gap-3 text-sm text-slate-600 border-b border-slate-50 pb-3 last:border-0">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    {act.text}
                  </li>
                ))}
          </ul>
        )}
      </div>
    </div>
  );
};

const SignupSuccessPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || '';
  const username = location.state?.username || '';

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      <div className="p-8 bg-white shadow-2xl rounded-lg w-96 text-center">
        <div className="mb-6 flex justify-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          </div>
        </div>

        <h2 className="text-3xl font-bold mb-2 text-green-600">Welcome to Gaatha Suite!</h2>
        <p className="text-slate-600 mb-4">Your account has been successfully created.</p>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-left">
          <div className="mb-3">
            <p className="text-sm font-medium text-slate-600">Username</p>
            <p className="text-base font-semibold text-slate-900">{username}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-600">Email</p>
            <p className="text-base font-semibold text-slate-900">{email}</p>
          </div>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-green-700">
            ✓ A welcome email has been sent to your email address. Please check your inbox and spam folder.
          </p>
        </div>

        <p className="text-slate-600 text-sm mb-6">
          You can now log in with your credentials and start using Gaatha Suite to manage your business.
        </p>

        <button
          onClick={() => navigate('/auth/login?next=/dashboard')}
          className="w-full bg-blue-600 text-white py-3 rounded-md hover:bg-blue-700 font-medium transition"
        >
          Go to Login
        </button>

        <p className="text-slate-500 text-xs mt-4">
          This page will automatically redirect in <span className="font-semibold">5 seconds...</span>
        </p>
      </div>

      {/* Auto redirect after 5 seconds */}
      {(() => {
        setTimeout(() => navigate('/auth/login?next=/dashboard'), 5000);
        return null;
      })()}
    </div>
  );
};

const RegisterPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    organizationName: '',
    website: '',
    industry: '',
    companySize: '',
    phone: '',
    username: '',
    email: '',
    password: '',
  });
  const [status, setStatus] = useState({ type: '', msg: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus({ type: 'info', msg: 'Creating account...' });

    try {
      setIsSubmitting(true);
      const response = await fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify(formData),
      });
      const data = await response.json();
      if (response.ok) {
        // Pass user data to success page via state
        navigate('/auth/register/success', { 
          state: { 
            user: data,
            email: formData.email,
            username: formData.username 
          } 
        });
      } else {
        setStatus({ type: 'error', msg: data.detail || data.message || 'Registration failed' });
      }
    } catch (err) {
      setStatus({ type: 'error', msg: 'Server error: ' + err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-100">
      <div className="p-8 bg-white shadow-lg rounded-lg w-96">
        <h2 className="text-2xl font-bold mb-2 text-center">Create your Gaatha organization account</h2>
        <p className="text-sm text-slate-500 mb-6 text-center">Tell us about your organization so we can tailor the onboarding experience.</p>
        {status.msg && (
          <div className={`p-3 rounded mb-4 text-sm ${status.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
            {status.msg}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Organization Name</label>
            <input
              type="text"
              className="mt-1 block w-full border border-gray-300 rounded-md p-2"
              value={formData.organizationName}
              onChange={(e) => setFormData({ ...formData, organizationName: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Website</label>
            <input
              type="url"
              className="mt-1 block w-full border border-gray-300 rounded-md p-2"
              placeholder="https://yourcompany.com"
              value={formData.website}
              onChange={(e) => setFormData({ ...formData, website: e.target.value })}
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Industry</label>
              <select
                className="mt-1 block w-full border border-gray-300 rounded-md p-2 bg-white"
                value={formData.industry}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
              >
                <option value="">Select your industry</option>
                <option>Retail</option>
                <option>Manufacturing</option>
                <option>Services</option>
                <option>Hospitality</option>
                <option>Healthcare</option>
                <option>Wholesale</option>
                <option>Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Company Size</label>
              <select
                className="mt-1 block w-full border border-gray-300 rounded-md p-2 bg-white"
                value={formData.companySize}
                onChange={(e) => setFormData({ ...formData, companySize: e.target.value })}
              >
                <option value="">Select company size</option>
                <option>1-10 employees</option>
                <option>11-50 employees</option>
                <option>51-200 employees</option>
                <option>201-500 employees</option>
                <option>501+ employees</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Phone Number</label>
            <input
              type="tel"
              className="mt-1 block w-full border border-gray-300 rounded-md p-2"
              placeholder="+91 98765 43210"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Username</label>
            <input
              type="text"
              className="mt-1 block w-full border border-gray-300 rounded-md p-2"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              className="mt-1 block w-full border border-gray-300 rounded-md p-2"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Password</label>
            <input
              type="password"
              className="mt-1 block w-full border border-gray-300 rounded-md p-2"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
            />
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 font-medium disabled:opacity-50 flex justify-center items-center gap-2"
          >
            {isSubmitting ? <LoadingSpinner size="sm" label="" color="white" /> : "Create Account"}
          </button>
        </form>
        <div className="mt-6 text-center text-sm text-slate-500">
          Already have an account? <Link to="/auth/login" className="text-blue-600">Sign In</Link>
        </div>
      </div>
    </div>
  );
};

/**
 * ProtectedRoute: Wraps components that require authentication.
 */
const ProtectedRoute = () => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50">
      <LoadingSpinner size="lg" label="Securing session..." />
    </div>
  );
  
  if (!isAuthenticated) {
    return <Navigate to={`/auth/login?next=${location.pathname}`} replace />;
  }

  return <Outlet />;
};

/**
 * Sidebar: Navigation that adjusts based on user role.
 */
const Sidebar = () => {
  const { user, logout, notifications, removeNotification, clearNotifications } = useAuth();
  if (!user) return null;

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 min-h-screen p-4 flex flex-col sticky top-0">
      <div className="mb-8 px-2 font-bold text-white text-lg flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center text-white text-xs">G</div>
          Gaatha OS
        </div>
        <NotificationCenter notifications={notifications} onRemove={removeNotification} onClear={clearNotifications} />
      </div>
      <nav className="flex-1 space-y-1">
        <Link to="/dashboard" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><LayoutDashboard size={18} /> Dashboard</Link>
        <Link to="/crm" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><Users size={18} /> CRM</Link>
        <Link to="/books" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><BookOpen size={18} /> Accounting</Link>
        <Link to="/invoices" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><Mail size={18} /> Invoices</Link>
        <Link to="/inventory" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><Package size={18} /> Inventory</Link>
        <Link to="/vendors" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><Briefcase size={18} /> Vendors</Link>
        <Link to="/payroll" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><Users size={18} /> Payroll</Link>
        <Link to="/employees" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><Users size={18} /> Employees</Link>
        <Link to="/attendance" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><Clock size={18} /> Attendance</Link>
        <Link to="/custom-fields" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><Settings size={18} /> Custom Fields</Link>
        <Link to="/performance" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><Star size={18} /> Performance</Link>
        <Link to="/pay" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><CreditCard size={18} /> Payments</Link>
        <Link to="/projects" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><Briefcase size={18} /> Projects</Link>
        <Link to="/desk" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded transition"><Headphones size={18} /> Helpdesk</Link>
        {(user.role === 'admin' || user.role === 'super_admin' || user.role === 'orgadmin' || user.role === 'superadmin') && (
          <>
            <Link to="/auth/users" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded text-blue-400 font-medium transition"><ShieldCheck size={18} /> Manage Users</Link>
            <Link to="/settings" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded text-blue-400 font-medium transition"><Settings size={18} /> Organization Settings</Link>
            <Link to="/departments" className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded text-blue-400 font-medium transition"><Building2 size={18} /> Departments</Link>
          </>
        )}
      </nav>

      <div className="mt-auto pt-4 border-t border-slate-800">
        <div className="px-4 py-1 text-[10px] uppercase text-slate-500 font-bold tracking-wider">{user.role}</div>
        <Link to="/auth/profile" className="flex items-center gap-3 px-4 py-2 text-sm text-slate-100 mb-2 hover:text-blue-400 transition"><User size={16} /> {user.username}</Link>
        <button onClick={logout} className="flex items-center gap-3 w-full text-left px-4 py-2 hover:bg-red-900/50 hover:text-red-200 rounded transition text-sm"><LogOut size={16} /> Logout</button>
      </div>
    </aside>
  );
};

const Layout = ({ children }) => {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 min-h-screen">{children}</main>
    </div>
  );
};

const App = () => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BetaBanner />
        <Router>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/auth/login" element={<LoginPage />} />
            <Route path="/auth/register" element={<RegisterPage />} />
            <Route path="/auth/register/success" element={<SignupSuccessPage />} />
            <Route path="/privacy" element={<ModulePage moduleName="Privacy Policy" />} />
            <Route path="/terms" element={<ModulePage moduleName="Terms of Service" />} />
            <Route path="/modules" element={<ModulesPage />} />

            <Route element={<ProtectedRoute />}>
              <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
              <Route path="/superadmin/dashboard" element={<Layout><SuperadminDashboard /></Layout>} />
              <Route path="/crm" element={<Layout><CRMHub /></Layout>} />
              <Route path="/books" element={<Layout><AccountingPage /></Layout>} />
              <Route path="/invoices" element={<Layout><InvoicesPage /></Layout>} />
              <Route path="/inventory" element={<Layout><InventoryPage /></Layout>} />
              <Route path="/vendors" element={<Layout><VendorManagementPage /></Layout>} />
              <Route path="/payroll" element={<Layout><PayrollPage /></Layout>} />
              <Route path="/employees" element={<Layout><EmployeesPage /></Layout>} />
              <Route path="/attendance" element={<Layout><AttendancePage /></Layout>} />
              <Route path="/performance" element={<Layout><PerformancePage /></Layout>} />
              <Route path="/pay" element={<Layout><PaymentsPage /></Layout>} />
              <Route path="/projects" element={<Layout><ProjectsPage /></Layout>} />
              <Route path="/desk" element={<Layout><HelpdeskPage /></Layout>} />
              <Route path="/auth/profile" element={<Layout><ProfilePage /></Layout>} />
              <Route path="/settings" element={<Layout><OrganizationSettingsPage /></Layout>} />
              <Route path="/auth/users" element={<Layout><UsersListPage /></Layout>} />
              <Route path="/custom-fields" element={<Layout><CustomFieldsPage /></Layout>} />
              <Route path="/departments" element={<Layout><DepartmentsPage /></Layout>} />
            </Route>

            <Route path="*" element={<LandingPage />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
};

const rootElement = document.getElementById('root');
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<App />);
} else {
  console.error('React root element not found');
}
