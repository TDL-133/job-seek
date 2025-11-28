import { MainLayout } from '../components/layout/MainLayout';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';
import { User, Bell, LogOut, Trash2 } from 'lucide-react';

export default function Settings() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  
  const handleLogout = () => {
    logout();
    navigate('/');
  };
  
  return (
    <MainLayout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-neutral-900 mb-6">Paramètres</h1>
        
        <div className="space-y-6">
          {/* Account */}
          <div className="card">
            <div className="flex items-center mb-4">
              <User className="h-5 w-5 text-primary-600 mr-2" />
              <h2 className="text-lg font-semibold">Compte</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="label">Email</label>
                <p className="text-neutral-900">{user?.email || 'Non connecté'}</p>
              </div>
              
              <div>
                <label className="label">Nom</label>
                <p className="text-neutral-900">{user?.full_name || 'Non renseigné'}</p>
              </div>
            </div>
          </div>
          
          {/* Notifications */}
          <div className="card">
            <div className="flex items-center mb-4">
              <Bell className="h-5 w-5 text-primary-600 mr-2" />
              <h2 className="text-lg font-semibold">Notifications</h2>
            </div>
            
            <div className="space-y-4">
              <label className="flex items-center justify-between cursor-pointer">
                <div>
                  <p className="font-medium text-neutral-900">Alertes email</p>
                  <p className="text-sm text-neutral-500">Reçois des alertes quand de nouvelles offres correspondent à tes critères</p>
                </div>
                <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-neutral-300">
                  <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-1" />
                </button>
              </label>
              
              <label className="flex items-center justify-between cursor-pointer">
                <div>
                  <p className="font-medium text-neutral-900">Résumé hebdomadaire</p>
                  <p className="text-sm text-neutral-500">Reçois un récapitulatif des meilleures offres chaque semaine</p>
                </div>
                <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-neutral-300">
                  <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-1" />
                </button>
              </label>
            </div>
          </div>
          
          {/* Danger zone */}
          <div className="card border-red-200">
            <h2 className="text-lg font-semibold text-red-600 mb-4">Zone de danger</h2>
            
            <div className="space-y-4">
              <button
                onClick={handleLogout}
                className="btn-secondary w-full text-neutral-700 hover:text-neutral-900"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Se déconnecter
              </button>
              
              <button
                className="btn-secondary w-full text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Supprimer mon compte
              </button>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
