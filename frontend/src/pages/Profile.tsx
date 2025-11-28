import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { api } from '../services/api';
import type { UserProfile, Experience } from '../types';
import { Loader2, Briefcase, Code, Languages, Sparkles, Edit2, Save, X, Plus } from 'lucide-react';

export default function Profile() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(false);
  
  // Editable fields
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [skills, setSkills] = useState<string[]>([]);
  const [newSkill, setNewSkill] = useState('');
  const [languages, setLanguages] = useState<string[]>([]);
  const [newLanguage, setNewLanguage] = useState('');
  const [experiences, setExperiences] = useState<Experience[]>([]);
  
  useEffect(() => {
    loadProfile();
  }, []);
  
  const loadProfile = async () => {
    try {
      const data = await api.profile.getProfile();
      if (!data) {
        navigate('/onboarding');
        return;
      }
      setProfile(data);
      // Initialize editable fields - map backend fields to frontend
      setTitle(data.latest_job_title || '');
      setSummary(data.ai_description || '');
      setSkills(data.skills || []);
      // Languages from backend are objects {language, level}, extract just language names
      const langNames = (data.languages || []).map((l: any) => 
        typeof l === 'string' ? l : l.language || l
      );
      setLanguages(langNames);
      // Experiences from backend have different field names
      const mappedExps = (data.experiences || []).map((e: any) => ({
        title: e.poste || e.title || '',
        company: e.entreprise || e.company || '',
        start_date: e.date_debut || e.start_date || e.dates || '',
        end_date: e.date_fin || e.end_date || '',
        location: e.lieu || e.location || '',
        description: e.description || '',
      }));
      setExperiences(mappedExps);
    } catch (err: any) {
      if (err.response?.status === 404) {
        // No profile yet, redirect to onboarding
        navigate('/onboarding');
      } else {
        setError('Erreur lors du chargement du profil');
      }
    } finally {
      setLoading(false);
    }
  };
  
  const handleSave = async () => {
    setSaving(true);
    setError('');
    
    try {
      const updatedProfile = await api.profile.updateProfile({
        title,
        summary,
        skills,
        languages,
        experiences,
      });
      setProfile(updatedProfile);
      setEditMode(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };
  
  const addSkill = () => {
    if (newSkill.trim() && !skills.includes(newSkill.trim())) {
      setSkills([...skills, newSkill.trim()]);
      setNewSkill('');
    }
  };
  
  const removeSkill = (skill: string) => {
    setSkills(skills.filter(s => s !== skill));
  };
  
  const addLanguage = () => {
    if (newLanguage.trim() && !languages.includes(newLanguage.trim())) {
      setLanguages([...languages, newLanguage.trim()]);
      setNewLanguage('');
    }
  };
  
  const removeLanguage = (lang: string) => {
    setLanguages(languages.filter(l => l !== lang));
  };
  
  const handleContinue = () => {
    navigate('/criteria');
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
            <div className="w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center font-semibold">2</div>
            <div className="w-16 h-1 bg-neutral-300 rounded"></div>
            <div className="w-8 h-8 rounded-full bg-neutral-300 text-neutral-600 flex items-center justify-center font-semibold">3</div>
          </div>
        </div>
        
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Mon Profil</h1>
            <p className="text-neutral-600">Vérifie et complète les informations extraites de ton CV.</p>
          </div>
          {!editMode ? (
            <button onClick={() => setEditMode(true)} className="btn-secondary">
              <Edit2 className="h-4 w-4 mr-2" />
              Modifier
            </button>
          ) : (
            <div className="flex gap-2">
              <button onClick={() => setEditMode(false)} className="btn-secondary">
                <X className="h-4 w-4 mr-2" />
                Annuler
              </button>
              <button onClick={handleSave} disabled={saving} className="btn-primary">
                {saving ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                Sauvegarder
              </button>
            </div>
          )}
        </div>
        
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm">
            {error}
          </div>
        )}
        
        <div className="space-y-6">
          {/* Title & Summary */}
          <div className="card">
            <div className="flex items-center mb-4">
              <Sparkles className="h-5 w-5 text-primary-600 mr-2" />
              <h2 className="text-lg font-semibold">Résumé</h2>
            </div>
            
            {editMode ? (
              <div className="space-y-4">
                <div>
                  <label className="label">Titre du profil</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="input"
                    placeholder="Ex: Développeur Full Stack Senior"
                  />
                </div>
                <div>
                  <label className="label">Description</label>
                  <textarea
                    value={summary}
                    onChange={(e) => setSummary(e.target.value)}
                    className="input min-h-[120px]"
                    placeholder="Une description de ton parcours et de tes aspirations..."
                  />
                </div>
              </div>
            ) : (
              <div>
                <h3 className="text-xl font-medium text-neutral-900 mb-2">
                  {title || 'Pas de titre défini'}
                </h3>
                <p className="text-neutral-600">
                  {summary || 'Aucune description disponible'}
                </p>
              </div>
            )}
            
            {profile?.ai_description && !editMode && (
              <div className="mt-4 p-3 bg-primary-50 rounded-lg">
                <p className="text-xs text-primary-700 font-medium mb-1">✨ Généré par IA</p>
                <p className="text-sm text-neutral-700">{profile.ai_description}</p>
              </div>
            )}
          </div>
          
          {/* Skills */}
          <div className="card">
            <div className="flex items-center mb-4">
              <Code className="h-5 w-5 text-primary-600 mr-2" />
              <h2 className="text-lg font-semibold">Compétences</h2>
            </div>
            
            {editMode && (
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                  className="input flex-1"
                  placeholder="Ajouter une compétence..."
                />
                <button onClick={addSkill} className="btn-secondary">
                  <Plus className="h-4 w-4" />
                </button>
              </div>
            )}
            
            <div className="flex flex-wrap gap-2">
              {skills.length > 0 ? (
                skills.map((skill) => (
                  <span key={skill} className="badge-primary flex items-center gap-1">
                    {skill}
                    {editMode && (
                      <button onClick={() => removeSkill(skill)} className="hover:text-red-600">
                        <X className="h-3 w-3" />
                      </button>
                    )}
                  </span>
                ))
              ) : (
                <p className="text-neutral-500 text-sm">Aucune compétence définie</p>
              )}
            </div>
          </div>
          
          {/* Languages */}
          <div className="card">
            <div className="flex items-center mb-4">
              <Languages className="h-5 w-5 text-primary-600 mr-2" />
              <h2 className="text-lg font-semibold">Langues</h2>
            </div>
            
            {editMode && (
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={newLanguage}
                  onChange={(e) => setNewLanguage(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addLanguage())}
                  className="input flex-1"
                  placeholder="Ajouter une langue..."
                />
                <button onClick={addLanguage} className="btn-secondary">
                  <Plus className="h-4 w-4" />
                </button>
              </div>
            )}
            
            <div className="flex flex-wrap gap-2">
              {languages.length > 0 ? (
                languages.map((lang) => (
                  <span key={lang} className="badge-neutral flex items-center gap-1">
                    {lang}
                    {editMode && (
                      <button onClick={() => removeLanguage(lang)} className="hover:text-red-600">
                        <X className="h-3 w-3" />
                      </button>
                    )}
                  </span>
                ))
              ) : (
                <p className="text-neutral-500 text-sm">Aucune langue définie</p>
              )}
            </div>
          </div>
          
          {/* Experiences */}
          <div className="card">
            <div className="flex items-center mb-4">
              <Briefcase className="h-5 w-5 text-primary-600 mr-2" />
              <h2 className="text-lg font-semibold">Expériences</h2>
            </div>
            
            {experiences.length > 0 ? (
              <div className="space-y-4">
                {experiences.map((exp, index) => (
                  <div key={index} className="border-l-2 border-primary-200 pl-4">
                    <h3 className="font-medium text-neutral-900">{exp.title}</h3>
                    <p className="text-sm text-primary-600">{exp.company}</p>
                    <p className="text-xs text-neutral-500">
                      {exp.start_date} - {exp.end_date || 'Présent'}
                    </p>
                    {exp.description && (
                      <p className="text-sm text-neutral-600 mt-1">{exp.description}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-neutral-500 text-sm">Aucune expérience définie</p>
            )}
          </div>
        </div>
        
        {/* Continue button */}
        <div className="mt-8 flex justify-end">
          <button onClick={handleContinue} className="btn-primary py-3 px-8">
            Continuer vers les critères
          </button>
        </div>
      </div>
    </MainLayout>
  );
}
