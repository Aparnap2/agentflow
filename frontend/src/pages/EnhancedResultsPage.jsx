import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  FileText, 
  Download, 
  Share2, 
  TrendingUp, 
  DollarSign, 
  Users, 
  Scale,
  BarChart3,
  PieChart,
  Activity,
  CheckCircle,
  ArrowLeft,
  Eye,
  ExternalLink
} from 'lucide-react';
import apiService from '../services/api';

const RESULT_SECTIONS = {
  VISION: 'Vision & Strategy',
  PRODUCT: 'Product Development', 
  FINANCE: 'Financial Planning',
  MARKETING: 'Marketing Strategy',
  LEGAL: 'Legal & Compliance'
};

const SECTION_ICONS = {
  [RESULT_SECTIONS.VISION]: TrendingUp,
  [RESULT_SECTIONS.PRODUCT]: Users,
  [RESULT_SECTIONS.FINANCE]: DollarSign,
  [RESULT_SECTIONS.MARKETING]: Share2,
  [RESULT_SECTIONS.LEGAL]: Scale
};

const SECTION_COLORS = {
  [RESULT_SECTIONS.VISION]: 'bg-purple-100 text-purple-800',
  [RESULT_SECTIONS.PRODUCT]: 'bg-blue-100 text-blue-800',
  [RESULT_SECTIONS.FINANCE]: 'bg-green-100 text-green-800',
  [RESULT_SECTIONS.MARKETING]: 'bg-orange-100 text-orange-800',
  [RESULT_SECTIONS.LEGAL]: 'bg-red-100 text-red-800'
};

const ResultCard = ({ title, content, confidence, icon: Icon, color, onExpand }) => {
  const formatContent = (content) => {
    if (typeof content === 'string') {
      return content;
    }
    
    if (typeof content === 'object') {
      return JSON.stringify(content, null, 2);
    }
    
    return String(content);
  };

  const truncateContent = (text, maxLength = 200) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center">
            <div className={`p-2 rounded-lg ${color}`}>
              <Icon className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 ml-3">{title}</h3>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">
              Confidence: {Math.round((confidence || 0.8) * 100)}%
            </span>
            <div className={`w-2 h-2 rounded-full ${
              confidence >= 0.8 ? 'bg-green-500' : 
              confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
            }`} />
          </div>
        </div>
        
        <div className="text-gray-700 mb-4 font-mono text-sm bg-gray-50 p-3 rounded-md">
          <pre className="whitespace-pre-wrap">
            {truncateContent(formatContent(content))}
          </pre>
        </div>
        
        <div className="flex justify-between items-center">
          <button
            onClick={onExpand}
            className="flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            <Eye className="h-4 w-4 mr-1" />
            View Details
          </button>
          <button className="flex items-center text-gray-500 hover:text-gray-700 text-sm">
            <Download className="h-4 w-4 mr-1" />
            Export
          </button>
        </div>
      </div>
    </div>
  );
};

const DetailModal = ({ isOpen, onClose, title, content, confidence }) => {
  if (!isOpen) return null;

  const formatDetailedContent = (content) => {
    if (typeof content === 'object') {
      return JSON.stringify(content, null, 2);
    }
    return String(content);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onClick={onClose} />
        
        <div className="inline-block w-full max-w-4xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-xl rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">
                Confidence: {Math.round((confidence || 0.8) * 100)}%
              </span>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
          </div>
          
          <div className="max-h-96 overflow-y-auto bg-gray-50 p-4 rounded-md">
            <pre className="whitespace-pre-wrap text-sm font-mono text-gray-800">
              {formatDetailedContent(content)}
            </pre>
          </div>
          
          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Close
            </button>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
              <Download className="h-4 w-4 mr-2 inline" />
              Export This Section
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const SummaryPanel = ({ sessionData, results }) => {
  const calculateOverallScore = () => {
    if (!results || Object.keys(results).length === 0) return 0;
    
    const scores = Object.values(results).map(result => result.confidence || 0.8);
    return scores.reduce((acc, score) => acc + score, 0) / scores.length;
  };

  const overallScore = calculateOverallScore();

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 mb-8">
      <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
        <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
        Project Summary
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="text-center">
          <div className="text-3xl font-bold text-blue-600">
            {Math.round(overallScore * 100)}%
          </div>
          <div className="text-sm text-gray-600">Overall Confidence</div>
          <div className={`mt-2 w-full h-2 rounded-full ${
            overallScore >= 0.8 ? 'bg-green-200' : 
            overallScore >= 0.6 ? 'bg-yellow-200' : 'bg-red-200'
          }`}>
            <div 
              className={`h-2 rounded-full ${
                overallScore >= 0.8 ? 'bg-green-500' : 
                overallScore >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${overallScore * 100}%` }}
            />
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-3xl font-bold text-green-600">
            {Object.keys(results || {}).length}
          </div>
          <div className="text-sm text-gray-600">Sections Generated</div>
        </div>
        
        <div className="text-center">
          <div className="text-3xl font-bold text-purple-600">
            {sessionData?.execution_time ? Math.round(sessionData.execution_time / 60) : '--'}
          </div>
          <div className="text-sm text-gray-600">Minutes to Complete</div>
        </div>
        
        <div className="text-center">
          <div className="text-3xl font-bold text-orange-600">
            {sessionData?.agents_executed?.length || 0}
          </div>
          <div className="text-sm text-gray-600">Agents Involved</div>
        </div>
      </div>
      
      {sessionData?.vision && (
        <div className="mt-6 p-4 bg-gray-50 rounded-md">
          <h3 className="font-medium text-gray-900 mb-2">Original Vision</h3>
          <p className="text-gray-700 italic">"{sessionData.vision}"</p>
        </div>
      )}
    </div>
  );
};

const EnhancedResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState(null);
  const [results, setResults] = useState({});
  const [sessionData, setSessionData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSection, setSelectedSection] = useState(null);
  const [modalData, setModalData] = useState({ isOpen: false, title: '', content: '', confidence: 0 });

  useEffect(() => {
    if (location.state?.sessionId) {
      setSessionId(location.state.sessionId);
      loadResults(location.state.sessionId);
      
      // Set up real-time updates for results
      apiService.connectWebSocket();
      
      const handleTaskCompleted = (event) => {
        if (event.data.session_id === location.state.sessionId) {
          // Reload results when new agent completes
          setTimeout(() => loadResults(location.state.sessionId), 1000);
        }
      };

      apiService.on('event:task_completed', handleTaskCompleted);
      
      return () => {
        apiService.off('event:task_completed', handleTaskCompleted);
      };
    } else {
      navigate('/');
    }
  }, [location.state, navigate]);

  const loadResults = async (sessionId) => {
    try {
      setLoading(true);
      const response = await apiService.getSessionResults(sessionId);
      
      if (response.error) {
        setError(response.error);
      } else {
        setResults(response.results || {});
        setSessionData(response.summary || {});
      }
    } catch (err) {
      console.error('Failed to load results:', err);
      setError('Failed to load results. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleExportAll = async () => {
    try {
      // Create comprehensive export data
      const exportData = {
        session_id: sessionId,
        session_data: sessionData,
        results: results,
        exported_at: new Date().toISOString(),
        sections: Object.entries(RESULT_SECTIONS).map(([key, title]) => ({
          section: title,
          results: Object.entries(results).filter(([agentName]) => 
            mapResultToSection(agentName) === title
          ).map(([agentName, result]) => ({
            agent: agentName,
            content: result.output || result.data || result,
            confidence: result.confidence || 0.8
          }))
        })).filter(section => section.results.length > 0)
      };

      // Create and download JSON file
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
        type: 'application/json' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `agentflow-results-${sessionId?.slice(0, 8)}-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      console.log('✅ Results exported successfully');
    } catch (err) {
      console.error('Failed to export:', err);
      setError('Failed to export results. Please try again.');
    }
  };

  const openModal = (title, content, confidence) => {
    setModalData({
      isOpen: true,
      title,
      content,
      confidence
    });
  };

  const closeModal = () => {
    setModalData({ isOpen: false, title: '', content: '', confidence: 0 });
  };

  const mapResultToSection = (agentName) => {
    const mapping = {
      'Cofounder': RESULT_SECTIONS.VISION,
      'Manager': RESULT_SECTIONS.VISION,
      'Product': RESULT_SECTIONS.PRODUCT,
      'Finance': RESULT_SECTIONS.FINANCE,
      'Marketing': RESULT_SECTIONS.MARKETING,
      'Legal': RESULT_SECTIONS.LEGAL
    };
    return mapping[agentName] || RESULT_SECTIONS.VISION;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your project results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Results</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <button
                onClick={() => navigate('/')}
                className="mr-4 p-2 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                  <FileText className="h-6 w-6 mr-2 text-blue-600" />
                  Project Results
                </h1>
                <p className="text-gray-600 mt-1">
                  Comprehensive analysis generated by your AI team
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className="text-sm text-gray-500">
                Session: {sessionId?.slice(0, 8)}...
              </div>
              <button
                onClick={handleExportAll}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <Download className="h-4 w-4 mr-2" />
                Export All
              </button>
            </div>
          </div>
        </div>

        {/* Summary Panel */}
        <SummaryPanel sessionData={sessionData} results={results} />

        {/* Results Grid */}
        {Object.keys(results).length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
            <Activity className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Results Yet</h3>
            <p className="text-gray-600">
              Results will appear here once agents complete their work.
            </p>
          </div>
        ) : (
          <div className="space-y-8">
            {Object.entries(RESULT_SECTIONS).map(([sectionKey, sectionTitle]) => {
              // Filter results for this section
              const sectionResults = Object.entries(results).filter(([agentName, result]) => 
                mapResultToSection(agentName) === sectionTitle
              );

              if (sectionResults.length === 0) return null;

              const SectionIcon = SECTION_ICONS[sectionTitle];
              const sectionColor = SECTION_COLORS[sectionTitle];

              return (
                <div key={sectionKey}>
                  <div className="flex items-center mb-4">
                    <div className={`p-2 rounded-lg mr-3 ${sectionColor}`}>
                      <SectionIcon className="h-5 w-5" />
                    </div>
                    <h2 className="text-xl font-semibold text-gray-900">{sectionTitle}</h2>
                    <div className="ml-auto text-sm text-gray-500">
                      {sectionResults.length} result{sectionResults.length !== 1 ? 's' : ''}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {sectionResults.map(([agentName, result]) => (
                      <ResultCard
                        key={agentName}
                        title={`${agentName} Analysis`}
                        content={result.output || result.data || result}
                        confidence={result.confidence || 0.8}
                        icon={SectionIcon}
                        color={sectionColor}
                        onExpand={() => openModal(
                          `${agentName} Analysis`,
                          result.output || result.data || result,
                          result.confidence || 0.8
                        )}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Detail Modal */}
        <DetailModal
          isOpen={modalData.isOpen}
          onClose={closeModal}
          title={modalData.title}
          content={modalData.content}
          confidence={modalData.confidence}
        />

        {/* Actions Footer */}
        <div className="mt-12 bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">What's Next?</h3>
              <p className="text-gray-600 mt-1">
                Use these insights to refine your strategy and move forward with confidence.
              </p>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={() => navigate('/enhanced-workflow')}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                Start New Analysis
              </button>
              <button
                onClick={handleExportAll}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Share Results
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedResultsPage;
