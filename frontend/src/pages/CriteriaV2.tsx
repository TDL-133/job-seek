import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { scoringPreferencesApi, profileApi, type ScoringPreferences } from '../services/api';
import { 
  Loader2, MapPin, Briefcase, DollarSign, Sparkles, 
  AlertTriangle, Target, X, Plus, Check, RotateCcw
} from 'lucide-react';

const SENIORITY_LEVELS = [
  { value: 'junior', label: 'Junior', points: 8, emoji: '🌱' },
  { value: 'mid', label: 'PM', points: 15, emoji: '💼' },
  { value: 'senior', label: 'Senior', points: 25, emoji: '⭐' },
  { value: 'head', label: 'Head/VP', points: 35, emoji: '👑' },
] as const;

const DEFAULT_SOURCES = [
  { id: 'linkedin', name: 'LinkedIn', emoji: '🔗' },
  { id: 'indeed', name: 'Indeed', emoji: '📋' },
  { id: 'glassdoor', name: 'Glassdoor', emoji: '🚪' },
  { id: 'welcometothejungle', name: 'WTTJ', emoji: '🌴' },
];

export default function CriteriaV2() {
  const navigate = useNavigate();
  const [preferences, setPreferences] = useState<ScoringPreferences | null>(null);
  const [cvSkills, setCvSkills] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [newSkill, setNewSkill] = useState('');
  
  useEffect(() => {
    loadData();
  }, []);
  
  const loadData = async () => {
    try {
      const [prefsData, profileData] = await Promise.all([
        scoringPreferencesApi.get(),
        profileApi.get()
      ]);
      setPreferences(prefsData);
      if (profileData?.skills) {
        setCvSkills(Array.isArray(profileData.skills) ? profileData.skills : []);
      }
    } catch (err: any) {
      setError('Erreur lors du chargement des préférences');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const updatePreference = async (key: keyof ScoringPreferences, value: any) => {
    if (!preferences) return;
    
    // Optimistic update
    setPreferences({ ...preferences, [key]: value });
    
    try {
      setSaving(true);
      const updated = await scoringPreferencesApi.update({ [key]: value });
      setPreferences(updated);
    } catch (err) {
      // Revert on error
      loadData();
      setError('Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };
  
  const toggleSource = async (sourceId: string) => {
    if (!preferences) return;
    
    const currentTrust = preferences.trusted_sources[sourceId] ?? true;
    const newSources = { ...preferences.trusted_sources, [sourceId]: !currentTrust };
    
    setPreferences({ ...preferences, trusted_sources: newSources });
    
    try {
      setSaving(true);
      await scoringPreferencesApi.toggleSource(sourceId, !currentTrust);
    } catch (err) {
      loadData();
      setError('Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };
  
  const addPrioritySkill = async () => {
    if (!newSkill.trim() || !preferences) return;
    
    try {
      setSaving(true);
      const updated = await scoringPreferencesApi.addSkill(newSkill.trim());
      setPreferences(updated);
      setNewSkill('');
    } catch (err) {
      setError('Erreur lors de l\'ajout de la compétence');
    } finally {
      setSaving(false);
    }
  };
  
  const removePrioritySkill = async (skill: string) => {
    try {
      setSaving(true);
      const updated = await scoringPreferencesApi.removeSkill(skill);
      setPreferences(updated);
    } catch (err) {
      setError('Erreur lors de la suppression');
    } finally {
      setSaving(false);
    }
  };
  
  const resetPreferences = async () => {
    if (!confirm('Réinitialiser toutes les préférences ?')) return;
    
    try {
      setSaving(true);
      const updated = await scoringPreferencesApi.reset();
      setPreferences(updated);
    } catch (err) {
      setError('Erreur lors de la réinitialisation');
    } finally {
      setSaving(false);
    }
  };
  
  const calculatePreviewScore = () => {
    if (!preferences) return 0;
    
    // Role points
    const rolePoints = SENIORITY_LEVELS.find(s => s.value === preferences.target_seniority)?.points || 15;
    
    // Geo points (assume remote for preview)
    const geoPoints = 25;
    
    // Salary points
    let salaryPoints = 7;
    if (preferences.min_salary >= 80000) salaryPoints = 15;
    else if (preferences.min_salary >= 60000) salaryPoints = 10;
    else if (preferences.min_salary >= 50000) salaryPoints = 5;
    
    // Skills (estimate based on configured skills)
    const totalSkills = cvSkills.length + (preferences.priority_skills?.length || 0);
    let skillPoints = 10;
    if (totalSkills >= 10) skillPoints = 20;
    else if (totalSkills >= 5) skillPoints = 15;
    
    // Attractiveness (assume medium)
    const attractivenessPoints = 6;
    
    // No penalties for preview
    const penalties = 0;
    
    return rolePoints + geoPoints + salaryPoints + skillPoints + attractivenessPoints + penalties;
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
  
  if (!preferences) {
    return (
      <MainLayout>
        <div className="text-center py-12">
          <p className="text-red-600">{error || 'Impossible de charger les préférences'}</p>
          <button onClick={loadData} className="btn-primary mt-4">Réessayer</button>
        </div>
      </MainLayout>
    );
  }
  
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">🎯 Configure ton scoring</h1>
            <p className="text-neutral-600 mt-1">
              Système de points fixes pour matcher les offres PM
            </p>
          </div>
          <button
            onClick={resetPreferences}
            className="btn-secondary flex items-center gap-2 text-sm"
            disabled={saving}
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </button>
        </div>
        
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm flex items-center justify-between">
            {error}
            <button onClick={() => setError('')}><X className="h-4 w-4" /></button>
          </div>
        )}
        
        {saving && (
          <div className="fixed top-4 right-4 bg-primary-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 z-50">
            <Loader2 className="h-4 w-4 animate-spin" />
            Sauvegarde...
          </div>
        )}
        
        <div className="space-y-6">
          {/* 1. Role/Seniority (35 pts) */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                <Briefcase className="h-5 w-5 text-primary-600" />
              </div>
              <div>
                <h3 className="font-semibold text-neutral-900">🎭 Role / Seniority</h3>
                <p className="text-sm text-neutral-500">35 points max</p>
              </div>
            </div>
            
            <div className="grid grid-cols-4 gap-3">
              {SENIORITY_LEVELS.map((level) => (
                <button
                  key={level.value}
                  onClick={() => updatePreference('target_seniority', level.value)}
                  className={`p-4 rounded-xl border-2 transition-all text-center ${
                    preferences.target_seniority === level.value
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-neutral-200 hover:border-primary-300'
                  }`}
                >
                  <div className="text-2xl mb-1">{level.emoji}</div>
                  <div className="font-medium text-neutral-900">{level.label}</div>
                  <div className="text-sm text-primary-600 font-semibold">{level.points} pts</div>
                </button>
              ))}
            </div>
            
            <p className="text-xs text-neutral-400 mt-3">
              Le système détecte automatiquement le niveau du poste dans le titre de l'offre
            </p>
          </div>
          
          {/* 2. Geography (25 pts) */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <MapPin className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-neutral-900">🌍 Géographie / Remote</h3>
                <p className="text-sm text-neutral-500">25 points max</p>
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Ville préférée
              </label>
              <input
                type="text"
                value={preferences.preferred_city}
                onChange={(e) => updatePreference('preferred_city', e.target.value)}
                placeholder="Ex: Toulouse, Paris, Lyon..."
                className="input-field"
              />
            </div>
            
            <div className="bg-neutral-50 rounded-lg p-4">
              <div className="text-sm text-neutral-600 space-y-2">
                <div className="flex justify-between">
                  <span>🏠 Full remote</span>
                  <span className="font-semibold text-green-600">25 pts</span>
                </div>
                <div className="flex justify-between">
                  <span>🏢 Bureau dans ta ville</span>
                  <span className="font-semibold text-blue-600">20 pts</span>
                </div>
                <div className="flex justify-between">
                  <span>🚗 Hybride autre ville</span>
                  <span className="font-semibold text-amber-600">15 pts</span>
                </div>
                <div className="flex justify-between">
                  <span>📍 Bureau autre ville</span>
                  <span className="font-semibold text-neutral-500">10 pts</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* 3. Salary (15 pts) */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                <DollarSign className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-neutral-900">💰 Salaire</h3>
                <p className="text-sm text-neutral-500">15 points max</p>
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Salaire minimum attendu (€/an)
              </label>
              <input
                type="number"
                value={preferences.min_salary}
                onChange={(e) => updatePreference('min_salary', parseInt(e.target.value) || 0)}
                placeholder="60000"
                step="5000"
                min="0"
                max="500000"
                className="input-field"
              />
            </div>
            
            <div className="bg-neutral-50 rounded-lg p-4">
              <div className="text-sm text-neutral-600 space-y-2">
                <div className="flex justify-between">
                  <span>€80k+</span>
                  <span className="font-semibold text-green-600">15 pts</span>
                </div>
                <div className="flex justify-between">
                  <span>€60k - €80k</span>
                  <span className="font-semibold text-blue-600">10-15 pts</span>
                </div>
                <div className="flex justify-between">
                  <span>€50k - €60k</span>
                  <span className="font-semibold text-amber-600">5-10 pts</span>
                </div>
                <div className="flex justify-between">
                  <span>&lt;€50k</span>
                  <span className="font-semibold text-neutral-500">0-5 pts</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* 4. Skills (20 pts) */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                <Target className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-neutral-900">🎯 Compétences</h3>
                <p className="text-sm text-neutral-500">20 points max</p>
              </div>
            </div>
            
            {/* CV Skills */}
            {cvSkills.length > 0 && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Depuis ton CV ({cvSkills.length})
                </label>
                <div className="flex flex-wrap gap-2">
                  {cvSkills.slice(0, 10).map((skill) => (
                    <span
                      key={skill}
                      className="px-3 py-1 bg-neutral-100 text-neutral-700 rounded-full text-sm"
                    >
                      {skill}
                    </span>
                  ))}
                  {cvSkills.length > 10 && (
                    <span className="px-3 py-1 bg-neutral-50 text-neutral-500 rounded-full text-sm">
                      +{cvSkills.length - 10} autres
                    </span>
                  )}
                </div>
              </div>
            )}
            
            {/* Priority Skills */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Compétences prioritaires
              </label>
              <div className="flex flex-wrap gap-2 mb-3">
                {preferences.priority_skills.map((skill) => (
                  <span
                    key={skill}
                    className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm flex items-center gap-1"
                  >
                    {skill}
                    <button
                      onClick={() => removePrioritySkill(skill)}
                      className="hover:text-primary-900"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
              
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addPrioritySkill()}
                  placeholder="Ajouter une compétence..."
                  className="input-field flex-1"
                />
                <button
                  onClick={addPrioritySkill}
                  disabled={!newSkill.trim()}
                  className="btn-primary px-4"
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>
            </div>
            
            <div className="bg-neutral-50 rounded-lg p-4">
              <div className="text-sm text-neutral-600 space-y-2">
                <div className="flex justify-between">
                  <span>10+ compétences matchées</span>
                  <span className="font-semibold text-green-600">20 pts</span>
                </div>
                <div className="flex justify-between">
                  <span>5 compétences matchées</span>
                  <span className="font-semibold text-blue-600">15 pts</span>
                </div>
                <div className="flex justify-between">
                  <span>2 compétences matchées</span>
                  <span className="font-semibold text-amber-600">10 pts</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* 5. Attractiveness (10 pts) */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                <Sparkles className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <h3 className="font-semibold text-neutral-900">✨ Attractivité</h3>
                <p className="text-sm text-neutral-500">10 points max</p>
              </div>
            </div>
            
            <p className="text-sm text-neutral-600 mb-4">
              Le système détecte automatiquement les entreprises attractives via des mots-clés dans les descriptions.
            </p>
            
            <div className="bg-neutral-50 rounded-lg p-4">
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-medium text-green-700">🚀 Mission-driven / Hot tech (10 pts)</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {['AI', 'ML', 'Climate', 'Impact', 'Healthtech', 'Unicorn', 'Series B/C'].map(kw => (
                      <span key={kw} className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">{kw}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-medium text-blue-700">📈 Startup en croissance (6 pts)</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {['Startup', 'Scale-up', 'Series A', 'Fintech', 'Fast-growing'].map(kw => (
                      <span key={kw} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">{kw}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm">
                    <span className="font-medium text-neutral-500">🏢 Entreprise classique (2 pts)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* 6. Sources / Penalties */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <h3 className="font-semibold text-neutral-900">📡 Sources & Pénalités</h3>
                <p className="text-sm text-neutral-500">-10 points max</p>
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-neutral-700 mb-3">
                Sources de confiance
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {DEFAULT_SOURCES.map((source) => {
                  const isTrusted = preferences.trusted_sources[source.id] ?? true;
                  return (
                    <button
                      key={source.id}
                      onClick={() => toggleSource(source.id)}
                      className={`p-3 rounded-xl border-2 transition-all flex items-center gap-2 ${
                        isTrusted
                          ? 'border-green-500 bg-green-50'
                          : 'border-red-300 bg-red-50'
                      }`}
                    >
                      <span className="text-xl">{source.emoji}</span>
                      <span className="font-medium text-sm">{source.name}</span>
                      {isTrusted ? (
                        <Check className="h-4 w-4 text-green-600 ml-auto" />
                      ) : (
                        <X className="h-4 w-4 text-red-600 ml-auto" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
            
            <div className="bg-neutral-50 rounded-lg p-4">
              <div className="text-sm text-neutral-600 space-y-2">
                <div className="flex justify-between">
                  <span>❌ Pas de date de publication</span>
                  <span className="font-semibold text-red-600">-5 pts</span>
                </div>
                <div className="flex justify-between">
                  <span>📝 Description trop courte</span>
                  <span className="font-semibold text-red-600">-3 pts</span>
                </div>
                <div className="flex justify-between">
                  <span>⚠️ Source non fiable</span>
                  <span className="font-semibold text-red-600">-2 pts</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Preview & Action */}
        <div className="mt-8 p-6 bg-gradient-to-r from-primary-50 to-primary-100 rounded-xl">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-primary-900 mb-1">Score estimé pour un job idéal</h3>
              <p className="text-sm text-primary-700">
                {preferences.target_seniority === 'head' ? 'Head/VP' : 
                 preferences.target_seniority === 'senior' ? 'Senior PM' : 
                 preferences.target_seniority === 'mid' ? 'Product Manager' : 'Junior PM'}
                {preferences.preferred_city && ` @ ${preferences.preferred_city}`}
                {' '}remote avec {cvSkills.length + preferences.priority_skills.length} skills
              </p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold text-primary-700">
                ~{calculatePreviewScore()}
              </div>
              <div className="text-sm text-primary-600">/ 100 pts</div>
            </div>
          </div>
        </div>
        
        {/* Navigation */}
        <div className="mt-8 flex justify-between">
          <button
            onClick={() => navigate('/profile')}
            className="btn-secondary py-3 px-6"
          >
            ← Retour au profil
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="btn-primary py-3 px-8"
          >
            Voir les offres →
          </button>
        </div>
      </div>
    </MainLayout>
  );
}
