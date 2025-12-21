import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import InputArea from './InputArea';

describe('InputArea', () => {
  describe('rendering', () => {
    it('should render textarea with placeholder', () => {
      render(<InputArea onSend={vi.fn()} />);

      expect(screen.getByPlaceholderText('כתבי כאן את המחשבות שלך...')).toBeInTheDocument();
    });

    it('should render send button', () => {
      render(<InputArea onSend={vi.fn()} />);

      expect(screen.getByTitle('שלח')).toBeInTheDocument();
    });

    it('should render suggestions button when hasSuggestions is true', () => {
      render(<InputArea onSend={vi.fn()} hasSuggestions={true} onSuggestionsClick={vi.fn()} />);

      expect(screen.getByTitle('הצעות')).toBeInTheDocument();
    });

    it('should not render suggestions button when hasSuggestions is false', () => {
      render(<InputArea onSend={vi.fn()} hasSuggestions={false} />);

      expect(screen.queryByTitle('הצעות')).not.toBeInTheDocument();
    });

    it('should display controlled value', () => {
      render(<InputArea onSend={vi.fn()} value="שלום עולם" onChange={vi.fn()} />);

      expect(screen.getByDisplayValue('שלום עולם')).toBeInTheDocument();
    });
  });

  describe('send button', () => {
    it('should be disabled when textarea is empty', () => {
      render(<InputArea onSend={vi.fn()} value="" />);

      const sendButton = screen.getByTitle('שלח');
      expect(sendButton).toBeDisabled();
    });

    it('should be disabled when textarea has only whitespace', () => {
      render(<InputArea onSend={vi.fn()} value="   " />);

      const sendButton = screen.getByTitle('שלח');
      expect(sendButton).toBeDisabled();
    });

    it('should be enabled when textarea has content', () => {
      render(<InputArea onSend={vi.fn()} value="הודעה" />);

      const sendButton = screen.getByTitle('שלח');
      expect(sendButton).not.toBeDisabled();
    });

    it('should call onSend with message when clicked', async () => {
      const onSend = vi.fn();
      render(<InputArea onSend={onSend} value="הודעה לשליחה" />);

      fireEvent.click(screen.getByTitle('שלח'));

      await waitFor(() => {
        expect(onSend).toHaveBeenCalledWith('הודעה לשליחה');
      });
    });

    it('should not call onSend when empty', () => {
      const onSend = vi.fn();
      render(<InputArea onSend={onSend} value="" />);

      fireEvent.click(screen.getByTitle('שלח'));

      expect(onSend).not.toHaveBeenCalled();
    });
  });

  describe('keyboard handling', () => {
    it('should send message on Enter key', async () => {
      const onSend = vi.fn();
      render(<InputArea onSend={onSend} value="הודעה" onChange={vi.fn()} />);

      const textarea = screen.getByPlaceholderText('כתבי כאן את המחשבות שלך...');
      fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

      await waitFor(() => {
        expect(onSend).toHaveBeenCalledWith('הודעה');
      });
    });

    it('should not send message on Shift+Enter', () => {
      const onSend = vi.fn();
      render(<InputArea onSend={onSend} value="הודעה" onChange={vi.fn()} />);

      const textarea = screen.getByPlaceholderText('כתבי כאן את המחשבות שלך...');
      fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });

      expect(onSend).not.toHaveBeenCalled();
    });

    it('should not send empty message on Enter', () => {
      const onSend = vi.fn();
      render(<InputArea onSend={onSend} value="" onChange={vi.fn()} />);

      const textarea = screen.getByPlaceholderText('כתבי כאן את המחשבות שלך...');
      fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

      expect(onSend).not.toHaveBeenCalled();
    });
  });

  describe('onChange', () => {
    it('should call onChange when typing', () => {
      const onChange = vi.fn();
      render(<InputArea onSend={vi.fn()} value="" onChange={onChange} />);

      const textarea = screen.getByPlaceholderText('כתבי כאן את המחשבות שלך...');
      fireEvent.change(textarea, { target: { value: 'טקסט חדש' } });

      expect(onChange).toHaveBeenCalledWith('טקסט חדש');
    });
  });

  describe('suggestions button', () => {
    it('should call onSuggestionsClick when clicked', () => {
      const onSuggestionsClick = vi.fn();
      render(
        <InputArea
          onSend={vi.fn()}
          hasSuggestions={true}
          onSuggestionsClick={onSuggestionsClick}
        />
      );

      fireEvent.click(screen.getByTitle('הצעות'));

      expect(onSuggestionsClick).toHaveBeenCalled();
    });
  });

  describe('focus state', () => {
    it('should show keyboard hint when focused and empty', () => {
      render(<InputArea onSend={vi.fn()} value="" onChange={vi.fn()} />);

      const textarea = screen.getByPlaceholderText('כתבי כאן את המחשבות שלך...');
      fireEvent.focus(textarea);

      expect(screen.getByText('Shift+Enter לשורה חדשה • Enter לשליחה')).toBeInTheDocument();
    });

    it('should apply focused styling when textarea is focused', () => {
      render(<InputArea onSend={vi.fn()} value="" onChange={vi.fn()} />);

      const textarea = screen.getByPlaceholderText('כתבי כאן את המחשבות שלך...');
      fireEvent.focus(textarea);

      expect(textarea).toHaveClass('border-indigo-400');
    });

    it('should remove focused styling when textarea is blurred', () => {
      render(<InputArea onSend={vi.fn()} value="" onChange={vi.fn()} />);

      const textarea = screen.getByPlaceholderText('כתבי כאן את המחשבות שלך...');
      fireEvent.focus(textarea);
      fireEvent.blur(textarea);

      expect(textarea).toHaveClass('border-gray-200');
    });
  });

  describe('typing indicator', () => {
    it('should show encouragement message for long text', () => {
      const longText = 'א'.repeat(101); // 101 characters
      render(<InputArea onSend={vi.fn()} value={longText} onChange={vi.fn()} />);

      expect(screen.getByText('✨ מדהים! המשיכי לשתף')).toBeInTheDocument();
    });

    it('should not show encouragement for short text', () => {
      render(<InputArea onSend={vi.fn()} value="טקסט קצר" onChange={vi.fn()} />);

      expect(screen.queryByText('✨ מדהים! המשיכי לשתף')).not.toBeInTheDocument();
    });
  });

  describe('RTL support', () => {
    it('should have RTL direction on textarea', () => {
      render(<InputArea onSend={vi.fn()} />);

      const textarea = screen.getByPlaceholderText('כתבי כאן את המחשבות שלך...');
      expect(textarea).toHaveAttribute('dir', 'rtl');
    });
  });

  describe('sending state', () => {
    it('should disable send button while sending', async () => {
      const onSend = vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
      render(<InputArea onSend={onSend} value="הודעה" />);

      const sendButton = screen.getByTitle('שלח');
      fireEvent.click(sendButton);

      // Button should be disabled while sending
      await waitFor(() => {
        expect(sendButton).toBeDisabled();
      });
    });
  });
});
