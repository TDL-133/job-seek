import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { api } from '../services/api';
import type { ScoringCriteria } from '../types';
import { 
  Loader2, MapPin, Briefcase, DollarSign, Building2, 
  Sparkles, Clock, Users, Shield, Target, ChevronDown, ChevronUp 
} from 'lucide-react';

const CRITERIA_ICONS: Record<string, any> = {
  location: MapPin,
  contract_type: Briefcase,
  salary: DollarSign,
  company_size: Building2,
  skills_match: Sparkles,
  experience_level: Clock,
  remote_work: Users,
  industry: Building2,
  benefits: Shield,
  growth_potential: Target,
};

const CRITERIA_LABELS: Record<string, string> = {
  location: 'Localisation',
  contract_type: 'Type de contrat',
  salary: 'Salaire',
  company_size: 'Taille entreprise',
  skills_match: 'Match compétences',
  experience_level: 'Niveau d\'expérience',
  remote_work: 'Télétravail',
  industry: 'Secteur d\'activité',
  benefits: 'Avantages',
  growth_potential: 'Potentiel de croissance',
};

const CRITERIA_DESCRIPTIONS: Record<string, string> = {
  location: 'Proximité avec ton lieu de résidence ou ta zone préférée',
  contract_type: 'CDI, CDD, Freelance, Stage...',
  salary: 'Fourchette salariale correspondant à tes attentes',
  company_size: 'Startup, PME, Grande entreprise...',
  skills_match: 'Correspondance entre tes compétences et celles demandées',
  experience_level: 'Niveau d\'expérience requis vs le tien',
  remote_work: 'Possibilité de télétravail (full remote, hybride)',
  industry: 'Secteur d\'activité de l\'entreprise',
  benefits: 'RTT, tickets restaurant, mutuelle, stock options...',
  growth_potential: 'Opportunités d\'évolution et de formation',
};

export default function Criteria() {
  const navigate = useNavigate();
  const [criteria, setCriteria] = useState<ScoringCriteria[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedCriteria, setExpandedCriteria] = useState<string | null>(null);
  
  useEffect(() => {
    loadCriteria();
  }, []);
  
  const loadCriteria = async () => {
    try {
      const data = await api.criteria.list();
      setCriteria(data);
    } catch (err: any) {
      setError('Erreur lors du chargement des critères');
    } finally {
      setLoading(false);
    }
  };
  
  const handleToggle = async (criterion: ScoringCriteria) => {
    const updated = { ...criterion, enabled: !criterion.enabled };
    setCriteria(criteria.map(c => c.id === criterion.id ? updated : c));
    
    try {
      await api.criteria.update(criterion.id, { enabled: updated.enabled });
    } catch (err) {
      // Revert on error
      setCriteria(criteria.map(c => c.id === criterion.id ? criterion : c));
    }
  };
  
  const handleImportanceChange = async (criterion: ScoringCriteria, value: number) => {
    const updated = { ...criterion, importance: value };
    setCriteria(criteria.map(c => c.id === criterion.id ? updated : c));
  };
  
  const handleImportanceCommit = async (criterion: ScoringCriteria) => {
    try {
      await api.criteria.update(criterion.id, { importance: criterion.importance });
    } catch (err) {
      setError('Erreur lors de la sauvegarde');
    }
  };
  
  const handleContinue = () => {
    navigate('/dashboard');
  };
  
  const getImportanceLabel = (value: number) => {
    if (value <= 20) return 'Peu important';
    if (value <= 40) return 'Assez important';
    if (value <= 60) return 'Important';
    if (value <= 80) return 'Très important';
    return 'Essentiel';
  };
  
  const getImportanceColor = (value: number) => {
    if (value <= 20) return 'bg-neutral-300';
    if (value <= 40) return 'bg-blue-400';
    if (value <= 60) return 'bg-primary-400';
    if (value <= 80) return 'bg-primary-500';
    return 'bg-primary-600';
  };
  
  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        </div>
      </MainLayout>
    );
  }
  
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        {/* Progress indicator */}
        <div className="flex items-center justify-center mb-8">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center font-semibold">✓</div>
            <div className="w-16 h-1 bg-primary-600 rounded"></div>
            <div className="w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center font-semibold">✓</div>
            <div className="w-16 h-1 bg-primary-600 rounded"></div>
            <div className="w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center font-semibold">3</div>
          </div>
        </div>
        
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-neutral-900">Configure tes critères</h1>
          <p className="text-neutral-600 mt-1">
            Active les critères qui comptent pour toi et ajuste leur importance pour un matching personnalisé.
          </p>
        </div>
        
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm">
            {error}
          </div>
        )}
        
        <div className="space-y-4">
          {criteria.map((criterion) => {
            const Icon = CRITERIA_ICONS[criterion.name] || Target;
            const isExpanded = expandedCriteria === criterion.id;
            
            return (
              <div
                key={criterion.id}
                className={`card transition-all ${criterion.enabled ? 'border-primary-200' : 'border-neutral-200 opacity-60'}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center flex-1 min-w-0">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center mr-4 ${criterion.enabled ? 'bg-primary-100' : 'bg-neutral-100'}`}>
                      <Icon className={`h-5 w-5 ${criterion.enabled ? 'text-primary-600' : 'text-neutral-400'}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-neutral-900">
                        {CRITERIA_LABELS[criterion.name] || criterion.name}
                      </h3>
                      <p className="text-sm text-neutral-500 truncate">
                        {CRITERIA_DESCRIPTIONS[criterion.name]}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4 ml-4">
                    {criterion.enabled && (
                      <div className="hidden sm:flex items-center gap-2 text-sm">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          criterion.importance >= 80 ? 'bg-primary-100 text-primary-700' :
                          criterion.importance >= 60 ? 'bg-primary-50 text-primary-600' :
                          'bg-neutral-100 text-neutral-600'
                        }`}>
                          {getImportanceLabel(criterion.importance)}
                        </span>
                      </div>
                    )}
                    
                    {/* Toggle */}
                    <button
                      onClick={() => handleToggle(criterion)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        criterion.enabled ? 'bg-primary-600' : 'bg-neutral-300'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          criterion.enabled ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                    
                    {criterion.enabled && (
                      <button
                        onClick={() => setExpandedCriteria(isExpanded ? null : criterion.id)}
                        className="p-1 hover:bg-neutral-100 rounded"
                      >
                        {isExpanded ? (
                          <ChevronUp className="h-5 w-5 text-neutral-400" />
                        ) : (
                          <ChevronDown className="h-5 w-5 text-neutral-400" />
                        )}
                      </button>
                    )}
                  </div>
                </div>
                
                {/* Expanded slider section */}
                {criterion.enabled && isExpanded && (
                  <div className="mt-4 pt-4 border-t border-neutral-100">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-neutral-600">Importance</span>
                      <span className="text-sm font-medium text-primary-600">
                        {criterion.importance}%
                      </span>
                    </div>
                    <div className="relative">
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={criterion.importance}
                        onChange={(e) => handleImportanceChange(criterion, parseInt(e.target.value))}
                        onMouseUp={() => handleImportanceCommit(criterion)}
                        onTouchEnd={() => handleImportanceCommit(criterion)}
                        className="w-full h-2 bg-neutral-200 rounded-lg appearance-none cursor-pointer slider-thumb"
                      />
                      <div 
                        className={`absolute top-0 left-0 h-2 rounded-lg pointer-events-none ${getImportanceColor(criterion.importance)}`}
                        style={{ width: `${criterion.importance}%` }}
                      />
                    </div>
                    <div className="flex justify-between mt-1">
                      <span className="text-xs text-neutral-400">Peu important</span>
                      <span className="text-xs text-neutral-400">Essentiel</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        
        {/* Summary */}
        <div className="mt-8 p-4 bg-primary-50 rounded-xl">
          <h3 className="font-medium text-primary-900 mb-2">Résumé de ta configuration</h3>
          <div className="flex flex-wrap gap-2">
            {criteria.filter(c => c.enabled).length === 0 ? (
              <p className="text-sm text-primary-700">Aucun critère activé. Active au moins un critère pour commencer.</p>
            ) : (
              criteria
                .filter(c => c.enabled)
                .sort((a, b) => b.importance - a.importance)
                .map(c => (
                  <span
                    key={c.id}
                    className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${
                      c.importance >= 80 ? 'bg-primary-200 text-primary-800' :
                      c.importance >= 60 ? 'bg-primary-100 text-primary-700' :
                      'bg-white text-neutral-600'
                    }`}
                  >
                    {CRITERIA_LABELS[c.name] || c.name}
                    <span className="ml-1 text-xs opacity-70">{c.importance}%</span>
                  </span>
                ))
            )}
          </div>
        </div>
        
        {/* Continue button */}
        <div className="mt-8 flex justify-between">
          <button
            onClick={() => navigate('/profile')}
            className="btn-secondary py-3 px-6"
          >
            Retour au profil
          </button>
          <button
            onClick={handleContinue}
            disabled={criteria.filter(c => c.enabled).length === 0}
            className="btn-primary py-3 px-8"
          >
            Voir les offres
          </button>
        </div>
      </div>
    </MainLayout>
  );
}
