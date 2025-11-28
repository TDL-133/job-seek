import { Link, Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { Briefcase, Target, Sparkles, Mail } from 'lucide-react';

export default function Landing() {
  const { isAuthenticated, profile } = useAuthStore();
  
  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to={profile ? '/dashboard' : '/onboarding'} replace />;
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-primary-50">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-4">
        <span className="text-2xl font-bold text-primary-600">Job Seek</span>
        <div className="flex gap-3">
          <Link to="/login" className="btn-secondary">
            Se connecter
          </Link>
          <Link to="/register" className="btn-primary">
            Créer un compte
          </Link>
        </div>
      </header>
      
      {/* Hero */}
      <main className="max-w-6xl mx-auto px-8 py-20">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-neutral-900 mb-6">
            Trouve les offres qui te<br />
            <span className="text-primary-600">correspondent vraiment</span>
          </h1>
          <p className="text-xl text-neutral-600 mb-10 max-w-2xl mx-auto">
            Assistant intelligent de recherche d'emploi avec analyse de CV, 
            scoring personnalisé et génération de lettres de motivation.
          </p>
          <Link to="/register" className="btn-primary text-lg px-8 py-3">
            Commencer gratuitement
          </Link>
        </div>
        
        {/* Features */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="card-hover">
            <div className="w-12 h-12 rounded-lg bg-primary-100 flex items-center justify-center mb-4">
              <Briefcase className="h-6 w-6 text-primary-600" />
            </div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">
              Multi-plateformes
            </h3>
            <p className="text-neutral-600 text-sm">
              Agrège les offres de LinkedIn, Indeed, Glassdoor et Welcome to the Jungle.
            </p>
          </div>
          
          <div className="card-hover">
            <div className="w-12 h-12 rounded-lg bg-primary-100 flex items-center justify-center mb-4">
              <Target className="h-6 w-6 text-primary-600" />
            </div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">
              Scoring intelligent
            </h3>
            <p className="text-neutral-600 text-sm">
              Chaque offre est notée selon tes critères pondérés personnalisés.
            </p>
          </div>
          
          <div className="card-hover">
            <div className="w-12 h-12 rounded-lg bg-primary-100 flex items-center justify-center mb-4">
              <Sparkles className="h-6 w-6 text-primary-600" />
            </div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">
              IA générative
            </h3>
            <p className="text-neutral-600 text-sm">
              Analyse ton CV et génère des lettres de motivation personnalisées.
            </p>
          </div>
          
          <div className="card-hover">
            <div className="w-12 h-12 rounded-lg bg-primary-100 flex items-center justify-center mb-4">
              <Mail className="h-6 w-6 text-primary-600" />
            </div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">
              Alertes quotidiennes
            </h3>
            <p className="text-neutral-600 text-sm">
              Reçois chaque matin les nouvelles offres qui correspondent à ton profil.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
