import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import CuriosityPanel from './CuriosityPanel';

describe('CuriosityPanel', () => {
  describe('rendering', () => {
    it('should return null when curiosityState is undefined', () => {
      const { container } = render(<CuriosityPanel curiosityState={undefined} />);
      expect(container.firstChild).toBeNull();
    });

    it('should return null when curiosities and questions are empty', () => {
      const { container } = render(
        <CuriosityPanel curiosityState={{ active_curiosities: [], open_questions: [] }} />
      );
      expect(container.firstChild).toBeNull();
    });

    it('should render header with curiosity count', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'discovery', focus: 'מי הילד הזה?' },
          { type: 'question', focus: 'מה הוא אוהב?' }
        ],
        open_questions: []
      };

      render(<CuriosityPanel curiosityState={curiosityState} />);

      expect(screen.getByText('מה אני סקרנית לגביו')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('should render only with open questions (no curiosities)', () => {
      const curiosityState = {
        active_curiosities: [],
        open_questions: ['שאלה ראשונה', 'שאלה שניה']
      };

      render(<CuriosityPanel curiosityState={curiosityState} />);

      expect(screen.getByText('מה אני סקרנית לגביו')).toBeInTheDocument();
      expect(screen.getByText('0')).toBeInTheDocument();
    });
  });

  describe('curiosity types', () => {
    it('should render discovery curiosity with blue styling', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'discovery', focus: 'מי הילד הזה?', activation: 0.8 }
        ],
        open_questions: []
      };

      const { container } = render(<CuriosityPanel curiosityState={curiosityState} />);

      expect(screen.getByText('גילוי')).toBeInTheDocument();
      expect(screen.getByText('מי הילד הזה?')).toBeInTheDocument();
      expect(container.querySelector('.bg-blue-50')).toBeInTheDocument();
    });

    it('should render question curiosity with yellow styling', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'question', focus: 'מה מפריע לו?', question: 'האם יש טריגרים ספציפיים?' }
        ],
        open_questions: []
      };

      const { container } = render(<CuriosityPanel curiosityState={curiosityState} />);

      expect(screen.getByText('שאלה')).toBeInTheDocument();
      expect(screen.getByText('מה מפריע לו?')).toBeInTheDocument();
      expect(screen.getByText('האם יש טריגרים ספציפיים?')).toBeInTheDocument();
      expect(container.querySelector('.bg-yellow-50')).toBeInTheDocument();
    });

    it('should render hypothesis curiosity with purple styling and theory', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'hypothesis', focus: 'ויסות חושי', theory: 'מוזיקה עוזרת לו להתארגן' }
        ],
        open_questions: []
      };

      const { container } = render(<CuriosityPanel curiosityState={curiosityState} />);

      expect(screen.getByText('השערה')).toBeInTheDocument();
      expect(screen.getByText('ויסות חושי')).toBeInTheDocument();
      expect(screen.getByText('מוזיקה עוזרת לו להתארגן')).toBeInTheDocument();
      expect(container.querySelector('.bg-purple-50')).toBeInTheDocument();
    });

    it('should render pattern curiosity with green styling', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'pattern', focus: 'קשר בין עייפות להתפרצויות' }
        ],
        open_questions: []
      };

      const { container } = render(<CuriosityPanel curiosityState={curiosityState} />);

      expect(screen.getByText('תבנית')).toBeInTheDocument();
      expect(screen.getByText('קשר בין עייפות להתפרצויות')).toBeInTheDocument();
      expect(container.querySelector('.bg-green-50')).toBeInTheDocument();
    });

    it('should use discovery config for unknown curiosity types', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'unknown_type', focus: 'Test focus' }
        ],
        open_questions: []
      };

      const { container } = render(<CuriosityPanel curiosityState={curiosityState} />);

      // Falls back to discovery styling
      expect(screen.getByText('גילוי')).toBeInTheDocument();
      expect(container.querySelector('.bg-blue-50')).toBeInTheDocument();
    });
  });

  describe('open questions', () => {
    it('should render open questions section', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'discovery', focus: 'Test' }
        ],
        open_questions: ['מה הוא אוהב לאכול?', 'איך הוא ישן?']
      };

      render(<CuriosityPanel curiosityState={curiosityState} />);

      expect(screen.getByText('שאלות פתוחות')).toBeInTheDocument();
      expect(screen.getByText('מה הוא אוהב לאכול?')).toBeInTheDocument();
      expect(screen.getByText('איך הוא ישן?')).toBeInTheDocument();
    });

    it('should limit open questions to 3', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'discovery', focus: 'Test' }
        ],
        open_questions: ['שאלה 1', 'שאלה 2', 'שאלה 3', 'שאלה 4', 'שאלה 5']
      };

      render(<CuriosityPanel curiosityState={curiosityState} />);

      expect(screen.getByText('שאלה 1')).toBeInTheDocument();
      expect(screen.getByText('שאלה 2')).toBeInTheDocument();
      expect(screen.getByText('שאלה 3')).toBeInTheDocument();
      expect(screen.queryByText('שאלה 4')).not.toBeInTheDocument();
      expect(screen.queryByText('שאלה 5')).not.toBeInTheDocument();
    });

    it('should not render open questions section when empty', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'discovery', focus: 'Test' }
        ],
        open_questions: []
      };

      render(<CuriosityPanel curiosityState={curiosityState} />);

      expect(screen.queryByText('שאלות פתוחות')).not.toBeInTheDocument();
    });
  });

  describe('collapse/expand', () => {
    it('should be expanded by default', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'discovery', focus: 'מי הילד הזה?' }
        ],
        open_questions: []
      };

      render(<CuriosityPanel curiosityState={curiosityState} />);

      // Content should be visible
      expect(screen.getByText('מי הילד הזה?')).toBeInTheDocument();
    });

    it('should be collapsed when collapsed prop is true', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'discovery', focus: 'מי הילד הזה?' }
        ],
        open_questions: []
      };

      render(<CuriosityPanel curiosityState={curiosityState} collapsed={true} />);

      // Content should not be visible (only header)
      expect(screen.queryByText('מי הילד הזה?')).not.toBeInTheDocument();
      // Header should still be visible
      expect(screen.getByText('מה אני סקרנית לגביו')).toBeInTheDocument();
    });

    it('should toggle expand/collapse on header click', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'discovery', focus: 'מי הילד הזה?' }
        ],
        open_questions: []
      };

      render(<CuriosityPanel curiosityState={curiosityState} />);

      // Initially expanded
      expect(screen.getByText('מי הילד הזה?')).toBeInTheDocument();

      // Click header to collapse
      fireEvent.click(screen.getByText('מה אני סקרנית לגביו'));

      // Should be collapsed now
      expect(screen.queryByText('מי הילד הזה?')).not.toBeInTheDocument();

      // Click again to expand
      fireEvent.click(screen.getByText('מה אני סקרנית לגביו'));

      // Should be expanded again
      expect(screen.getByText('מי הילד הזה?')).toBeInTheDocument();
    });

    it('should call onToggle callback when toggled', () => {
      const onToggle = vi.fn();
      const curiosityState = {
        active_curiosities: [
          { type: 'discovery', focus: 'Test' }
        ],
        open_questions: []
      };

      render(<CuriosityPanel curiosityState={curiosityState} onToggle={onToggle} />);

      // Click to collapse
      fireEvent.click(screen.getByText('מה אני סקרנית לגביו'));

      expect(onToggle).toHaveBeenCalledWith(false);

      // Click to expand
      fireEvent.click(screen.getByText('מה אני סקרנית לגביו'));

      expect(onToggle).toHaveBeenCalledWith(true);
    });
  });

  describe('activation indicator', () => {
    it('should show activation percentage as progress bar width', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'discovery', focus: 'Test', activation: 0.75 }
        ],
        open_questions: []
      };

      const { container } = render(<CuriosityPanel curiosityState={curiosityState} />);

      // Find the progress bar inner div
      const progressBar = container.querySelector('[style*="width"]');
      expect(progressBar).toHaveStyle({ width: '75%' });
    });

    it('should handle zero activation', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'discovery', focus: 'Test', activation: 0 }
        ],
        open_questions: []
      };

      const { container } = render(<CuriosityPanel curiosityState={curiosityState} />);

      const progressBar = container.querySelector('[style*="width"]');
      expect(progressBar).toHaveStyle({ width: '0%' });
    });

    it('should handle missing activation', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'discovery', focus: 'Test' } // no activation field
        ],
        open_questions: []
      };

      const { container } = render(<CuriosityPanel curiosityState={curiosityState} />);

      const progressBar = container.querySelector('[style*="width"]');
      expect(progressBar).toHaveStyle({ width: '0%' });
    });
  });

  describe('multiple curiosities', () => {
    it('should render all curiosities in order', () => {
      const curiosityState = {
        active_curiosities: [
          { type: 'discovery', focus: 'First curiosity' },
          { type: 'hypothesis', focus: 'Second curiosity', theory: 'A theory' },
          { type: 'pattern', focus: 'Third curiosity' }
        ],
        open_questions: []
      };

      render(<CuriosityPanel curiosityState={curiosityState} />);

      expect(screen.getByText('First curiosity')).toBeInTheDocument();
      expect(screen.getByText('Second curiosity')).toBeInTheDocument();
      expect(screen.getByText('Third curiosity')).toBeInTheDocument();
      expect(screen.getByText('A theory')).toBeInTheDocument();
    });
  });
});
