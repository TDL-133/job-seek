import { useState } from 'react';
import { Link, useNavigate, Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { Loader2 } from 'lucide-react';

export default function Register() {
  const navigate = useNavigate();
  const { register, isAuthenticated, isLoading, error, clearError } = useAuthStore();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [validationError, setValidationError] = useState('');
  
  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/onboarding" replace />;
  }
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setValidationError('');
    
    if (password !== confirmPassword) {
      setValidationError('Les mots de passe ne correspondent pas');
      return;
    }
    
    if (password.length < 8) {
      setValidationError('Le mot de passe doit contenir au moins 8 caractères');
      return;
    }
    
    try {
      await register(email, password, fullName);
      navigate('/onboarding');
    } catch (err) {
      // Error is handled in the store
    }
  };
  
  const displayError = validationError || error;
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-neutral-50 to-primary-50 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="text-2xl font-bold text-primary-600">
            Job Seek
          </Link>
          <h1 className="mt-6 text-3xl font-bold text-neutral-900">
            Crée ton compte
          </h1>
          <p className="mt-2 text-neutral-600">
            Trouve ton prochain job en quelques clics.
          </p>
        </div>
        
        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-5">
            {displayError && (
              <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">
                {displayError}
              </div>
            )}
            
            <div>
              <label htmlFor="fullName" className="label">Nom complet</label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="input"
                placeholder="Jean Dupont"
                required
              />
            </div>
            
            <div>
              <label htmlFor="email" className="label">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="ton@email.com"
                required
              />
            </div>
            
            <div>
              <label htmlFor="password" className="label">Mot de passe</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
                required
              />
              <p className="mt-1 text-xs text-neutral-500">Minimum 8 caractères</p>
            </div>
            
            <div>
              <label htmlFor="confirmPassword" className="label">Confirmer le mot de passe</label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
                required
              />
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full py-3"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin mr-2" />
                  Création...
                </>
              ) : (
                'Créer mon compte'
              )}
            </button>
          </form>
          
          <p className="mt-6 text-center text-sm text-neutral-600">
            Déjà un compte ?{' '}
            <Link to="/login" className="text-primary-600 font-medium hover:text-primary-700">
              Se connecter
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
