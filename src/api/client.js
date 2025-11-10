/**
 * Chitta API Client
 * מתחבר ל-FastAPI backend
 */

import { demoOrchestrator } from '../services/DemoOrchestrator.jsx';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ChittaAPIClient {
  /**
   * שליחת הודעה לצ'יטה
   */
  async sendMessage(familyId, message, parentName = 'הורה') {
    // 🎬 Demo Mode: Check if demo trigger detected
    if (this._isDemoTrigger(message) && !demoOrchestrator.isActive()) {
      // Start demo mode - orchestrator will inject messages
      const scenario = demoOrchestrator.getScenario();

      // Return first message as if it came from backend
      return {
        response: scenario.messages[0].content,
        stage: 'demo',
        ui_data: {
          demo_mode: true,
          cards: []
        }
      };
    }

    // 🎬 Demo Mode: If demo is active, don't make real API calls
    if (demoOrchestrator.isActive()) {
      // Demo orchestrator handles everything
      // Return empty response - orchestrator will inject messages
      return {
        response: '',
        stage: 'demo',
        ui_data: {
          demo_mode: true,
          cards: []
        }
      };
    }

    // Normal flow: Real API call
    const response = await fetch(`${API_BASE_URL}/chat/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        family_id: familyId,
        message: message,
        parent_name: parentName
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Detect if message is a test mode trigger
   */
  _isTestModeTrigger(message) {
    const triggers = [
      'test mode',
      'start test',
      'מצב בדיקה',
      'התחל בדיקה',
      'טסט'
    ];

    const lowerMessage = message.toLowerCase();
    return triggers.some(trigger => lowerMessage.includes(trigger));
  }

  /**
   * Detect if message is a demo trigger (DEPRECATED - use test mode)
   */
  _isDemoTrigger(message) {
    // Demo mode disabled - use test mode instead
    return false;
  }

  /**
   * סיום ראיון
   */
  async completeInterview(familyId) {
    const response = await fetch(`${API_BASE_URL}/interview/complete?family_id=${familyId}`, {
      method: 'POST'
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * העלאת וידאו
   */
  async uploadVideo(familyId, videoId, scenario, durationSeconds) {
    const response = await fetch(`${API_BASE_URL}/video/upload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        family_id: familyId,
        video_id: videoId,
        scenario: scenario,
        duration_seconds: durationSeconds
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * ניתוח וידאואים
   */
  async analyzeVideos(familyId) {
    const response = await fetch(`${API_BASE_URL}/video/analyze?family_id=${familyId}`, {
      method: 'POST'
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * יצירת דוחות
   */
  async generateReports(familyId) {
    const response = await fetch(`${API_BASE_URL}/reports/generate?family_id=${familyId}`, {
      method: 'POST'
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * קבלת timeline
   */
  async getTimeline(familyId) {
    const response = await fetch(`${API_BASE_URL}/timeline/${familyId}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * בדיקת health
   */
  async checkHealth() {
    const response = await fetch(`${API_BASE_URL.replace('/api', '')}/health`);
    return response.json();
  }

  /**
   * קבלת מצב המשפחה (State)
   */
  async getState(familyId) {
    const response = await fetch(`${API_BASE_URL}/state/${familyId}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 🧪 Test Mode: Get available personas
   */
  async getTestPersonas() {
    const response = await fetch(`${API_BASE_URL}/test/personas`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 🧪 Test Mode: Start test with persona
   */
  async startTest(personaId, familyId = null) {
    const response = await fetch(`${API_BASE_URL}/test/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        persona_id: personaId,
        family_id: familyId
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 🧪 Test Mode: Generate parent response
   */
  async generateParentResponse(familyId, chittaQuestion) {
    const response = await fetch(`${API_BASE_URL}/test/generate-response`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        family_id: familyId,
        chitta_question: chittaQuestion
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 🎬 Demo Mode: Get next demo step
   */
  async getNextDemoStep(demoFamilyId) {
    const response = await fetch(`${API_BASE_URL}/demo/${demoFamilyId}/next`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 🎬 Demo Mode: Stop demo
   */
  async stopDemo(demoFamilyId) {
    const response = await fetch(`${API_BASE_URL}/demo/${demoFamilyId}/stop`, {
      method: 'POST'
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 🎬 Demo Mode: Start demo manually
   */
  async startDemo(scenarioId = 'language_concerns') {
    const response = await fetch(`${API_BASE_URL}/demo/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        scenario_id: scenarioId
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }
}

// Singleton instance
export const api = new ChittaAPIClient();
