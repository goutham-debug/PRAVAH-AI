import React, { useState } from 'react';
import { useAssessment } from '../../context/AssessmentContext';
import { api } from '../../api/client';
import { Bot, Send, ShieldAlert, Sparkles, AlertCircle, Database, CheckCircle2, Loader2, ArrowRight } from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  dataUsed?: string[];
  intent?: string;
  classification?: string;
  assessmentId?: string;
  uncertaintyNote?: string;
}

export const AIAssistantPage: React.FC = () => {
  const { closedRoads, rainfall } = useAssessment();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: (
        "Welcome to the **PRAVAH AI Operational Intelligence Assistant**.\n\n" +
        "I provide answers grounded strictly in real-time and modelled backend assessment datasets " +
        "for the Whitefield–Mahadevapura urban corridor. I do not invent statistics, facilities, or incidents.\n\n" +
        "Select a prompt below or enter an operational query:"
      ),
      timestamp: new Date().toLocaleTimeString(),
      classification: 'OFFICIAL',
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const presets = [
    "Which neighbourhoods have the greatest assessed risk?",
    "Which road closures affect network connectivity?",
    "Which hospitals have reduced accessibility?",
    "Which shelters have remaining capacity?",
    "What changes between baseline and current scenario?",
  ];

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages(prev => [...prev, userMsg]);
    if (!queryText) setInput('');
    setLoading(true);

    try {
      const res = await api.queryAI({
        question: textToSend,
        rainfall_scenario: rainfall,
        closed_road_ids: closedRoads,
      });

      if (res.success) {
        const botMsg: ChatMessage = {
          id: `bot-${Date.now()}`,
          sender: 'assistant',
          text: res.answer,
          timestamp: new Date().toLocaleTimeString(),
          dataUsed: res.data_used,
          intent: res.intent,
          classification: res.classification,
          assessmentId: res.assessment_id,
          uncertaintyNote: res.uncertainty_note,
        };
        setMessages(prev => [...prev, botMsg]);
      } else {
        const errorMsg: ChatMessage = {
          id: `bot-err-${Date.now()}`,
          sender: 'assistant',
          text: `⚠️ Query evaluation error: ${res.error || 'Unable to retrieve assessment data.'}`,
          timestamp: new Date().toLocaleTimeString(),
        };
        setMessages(prev => [...prev, errorMsg]);
      }
    } catch (e: any) {
      const errorMsg: ChatMessage = {
        id: `bot-err-${Date.now()}`,
        sender: 'assistant',
        text: `⚠️ Network error: Cannot reach PRAVAH AI backend services.`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <div>
        <h1 className="text-xl sm:text-2xl font-black text-pravah-navy flex items-center gap-2">
          <Bot className="w-6 h-6 text-pravah-teal" />
          AI Situation Intelligence Assistant
        </h1>
        <p className="text-xs text-pravah-slate">
          Audited algorithmic synthesis querying live flood screening, topological graph cuts, and resource allocations.
        </p>
      </div>

      {/* Preset Question Pills */}
      <div className="flex flex-wrap gap-2">
        {presets.map((preset, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(preset)}
            disabled={loading}
            className="text-xs px-3 py-1.5 rounded-xl bg-white border border-slate-200 text-pravah-navy hover:border-pravah-teal hover:text-pravah-teal transition-all shadow-sm font-medium flex items-center gap-1.5 disabled:opacity-50"
          >
            <Sparkles className="w-3 h-3 text-pravah-teal" />
            {preset}
          </button>
        ))}
      </div>

      {/* Chat Messages Window */}
      <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm min-h-[440px] max-h-[600px] overflow-y-auto space-y-4">
        {messages.map(m => (
          <div
            key={m.id}
            className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed space-y-2 ${
                m.sender === 'user'
                  ? 'bg-pravah-navy text-white rounded-br-sm shadow-sm'
                  : 'bg-slate-50 border border-slate-200 text-pravah-navy rounded-bl-sm shadow-sm'
              }`}
            >
              <div className="flex items-center justify-between gap-3 text-[10px] pb-1 border-b border-black/10">
                <span className="font-bold uppercase tracking-wider flex items-center gap-1">
                  {m.sender === 'user' ? 'Disaster Operations Officer' : 'PRAVAH Grounded Intelligence'}
                </span>
                <span className="opacity-70">{m.timestamp}</span>
              </div>

              {/* Message Content */}
              <div className="whitespace-pre-wrap font-sans text-xs">
                {m.text}
              </div>

              {/* Data Provenance & Grounding Footnote for Assistant Responses */}
              {m.sender === 'assistant' && (m.dataUsed || m.classification) && (
                <div className="pt-2 border-t border-slate-200/80 text-[10px] text-pravah-slate space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    {m.classification && (
                      <span className="px-2 py-0.5 rounded font-bold bg-pravah-teal/10 text-pravah-teal border border-pravah-teal/20">
                        {m.classification}
                      </span>
                    )}
                    {m.assessmentId && (
                      <span className="font-mono">Assessment ID: {m.assessmentId}</span>
                    )}
                  </div>
                  {m.dataUsed && m.dataUsed.length > 0 && (
                    <div className="flex items-center gap-1 text-[10px] text-slate-500">
                      <Database className="w-3 h-3 text-pravah-teal" />
                      <span>Grounded on: {m.dataUsed.join(', ')}</span>
                    </div>
                  )}
                  {m.uncertaintyNote && (
                    <div className="text-[10px] text-slate-500 italic">
                      {m.uncertaintyNote}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-xs text-pravah-slate p-3 bg-slate-50 rounded-2xl w-fit">
            <Loader2 className="w-4 h-4 animate-spin text-pravah-teal" />
            <span>Querying active graph topology and flood models...</span>
          </div>
        )}
      </div>

      {/* Input Box */}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Ask about flood risk, road closures, hospital access, or evacuation shelters..."
          className="flex-1 px-4 py-2.5 rounded-2xl border border-slate-200 text-xs text-pravah-navy focus:outline-none focus:border-pravah-teal shadow-sm bg-white"
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          className="flex items-center gap-1.5 px-5 py-2.5 rounded-2xl bg-pravah-teal text-white text-xs font-bold shadow-md hover:bg-pravah-teal-dark transition-all disabled:opacity-50"
        >
          <Send className="w-3.5 h-3.5" />
          Ask
        </button>
      </div>

      {/* Safety Notice */}
      <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200 text-[11px] text-amber-900 flex items-start gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <strong>Operational Policy Guardrail:</strong> PRAVAH AI Assistant answers are deterministically computed
          from validated algorithms and current scenario inputs. Responses must not be used as autonomous dispatch orders
          without human command verification.
        </div>
      </div>
    </div>
  );
};
