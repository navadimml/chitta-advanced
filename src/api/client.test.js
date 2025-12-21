import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from './client';

// Helper to create mock fetch response
const mockFetch = (data, ok = true) => {
  global.fetch = vi.fn().mockResolvedValue({
    ok,
    statusText: ok ? 'OK' : 'Error',
    json: () => Promise.resolve(data)
  });
};

describe('ChittaAPIClient', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
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
        expect.stringContaining('/state/test_family')
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
        expect.stringContaining('/chat/v2/curiosity/test_family')
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
        expect.stringContaining('/chat/v2/video/guidelines/test_family/cycle_123')
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
        expect.stringContaining('/gestalt/test_family/insights/cycle_123')
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
        expect.stringContaining('/family/test_family/child-space')
      );
      expect(result.essence.narrative).toBe('ילד מקסים');
    });
  });

  describe('getChildSpace', () => {
    it('should fetch child space', async () => {
      mockFetch({ slots: [] });

      const result = await api.getChildSpace('test_family');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/family/test_family/space')
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
        expect.stringContaining('/family/test_family/space/header')
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
        expect.stringContaining('/family/test_family/space/slot/report')
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
        expect.stringContaining('/artifacts/baseline_report?family_id=test_family')
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
        expect.stringContaining('/artifact/report_1/structured?family_id=test_family')
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
        expect.stringContaining('/artifact/report_1/threads?family_id=test_family')
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
        expect.stringContaining('/thread/thread_123?artifact_id=report_1&family_id=test_family')
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
        expect.stringContaining('/test/personas')
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
        expect.stringContaining('/family/test_family/child-space/share/readiness/pediatrician')
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
        expect.stringContaining('/timeline/test_family')
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
  });
});
