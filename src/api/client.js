/**
 * Chitta API Client
 * מתחבר ל-FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ChittaAPIClient {
  /**
   * שליחת הודעה לצ'יטה
   */
  async sendMessage(familyId, message, parentName = 'הורה') {
    // Real API call - Using V2 endpoint with Living Gestalt / ChittaService
    const response = await fetch(`${API_BASE_URL}/chat/v2/send`, {
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
   * העלאת וידאו (actual file upload with progress callback)
   */
  async uploadVideo(familyId, videoId, scenario, durationSeconds, videoFile, onProgress = null) {
    // Create FormData for multipart/form-data upload
    const formData = new FormData();
    formData.append('family_id', familyId);
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
      xhr.send(formData);
    });
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
   * Get artifact content
   * Fetches generated artifacts like video guidelines, reports, etc.
   */
  async getArtifact(familyId, artifactId) {
    const response = await fetch(`${API_BASE_URL}/artifacts/${artifactId}?family_id=${familyId}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  // ==========================================
  // Living Dashboard Phase 2: Daniel's Space
  // ==========================================

  /**
   * Get full child space with all slots
   */
  async getChildSpace(familyId) {
    const response = await fetch(`${API_BASE_URL}/family/${familyId}/space`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get header badges only (lightweight)
   */
  async getChildSpaceHeader(familyId) {
    const response = await fetch(`${API_BASE_URL}/family/${familyId}/space/header`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get slot detail with history
   */
  async getSlotDetail(familyId, slotId) {
    const response = await fetch(`${API_BASE_URL}/family/${familyId}/space/slot/${slotId}`);

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
  async getStructuredArtifact(familyId, artifactId) {
    const response = await fetch(
      `${API_BASE_URL}/artifact/${artifactId}/structured?family_id=${familyId}`
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get all threads for an artifact
   */
  async getArtifactThreads(familyId, artifactId) {
    const response = await fetch(
      `${API_BASE_URL}/artifact/${artifactId}/threads?family_id=${familyId}`
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Create a new thread on an artifact section
   */
  async createThread(familyId, artifactId, sectionId, question, sectionTitle = null, sectionText = null) {
    const response = await fetch(
      `${API_BASE_URL}/artifact/${artifactId}/section/${sectionId}/thread`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          family_id: familyId,
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
  async getThread(threadId, artifactId, familyId) {
    const response = await fetch(
      `${API_BASE_URL}/thread/${threadId}?artifact_id=${artifactId}&family_id=${familyId}`
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Add message to thread and get AI response
   */
  async addThreadMessage(threadId, familyId, content) {
    const response = await fetch(
      `${API_BASE_URL}/thread/${threadId}/message`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          family_id: familyId,
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
        method: 'POST'
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
   * Get current curiosity state for a family
   * Returns what the Gestalt is "curious about" - drives exploration
   */
  async getCuriosityState(familyId) {
    const response = await fetch(`${API_BASE_URL}/chat/v2/curiosity/${familyId}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Request on-demand synthesis report
   * Uses strongest model for deep pattern analysis
   */
  async requestSynthesis(familyId) {
    const response = await fetch(`${API_BASE_URL}/chat/v2/synthesis/${familyId}`, {
      method: 'POST'
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
  async acceptVideoSuggestion(familyId, cycleId) {
    const response = await fetch(`${API_BASE_URL}/chat/v2/video/accept`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        family_id: familyId,
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
  async declineVideoSuggestion(familyId, cycleId) {
    const response = await fetch(`${API_BASE_URL}/chat/v2/video/decline`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        family_id: familyId,
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
  async getVideoGuidelines(familyId, cycleId) {
    const response = await fetch(
      `${API_BASE_URL}/chat/v2/video/guidelines/${familyId}/${cycleId}`
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
  async getVideoInsights(familyId, cycleId) {
    const response = await fetch(
      `${API_BASE_URL}/gestalt/${familyId}/insights/${cycleId}`
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
  async uploadVideoV2(familyId, cycleId, scenarioId, videoFile, onProgress = null) {
    const formData = new FormData();
    formData.append('family_id', familyId);
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
      xhr.send(formData);
    });
  }

  /**
   * Analyze uploaded videos for a cycle
   * Returns insights (parent-facing) and updates hypothesis confidence
   */
  async analyzeVideos(familyId, cycleId) {
    const response = await fetch(
      `${API_BASE_URL}/chat/v2/video/analyze/${familyId}/${cycleId}`,
      { method: 'POST' }
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
  async executeCardAction(familyId, action, params = {}) {
    const response = await fetch(`${API_BASE_URL}/gestalt/card-action`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        family_id: familyId,
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
  async generateTimeline(familyId, style = 'warm') {
    const response = await fetch(`${API_BASE_URL}/timeline/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        family_id: familyId,
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
  async getTimeline(familyId) {
    const response = await fetch(`${API_BASE_URL}/timeline/${familyId}`);

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
  async getChildSpaceFull(familyId) {
    const response = await fetch(`${API_BASE_URL}/family/${familyId}/child-space`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Check if we have enough data to generate a useful summary for a recipient type
   * Returns readiness status with missing info details
   */
  async checkSummaryReadiness(familyId, recipientType) {
    const response = await fetch(
      `${API_BASE_URL}/family/${familyId}/child-space/share/readiness/${recipientType}`
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
  async startGuidedCollection(familyId, recipientType) {
    const response = await fetch(
      `${API_BASE_URL}/family/${familyId}/child-space/share/guided-collection/start`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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
  async generateShareableSummary(familyId, { expert, expertDescription, context, crystalInsights, comprehensive, missingGaps }) {
    const response = await fetch(`${API_BASE_URL}/family/${familyId}/child-space/share/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
