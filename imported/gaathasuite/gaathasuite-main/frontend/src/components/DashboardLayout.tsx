import React, { useState, useRef, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Users, 
  Package, 
  BookOpen, 
  Settings, 
  Bell, 
  Search,
  LogOut,
  Menu
} from 'lucide-react';
import { Text } from '../../../Text';
import { NoraChat } from '../components/NoraChat';

interface SearchResult {
  id: string;
  title: string;
  subtitle: string;
  type: 'Customer' | 'Invoice';
}

const MOCK_RESULTS: SearchResult[] = [];

const NavItem = ({ icon: Icon, label, active = false }: { icon: any, label: string, active?: boolean }) => (
  <div className={`flex items-center gap-3 px-4 py-3 rounded-lg cursor-pointer transition-colors ${
    active ? 'bg-gaatha-blue-600 text-white' : 'text-gaatha-gray-600 hover:bg-gaatha-gray-100'
  }`}>
    <Icon size={20} />
    <span className="font-medium text-sm">{label}</span>
  </div>
);

export const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  const filteredResults = MOCK_RESULTS.filter(r => 
    r.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
    r.subtitle.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) setIsSearchOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="flex h-screen bg-gaatha-gray-50 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gaatha-gray-100 flex flex-col hidden md:flex">
        <div className="p-6 border-b border-gaatha-gray-100 flex items-center gap-2">
          <div className="w-8 h-8 bg-gaatha-blue-600 rounded-lg flex items-center justify-center text-white font-bold">G</div>
          <Text variant="h3" className="text-gaatha-gray-900 tracking-tight">Gaatha Suite</Text>
        </div>
        
        <nav className="flex-1 p-4 flex flex-col gap-1">
          <NavItem icon={LayoutDashboard} label="Dashboard" active />
          <NavItem icon={Users} label="CRM & Leads" />
          <NavItem icon={Package} label="Inventory" />
          <NavItem icon={BookOpen} label="Books & Finance" />
          <div className="mt-auto pt-4 border-t border-gaatha-gray-100">
            <NavItem icon={Settings} label="Settings" />
            <NavItem icon={LogOut} label="Logout" />
          </div>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {/* Top Navigation */}
        <header className="h-16 bg-white border-b border-gaatha-gray-100 flex items-center justify-between px-8 z-10">
          <div className="flex items-center gap-4 flex-1">
            <Menu className="md:hidden text-gaatha-gray-600" />
            <div className="relative w-full max-w-md hidden sm:block" ref={searchRef}>
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gaatha-gray-400" size={18} />
              <input 
                type="text" 
                placeholder="Search across Gaatha..." 
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearchOpen(true);
                }}
                onFocus={() => setIsSearchOpen(true)}
                className="w-full pl-10 pr-4 py-2 bg-gaatha-gray-50 border-none rounded-lg text-sm focus:ring-2 focus:ring-gaatha-blue-600 focus:bg-white transition-all"
              />

              {isSearchOpen && searchQuery.length > 0 && (
                <div className="absolute top-full left-0 w-full mt-2 bg-white rounded-xl shadow-2xl border border-gaatha-gray-100 overflow-hidden">
                  <div className="p-2 border-b border-gaatha-gray-50 bg-gaatha-gray-50/50">
                    <Text variant="small" className="font-bold text-gaatha-gray-400 px-2 uppercase tracking-widest text-[10px]">Quick Results</Text>
                  </div>
                  <div className="max-h-80 overflow-y-auto">
                    {filteredResults.length > 0 ? filteredResults.map(result => (
                      <div key={result.id} className="p-3 hover:bg-gaatha-gray-50 cursor-pointer flex items-center justify-between group transition-colors">
                        <div>
                          <Text variant="body" className="font-semibold group-hover:text-gaatha-blue-600">{result.title}</Text>
                          <Text variant="small" className="text-gaatha-gray-500">{result.subtitle}</Text>
                        </div>
                        <Text variant="small" className="bg-gaatha-blue-50 text-gaatha-blue-600 px-2 py-0.5 rounded uppercase font-bold text-[10px]">
                          {result.type}
                        </Text>
                      </div>
                    )) : <div className="p-4 text-center"><Text variant="small">No matches found for "{searchQuery}"</Text></div>}
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="relative">
              <Bell size={20} className="text-gaatha-gray-600 cursor-pointer" />
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-gaatha-danger rounded-full border-2 border-white"></span>
            </div>
            <div className="flex items-center gap-3 pl-6 border-l border-gaatha-gray-100">
              <div className="text-right">
                <Text variant="caption" className="block leading-none">User</Text>
                <Text variant="small" className="text-gaatha-blue-600">Signed in</Text>
              </div>
              <div className="w-10 h-10 bg-gaatha-blue-100 text-gaatha-blue-600 rounded-full flex items-center justify-center font-bold">
                JD
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto p-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </div>

        {/* Floating AI Assistant */}
        <NoraChat />
      </main>
    </div>
  );
};