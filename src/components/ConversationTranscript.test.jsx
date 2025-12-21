import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ConversationTranscript from './ConversationTranscript';

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

describe('ConversationTranscript', () => {
  describe('rendering', () => {
    it('should render empty state when no messages', () => {
      const { container } = render(<ConversationTranscript messages={[]} isTyping={false} />);

      // Should still render the container
      expect(container.firstChild).toBeInTheDocument();
    });

    it('should render user message', () => {
      const messages = [
        { sender: 'user', text: 'שלום, אני דני' }
      ];

      render(<ConversationTranscript messages={messages} isTyping={false} />);

      expect(screen.getByText('שלום, אני דני')).toBeInTheDocument();
    });

    it('should render chitta message', () => {
      const messages = [
        { sender: 'chitta', text: 'היי דני! נעים להכיר' }
      ];

      render(<ConversationTranscript messages={messages} isTyping={false} />);

      expect(screen.getByText('היי דני! נעים להכיר')).toBeInTheDocument();
    });

    it('should render multiple messages in order', () => {
      const messages = [
        { sender: 'chitta', text: 'שלום! מה שמך?' },
        { sender: 'user', text: 'אני דני' },
        { sender: 'chitta', text: 'נעים מאוד דני!' }
      ];

      render(<ConversationTranscript messages={messages} isTyping={false} />);

      expect(screen.getByText('שלום! מה שמך?')).toBeInTheDocument();
      expect(screen.getByText('אני דני')).toBeInTheDocument();
      expect(screen.getByText('נעים מאוד דני!')).toBeInTheDocument();
    });
  });

  describe('message styling', () => {
    it('should align user messages to the right', () => {
      const messages = [
        { sender: 'user', text: 'הודעת משתמש' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={false} />);

      const messageContainer = container.querySelector('.justify-end');
      expect(messageContainer).toBeInTheDocument();
    });

    it('should align chitta messages to the left', () => {
      const messages = [
        { sender: 'chitta', text: 'הודעת צ\'יטה' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={false} />);

      const messageContainer = container.querySelector('.justify-start');
      expect(messageContainer).toBeInTheDocument();
    });

    it('should apply gradient background to user messages', () => {
      const messages = [
        { sender: 'user', text: 'הודעת משתמש' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={false} />);

      const messageBubble = container.querySelector('.from-indigo-500');
      expect(messageBubble).toBeInTheDocument();
    });

    it('should apply white background to chitta messages', () => {
      const messages = [
        { sender: 'chitta', text: 'הודעת צ\'יטה' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={false} />);

      const messageBubble = container.querySelector('.bg-white');
      expect(messageBubble).toBeInTheDocument();
    });
  });

  describe('typing indicator', () => {
    it('should show typing indicator when isTyping is true', () => {
      const { container } = render(<ConversationTranscript messages={[]} isTyping={true} />);

      // Should have bouncing dots
      const bouncingDots = container.querySelectorAll('.animate-bounce');
      expect(bouncingDots.length).toBe(3);
    });

    it('should not show typing indicator when isTyping is false', () => {
      const { container } = render(<ConversationTranscript messages={[]} isTyping={false} />);

      const bouncingDots = container.querySelectorAll('.animate-bounce');
      expect(bouncingDots.length).toBe(0);
    });

    it('should show typing indicator after messages', () => {
      const messages = [
        { sender: 'user', text: 'שאלה' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={true} />);

      expect(screen.getByText('שאלה')).toBeInTheDocument();
      const bouncingDots = container.querySelectorAll('.animate-bounce');
      expect(bouncingDots.length).toBe(3);
    });
  });

  describe('markdown rendering', () => {
    it('should render bold text', () => {
      const messages = [
        { sender: 'chitta', text: 'זה **טקסט מודגש**' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={false} />);

      const boldText = container.querySelector('strong');
      expect(boldText).toBeInTheDocument();
      expect(boldText).toHaveTextContent('טקסט מודגש');
    });

    it('should render italic text', () => {
      const messages = [
        { sender: 'chitta', text: 'זה *טקסט נטוי*' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={false} />);

      const italicText = container.querySelector('em');
      expect(italicText).toBeInTheDocument();
      expect(italicText).toHaveTextContent('טקסט נטוי');
    });

    it('should render unordered list', () => {
      const messages = [
        { sender: 'chitta', text: '- פריט ראשון\n- פריט שני' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={false} />);

      const list = container.querySelector('ul');
      expect(list).toBeInTheDocument();
      const items = container.querySelectorAll('li');
      expect(items.length).toBe(2);
    });

    it('should render ordered list', () => {
      const messages = [
        { sender: 'chitta', text: '1. ראשון\n2. שני\n3. שלישי' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={false} />);

      const list = container.querySelector('ol');
      expect(list).toBeInTheDocument();
      const items = container.querySelectorAll('li');
      expect(items.length).toBe(3);
    });

    it('should render headings', () => {
      const messages = [
        { sender: 'chitta', text: '# כותרת ראשית\n## כותרת משנית' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={false} />);

      const h1 = container.querySelector('h1');
      const h2 = container.querySelector('h2');
      expect(h1).toHaveTextContent('כותרת ראשית');
      expect(h2).toHaveTextContent('כותרת משנית');
    });

    it('should render inline code', () => {
      const messages = [
        { sender: 'chitta', text: 'זה `קוד` בתוך משפט' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={false} />);

      const code = container.querySelector('code');
      expect(code).toBeInTheDocument();
      expect(code).toHaveTextContent('קוד');
    });

    it('should render links', () => {
      const messages = [
        { sender: 'chitta', text: 'בדוק את [הקישור](https://example.com)' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={false} />);

      const link = container.querySelector('a');
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', 'https://example.com');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('should render blockquote', () => {
      const messages = [
        { sender: 'chitta', text: '> ציטוט חשוב' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={false} />);

      const blockquote = container.querySelector('blockquote');
      expect(blockquote).toBeInTheDocument();
    });
  });

  describe('auto-scroll', () => {
    it('should call scrollIntoView when messages change', () => {
      const messages = [
        { sender: 'user', text: 'הודעה ראשונה' }
      ];

      render(<ConversationTranscript messages={messages} isTyping={false} />);

      expect(Element.prototype.scrollIntoView).toHaveBeenCalledWith({
        behavior: 'smooth',
        block: 'end'
      });
    });

    it('should call scrollIntoView when isTyping changes', () => {
      const { rerender } = render(<ConversationTranscript messages={[]} isTyping={false} />);

      vi.clearAllMocks();

      rerender(<ConversationTranscript messages={[]} isTyping={true} />);

      expect(Element.prototype.scrollIntoView).toHaveBeenCalled();
    });
  });

  describe('RTL support', () => {
    it('should have dir="auto" on message bubbles', () => {
      const messages = [
        { sender: 'chitta', text: 'הודעה בעברית' }
      ];

      const { container } = render(<ConversationTranscript messages={messages} isTyping={false} />);

      const messageBubble = container.querySelector('[dir="auto"]');
      expect(messageBubble).toBeInTheDocument();
    });
  });
});
