/**
 * Test Mode Orchestrator
 *
 * Automates test conversations using REAL backend processing.
 * Unlike demo mode (mocked), this validates the entire Wu Wei dependency graph.
 *
 * Architecture:
 * 1. Monitors for Chitta's questions (last assistant message)
 * 2. Calls ParentSimulator API to generate realistic response
 * 3. Auto-submits response with configurable timing
 * 4. Repeats until conversation naturally completes
 */

import { api } from '../api/client.js';

class TestModeOrchestrator {
  constructor() {
    this.active = false;
    this.familyId = null;
    this.personaId = null;
    this.personaInfo = null;
    this.speed = 1.0; // 1x = normal speed
    this.paused = false;
    this.autoRunning = false;
    this.processing = false; // NEW: Track if currently processing a response
    this.lastProcessedMessageTimestamp = null; // NEW: Track last processed message

    // Callbacks
    this.onMessageGenerated = null; // (message) => void
    this.onError = null; // (error) => void
    this.onComplete = null; // () => void
  }

  /**
   * Start test mode with a specific persona
   */
  async start(personaId, personaInfo, familyId) {
    console.log('🧪 TestModeOrchestrator: Starting test mode', { personaId, familyId });

    this.active = true;
    this.familyId = familyId;
    this.personaId = personaId;
    this.personaInfo = personaInfo;
    this.paused = false;
    this.autoRunning = false;
    this.processing = false; // Reset processing flag
    this.lastProcessedMessageTimestamp = null; // Reset tracking

    return {
      success: true,
      familyId: this.familyId,
      persona: this.personaInfo
    };
  }

  /**
   * Start automated conversation flow
   * Monitors for Chitta's questions and auto-generates parent responses
   */
  async startAutoConversation(messages, sendMessageCallback) {
    if (!this.active) {
      console.warn('🧪 Cannot start auto-conversation: test mode not active');
      return;
    }

    if (this.autoRunning) {
      console.warn('🧪 Auto-conversation already running');
      return;
    }

    console.log('🧪 Starting auto-conversation');
    this.autoRunning = true;

    // Wait for next Chitta question and respond
    this._scheduleNextResponse(messages, sendMessageCallback);
  }

  /**
   * Schedule next parent response based on last Chitta message
   */
  async _scheduleNextResponse(messages, sendMessageCallback) {
    if (!this.autoRunning || !this.active) {
      return;
    }

    // CRITICAL: Prevent duplicate processing
    if (this.processing) {
      console.log('🧪 Already processing a response, skipping...');
      return;
    }

    // Wait for pause to be lifted
    if (this.paused) {
      console.log('🧪 Auto-conversation paused, waiting...');
      return; // Don't schedule when paused
    }

    // Find last Chitta message
    const lastChittaMessage = [...messages].reverse().find(m => m.sender === 'chitta');

    if (!lastChittaMessage) {
      console.log('🧪 No Chitta message found, waiting...');
      return;
    }

    // CRITICAL: Check if we already processed this message
    if (this.lastProcessedMessageTimestamp === lastChittaMessage.timestamp) {
      console.log('🧪 Already processed this message, skipping...');
      return;
    }

    console.log('🧪 Found Chitta question:', lastChittaMessage.text);

    // Mark as processing and track this message
    this.processing = true;
    this.lastProcessedMessageTimestamp = lastChittaMessage.timestamp;

    try {
      // Calculate delay based on speed (base delay: 2 seconds)
      const baseDelay = 2000;
      const delay = baseDelay / this.speed;

      console.log(`🧪 Waiting ${delay}ms before generating response (speed: ${this.speed}x)`);
      await this._sleep(delay);

      // Check if still active after delay
      if (!this.autoRunning || !this.active) {
        return;
      }

      // Generate parent response using ParentSimulator
      console.log('🧪 Generating parent response for:', lastChittaMessage.text);
      const result = await api.generateParentResponse(
        this.familyId,
        lastChittaMessage.text
      );

      const parentResponse = result.parent_response;
      console.log('🧪 Generated response:', parentResponse);

      // Notify callback
      if (this.onMessageGenerated) {
        this.onMessageGenerated({
          sender: 'user',
          text: parentResponse,
          timestamp: new Date().toISOString(),
          testMode: true
        });
      }

      // Auto-submit the response
      await this._sleep(500); // Small delay before submitting

      if (this.autoRunning && this.active) {
        console.log('🧪 Auto-submitting parent response');
        await sendMessageCallback(parentResponse);
      }

    } catch (error) {
      console.error('🧪 Error generating parent response:', error);
      if (this.onError) {
        this.onError(error);
      }
    } finally {
      // CRITICAL: Always reset processing flag when done
      this.processing = false;
      console.log('🧪 Response processing complete');
    }
  }

  /**
   * Trigger next response manually (called after Chitta responds)
   */
  async generateNextResponse(messages, sendMessageCallback) {
    if (!this.active || !this.autoRunning) {
      return;
    }

    // Schedule next response
    this._scheduleNextResponse(messages, sendMessageCallback);
  }

  /**
   * Pause auto-conversation
   */
  pause() {
    console.log('🧪 Pausing auto-conversation');
    this.paused = true;
  }

  /**
   * Resume auto-conversation
   */
  resume() {
    console.log('🧪 Resuming auto-conversation');
    this.paused = false;
  }

  /**
   * Set conversation speed
   */
  setSpeed(speed) {
    console.log(`🧪 Setting speed to ${speed}x`);
    this.speed = speed;
  }

  /**
   * Stop test mode completely
   */
  stop() {
    console.log('🧪 Stopping test mode');
    this.active = false;
    this.autoRunning = false;
    this.paused = false;
    this.processing = false; // Reset processing flag
    this.lastProcessedMessageTimestamp = null; // Reset tracking
    this.familyId = null;
    this.personaId = null;
    this.personaInfo = null;
  }

  /**
   * Check if test mode is active
   */
  isActive() {
    return this.active;
  }

  /**
   * Check if auto-conversation is running
   */
  isAutoRunning() {
    return this.autoRunning;
  }

  /**
   * Get current persona info
   */
  getPersonaInfo() {
    return this.personaInfo;
  }

  /**
   * Get current state
   */
  getState() {
    return {
      active: this.active,
      autoRunning: this.autoRunning,
      paused: this.paused,
      speed: this.speed,
      familyId: this.familyId,
      personaId: this.personaId,
      personaInfo: this.personaInfo
    };
  }

  /**
   * Helper: sleep
   */
  _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Singleton instance
export const testModeOrchestrator = new TestModeOrchestrator();
