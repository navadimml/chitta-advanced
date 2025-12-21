/**
 * Chitta API Client
 * מתחבר ל-FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ChittaAPIClient {
  constructor() {
    this.accessToken = null;
  }

  /**
   * Set the access token for authenticated requests
   */
  setAccessToken(token) {
    this.accessToken = token;
  }

  /**
   * Get headers with auth token if available
   */
  getAuthHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }
    return headers;
  }

  // ==========================================
  // Authentication
  // ==========================================

  /**
   * Register a new user
   */
  async register(email, password, displayName) {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        display_name: displayName
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'שגיאה בהרשמה');
    }

    return response.json();
  }

  /**
   * Login with email and password
   */
  async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'שגיאה בהתחברות');
    }

    return response.json();
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshToken(refreshToken) {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: refreshToken
      })
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    return response.json();
  }

  /**
   * Logout - revoke refresh token
   */
  async logout(refreshToken) {
    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        refresh_token: refreshToken
      })
    });

    // Don't throw on logout failure - just log it
    if (!response.ok) {
      console.warn('Logout request failed');
    }
  }

  /**
   * Get current user info
   */
  async getMe() {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to get user info');
    }

    return response.json();
  }

  // ==========================================
  // Family & Children
  // ==========================================

  /**
   * Get current user's family with all children.
   * Auto-creates family + child placeholder for new users.
   */
  async getMyFamily() {
    const response = await fetch(`${API_BASE_URL}/user/me/family`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch family');
    }

    return response.json();
  }

  /**
   * Add a new child placeholder to family.
   * Child identity will be filled via conversation.
   */
  async addChild(familyId) {
    const response = await fetch(`${API_BASE_URL}/family/${familyId}/children`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to add child');
    }

    return response.json();
  }

  // ==========================================
  // Chat & Conversation
  // ==========================================

  /**
   * שליחת הודעה לצ'יטה
   */
  async sendMessage(childId, message, parentName = 'הורה') {
    // Real API call - Using V2 endpoint with Living Gestalt / ChittaService
    const response = await fetch(`${API_BASE_URL}/chat/v2/send`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        child_id: childId,
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
   * העלאת וידאו (actual file upload with progress callback)
   */
  async uploadVideo(childId, videoId, scenario, durationSeconds, videoFile, onProgress = null) {
    // Create FormData for multipart/form-data upload
    const formData = new FormData();
    formData.append('child_id', childId);
    formData.append('video_id', videoId);
    formData.append('scenario', scenario);
    formData.append('duration_seconds', durationSeconds);
    formData.append('file', videoFile);

    // Use XMLHttpRequest for upload progress tracking
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      if (onProgress) {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            onProgress(percentComplete);
          }
        });
      }

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const result = JSON.parse(xhr.responseText);
            resolve(result);
          } catch (e) {
            reject(new Error('Failed to parse response'));
          }
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      });

      // Handle errors
      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });

      xhr.addEventListener('abort', () => {
        reject(new Error('Upload cancelled'));
      });

      // Send request
      xhr.open('POST', `${API_BASE_URL}/video/upload`);
      if (this.accessToken) {
        xhr.setRequestHeader('Authorization', `Bearer ${this.accessToken}`);
      }
      xhr.send(formData);
    });
  }

  /**
   * קבלת timeline
   */
  async getTimeline(childId) {
    const response = await fetch(`${API_BASE_URL}/timeline/${childId}`, {
      headers: this.getAuthHeaders()
    });

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
   * קבלת מצב הילד (State)
   */
  async getState(childId) {
    const response = await fetch(`${API_BASE_URL}/state/${childId}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 🧪 Test Mode: Get available personas
   */
  async getTestPersonas() {
    const response = await fetch(`${API_BASE_URL}/test/personas`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 🧪 Test Mode: Start test with persona
   */
  async startTest(personaId, childId = null) {
    const response = await fetch(`${API_BASE_URL}/test/start`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        persona_id: personaId,
        child_id: childId
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
  async generateParentResponse(childId, chittaQuestion) {
    const response = await fetch(`${API_BASE_URL}/test/generate-response`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        child_id: childId,
        chitta_question: chittaQuestion
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get artifact content
   * Fetches generated artifacts like video guidelines, reports, etc.
   */
  async getArtifact(childId, artifactId) {
    const response = await fetch(`${API_BASE_URL}/artifacts/${artifactId}?child_id=${childId}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  // ==========================================
  // Living Dashboard Phase 2: Child's Space
  // ==========================================

  /**
   * Get full child space with all slots
   */
  async getChildSpace(childId) {
    const response = await fetch(`${API_BASE_URL}/family/${childId}/space`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get header badges only (lightweight)
   */
  async getChildSpaceHeader(childId) {
    const response = await fetch(`${API_BASE_URL}/family/${childId}/space/header`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get slot detail with history
   */
  async getSlotDetail(childId, slotId) {
    const response = await fetch(`${API_BASE_URL}/family/${childId}/space/slot/${slotId}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  // ==========================================
  // Living Dashboard Phase 3: Living Documents
  // ==========================================

  /**
   * Get structured artifact with sections
   */
  async getStructuredArtifact(childId, artifactId) {
    const response = await fetch(
      `${API_BASE_URL}/artifact/${artifactId}/structured?child_id=${childId}`,
      { headers: this.getAuthHeaders() }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get all threads for an artifact
   */
  async getArtifactThreads(childId, artifactId) {
    const response = await fetch(
      `${API_BASE_URL}/artifact/${artifactId}/threads?child_id=${childId}`,
      { headers: this.getAuthHeaders() }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Create a new thread on an artifact section
   */
  async createThread(childId, artifactId, sectionId, question, sectionTitle = null, sectionText = null) {
    const response = await fetch(
      `${API_BASE_URL}/artifact/${artifactId}/section/${sectionId}/thread`,
      {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          child_id: childId,
          initial_question: question,
          section_title: sectionTitle,
          section_text: sectionText
        })
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get a specific thread
   */
  async getThread(threadId, artifactId, childId) {
    const response = await fetch(
      `${API_BASE_URL}/thread/${threadId}?artifact_id=${artifactId}&child_id=${childId}`,
      { headers: this.getAuthHeaders() }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Add message to thread and get AI response
   */
  async addThreadMessage(threadId, childId, content) {
    const response = await fetch(
      `${API_BASE_URL}/thread/${threadId}/message`,
      {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          child_id: childId,
          content: content
        })
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Mark thread as resolved
   */
  async resolveThread(threadId, artifactId) {
    const response = await fetch(
      `${API_BASE_URL}/thread/${threadId}/resolve?artifact_id=${artifactId}`,
      {
        method: 'POST',
        headers: this.getAuthHeaders()
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  // ==========================================
  // Living Gestalt: Curiosity-Driven Architecture
  // ==========================================

  /**
   * Get current curiosity state for a child
   * Returns what the Gestalt is "curious about" - drives exploration
   */
  async getCuriosityState(childId) {
    const response = await fetch(`${API_BASE_URL}/chat/v2/curiosity/${childId}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Request on-demand synthesis report
   * Uses strongest model for deep pattern analysis
   */
  async requestSynthesis(childId) {
    const response = await fetch(`${API_BASE_URL}/chat/v2/synthesis/${childId}`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  // ==========================================
  // Living Gestalt: Video Evidence Flow (v2)
  // Consent-first: suggest → accept → generate → upload → analyze
  // ==========================================

  /**
   * Accept video suggestion - triggers personalized guidelines generation
   * Parent accepts the video suggestion, THEN we generate guidelines
   */
  async acceptVideoSuggestion(childId, cycleId) {
    const response = await fetch(`${API_BASE_URL}/chat/v2/video/accept`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        child_id: childId,
        cycle_id: cycleId
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Decline video suggestion - we respect their choice and don't re-ask
   */
  async declineVideoSuggestion(childId, cycleId) {
    const response = await fetch(`${API_BASE_URL}/chat/v2/video/decline`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        child_id: childId,
        cycle_id: cycleId
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get video guidelines for a cycle (after consent was given)
   * Returns parent-facing format only - no hypothesis revealed
   */
  async getVideoGuidelines(childId, cycleId) {
    const response = await fetch(
      `${API_BASE_URL}/chat/v2/video/guidelines/${childId}/${cycleId}`,
      { headers: this.getAuthHeaders() }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get video analysis insights for a cycle
   * Returns parent-appropriate insights from analyzed videos
   */
  async getVideoInsights(childId, cycleId) {
    const response = await fetch(
      `${API_BASE_URL}/gestalt/${childId}/insights/${cycleId}`,
      { headers: this.getAuthHeaders() }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Upload video for a scenario (v2 - Living Gestalt)
   * Returns upload status, triggers "uploaded" card
   */
  async uploadVideoV2(childId, cycleId, scenarioId, videoFile, onProgress = null) {
    const formData = new FormData();
    formData.append('child_id', childId);
    formData.append('cycle_id', cycleId);
    formData.append('scenario_id', scenarioId);
    formData.append('video', videoFile);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      if (onProgress) {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            onProgress(percentComplete);
          }
        });
      }

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch (e) {
            reject(new Error('Failed to parse response'));
          }
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      });

      xhr.addEventListener('error', () => reject(new Error('Upload failed')));
      xhr.addEventListener('abort', () => reject(new Error('Upload cancelled')));

      xhr.open('POST', `${API_BASE_URL}/chat/v2/video/upload`);
      if (this.accessToken) {
        xhr.setRequestHeader('Authorization', `Bearer ${this.accessToken}`);
      }
      xhr.send(formData);
    });
  }

  /**
   * Analyze uploaded videos for a cycle
   * Returns insights (parent-facing) and updates hypothesis confidence
   */
  async analyzeVideos(childId, cycleId) {
    const response = await fetch(
      `${API_BASE_URL}/chat/v2/video/analyze/${childId}/${cycleId}`,
      {
        method: 'POST',
        headers: this.getAuthHeaders()
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Execute a card action (dismiss_reminder, reject_guidelines, etc.)
   * Used for actions that need backend processing but don't have dedicated endpoints
   */
  async executeCardAction(childId, action, params = {}) {
    const response = await fetch(`${API_BASE_URL}/gestalt/card-action`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        child_id: childId,
        action: action,
        params: params
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Generate timeline infographic
   */
  async generateTimeline(childId, style = 'warm') {
    const response = await fetch(`${API_BASE_URL}/timeline/generate`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        child_id: childId,
        style: style
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get existing timeline
   */
  async getExistingTimeline(childId) {
    const response = await fetch(`${API_BASE_URL}/timeline/${childId}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  // ==========================================
  // Child Space - Living Portrait
  // ==========================================

  /**
   * Get complete ChildSpace data for the Living Portrait UI
   * Returns data for all four tabs: essence, discoveries, observations, share
   */
  async getChildSpaceFull(childId) {
    const response = await fetch(`${API_BASE_URL}/family/${childId}/child-space`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Check if we have enough data to generate a useful summary for a recipient type
   * Returns readiness status with missing info details
   */
  async checkSummaryReadiness(childId, recipientType) {
    const response = await fetch(
      `${API_BASE_URL}/family/${childId}/child-space/share/readiness/${recipientType}`,
      { headers: this.getAuthHeaders() }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Start guided collection mode for preparing a summary
   * Sets session flag that injects gap context into chat responses
   */
  async startGuidedCollection(childId, recipientType) {
    const response = await fetch(
      `${API_BASE_URL}/family/${childId}/child-space/share/guided-collection/start`,
      {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ recipient_type: recipientType })
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Generate a shareable summary adapted for a specific expert
   * Pass expert info and let model determine appropriate style
   */
  async generateShareableSummary(childId, { expert, expertDescription, context, crystalInsights, comprehensive, missingGaps }) {
    const response = await fetch(`${API_BASE_URL}/family/${childId}/child-space/share/generate`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        expert,
        expert_description: expertDescription,
        context,
        crystal_insights: crystalInsights,
        comprehensive: comprehensive || false,
        missing_gaps: missingGaps || null
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
