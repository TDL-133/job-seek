import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Briefcase, 
  FileText, 
  Building2, 
  Settings, 
  SlidersHorizontal,
  Ban,
  LogOut,
  User
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

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
