import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api } from './client';

// Helper to create mock fetch response
const mockFetch = (data, ok = true) => {
  global.fetch = vi.fn().mockResolvedValue({
    ok,
    statusText: ok ? 'OK' : 'Error',
    json: () => Promise.resolve(data)
  });
};

// Helper to create mock XMLHttpRequest class
const createMockXHRClass = (options = {}) => {
  const {
    status = 200,
    statusText = 'OK',
    responseText = '{}',
    shouldError = false,
    shouldAbort = false
  } = options;

  return class MockXHR {
    constructor() {
      this.open = vi.fn();
      this.send = vi.fn().mockImplementation(() => {
        setTimeout(() => {
          if (shouldError) {
            if (this._errorHandler) this._errorHandler();
          } else if (shouldAbort) {
            if (this._abortHandler) this._abortHandler();
          } else {
            if (this._loadHandler) this._loadHandler();
          }
        }, 0);
      });
      this.upload = {
        addEventListener: vi.fn().mockImplementation((event, handler) => {
          if (event === 'progress') {
            this._progressHandler = handler;
          }
        })
      };
      this.addEventListener = vi.fn().mockImplementation((event, handler) => {
        if (event === 'load') this._loadHandler = handler;
        if (event === 'error') this._errorHandler = handler;
        if (event === 'abort') this._abortHandler = handler;
      });
      this.status = status;
      this.statusText = statusText;
      this.responseText = responseText;
    }

    // Allow triggering progress from tests
    triggerProgress(loaded, total) {
      if (this._progressHandler) {
        this._progressHandler({ lengthComputable: true, loaded, total });
      }
    }
  };
};

describe('ChittaAPIClient', () => {
  let originalXHR;

  beforeEach(() => {
    vi.restoreAllMocks();
    originalXHR = global.XMLHttpRequest;
  });

  afterEach(() => {
    global.XMLHttpRequest = originalXHR;
  });

  describe('sendMessage', () => {
    it('should send message and return response', async () => {
      const mockResponse = {
        response: 'שלום! נעים מאוד להכיר.',
        ui_data: { cards: [], curiosity_state: {} }
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const result = await api.sendMessage('test_family', 'שלום');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/chat/v2/send'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('test_family')
        })
      );
      expect(result.response).toBe('שלום! נעים מאוד להכיר.');
    });

    it('should throw error on API failure', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error'
      });

      await expect(api.sendMessage('test_family', 'שלום'))
        .rejects.toThrow('API error: Internal Server Error');
    });
  });

  // ==========================================
  // Authentication tests
  // ==========================================

  describe('setAccessToken', () => {
    it('should set access token and include it in headers', async () => {
      api.setAccessToken('test_token_123');
      mockFetch({ message: 'ok' });

      await api.getState('test_family');

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test_token_123'
          })
        })
      );

      // Clean up
      api.setAccessToken(null);
    });

    it('should not include Authorization header when token is null', async () => {
      api.setAccessToken(null);
      mockFetch({ message: 'ok' });

      await api.getState('test_family');

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: { 'Content-Type': 'application/json' }
        })
      );
    });
  });

  describe('register', () => {
    it('should register a new user', async () => {
      const mockUser = { id: 'user_123', email: 'test@example.com', display_name: 'Test User' };
      mockFetch(mockUser);

      const result = await api.register('test@example.com', 'password123', 'Test User');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/register'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('test@example.com')
        })
      );
      expect(result.email).toBe('test@example.com');
    });

    it('should throw error with Hebrew message on failure', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: 'Email already exists' })
      });

      await expect(api.register('test@example.com', 'password123', 'Test User'))
        .rejects.toThrow('Email already exists');
    });

    it('should use default Hebrew error message on unknown failure', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        json: () => Promise.reject(new Error('Parse error'))
      });

      await expect(api.register('test@example.com', 'password123', 'Test User'))
        .rejects.toThrow('שגיאה בהרשמה');
    });
  });

  describe('login', () => {
    it('should login and return tokens', async () => {
      const mockResponse = {
        access_token: 'access_123',
        refresh_token: 'refresh_123',
        user: { id: 'user_123', email: 'test@example.com' }
      };
      mockFetch(mockResponse);

      const result = await api.login('test@example.com', 'password123');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('test@example.com')
        })
      );
      expect(result.access_token).toBe('access_123');
    });

    it('should throw error with Hebrew message on failure', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: 'Invalid credentials' })
      });

      await expect(api.login('test@example.com', 'wrongpassword'))
        .rejects.toThrow('Invalid credentials');
    });
  });

  describe('refreshToken', () => {
    it('should refresh access token', async () => {
      const mockResponse = { access_token: 'new_access_123' };
      mockFetch(mockResponse);

      const result = await api.refreshToken('refresh_123');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/refresh'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('refresh_123')
        })
      );
      expect(result.access_token).toBe('new_access_123');
    });

    it('should throw error on refresh failure', async () => {
      mockFetch({}, false);

      await expect(api.refreshToken('invalid_refresh'))
        .rejects.toThrow('Token refresh failed');
    });
  });

  describe('logout', () => {
    it('should logout successfully', async () => {
      mockFetch({ message: 'Logged out' });

      // Should not throw
      await api.logout('refresh_123');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/logout'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('refresh_123')
        })
      );
    });

    it('should not throw on logout failure', async () => {
      mockFetch({}, false);

      // Should not throw even on failure
      await expect(api.logout('refresh_123')).resolves.not.toThrow();
    });
  });

  describe('getMe', () => {
    it('should get current user info', async () => {
      const mockUser = { id: 'user_123', email: 'test@example.com', display_name: 'Test User' };
      mockFetch(mockUser);

      const result = await api.getMe();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/me'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.email).toBe('test@example.com');
    });

    it('should throw error on failure', async () => {
      mockFetch({}, false);

      await expect(api.getMe()).rejects.toThrow('Failed to get user info');
    });
  });

  describe('getState', () => {
    it('should fetch family state', async () => {
      const mockState = {
        state: { child: { name: 'דני' }, conversation: [] },
        ui: { cards: [], greeting: 'שלום!' }
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockState)
      });

      const result = await api.getState('test_family');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/state/test_family'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.state.child.name).toBe('דני');
    });
  });

  describe('getCuriosityState', () => {
    it('should fetch curiosity state', async () => {
      const mockCuriosity = {
        active_curiosities: [
          { focus: 'מי הילד הזה?', type: 'discovery', pull: 1.0 }
        ],
        open_questions: ['מה הוא אוהב?']
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockCuriosity)
      });

      const result = await api.getCuriosityState('test_family');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/chat/v2/curiosity/test_family'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.active_curiosities).toHaveLength(1);
      expect(result.active_curiosities[0].type).toBe('discovery');
    });
  });

  describe('acceptVideoSuggestion', () => {
    it('should accept video and return guidelines', async () => {
      const mockResult = {
        status: 'accepted',
        guidelines: { scenarios: [] }
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResult)
      });

      const result = await api.acceptVideoSuggestion('test_family', 'cycle_123');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/chat/v2/video/accept'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('cycle_123')
        })
      );
      expect(result.status).toBe('accepted');
    });
  });

  describe('declineVideoSuggestion', () => {
    it('should decline video suggestion', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: 'declined' })
      });

      const result = await api.declineVideoSuggestion('test_family', 'cycle_123');

      expect(result.status).toBe('declined');
    });
  });

  describe('executeCardAction', () => {
    it('should execute card action with params', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

      const result = await api.executeCardAction('test_family', 'dismiss', {
        cycle_id: 'cycle_123',
        card_type: 'video_suggestion'
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/gestalt/card-action'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('dismiss')
        })
      );
      expect(result.success).toBe(true);
    });
  });

  describe('getVideoGuidelines', () => {
    it('should fetch video guidelines for a cycle', async () => {
      const mockGuidelines = {
        scenarios: [
          { id: 'scenario_1', title: 'משחק חופשי', description: 'צלמו את הילד משחק' }
        ]
      };

      mockFetch(mockGuidelines);

      const result = await api.getVideoGuidelines('test_family', 'cycle_123');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/chat/v2/video/guidelines/test_family/cycle_123'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.scenarios).toHaveLength(1);
    });

    it('should throw error on failure', async () => {
      mockFetch({}, false);

      await expect(api.getVideoGuidelines('test_family', 'cycle_123'))
        .rejects.toThrow('API error');
    });
  });

  describe('getVideoInsights', () => {
    it('should fetch video insights for a cycle', async () => {
      const mockInsights = {
        insights: ['תצפית ראשונה', 'תצפית שניה'],
        confidence: 0.8
      };

      mockFetch(mockInsights);

      const result = await api.getVideoInsights('test_family', 'cycle_123');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/gestalt/test_family/insights/cycle_123'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.insights).toHaveLength(2);
    });
  });

  describe('analyzeVideos', () => {
    it('should trigger video analysis for a cycle', async () => {
      mockFetch({ status: 'analyzing', message: 'Analysis started' });

      const result = await api.analyzeVideos('test_family', 'cycle_123');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/chat/v2/video/analyze/test_family/cycle_123'),
        expect.objectContaining({ method: 'POST' })
      );
      expect(result.status).toBe('analyzing');
    });
  });

  describe('requestSynthesis', () => {
    it('should request synthesis report', async () => {
      const mockSynthesis = {
        essence_narrative: 'דני הוא ילד סקרן',
        patterns: [{ description: 'אוהב מוזיקה' }]
      };

      mockFetch(mockSynthesis);

      const result = await api.requestSynthesis('test_family');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/chat/v2/synthesis/test_family'),
        expect.objectContaining({ method: 'POST' })
      );
      expect(result.essence_narrative).toBe('דני הוא ילד סקרן');
    });
  });

  describe('getChildSpaceFull', () => {
    it('should fetch complete child space data', async () => {
      const mockChildSpace = {
        essence: { narrative: 'ילד מקסים' },
        discoveries: [],
        observations: []
      };

      mockFetch(mockChildSpace);

      const result = await api.getChildSpaceFull('test_family');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/family/test_family/child-space'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.essence.narrative).toBe('ילד מקסים');
    });
  });

  describe('getChildSpace', () => {
    it('should fetch child space', async () => {
      mockFetch({ slots: [] });

      const result = await api.getChildSpace('test_family');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/family/test_family/space'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.slots).toEqual([]);
    });
  });

  describe('getChildSpaceHeader', () => {
    it('should fetch header badges', async () => {
      const mockHeader = { badges: ['badge1', 'badge2'] };

      mockFetch(mockHeader);

      const result = await api.getChildSpaceHeader('test_family');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/family/test_family/space/header'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.badges).toHaveLength(2);
    });
  });

  describe('getSlotDetail', () => {
    it('should fetch slot detail with history', async () => {
      const mockSlot = { id: 'report', history: [] };

      mockFetch(mockSlot);

      const result = await api.getSlotDetail('test_family', 'report');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/family/test_family/space/slot/report'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.id).toBe('report');
    });
  });

  describe('getArtifact', () => {
    it('should fetch artifact content', async () => {
      const mockArtifact = { content: 'Report content', status: 'ready' };

      mockFetch(mockArtifact);

      const result = await api.getArtifact('test_family', 'baseline_report');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/artifacts/baseline_report?child_id=test_family'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.content).toBe('Report content');
    });
  });

  describe('getStructuredArtifact', () => {
    it('should fetch structured artifact with sections', async () => {
      const mockArtifact = {
        sections: [{ id: 's1', title: 'סיכום', content: 'תוכן' }]
      };

      mockFetch(mockArtifact);

      const result = await api.getStructuredArtifact('test_family', 'report_1');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/artifact/report_1/structured?child_id=test_family'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.sections).toHaveLength(1);
    });
  });

  describe('getArtifactThreads', () => {
    it('should fetch threads for artifact', async () => {
      const mockThreads = { threads: [{ id: 't1', section_id: 's1' }] };

      mockFetch(mockThreads);

      const result = await api.getArtifactThreads('test_family', 'report_1');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/artifact/report_1/threads?child_id=test_family'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.threads).toHaveLength(1);
    });
  });

  describe('createThread', () => {
    it('should create thread on artifact section', async () => {
      const mockThread = { thread_id: 'thread_123', status: 'created' };

      mockFetch(mockThread);

      const result = await api.createThread(
        'test_family',
        'report_1',
        'section_1',
        'מה זה אומר?',
        'סיכום',
        'תוכן הסעיף'
      );

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/artifact/report_1/section/section_1/thread'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('מה זה אומר?')
        })
      );
      expect(result.thread_id).toBe('thread_123');
    });
  });

  describe('getThread', () => {
    it('should fetch thread by id', async () => {
      const mockThread = { id: 'thread_123', messages: [] };

      mockFetch(mockThread);

      const result = await api.getThread('thread_123', 'report_1', 'test_family');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/thread/thread_123?artifact_id=report_1&child_id=test_family'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.id).toBe('thread_123');
    });
  });

  describe('addThreadMessage', () => {
    it('should add message to thread', async () => {
      const mockResponse = { message: 'תשובה', thread_id: 'thread_123' };

      mockFetch(mockResponse);

      const result = await api.addThreadMessage('thread_123', 'test_family', 'שאלה נוספת');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/thread/thread_123/message'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('שאלה נוספת')
        })
      );
      expect(result.message).toBe('תשובה');
    });
  });

  describe('resolveThread', () => {
    it('should resolve thread', async () => {
      mockFetch({ status: 'resolved' });

      const result = await api.resolveThread('thread_123', 'report_1');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/thread/thread_123/resolve?artifact_id=report_1'),
        expect.objectContaining({ method: 'POST' })
      );
      expect(result.status).toBe('resolved');
    });
  });

  describe('getTestPersonas', () => {
    it('should fetch test personas', async () => {
      const mockPersonas = {
        personas: [
          { id: 'p1', name: 'דני ומיכל', child: 'יוני' }
        ]
      };

      mockFetch(mockPersonas);

      const result = await api.getTestPersonas();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test/personas'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.personas).toHaveLength(1);
    });
  });

  describe('startTest', () => {
    it('should start test with persona', async () => {
      mockFetch({ family_id: 'test_family_123', status: 'started' });

      const result = await api.startTest('persona_1');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test/start'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('persona_1')
        })
      );
      expect(result.status).toBe('started');
    });

    it('should start test with custom family id', async () => {
      mockFetch({ family_id: 'custom_family', status: 'started' });

      const result = await api.startTest('persona_1', 'custom_family');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test/start'),
        expect.objectContaining({
          body: expect.stringContaining('custom_family')
        })
      );
      expect(result.family_id).toBe('custom_family');
    });
  });

  describe('generateParentResponse', () => {
    it('should generate parent response for test mode', async () => {
      mockFetch({ response: 'תשובת הורה מדומה' });

      const result = await api.generateParentResponse('test_family', 'מה שם הילד?');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test/generate-response'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('מה שם הילד?')
        })
      );
      expect(result.response).toBe('תשובת הורה מדומה');
    });
  });

  describe('generateShareableSummary', () => {
    it('should generate shareable summary', async () => {
      const mockSummary = { content: 'סיכום לשיתוף', format: 'markdown' };

      mockFetch(mockSummary);

      const result = await api.generateShareableSummary('test_family', {
        expert: { type: 'pediatrician' },
        expertDescription: 'רופא ילדים',
        context: 'בדיקה שנתית',
        crystalInsights: {},
        comprehensive: true,
        missingGaps: []
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/family/test_family/child-space/share/generate'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('pediatrician')
        })
      );
      expect(result.content).toBe('סיכום לשיתוף');
    });
  });

  describe('checkSummaryReadiness', () => {
    it('should check summary readiness for recipient', async () => {
      mockFetch({ ready: true, missing: [] });

      const result = await api.checkSummaryReadiness('test_family', 'pediatrician');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/family/test_family/child-space/share/readiness/pediatrician'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.ready).toBe(true);
    });
  });

  describe('startGuidedCollection', () => {
    it('should start guided collection mode', async () => {
      mockFetch({ status: 'started', greeting: 'בוא נתחיל' });

      const result = await api.startGuidedCollection('test_family', 'speech_therapist');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/family/test_family/child-space/share/guided-collection/start'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('speech_therapist')
        })
      );
      expect(result.status).toBe('started');
    });
  });

  describe('getTimeline', () => {
    it('should fetch timeline', async () => {
      mockFetch({ events: [], milestones: [] });

      const result = await api.getTimeline('test_family');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/timeline/test_family'),
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.events).toEqual([]);
    });
  });

  describe('generateTimeline', () => {
    it('should generate timeline infographic', async () => {
      mockFetch({ timeline_url: '/timeline/123.png' });

      const result = await api.generateTimeline('test_family', 'warm');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/timeline/generate'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('warm')
        })
      );
      expect(result.timeline_url).toBe('/timeline/123.png');
    });

    it('should throw error on failure', async () => {
      mockFetch({}, false);

      await expect(api.generateTimeline('test_family'))
        .rejects.toThrow('API error');
    });
  });

  // ==========================================
  // checkHealth tests
  // ==========================================

  describe('checkHealth', () => {
    it('should check health endpoint', async () => {
      const mockHealth = { status: 'healthy', version: '1.0.0' };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockHealth)
      });

      const result = await api.checkHealth();

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/health')
      );
      expect(result.status).toBe('healthy');
    });
  });

  // ==========================================
  // uploadVideo tests (XMLHttpRequest)
  // ==========================================

  describe('uploadVideo', () => {
    it('should upload video successfully', async () => {
      const MockXHR = createMockXHRClass({
        status: 200,
        responseText: JSON.stringify({ status: 'uploaded', video_id: 'vid_123' })
      });

      global.XMLHttpRequest = MockXHR;

      const mockFile = new Blob(['video content'], { type: 'video/mp4' });
      const result = await api.uploadVideo('test_family', 'vid_123', 'play', 60, mockFile);

      expect(result.status).toBe('uploaded');
    });

    it('should track upload progress', async () => {
      let xhrInstance;
      const MockXHR = class extends createMockXHRClass({
        status: 200,
        responseText: JSON.stringify({ status: 'uploaded' })
      }) {
        constructor() {
          super();
          xhrInstance = this;
        }
      };

      global.XMLHttpRequest = MockXHR;

      const onProgress = vi.fn();
      const mockFile = new Blob(['video content'], { type: 'video/mp4' });

      // Start upload (don't await yet)
      const uploadPromise = api.uploadVideo('test_family', 'vid_123', 'play', 60, mockFile, onProgress);

      // Wait for XHR to be created
      await new Promise(resolve => setTimeout(resolve, 0));

      // Trigger progress
      if (xhrInstance) {
        xhrInstance.triggerProgress(50, 100);
      }

      await uploadPromise;

      expect(onProgress).toHaveBeenCalledWith(50);
    });

    it('should handle upload error', async () => {
      global.XMLHttpRequest = createMockXHRClass({ shouldError: true });

      const mockFile = new Blob(['video content'], { type: 'video/mp4' });

      await expect(api.uploadVideo('test_family', 'vid_123', 'play', 60, mockFile))
        .rejects.toThrow('Upload failed');
    });

    it('should handle upload abort', async () => {
      global.XMLHttpRequest = createMockXHRClass({ shouldAbort: true });

      const mockFile = new Blob(['video content'], { type: 'video/mp4' });

      await expect(api.uploadVideo('test_family', 'vid_123', 'play', 60, mockFile))
        .rejects.toThrow('Upload cancelled');
    });

    it('should handle non-200 response', async () => {
      global.XMLHttpRequest = createMockXHRClass({
        status: 500,
        statusText: 'Internal Server Error'
      });

      const mockFile = new Blob(['video content'], { type: 'video/mp4' });

      await expect(api.uploadVideo('test_family', 'vid_123', 'play', 60, mockFile))
        .rejects.toThrow('Upload failed');
    });

    it('should handle invalid JSON response', async () => {
      global.XMLHttpRequest = createMockXHRClass({
        status: 200,
        responseText: 'not valid json'
      });

      const mockFile = new Blob(['video content'], { type: 'video/mp4' });

      await expect(api.uploadVideo('test_family', 'vid_123', 'play', 60, mockFile))
        .rejects.toThrow('Failed to parse response');
    });
  });

  // ==========================================
  // uploadVideoV2 tests (XMLHttpRequest)
  // ==========================================

  describe('uploadVideoV2', () => {
    it('should upload video v2 successfully', async () => {
      global.XMLHttpRequest = createMockXHRClass({
        status: 200,
        responseText: JSON.stringify({ status: 'uploaded', scenario_id: 'scenario_1' })
      });

      const mockFile = new Blob(['video content'], { type: 'video/mp4' });
      const result = await api.uploadVideoV2('test_family', 'cycle_123', 'scenario_1', mockFile);

      expect(result.status).toBe('uploaded');
    });

    it('should track upload progress for v2', async () => {
      let xhrInstance;
      const MockXHR = class extends createMockXHRClass({
        status: 200,
        responseText: JSON.stringify({ status: 'uploaded' })
      }) {
        constructor() {
          super();
          xhrInstance = this;
        }
      };

      global.XMLHttpRequest = MockXHR;

      const onProgress = vi.fn();
      const mockFile = new Blob(['video content'], { type: 'video/mp4' });

      const uploadPromise = api.uploadVideoV2('test_family', 'cycle_123', 'scenario_1', mockFile, onProgress);

      // Wait for XHR to be created
      await new Promise(resolve => setTimeout(resolve, 0));

      // Trigger progress
      if (xhrInstance) {
        xhrInstance.triggerProgress(75, 100);
      }

      await uploadPromise;

      expect(onProgress).toHaveBeenCalledWith(75);
    });

    it('should handle v2 upload error', async () => {
      global.XMLHttpRequest = createMockXHRClass({ shouldError: true });

      const mockFile = new Blob(['video content'], { type: 'video/mp4' });

      await expect(api.uploadVideoV2('test_family', 'cycle_123', 'scenario_1', mockFile))
        .rejects.toThrow('Upload failed');
    });

    it('should handle v2 upload abort', async () => {
      global.XMLHttpRequest = createMockXHRClass({ shouldAbort: true });

      const mockFile = new Blob(['video content'], { type: 'video/mp4' });

      await expect(api.uploadVideoV2('test_family', 'cycle_123', 'scenario_1', mockFile))
        .rejects.toThrow('Upload cancelled');
    });

    it('should handle v2 non-200 response', async () => {
      global.XMLHttpRequest = createMockXHRClass({
        status: 400,
        statusText: 'Bad Request'
      });

      const mockFile = new Blob(['video content'], { type: 'video/mp4' });

      await expect(api.uploadVideoV2('test_family', 'cycle_123', 'scenario_1', mockFile))
        .rejects.toThrow('Upload failed');
    });

    it('should handle v2 invalid JSON response', async () => {
      global.XMLHttpRequest = createMockXHRClass({
        status: 200,
        responseText: '{invalid json'
      });

      const mockFile = new Blob(['video content'], { type: 'video/mp4' });

      await expect(api.uploadVideoV2('test_family', 'cycle_123', 'scenario_1', mockFile))
        .rejects.toThrow('Failed to parse response');
    });
  });

  // ==========================================
  // Error handling tests for remaining methods
  // ==========================================

  describe('error handling', () => {
    it('getState should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.getState('test_family')).rejects.toThrow('API error');
    });

    it('getCuriosityState should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.getCuriosityState('test_family')).rejects.toThrow('API error');
    });

    it('requestSynthesis should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.requestSynthesis('test_family')).rejects.toThrow('API error');
    });

    it('acceptVideoSuggestion should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.acceptVideoSuggestion('test_family', 'cycle_1')).rejects.toThrow('API error');
    });

    it('declineVideoSuggestion should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.declineVideoSuggestion('test_family', 'cycle_1')).rejects.toThrow('API error');
    });

    it('getVideoInsights should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.getVideoInsights('test_family', 'cycle_1')).rejects.toThrow('API error');
    });

    it('analyzeVideos should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.analyzeVideos('test_family', 'cycle_1')).rejects.toThrow('API error');
    });

    it('executeCardAction should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.executeCardAction('test_family', 'dismiss')).rejects.toThrow('API error');
    });

    it('getTimeline should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.getTimeline('test_family')).rejects.toThrow('API error');
    });

    it('getChildSpace should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.getChildSpace('test_family')).rejects.toThrow('API error');
    });

    it('getChildSpaceHeader should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.getChildSpaceHeader('test_family')).rejects.toThrow('API error');
    });

    it('getSlotDetail should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.getSlotDetail('test_family', 'slot_1')).rejects.toThrow('API error');
    });

    it('getArtifact should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.getArtifact('test_family', 'artifact_1')).rejects.toThrow('API error');
    });

    it('getStructuredArtifact should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.getStructuredArtifact('test_family', 'artifact_1')).rejects.toThrow('API error');
    });

    it('getArtifactThreads should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.getArtifactThreads('test_family', 'artifact_1')).rejects.toThrow('API error');
    });

    it('createThread should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.createThread('test_family', 'artifact_1', 'section_1', 'question')).rejects.toThrow('API error');
    });

    it('getThread should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.getThread('thread_1', 'artifact_1', 'test_family')).rejects.toThrow('API error');
    });

    it('addThreadMessage should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.addThreadMessage('thread_1', 'test_family', 'message')).rejects.toThrow('API error');
    });

    it('resolveThread should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.resolveThread('thread_1', 'artifact_1')).rejects.toThrow('API error');
    });

    it('getTestPersonas should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.getTestPersonas()).rejects.toThrow('API error');
    });

    it('startTest should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.startTest('persona_1')).rejects.toThrow('API error');
    });

    it('generateParentResponse should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.generateParentResponse('test_family', 'question')).rejects.toThrow('API error');
    });

    it('getChildSpaceFull should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.getChildSpaceFull('test_family')).rejects.toThrow('API error');
    });

    it('checkSummaryReadiness should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.checkSummaryReadiness('test_family', 'pediatrician')).rejects.toThrow('API error');
    });

    it('startGuidedCollection should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.startGuidedCollection('test_family', 'pediatrician')).rejects.toThrow('API error');
    });

    it('generateShareableSummary should throw on failure', async () => {
      mockFetch({}, false);
      await expect(api.generateShareableSummary('test_family', {
        expert: {},
        expertDescription: 'test',
        context: 'test',
        crystalInsights: {}
      })).rejects.toThrow('API error');
    });
  });
});
