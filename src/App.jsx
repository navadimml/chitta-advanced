import React, { useState, useEffect, useRef } from 'react';
import { Menu, MessageCircle, LogOut } from 'lucide-react';

// API Client
import { api } from './api/client';

// Auth
import { useAuth } from './contexts/AuthContext';
import { FamilyProvider, useFamily } from './contexts/FamilyContext';
import { AuthPage } from './components/auth';
import LoadingScreen from './components/LoadingScreen';

// Test Mode Orchestrator
import { testModeOrchestrator } from './services/TestModeOrchestrator.jsx';

// UI Components
import ConversationTranscript from './components/ConversationTranscript';
import InputArea from './components/InputArea';
import SuggestionsPopup from './components/SuggestionsPopup';
import DeepViewManager from './components/DeepViewManager';
import VideoGuidelinesView from './components/VideoGuidelinesView';
import VideoInsightsView from './components/VideoInsightsView';
import { TestModeBannerPortal } from './components/TestModeBannerPortal.jsx';
import DevPanel from './components/DevPanel';

// Living Dashboard Components (Phase 2 & 3)
import ChildSpaceHeader from './components/ChildSpaceHeader';
import ChildSpace from './components/ChildSpace';
import LivingDocument from './components/LivingDocument';

// Living Gestalt Components
import GestaltCards from './components/GestaltCards';

// Family Components
import ChildSwitcher from './components/family/ChildSwitcher';

function App() {
  // Auth state
  const { isAuthenticated, isLoading: authLoading, logout } = useAuth();

  // Show loading screen while auth is being checked
  if (authLoading) {
    return <LoadingScreen />;
  }

  // Show auth page if not authenticated
  if (!isAuthenticated) {
    return <AuthPage />;
  }

  // Wrap authenticated app with FamilyProvider
  return (
    <FamilyProvider>
      <AuthenticatedAppWithFamily onLogout={logout} />
    </FamilyProvider>
  );
}

/**
 * Intermediate component that uses FamilyContext to get activeChildId
 */
function AuthenticatedAppWithFamily({ onLogout }) {
  const { activeChildId, isLoading: familyLoading, refreshFamily } = useFamily();

  // Show loading while family data is being fetched
  if (familyLoading) {
    return <LoadingScreen />;
  }

  // Use key={activeChildId} to force remount when switching children
  // This ensures all state (messages, cards, etc.) resets for the new child
  return (
    <AuthenticatedApp
      key={activeChildId}
      userFamilyId={activeChildId}
      onLogout={onLogout}
      onRefreshFamily={refreshFamily}
    />
  );
}

/**
 * Main app component for authenticated users
 */
function AuthenticatedApp({ userFamilyId, onLogout, onRefreshFamily }) {
  // Simple state - use user ID as default family ID
  const [familyId, setFamilyId] = useState(userFamilyId);
  const [messages, setMessages] = useState([]);
  const [cards, setCards] = useState([]);
  const [suggestions, setSuggestions] = useState([
    { text: "שמו יוני והוא בן 3.5", action: null },
    { text: "הילדה שלי בת 5", action: null },
    { text: "רוצה להתחיל בהערכה", action: null }
  ]);
  const [draftMessage, setDraftMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeDeepView, setActiveDeepView] = useState(null);
  const [activeViewData, setActiveViewData] = useState(null);
  const [videos, setVideos] = useState([]);
  const [journalEntries, setJournalEntries] = useState([]);
  const [childName, setChildName] = useState('');
  const [videoGuidelines, setVideoGuidelines] = useState(null);
  const [showGuidelinesView, setShowGuidelinesView] = useState(false);
  const [videoInsights, setVideoInsights] = useState(null);
  const [showInsightsView, setShowInsightsView] = useState(false);

  // Test mode state
  const [testMode, setTestMode] = useState(false);
  const [testPersonas, setTestPersonas] = useState([]);
  const [showPersonaSelector, setShowPersonaSelector] = useState(false);
  const [testFamilyId, setTestFamilyId] = useState(null); // Track test mode family ID

  // Living Dashboard state (Phase 2 & 3)
  const [showChildSpace, setShowChildSpace] = useState(false);
  const [childSpaceInitialTab, setChildSpaceInitialTab] = useState('essence');  // Which tab to open to
  const [livingDocumentArtifact, setLivingDocumentArtifact] = useState(null);

  // Living Gestalt state (curiosity-driven exploration)
  const [childSpace, setChildSpace] = useState(null);  // Badges and child space data
  const [curiosityState, setCuriosityState] = useState({
    active_curiosities: [],
    open_questions: []
  });

  // Ref to track last processed message (prevent duplicate triggers)
  const lastProcessedMessageRef = useRef(null);

  // Load journey state on mount
  useEffect(() => {
    async function loadJourney() {
      try {
        // Load complete state from backend
        const response = await api.getState(familyId);
        const { state, ui } = response;

        // Reconstruct UI from state - everything derives!
        const conversationMessages = state.conversation.map(msg => ({
          sender: msg.role === 'user' ? 'user' : 'chitta',
          text: msg.content,
          timestamp: msg.timestamp
        }));

        // Add greeting message
        setMessages([
          ...conversationMessages,
          {
            sender: 'chitta',
            text: ui.greeting,
            timestamp: new Date().toISOString()
          }
        ]);

        // Set derived UI elements
        setCards(ui.cards);
        setSuggestions(ui.suggestions);

        // 🌟 Living Gestalt: Load curiosity state
        if (ui.curiosity_state) {
          setCuriosityState(ui.curiosity_state);
          console.log('🌟 Loaded curiosity state:', ui.curiosity_state.active_curiosities?.length || 0, 'curiosities');
        }

        // 🌟 Living Gestalt: Load child space data for header
        if (ui.child_space) {
          setChildSpace(ui.child_space);
          console.log('🌟 Loaded child space:', ui.child_space.badges?.length || 0, 'badges');
        }

        // Set state data
        if (state.child) {
          setChildName(state.child.name || '');
        }
        // Also get child name from child_space if available
        if (ui.child_space?.child_name && !state.child?.name) {
          setChildName(ui.child_space.child_name);
        }

        if (state.artifacts?.baseline_video_guidelines) {
          const content = state.artifacts.baseline_video_guidelines.content;
          // Parse JSON content (artifact stores structured data as JSON string)
          const guidelinesData = typeof content === 'string' ? JSON.parse(content) : content;
          setVideoGuidelines(guidelinesData);
        }

        // Set activities
        setVideos(state.videos_uploaded || []);
        setJournalEntries(state.journal_entries || []);

      } catch (error) {
        console.error('Error loading journey:', error);
        // Fallback to default greeting
        setMessages([{
          sender: 'chitta',
          text: 'היי! אני צ\'יטה 💙\n\nכיף שהגעת! אשמח להכיר את הילד שלך ולהבין איך אפשר לעזור.\n\nמה השם והגיל?',
          timestamp: new Date().toISOString()
        }]);
      }
    }

    loadJourney();

    // 🧪 Setup test mode orchestrator callbacks
    testModeOrchestrator.onError = (error) => {
      console.error('🧪 Test mode error:', error);
      const errorMessage = {
        sender: 'chitta',
        text: 'שגיאה במצב בדיקה. בודק...',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    };
  }, []);

  // 🌟 SSE connection - dynamically updates when child_id changes (e.g., test mode)
  useEffect(() => {
    // Determine active child ID (test mode uses testFamilyId, normal mode uses familyId)
    const activeFamilyId = testMode && testFamilyId ? testFamilyId : familyId;

    console.log('📡 SSE: Connecting to child_id:', activeFamilyId);

    const eventSource = new EventSource(`/api/state/subscribe?child_id=${activeFamilyId}`);

    eventSource.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data);
        console.log('📡 SSE update received:', update.type, update.data);

        if (update.type === 'cards') {
          // Update cards in real-time
          console.log('📇 Updating cards from SSE:', update.data.cards.length, 'cards');
          setCards(update.data.cards);
        } else if (update.type === 'artifact') {
          // Artifact status changed - could trigger card refresh or UI updates
          console.log('📦 Artifact updated:', update.data.artifact_id, update.data.status);
          // Additional handling could go here (e.g., update specific artifact displays)
        }
      } catch (error) {
        console.error('Error processing SSE update:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      // Automatically reconnects on error
    };

    // Cleanup: close connection when child_id changes or component unmounts
    return () => {
      console.log('📡 SSE: Closing connection for child_id:', activeFamilyId);
      eventSource.close();
    };
  }, [testMode, testFamilyId, familyId]); // Re-create SSE connection when child_id changes

  // 🧪 Monitor messages and trigger next response in test mode
  useEffect(() => {
    if (!testModeOrchestrator.isActive() || !testModeOrchestrator.isAutoRunning()) {
      return;
    }

    // Find last Chitta message
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.sender === 'chitta') {
      // CRITICAL: Prevent duplicate triggers by checking if we already processed this message
      if (lastProcessedMessageRef.current === lastMessage.timestamp) {
        console.log('🧪 [App] Already triggered for this message, skipping...');
        return;
      }

      console.log('🧪 [App] Chitta responded, triggering next parent response');
      lastProcessedMessageRef.current = lastMessage.timestamp;

      // Trigger next response after a small delay
      setTimeout(() => {
        testModeOrchestrator.generateNextResponse(messages, handleSend);
      }, 500);
    }
  }, [messages]);

  // Handle sending a message
  // overrideFamilyId: Optional explicit family_id (for test mode to bypass async state issues)
  const handleSend = async (message, overrideFamilyId = null) => {
    if (!message.trim()) return;

    // Add user message to UI immediately
    const userMessage = {
      sender: 'user',
      text: message,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setDraftMessage('');
    setIsTyping(true);

    try {
      // 🧪 Check for test mode trigger
      const testTriggers = ['test mode', 'start test', 'מצב בדיקה', 'התחל בדיקה', 'טסט'];
      const isTestTrigger = testTriggers.some(trigger =>
        message.toLowerCase().includes(trigger)
      );

      if (isTestTrigger) {
        console.log('🧪 Test mode triggered - loading personas');
        setIsTyping(true);

        try {
          // Load available personas
          const { personas } = await api.getTestPersonas();
          setTestPersonas(personas);
          setShowPersonaSelector(true);

          // Show Chitta's response
          const assistantMessage = {
            sender: 'chitta',
            text: 'מצוין! 🧪\n\nנכנסנו למצב בדיקה. בחרי אחת מהפרסונות לסימולציה:',
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
          console.error('Error loading test personas:', error);
          const errorMessage = {
            sender: 'chitta',
            text: 'שגיאה בטעינת פרסונות בדיקה.',
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, errorMessage]);
        }

        setIsTyping(false);
        return;
      }

      // Call backend API (use override if provided, else test family ID if in test mode, else default)
      // BUG FIX: overrideFamilyId bypasses async state issues when test mode starts
      const activeFamilyId = overrideFamilyId || (testMode && testFamilyId ? testFamilyId : familyId);
      const response = await api.sendMessage(activeFamilyId, message);

      // Add assistant response (normal flow)
      const assistantMessage = {
        sender: 'chitta',
        text: response.response,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Update UI from backend response
      if (response.ui_data) {
        if (response.ui_data.suggestions) {
          setSuggestions(response.ui_data.suggestions.map(s =>
            typeof s === 'string' ? { text: s, action: null } : s
          ));
        }
        if (response.ui_data.cards) {
          setCards(response.ui_data.cards);
        }
        // CRITICAL: Save video guidelines when interview completes
        if (response.ui_data.video_guidelines) {
          setVideoGuidelines(response.ui_data.video_guidelines);
        }
        // Living Gestalt: Update curiosity state
        if (response.ui_data.curiosity_state) {
          setCuriosityState(response.ui_data.curiosity_state);
        }
      }

      // 🌟 Handle action validation (config-driven)
      if (response.action_validation) {
        const { action, feasible, view_to_open, explanation } = response.action_validation;

        if (feasible && view_to_open) {
          // Action is allowed - open the specified view
          console.log(`✅ Opening view: ${view_to_open} (action: ${action})`);
          setActiveDeepView(view_to_open);
        } else if (!feasible) {
          // Action not allowed - Chitta's response already includes explanation
          console.log(`❌ Action "${action}" not feasible: ${explanation || 'Prerequisites not met'}`);
        }
      }

      // Refresh family data to update ChildSwitcher with latest child names
      // This handles cases where child identity was extracted from conversation
      if (onRefreshFamily) {
        await onRefreshFamily();
        console.log('👨‍👩‍👧 Family data refreshed after message');
      }

    } catch (error) {
      console.error('Error sending message:', error);

      // Fallback message
      const errorMessage = {
        sender: 'chitta',
        text: 'מצטערת, הייתה בעיה. נסי שוב.',
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  // Handle card click
  // action: the action string (e.g., 'accept_video', 'view_guidelines')
  // card: the full card object (contains cycle_id for Living Gestalt cards)
  const handleCardClick = async (action, card = null) => {
    if (!action) return; // Status cards have no action

    const activeFamilyId = testMode && testFamilyId ? testFamilyId : familyId;
    const cycleId = card?.cycle_id;

    // === Living Gestalt Video Flow Actions ===

    // Accept video suggestion - triggers async guidelines generation
    if (action === 'accept_video' && cycleId) {
      console.log('📹 Accepting video suggestion for cycle:', cycleId);
      // Note: Don't set isTyping - the card shows its own loading state
      // Guidelines generate in background, SSE updates cards when ready

      try {
        const result = await api.acceptVideoSuggestion(activeFamilyId, cycleId);
        console.log('✅ Video accepted:', result);

        // If guidelines were returned synchronously (testing mode), show them
        if (result.guidelines) {
          setVideoGuidelines(result.guidelines);
          setShowGuidelinesView(true);
        }

        // Refresh cards to show new state (generating -> ready)
        await refreshCards();
      } catch (error) {
        console.error('❌ Error accepting video suggestion:', error);
        alert('שגיאה ביצירת ההנחיות. נא לנסות שוב.');
      }
      return;
    }

    // Decline video suggestion
    if (action === 'decline_video' && cycleId) {
      console.log('📹 Declining video suggestion for cycle:', cycleId);

      try {
        await api.declineVideoSuggestion(activeFamilyId, cycleId);
        console.log('✅ Video declined');

        // Refresh cards to remove the suggestion
        await refreshCards();
      } catch (error) {
        console.error('❌ Error declining video suggestion:', error);
      }
      return;
    }

    // Accept baseline video suggestion (early discovery video)
    if (action === 'accept_baseline_video') {
      console.log('📹 Accepting baseline video suggestion');

      try {
        const result = await api.executeCardAction(activeFamilyId, 'accept_baseline_video', {});
        console.log('✅ Baseline video accepted:', result);

        // If guidelines were returned, show them
        if (result.guidelines) {
          setVideoGuidelines({ scenarios: result.guidelines });
          setShowGuidelinesView(true);
        }

        // Refresh cards
        await refreshCards();
      } catch (error) {
        console.error('❌ Error accepting baseline video:', error);
        alert('שגיאה. נא לנסות שוב.');
      }
      return;
    }

    // Dismiss card (X button or אולי מאוחר יותר button)
    if (action === 'dismiss') {
      console.log('❌ Dismissing card:', card?.type, 'cycle:', cycleId);

      try {
        // For baseline video suggestions (no cycle_id), use card action
        if (card?.type === 'baseline_video_suggestion') {
          await api.executeCardAction(activeFamilyId, 'dismiss_baseline_video', {});
        }
        // For video suggestions with cycle, declining is the same as dismissing
        else if (card?.type === 'video_suggestion' && cycleId) {
          await api.declineVideoSuggestion(activeFamilyId, cycleId);
        }
        // For other cards with cycle_id
        else if (cycleId) {
          await api.executeCardAction(activeFamilyId, 'dismiss', {
            cycle_id: cycleId,
            card_type: card?.type,
            scenario_ids: card?.scenario_ids || [],
          });
        }
        console.log('✅ Card dismissed');
        await refreshCards();
      } catch (error) {
        console.error('❌ Error dismissing card:', error);
      }
      return;
    }

    // Confirm video (parent verifies it's the correct video despite concerns)
    if (action === 'confirm_video' && card?.scenario_id) {
      console.log('✅ Confirming video for scenario:', card.scenario_id);

      try {
        await api.executeCardAction(activeFamilyId, 'confirm_video', {
          cycle_id: cycleId,
          scenario_id: card.scenario_id,
        });
        console.log('✅ Video confirmed');
        await refreshCards();
      } catch (error) {
        console.error('❌ Error confirming video:', error);
      }
      return;
    }

    // Reject video (parent says it's not the right video)
    if (action === 'reject_video' && card?.scenario_id) {
      console.log('❌ Rejecting video for scenario:', card.scenario_id);

      try {
        await api.executeCardAction(activeFamilyId, 'reject_video', {
          cycle_id: cycleId,
          scenario_id: card.scenario_id,
        });
        console.log('✅ Video rejected - can upload new one');
        await refreshCards();
      } catch (error) {
        console.error('❌ Error rejecting video:', error);
      }
      return;
    }

    // View video insights
    if (action === 'view_insights' && card?.cycle_id) {
      try {
        const insightsData = await api.getVideoInsights(activeFamilyId, card.cycle_id);
        setVideoInsights(insightsData);
        setShowInsightsView(true);
      } catch (error) {
        console.error('Error fetching video insights:', error);
        alert('שגיאה בטעינת התובנות. נא לנסות שוב.');
      }
      return;
    }

    // View synthesis
    if (action === 'view_synthesis') {
      console.log('📊 Requesting synthesis');
      setIsTyping(true);

      try {
        const result = await api.requestSynthesis(activeFamilyId);
        console.log('✅ Synthesis result:', result);
        // TODO: Open synthesis view
        alert('סיכום עדיין בפיתוח');
      } catch (error) {
        console.error('❌ Error requesting synthesis:', error);
        alert('שגיאה ביצירת הסיכום. נא לנסות שוב.');
      } finally {
        setIsTyping(false);
      }
      return;
    }

    // Handle both 'view_guidelines' (old) and 'view_video_guidelines' (from action_graph.yaml)
    // Now opens ChildSpace to the observations tab instead of a modal
    if (action === 'view_guidelines' || action === 'view_video_guidelines') {
      console.log('📹 Opening ChildSpace observations tab for video guidelines');
      setChildSpaceInitialTab('observations');
      setShowChildSpace(true);
      return;
    }

    // Dismiss reminder - stop showing card but keep guidelines accessible
    if (action === 'dismiss_reminder' && card?.scenario_ids) {
      console.log('🔕 Dismissing reminder for scenarios:', card.scenario_ids);
      try {
        await api.executeCardAction(activeFamilyId, 'dismiss_reminder', {
          cycle_id: cycleId,
          scenario_ids: card.scenario_ids,
        });
        console.log('✅ Reminder dismissed - guidelines still in ChildSpace');
        await refreshCards();
      } catch (error) {
        console.error('❌ Error dismissing reminder:', error);
      }
      return;
    }

    // Reject guidelines - parent decided not to film
    if (action === 'reject_guidelines' && card?.scenario_ids) {
      console.log('❌ Rejecting guidelines for scenarios:', card.scenario_ids);
      try {
        await api.executeCardAction(activeFamilyId, 'reject_guidelines', {
          cycle_id: cycleId,
          scenario_ids: card.scenario_ids,
        });
        console.log('✅ Guidelines rejected');
        await refreshCards();
      } catch (error) {
        console.error('❌ Error rejecting guidelines:', error);
      }
      return;
    }

    if (action === 'analyze_videos' && cycleId) {
      // 🎥 Trigger video analysis - runs in background, doesn't block chat
      console.log('🎬 Starting video analysis for family:', activeFamilyId, 'cycle:', cycleId);

      // Fire and forget - SSE will notify when done
      api.analyzeVideos(activeFamilyId, cycleId)
        .then(result => {
          console.log('✅ Video analysis complete:', result);
          // SSE will automatically update cards
        })
        .catch(error => {
          console.error('❌ Error analyzing videos:', error);
          // Refresh cards to clear loading state
          refreshCards();
        });

      // Immediately refresh to show "analyzing" card state
      await refreshCards();
      return;
    }

    // Upload video action (from validation_failed card) - opens guidelines view
    if (action === 'upload_video' && cycleId) {
      console.log('📹 Opening guidelines for re-upload, cycle:', cycleId);
      try {
        const result = await api.getVideoGuidelines(activeFamilyId, cycleId);
        setVideoGuidelines(result);
        setShowGuidelinesView(true);
      } catch (error) {
        console.error('❌ Error fetching guidelines for re-upload:', error);
        alert('שגיאה בטעינת ההנחיות. נא לנסות שוב.');
      }
      return;
    }

    if (action === 'upload') {
      setActiveDeepView('upload');
      setActiveViewData(null);
    } else if (action === 'view_all_guidelines') {
      // Show all guidelines in instructions view
      setActiveDeepView('instructions');
      setActiveViewData(null);
    } else if (action === 'videoGallery') {
      setActiveDeepView('videoGallery');
      setActiveViewData(null);
    } else if (action === 'journal') {
      setActiveDeepView('journal');
      setActiveViewData(null);
    } else if (action === 'parentReport') {
      setActiveDeepView('parentReport');
      setActiveViewData(null);
    } else if (action === 'proReport') {
      setActiveDeepView('professionalReport');
      setActiveViewData(null);
    } else if (action === 'experts') {
      setActiveDeepView('findExperts');
      setActiveViewData(null);
    } else if (action && action.startsWith('view_guideline_')) {
      // Find the card by action (not by index, as there may be status cards)
      const card = cards.find(c => c.action === action);

      if (card) {
        setActiveDeepView('dynamic_guideline');
        setActiveViewData(card);
      }
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion) => {
    if (suggestion.action) {
      handleCardClick(suggestion.action);
    } else {
      handleSend(suggestion.text);
    }
    setShowSuggestions(false);
  };

  // Handle deep view close
  const handleCloseDeepView = () => {
    setActiveDeepView(null);
    setActiveViewData(null);
  };

  // Living Dashboard: Handle slot action from ChildSpace
  const handleSlotAction = (action, slot) => {
    console.log('Slot action:', action, slot);
    setShowChildSpace(false);

    // Map slot actions to deep views or living document
    if (action === 'view_report') {
      // Open as Living Document for threaded conversations
      setLivingDocumentArtifact({
        artifactId: 'baseline_parent_report',
        title: 'דוח הורים'
      });
    } else if (action === 'view_guidelines') {
      setShowGuidelinesView(true);
    } else if (action === 'view_videos') {
      setActiveDeepView('videoGallery');
    } else if (action === 'view_journal') {
      setActiveDeepView('journal');
    } else if (action === 'upload_video') {
      setActiveDeepView('upload');
    } else if (action === 'add_journal_entry') {
      setActiveDeepView('journal');
    } else if (action === 'download_report') {
      // Handle download
      console.log('Download report');
    } else if (action === 'view_artifact') {
      // Open specific artifact version (from history)
      const { artifact_id } = slot;
      if (artifact_id) {
        // Determine title based on artifact type
        const titleMap = {
          'baseline_parent_report': 'דוח הורים',
          'baseline_parent_report_v0': 'דוח הורים (גרסה ראשונית)',
          'baseline_parent_report_v1': 'דוח הורים (גרסה קודמת)',
        };
        const title = titleMap[artifact_id] || artifact_id.includes('report') ? 'דוח הורים' : 'מסמך';
        setLivingDocumentArtifact({
          artifactId: artifact_id,
          title: title
        });
      }
    }
  };

  // Living Dashboard: Handle header slot click
  const handleHeaderSlotClick = (slotId) => {
    // Direct navigation based on slot
    const activeFamilyId = testMode && testFamilyId ? testFamilyId : familyId;

    if (slotId === 'current_report') {
      setLivingDocumentArtifact({
        artifactId: 'baseline_parent_report',
        title: 'דוח הורים'
      });
    } else if (slotId === 'filming_guidelines') {
      setShowGuidelinesView(true);
    } else if (slotId === 'videos') {
      setActiveDeepView('videoGallery');
    } else if (slotId === 'journal') {
      setActiveDeepView('journal');
    }
  };

  // Function to refresh cards from backend
  const refreshCards = async () => {
    try {
      // Get cards from state endpoint
      const activeFamilyId = testMode && testFamilyId ? testFamilyId : familyId;
      const response = await api.getState(activeFamilyId);
      if (response.ui && response.ui.cards) {
        setCards(response.ui.cards);
      }
    } catch (error) {
      console.error('Error refreshing cards:', error);
    }
  };

  // CRUD handlers for videos
  const handleCreateVideo = async (videoData) => {
    const newVideo = {
      id: videoData.id || 'vid_' + Date.now(), // Use existing ID from upload
      title: videoData.title || 'סרטון חדש',
      description: videoData.description || '',
      date: new Date().toLocaleDateString('he-IL'),
      duration: videoData.duration || '0:00',
      thumbnail: videoData.thumbnail || null,
      url: videoData.url || null,
      file_path: videoData.file_path || null, // Server file path
      timestamp: Date.now()
    };

    setVideos(prev => [...prev, newVideo]);

    // Note: Video is already uploaded by VideoUploadView component
    // Just refresh cards to show updated progress
    try {
      await refreshCards();
    } catch (error) {
      console.error('Error refreshing cards:', error);
    }

    return { success: true, video: newVideo, message: 'הסרטון הועלה בהצלחה' };
  };

  const handleDeleteVideo = async (videoId) => {
    setVideos(prev => prev.filter(v => v.id !== videoId));
    return { success: true, message: 'הסרטון נמחק' };
  };

  // CRUD handlers for journal entries
  const handleCreateJournalEntry = async (text, status) => {
    const newEntry = {
      id: 'entry_' + Date.now(),
      text,
      status,
      timestamp: 'עכשיו',
      date: new Date()
    };

    setJournalEntries(prev => [newEntry, ...prev]);
    return { success: true, entry: newEntry, message: 'הרשומה נשמרה בהצלחה' };
  };

  const handleDeleteJournalEntry = async (entryId) => {
    setJournalEntries(prev => prev.filter(e => e.id !== entryId));
    return { success: true, message: 'הרשומה נמחקה' };
  };

  // Handle input change
  const handleInputChange = (value) => {
    setDraftMessage(value);
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-50" dir="rtl">
      {/* Dev Panel (Development Only) */}
      {import.meta.env.DEV && (
        <DevPanel
          currentFamilyId={familyId}
          onFamilyChange={(newFamilyId) => {
            setFamilyId(newFamilyId);
            localStorage.setItem('chitta_family_id', newFamilyId);
          }}
        />
      )}

      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-gray-100 rounded-full transition">
            <Menu className="w-5 h-5 text-gray-600" />
          </button>
          <button
            onClick={onLogout}
            className="p-2 hover:bg-gray-100 rounded-full transition"
            title="התנתק"
          >
            <LogOut className="w-5 h-5 text-gray-600" />
          </button>
          {/* Child Switcher - allows switching between children and adding new ones */}
          <ChildSwitcher />
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <h1 className="text-lg font-bold text-gray-800">Chitta</h1>
            <p className="text-xs text-gray-500">
              {childName ? `המסע ההתפתחותי של ${childName}` : 'המסע ההתפתחותי'}
            </p>
          </div>
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center shadow-md">
            <MessageCircle className="w-5 h-5 text-white" />
          </div>
        </div>
      </div>

      {/* Living Dashboard: Child Space Header (Phase 2) */}
      <ChildSpaceHeader
        familyId={testMode && testFamilyId ? testFamilyId : familyId}
        childName={childName}
        childSpace={childSpace}
        onSlotClick={handleHeaderSlotClick}
        isExpanded={showChildSpace}
        onExpandClick={(expanded) => {
          console.log('App.jsx: onExpandClick received, expanded:', expanded, 'setting showChildSpace');
          setShowChildSpace(expanded);
        }}
      />

      {/* Conversation Transcript */}
      <ConversationTranscript messages={messages} isTyping={isTyping} />

      {/* Living Gestalt Cards */}
      <GestaltCards cards={cards} onCardAction={handleCardClick} />

      {/* Input Area */}
      <InputArea
        onSend={handleSend}
        onSuggestionsClick={() => setShowSuggestions(true)}
        hasSuggestions={suggestions && suggestions.length > 0}
        value={draftMessage}
        onChange={handleInputChange}
      />

      {/* Suggestions Popup */}
      {showSuggestions && (
        <SuggestionsPopup
          suggestions={suggestions}
          onSuggestionClick={handleSuggestionClick}
          onClose={() => setShowSuggestions(false)}
        />
      )}

      {/* Deep View Manager */}
      <DeepViewManager
        activeView={activeDeepView}
        onClose={handleCloseDeepView}
        viewData={activeViewData || { data: { childName } }}
        videos={videos}
        videoGuidelines={videoGuidelines}
        journalEntries={journalEntries}
        onCreateJournalEntry={handleCreateJournalEntry}
        onDeleteJournalEntry={handleDeleteJournalEntry}
        onCreateVideo={handleCreateVideo}
        onDeleteVideo={handleDeleteVideo}
        familyId={testMode && testFamilyId ? testFamilyId : familyId}
      />

      {/* Video Guidelines View (works for both demo and real mode) */}
      {showGuidelinesView && videoGuidelines && (
        <VideoGuidelinesView
          guidelines={videoGuidelines}
          childName={childName || "דניאל"}
          uploadedVideos={videos}
          onClose={() => setShowGuidelinesView(false)}
          onUploadForScenario={(selectedData) => {
            // Pass selected data to upload view via activeViewData
            setActiveViewData({
              ...selectedData,
              onBackToGuidelines: () => {
                // Close upload view and return to guidelines view
                setActiveDeepView(null);
                setActiveViewData(null);
                setShowGuidelinesView(true);
              }
            });
            setShowGuidelinesView(false);
            setActiveDeepView('upload');
          }}
        />
      )}

      {/* Video Insights View */}
      {showInsightsView && videoInsights && (
        <VideoInsightsView
          insights={videoInsights}
          onClose={() => setShowInsightsView(false)}
        />
      )}

      {/* Living Dashboard: Child Space - The Living Portrait */}
      <ChildSpace
        familyId={testMode && testFamilyId ? testFamilyId : familyId}
        isOpen={showChildSpace}
        onClose={() => {
          setShowChildSpace(false);
          setChildSpaceInitialTab('essence');  // Reset to default tab on close
        }}
        childName={childName}
        initialTab={childSpaceInitialTab}
        onVideoClick={(video) => {
          // Open video insights or gallery when a video is clicked
          setShowChildSpace(false);
          if (video.status === 'analyzed' && video.cycle_id) {
            api.getVideoInsights(testMode && testFamilyId ? testFamilyId : familyId, video.cycle_id)
              .then((insights) => {
                setVideoInsights(insights);
                setShowInsightsView(true);
              })
              .catch((error) => console.error('Error loading video insights:', error));
          } else {
            setActiveDeepView('videoGallery');
          }
        }}
        onGenerateSummary={async ({ expert, expertDescription, context, crystalInsights, comprehensive, missingGaps }) => {
          const activeFamilyId = testMode && testFamilyId ? testFamilyId : familyId;
          const result = await api.generateShareableSummary(
            activeFamilyId,
            { expert, expertDescription, context, crystalInsights, comprehensive, missingGaps }
          );
          return result;
        }}
        onUploadVideo={(scenario) => {
          // Open video upload view for the selected scenario
          console.log('📹 Opening video upload for scenario:', scenario.title);
          setShowChildSpace(false);
          setActiveDeepView('upload');
          setActiveViewData(scenario);  // Pass scenario directly, VideoUploadView expects it as scenarioData
        }}
        onAddChittaMessage={(message) => {
          // Add a Chitta message to the chat (used for guided collection greeting)
          const chittaMessage = {
            sender: 'chitta',
            text: message,
            timestamp: new Date().toISOString(),
          };
          setMessages(prev => [...prev, chittaMessage]);
        }}
      />

      {/* Living Dashboard: Living Document (Phase 3) */}
      {livingDocumentArtifact && (
        <LivingDocument
          familyId={testMode && testFamilyId ? testFamilyId : familyId}
          artifactId={livingDocumentArtifact.artifactId}
          title={livingDocumentArtifact.title}
          onClose={() => setLivingDocumentArtifact(null)}
        />
      )}

      {/* 🧪 Test Mode Banner (shows when test mode is active) */}
      <TestModeBannerPortal />

      {/* 🧪 Test Mode: Persona Selector */}
      {showPersonaSelector && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-6">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">בחר פרסונה לבדיקה</h2>
            <p className="text-gray-600 mb-6">כל פרסונה מייצגת מקרה בדיקה מציאותי עם רקע מפורט</p>

            <div className="space-y-4">
              {testPersonas.map((persona) => (
                <button
                  key={persona.id}
                  onClick={async () => {
                    setShowPersonaSelector(false);
                    setIsTyping(true);

                    try {
                      // Start test with this persona - Use NEW family_id for fresh test session
                      // Each test should start clean without carrying over old session state
                      const result = await api.startTest(persona.id);

                      // Show Chitta's initial greeting (same as real conversation)
                      const greetingMessage = {
                        sender: 'chitta',
                        text: 'היי! אני צ\'יטה 💙\n\nכיף שהגעת! אשמח להכיר את הילד שלך ולהבין איך אפשר לעזור.\n\nמה השם והגיל?',
                        timestamp: new Date().toISOString()
                      };

                      // Set messages with greeting
                      const newMessages = [...messages, greetingMessage];
                      setMessages(newMessages);

                      // Mark test mode as active
                      setTestMode(true);

                      // Reset tracking ref
                      lastProcessedMessageRef.current = null;

                      // 🧪 Store test family ID and start orchestrator
                      const testFamId = result.family_id;
                      setTestFamilyId(testFamId); // Store for API calls
                      console.log('🧪 Test mode using family ID:', testFamId);

                      await testModeOrchestrator.start(
                        persona.id,
                        persona,
                        testFamId
                      );

                      // Start auto-conversation flow with updated messages
                      console.log('🧪 Starting auto-conversation with Chitta greeting');
                      testModeOrchestrator.startAutoConversation(newMessages, handleSend);

                    } catch (error) {
                      console.error('Error starting test:', error);
                    }

                    setIsTyping(false);
                  }}
                  className="w-full p-4 bg-gradient-to-r from-purple-50 to-indigo-50 hover:from-purple-100 hover:to-indigo-100 border-2 border-purple-200 rounded-xl transition-all duration-200 hover:scale-105 text-right"
                >
                  <div className="font-bold text-lg text-gray-800 mb-1">
                    {persona.parent} - {persona.child}
                  </div>
                  <div className="text-sm text-gray-600">{persona.concern}</div>
                </button>
              ))}
            </div>

            <button
              onClick={() => setShowPersonaSelector(false)}
              className="mt-6 w-full py-2 bg-gray-200 hover:bg-gray-300 rounded-lg transition"
            >
              ביטול
            </button>
          </div>
        </div>
      )}

      {/* Global Styles */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
        .animate-fadeIn { animation: fadeIn 0.3s ease-out; }
        .animate-slideUp { animation: slideUp 0.3s ease-out; }
      `}</style>
    </div>
  );
}

export default App;
