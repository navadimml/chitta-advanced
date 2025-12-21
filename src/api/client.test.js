import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from './client';

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
});
