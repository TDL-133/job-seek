import { useState, useEffect } from 'react';
import { MainLayout } from '../components/layout/MainLayout';
import { api } from '../services/api';
import type { BlacklistEntry } from '../types';
import { Loader2, Plus, Trash2, Building2, AlertCircle } from 'lucide-react';

export default function Blacklist() {
  const [entries, setEntries] = useState<BlacklistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Add form
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCompany, setNewCompany] = useState('');
  const [newReason, setNewReason] = useState('');
  const [adding, setAdding] = useState(false);
  
  useEffect(() => {
    loadBlacklist();
  }, []);
  
  const loadBlacklist = async () => {
    try {
      const data = await api.blacklist.list();
      setEntries(data);
    } catch (err: any) {
      setError('Erreur lors du chargement de la blacklist');
    } finally {
      setLoading(false);
    }
  };
  
  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCompany.trim()) return;
    
    setAdding(true);
    setError('');
    
    try {
      const entry = await api.blacklist.add({
        company_name: newCompany.trim(),
        reason: newReason.trim() || undefined,
      });
      setEntries([entry, ...entries]);
      setNewCompany('');
      setNewReason('');
      setShowAddForm(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erreur lors de l'ajout");
    } finally {
      setAdding(false);
    }
  };
  
  const handleRemove = async (id: string) => {
    try {
      await api.blacklist.remove(parseInt(id, 10));
      setEntries(entries.filter(e => e.id !== id));
    } catch (err) {
      setError('Erreur lors de la suppression');
    }
  };
  
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Blacklist</h1>
            <p className="text-neutral-600">
              Les entreprises blacklistées n'apparaîtront pas dans tes résultats de recherche.
            </p>
          </div>
          <button
            onClick={() => setShowAddForm(true)}
            className="btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            Ajouter
          </button>
        </div>
        
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm flex items-center">
            <AlertCircle className="h-4 w-4 mr-2" />
            {error}
          </div>
        )}
        
        {/* Add form modal */}
        {showAddForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl shadow-xl max-w-md w-full">
              <form onSubmit={handleAdd}>
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-neutral-900 mb-4">
                    Ajouter une entreprise à la blacklist
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="label">Nom de l'entreprise *</label>
                      <input
                        type="text"
                        value={newCompany}
                        onChange={(e) => setNewCompany(e.target.value)}
                        className="input"
                        placeholder="Ex: Acme Corp"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="label">Raison (optionnel)</label>
                      <textarea
                        value={newReason}
                        onChange={(e) => setNewReason(e.target.value)}
                        className="input"
                        placeholder="Ex: Mauvaise expérience en entretien"
                        rows={3}
                      />
                    </div>
                  </div>
                </div>
                
                <div className="p-6 border-t border-neutral-200 flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
                    className="btn-secondary"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    disabled={adding || !newCompany.trim()}
                    className="btn-primary"
                  >
                    {adding ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Ajout...
                      </>
                    ) : (
                      'Ajouter'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
        
        {/* List */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        ) : entries.length === 0 ? (
          <div className="card text-center py-12">
            <Building2 className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 mb-2">
              Aucune entreprise blacklistée
            </h3>
            <p className="text-neutral-600">
              Tu peux ajouter des entreprises pour qu'elles n'apparaissent plus dans tes recherches.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {entries.map((entry) => (
              <div
                key={entry.id}
                className="card flex items-center justify-between"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                    <Building2 className="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-neutral-900">
                      {entry.company_name}
                    </h3>
                    {entry.reason && (
                      <p className="text-sm text-neutral-500">{entry.reason}</p>
                    )}
                    <p className="text-xs text-neutral-400">
                      Ajouté le {new Date(entry.created_at).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={() => handleRemove(entry.id)}
                  className="p-2 hover:bg-red-50 rounded-lg text-neutral-400 hover:text-red-600 transition-colors"
                  title="Retirer de la blacklist"
                >
                  <Trash2 className="h-5 w-5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </MainLayout>
  );
}
