import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import GestaltCards from './GestaltCards';

describe('GestaltCards', () => {
  describe('rendering', () => {
    it('should return null when cards array is empty', () => {
      const { container } = render(<GestaltCards cards={[]} onCardAction={vi.fn()} />);
      expect(container.firstChild).toBeNull();
    });

    it('should return null when cards is undefined', () => {
      const { container } = render(<GestaltCards cards={undefined} onCardAction={vi.fn()} />);
      expect(container.firstChild).toBeNull();
    });

    it('should render section header when cards exist', () => {
      const cards = [{ type: 'video_suggestion', title: 'Test', description: 'Test desc' }];
      render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      expect(screen.getByText('מה עכשיו?')).toBeInTheDocument();
    });

    it('should render card title and description', () => {
      const cards = [{
        type: 'video_suggestion',
        title: 'הצעה לצילום',
        description: 'סרטון יעזור להבין את ההתנהגות'
      }];

      render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      expect(screen.getByText('הצעה לצילום')).toBeInTheDocument();
      expect(screen.getByText('סרטון יעזור להבין את ההתנהגות')).toBeInTheDocument();
    });

    it('should render multiple cards', () => {
      const cards = [
        { type: 'video_suggestion', title: 'Card 1', description: 'Desc 1' },
        { type: 'video_guidelines_ready', title: 'Card 2', description: 'Desc 2' },
      ];

      render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      expect(screen.getByText('Card 1')).toBeInTheDocument();
      expect(screen.getByText('Card 2')).toBeInTheDocument();
    });
  });

  describe('card types', () => {
    it('should render video_suggestion card with violet styling', () => {
      const cards = [{
        type: 'video_suggestion',
        title: 'Video Suggestion',
        description: 'Test'
      }];

      const { container } = render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      const card = container.querySelector('.border-violet-200');
      expect(card).toBeInTheDocument();
    });

    it('should render video_guidelines_ready card with emerald styling', () => {
      const cards = [{
        type: 'video_guidelines_ready',
        title: 'Guidelines Ready',
        description: 'Test'
      }];

      const { container } = render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      const card = container.querySelector('.border-emerald-200');
      expect(card).toBeInTheDocument();
    });

    it('should render video_analyzed card (feedback type)', () => {
      const cards = [{
        type: 'video_analyzed',
        title: 'Analysis Complete',
        description: 'Insights integrated'
      }];

      const { container } = render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      const card = container.querySelector('.border-teal-200');
      expect(card).toBeInTheDocument();
    });

    it('should use default styling for unknown card types', () => {
      const cards = [{
        type: 'unknown_type',
        title: 'Unknown Card',
        description: 'Test'
      }];

      const { container } = render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      const card = container.querySelector('.border-gray-200');
      expect(card).toBeInTheDocument();
    });
  });

  describe('actions', () => {
    it('should render action buttons', () => {
      const cards = [{
        type: 'video_suggestion',
        title: 'Test',
        description: 'Test',
        actions: [
          { action: 'accept_video', label: 'אשמח!', primary: true },
          { action: 'decline_video', label: 'לא עכשיו', primary: false }
        ]
      }];

      render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      expect(screen.getByText('אשמח!')).toBeInTheDocument();
      expect(screen.getByText('לא עכשיו')).toBeInTheDocument();
    });

    it('should call onCardAction with action and card when button clicked', async () => {
      const onCardAction = vi.fn();
      const cards = [{
        type: 'video_suggestion',
        title: 'Test',
        description: 'Test',
        cycle_id: 'cycle_123',
        actions: [
          { action: 'accept_video', label: 'אשמח!', primary: true }
        ]
      }];

      render(<GestaltCards cards={cards} onCardAction={onCardAction} />);

      fireEvent.click(screen.getByText('אשמח!'));

      await waitFor(() => {
        expect(onCardAction).toHaveBeenCalledWith('accept_video', expect.objectContaining({
          cycle_id: 'cycle_123',
          type: 'video_suggestion'
        }));
      });
    });

    it('should show loading state for long-running actions', async () => {
      const onCardAction = vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
      const cards = [{
        type: 'video_suggestion',
        title: 'Test',
        description: 'Test',
        actions: [
          { action: 'accept_video', label: 'אשמח!', primary: true }
        ]
      }];

      render(<GestaltCards cards={cards} onCardAction={onCardAction} />);

      fireEvent.click(screen.getByText('אשמח!'));

      // Should show loading text
      await waitFor(() => {
        expect(screen.getByText('מעבד...')).toBeInTheDocument();
      });
    });
  });

  describe('dismiss button', () => {
    it('should render dismiss button when card is dismissible', () => {
      const cards = [{
        type: 'video_suggestion',
        title: 'Test',
        description: 'Test',
        dismissible: true
      }];

      const { container } = render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      // X button should be present
      const dismissButton = container.querySelector('button');
      expect(dismissButton).toBeInTheDocument();
    });

    it('should not render dismiss button when card is not dismissible', () => {
      const cards = [{
        type: 'video_guidelines_generating',
        title: 'Test',
        description: 'Test',
        dismissible: false
      }];

      render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      // No buttons should be present (no actions, not dismissible)
      const buttons = screen.queryAllByRole('button');
      expect(buttons).toHaveLength(0);
    });

    it('should call onCardAction with dismiss when X clicked', async () => {
      const onCardAction = vi.fn();
      const cards = [{
        type: 'video_suggestion',
        title: 'Test',
        description: 'Test',
        dismissible: true,
        cycle_id: 'cycle_456'
      }];

      const { container } = render(<GestaltCards cards={cards} onCardAction={onCardAction} />);

      const dismissButton = container.querySelector('button');
      fireEvent.click(dismissButton);

      await waitFor(() => {
        expect(onCardAction).toHaveBeenCalledWith('dismiss', expect.objectContaining({
          cycle_id: 'cycle_456'
        }));
      });
    });
  });

  describe('loading states', () => {
    it('should show loading spinner for generating cards', () => {
      const cards = [{
        type: 'video_guidelines_generating',
        title: 'מכין הנחיות...',
        description: 'Test'
      }];

      const { container } = render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      // Should have animate-spin class on loader
      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should show loading spinner for analyzing cards', () => {
      const cards = [{
        type: 'video_analyzing',
        title: 'מנתח...',
        description: 'Test'
      }];

      const { container } = render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should show loading when card.loading is true', () => {
      const cards = [{
        type: 'video_suggestion',
        title: 'Test',
        description: 'Test',
        loading: true
      }];

      const { container } = render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should hide dismiss button when loading', () => {
      const cards = [{
        type: 'video_suggestion',
        title: 'Test',
        description: 'Test',
        dismissible: true,
        loading: true
      }];

      render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      // No dismiss button when loading
      const buttons = screen.queryAllByRole('button');
      expect(buttons).toHaveLength(0);
    });
  });

  describe('validation failed card', () => {
    it('should render validation failed card with amber styling', () => {
      const cards = [{
        type: 'video_validation_failed',
        title: 'הסרטון לא תואם',
        description: 'נסו שוב',
        actions: [
          { action: 'upload_video', label: 'להעלות שוב', primary: true }
        ]
      }];

      const { container } = render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      const card = container.querySelector('.border-amber-300');
      expect(card).toBeInTheDocument();
      expect(screen.getByText('להעלות שוב')).toBeInTheDocument();
    });
  });

  describe('baseline video suggestion', () => {
    it('should render baseline video suggestion with sky styling', () => {
      const cards = [{
        type: 'baseline_video_suggestion',
        title: 'סרטון היכרות',
        description: 'נשמח לראות את הילד',
        actions: [
          { action: 'accept_baseline_video', label: 'בשמחה', primary: true }
        ]
      }];

      const { container } = render(<GestaltCards cards={cards} onCardAction={vi.fn()} />);

      const card = container.querySelector('.border-sky-200');
      expect(card).toBeInTheDocument();
    });
  });
});
