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
    // Real API call
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
   * ניתוח וידאואים
   */
  async analyzeVideos(familyId, confirmed = false) {
    const url = new URL(`${API_BASE_URL}/video/analyze`);
    url.searchParams.append('family_id', familyId);
    if (confirmed) {
      url.searchParams.append('confirmed', 'true');
    }

    const response = await fetch(url.toString(), {
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
   * 🌟 Wu Wei: Get artifact content
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

}

// Singleton instance
export const api = new ChittaAPIClient();
