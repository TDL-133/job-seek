import { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Briefcase, 
  FileText, 
  Building2, 
  Settings, 
  SlidersHorizontal,
  Ban,
  LogOut,
  User,
  ChevronDown,
  Search,
  X,
  MapPin
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { savedSearchesApi, type SavedSearch } from '../../services/api';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Offres', href: '/jobs', icon: Briefcase },
  { name: 'Candidatures', href: '/applications', icon: FileText },
  { name: 'Entreprises', href: '/companies', icon: Building2 },
];

const settings = [
  { name: 'Critères', href: '/criteria', icon: SlidersHorizontal },
  { name: 'Blacklist', href: '/blacklist', icon: Ban },
  { name: 'Paramètres', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  
  // Saved searches state
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [isSearchesOpen, setIsSearchesOpen] = useState(() => {
    return localStorage.getItem('sidebar_searches_open') === 'true';
  });
  
  // Load saved searches
  useEffect(() => {
    loadSavedSearches();
  }, []);
  
  // Persist toggle state
  useEffect(() => {
    localStorage.setItem('sidebar_searches_open', String(isSearchesOpen));
  }, [isSearchesOpen]);
  
  const loadSavedSearches = async () => {
    try {
      const response = await savedSearchesApi.list();
      setSavedSearches(response.searches);
    } catch (err) {
      console.error('Failed to load saved searches:', err);
    }
  };
  
  const handleSearchClick = async (search: SavedSearch) => {
    // Mark as used
    try {
      await savedSearchesApi.markUsed(search.id);
    } catch (err) {
      console.error('Failed to mark search as used:', err);
    }
    // Navigate to dashboard with search params
    navigate(`/dashboard?keywords=${encodeURIComponent(search.keywords)}&location=${encodeURIComponent(search.location)}`);
  };
  
  const handleDeleteSearch = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    try {
      await savedSearchesApi.delete(id);
      setSavedSearches(prev => prev.filter(s => s.id !== id));
    } catch (err) {
      console.error('Failed to delete search:', err);
    }
  };
  
  return (
    <div className="flex h-screen w-64 flex-col bg-white border-r border-neutral-200">
      {/* Logo */}
      <div className="flex h-16 items-center px-6 border-b border-neutral-100">
        <span className="text-xl font-bold text-primary-600">Job Seek</span>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        <div className="space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900'
                }`
              }
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </NavLink>
          ))}
        </div>
        
        {/* Mes Recherches - Collapsible Section */}
        <div className="pt-6">
          <button
            onClick={() => setIsSearchesOpen(!isSearchesOpen)}
            className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-neutral-400 uppercase tracking-wider hover:text-neutral-600 transition-colors"
          >
            <span className="flex items-center gap-2">
              <Search className="h-4 w-4" />
              Mes Recherches
              {savedSearches.length > 0 && (
                <span className="bg-primary-100 text-primary-700 text-xs px-1.5 py-0.5 rounded-full">
                  {savedSearches.length}
                </span>
              )}
            </span>
            <ChevronDown className={`h-4 w-4 transition-transform ${isSearchesOpen ? 'rotate-180' : ''}`} />
          </button>
          
          {isSearchesOpen && (
            <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
              {savedSearches.length === 0 ? (
                <p className="px-3 py-2 text-xs text-neutral-400 italic">
                  Aucune recherche sauvegardée
                </p>
              ) : (
                savedSearches.map((search) => (
                  <div
                    key={search.id}
                    onClick={() => handleSearchClick(search)}
                    className="group flex items-center justify-between px-3 py-2 rounded-lg text-sm cursor-pointer hover:bg-neutral-50 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-neutral-700 truncate">{search.name}</p>
                      <p className="text-xs text-neutral-400 flex items-center gap-1 truncate">
                        <MapPin className="h-3 w-3" />
                        {search.location}
                      </p>
                    </div>
                    <button
                      onClick={(e) => handleDeleteSearch(e, search.id)}
                      className="p-1 text-neutral-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Supprimer"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
        
        <div className="pt-6">
          <p className="px-3 text-xs font-semibold text-neutral-400 uppercase tracking-wider">
            Configuration
          </p>
          <div className="mt-2 space-y-1">
            {settings.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900'
                  }`
                }
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </NavLink>
            ))}
          </div>
        </div>
      </nav>
      
      {/* User section */}
      <div className="border-t border-neutral-200 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-primary-600">
            <User className="h-5 w-5" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-neutral-900 truncate">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="text-xs text-neutral-500 truncate">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="p-2 text-neutral-400 hover:text-neutral-600 rounded-lg hover:bg-neutral-100"
            title="Déconnexion"
          >
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
