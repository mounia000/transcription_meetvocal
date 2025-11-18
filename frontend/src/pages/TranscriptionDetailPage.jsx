import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { filesAPI } from '../services/api';
import { 
  ArrowLeft, 
  Download, 
  Clock, 
  Users, 
  Loader,
  FileText,
  MessageSquare
} from 'lucide-react';

export default function TranscriptionDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTranscription();
  }, [id]);

  const loadTranscription = async () => {
    try {
      const response = await filesAPI.getCompteRendu(id);
      setData(response.data);
    } catch (error) {
      console.error('Erreur chargement transcription:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const response = await filesAPI.downloadPDF(id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${data.titre}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      alert('Erreur lors du téléchargement du PDF');
    }
  };

  // Fonction pour parser le compte-rendu structuré
  const parseCompteRendu = (text) => {
    if (!text) return {};
    
    const sections = {};
    const lines = text.split('\n');
    let currentSection = '';
    let currentContent = [];

    for (const line of lines) {
      if (line.trim().startsWith('# ')) {
        if (currentSection) {
          sections[currentSection] = currentContent.join('\n').trim();
        }
        currentSection = line.replace('# ', '').trim();
        currentContent = [];
      } else if (line.trim() && currentSection) {
        currentContent.push(line);
      }
    }
    
    if (currentSection) {
      sections[currentSection] = currentContent.join('\n').trim();
    }

    return sections;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Transcription non trouvée</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="mt-4 text-primary-600 hover:text-primary-700"
          >
            Retour au dashboard
          </button>
        </div>
      </div>
    );
  }

  const sections = parseCompteRendu(data.resume_general);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="p-2 hover:bg-gray-100 rounded-lg transition"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">{data.titre}</h1>
                <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {new Date(data.date).toLocaleDateString('fr-FR')}
                  </span>
                  {data.duree_minutes && (
                    <span className="flex items-center gap-1">
                      <FileText className="w-4 h-4" />
                      {data.duree_minutes} min
                    </span>
                  )}
                  {data.nombre_participants > 0 && (
                    <span className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      {data.nombre_participants} participant{data.nombre_participants > 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              </div>
            </div>
            
            <button
              onClick={handleDownloadPDF}
              className="flex items-center gap-2 btn-primary"
            >
              <Download className="w-4 h-4" />
              Télécharger PDF
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Résumé Exécutif */}
          {sections['RÉSUMÉ EXÉCUTIF'] && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-blue-600" />
                </div>
                <h2 className="text-lg font-bold text-gray-900">Résumé Exécutif</h2>
              </div>
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                {sections['RÉSUMÉ EXÉCUTIF']}
              </p>
            </div>
          )}

          {/* Contexte et Objectif */}
          {sections['CONTEXTE ET OBJECTIF'] && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <MessageSquare className="w-5 h-5 text-green-600" />
                </div>
                <h2 className="text-lg font-bold text-gray-900">Contexte et Objectif</h2>
              </div>
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                {sections['CONTEXTE ET OBJECTIF']}
              </p>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            {/* Points Clés Discutés */}
            {sections['POINTS CLÉS DISCUTÉS'] && (
              <div className="card">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-purple-600" />
                  </div>
                  <h2 className="text-base font-bold text-gray-900">Points Clés Discutés</h2>
                </div>
                <div className="text-gray-700 leading-relaxed whitespace-pre-wrap text-sm">
                  {sections['POINTS CLÉS DISCUTÉS']}
                </div>
              </div>
            )}

            {/* Décisions Prises */}
            {sections['DÉCISIONS PRISES'] && (
              <div className="card">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-yellow-600" />
                  </div>
                  <h2 className="text-base font-bold text-gray-900">Décisions Prises</h2>
                </div>
                <div className="text-gray-700 leading-relaxed whitespace-pre-wrap text-sm">
                  {sections['DÉCISIONS PRISES']}
                </div>
              </div>
            )}
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Actions à Entreprendre */}
            {sections['ACTIONS À ENTREPRENDRE'] && (
              <div className="card">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-orange-600" />
                  </div>
                  <h2 className="text-base font-bold text-gray-900">Actions à Entreprendre</h2>
                </div>
                <div className="text-gray-700 leading-relaxed whitespace-pre-wrap text-sm">
                  {sections['ACTIONS À ENTREPRENDRE']}
                </div>
              </div>
            )}

            {/* Prochaines Étapes */}
            {sections['PROCHAINES ÉTAPES'] && (
              <div className="card">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-red-600" />
                  </div>
                  <h2 className="text-base font-bold text-gray-900">Prochaines Étapes</h2>
                </div>
                <div className="text-gray-700 leading-relaxed whitespace-pre-wrap text-sm">
                  {sections['PROCHAINES ÉTAPES']}
                </div>
              </div>
            )}
          </div>

          {/* Transcription Complète */}
          {data.transcription_complete && data.transcription_complete.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-gray-600" />
                </div>
                <h2 className="text-lg font-bold text-gray-900">Transcription Complète</h2>
              </div>
              <div className="space-y-3">
                {data.transcription_complete.map((segment, index) => (
                  <div key={index} className="flex gap-3 pb-3 border-b border-gray-100 last:border-0">
                    {segment.temps && (
                      <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded h-fit">
                        {segment.temps}
                      </span>
                    )}
                    {segment.participant && (
                      <span className="text-xs font-semibold text-primary-600 bg-primary-50 px-2 py-1 rounded h-fit">
                        {segment.participant}
                      </span>
                    )}
                    <p className="text-gray-700 leading-relaxed flex-1 text-sm">
                      {segment.texte}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}