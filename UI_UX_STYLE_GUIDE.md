# Chitta UI/UX Style Guide

**Last Updated**: November 2, 2025
**Purpose**: Complete visual design system, animations, and micro-interactions

---

## 🎨 Design Philosophy

Chitta's interface is designed to be:
- **Minimal** - Remove cognitive burden, show only what's needed
- **Warm** - Soft colors, gradients, rounded corners
- **Delightful** - Subtle animations that feel magical
- **Clear** - High contrast, readable typography
- **Supportive** - Never intimidating, always helpful

**Core Principle**: The interface should fade into the background, letting the conversation be the star.

---

## 🎭 Visual Identity

### Color Palette

**Primary Gradient**
```css
/* Main brand gradient - used for Chitta's messages, header, buttons */
background: linear-gradient(to right, #6366f1, #a855f7);
/* Indigo-500 to Purple-500 */
```

**Background**
```css
/* Subtle background gradient */
background: linear-gradient(to bottom right, #eff6ff, #eef2ff);
/* Blue-50 to Indigo-50 */
```

**Status Colors** (Context Cards)
```css
Completed/Success:  bg-green-50   border-green-200   text-green-700
Pending:            bg-orange-50  border-orange-200  text-orange-700
Action:             bg-blue-50    border-blue-200    text-blue-700
New/Important:      bg-purple-50  border-purple-200  text-purple-700
Processing:         bg-yellow-50  border-yellow-200  text-yellow-700
Instruction:        bg-indigo-50  border-indigo-200  text-indigo-700
Expert/Profile:     bg-teal-50    border-teal-200    text-teal-700
Upcoming:           bg-pink-50    border-pink-200    text-pink-700
Active:             bg-violet-50  border-violet-200  text-violet-700
Progress:           bg-cyan-50    border-cyan-200    text-cyan-700
```

**Neutral Colors**
```css
White:      #ffffff
Gray-50:    #f9fafb   (hover backgrounds)
Gray-100:   #f3f4f6   (borders, dividers)
Gray-200:   #e5e7eb   (inactive borders)
Gray-600:   #4b5563   (secondary text)
Gray-800:   #1f2937   (primary text)
Gray-900:   #111827   (headings)
```

**Why These Colors?**
- **Pastels**: Soft, non-threatening, suitable for sensitive topics
- **Clear Status**: Each color has distinct meaning
- **Accessible**: All combinations meet WCAG AA contrast ratios

---

## 📐 Spacing & Layout

### Container Sizes
```css
max-w-2xl  → 672px   (Deep views, modals)
max-w-4xl  → 896px   (Wide content)
h-screen   → 100vh   (Full-height app)
```

### Padding Scale
```css
p-2  → 0.5rem  (8px)   - Icon buttons
p-3  → 0.75rem (12px)  - Compact cards
p-4  → 1rem    (16px)  - Standard padding
p-5  → 1.25rem (20px)  - Modal headers, spacious sections
```

### Gap Scale
```css
gap-1  → 0.25rem (4px)  - Tight icon groups
gap-2  → 0.5rem  (8px)  - Icon + text
gap-3  → 0.75rem (12px) - Card elements
gap-4  → 1rem    (16px) - Vertical sections
```

### Border Radius
```css
rounded-lg    → 8px    - Cards
rounded-xl    → 12px   - Context cards
rounded-2xl   → 16px   - Message bubbles
rounded-3xl   → 24px   - Modals (top corners)
rounded-full  → 9999px - Buttons, avatars, pills
```

**Why Rounded?** Creates friendly, approachable feel vs. sharp corners

---

## ✍️ Typography

### Font Family
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto',
             'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans',
             'Helvetica Neue', sans-serif;
```

**System Fonts**: Optimal for each platform, Hebrew support

### Font Sizes
```css
text-xs   → 0.75rem  (12px)  - Timestamps, metadata
text-sm   → 0.875rem (14px)  - Card subtitles, secondary text
text-base → 1rem     (16px)  - Message text, inputs
text-lg   → 1.125rem (18px)  - Modal headers
text-xl   → 1.25rem  (20px)  - Page headings
```

### Font Weights
```css
font-normal   → 400  - Body text
font-semibold → 600  - Card titles, emphasis
font-bold     → 700  - Headers, important labels
```

### Line Height
```css
leading-relaxed → 1.625  - Message bubbles (comfortable reading)
```

---

## 🎬 Animations

### Core Animation Principles

1. **Subtle** - Never distracting
2. **Quick** - 200-400ms duration
3. **Purposeful** - Guide attention
4. **Natural** - Ease-out curves (deceleration feels organic)

### Animation Catalog

#### 1. Message Appear (fadeIn)
```css
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fadeIn {
  animation: fadeIn 0.3s ease-out;
}
```

**Usage**: Every new message
**Effect**: Gentle upward fade-in
**Purpose**: Draws eye to new content without jarring

#### 2. Modal Appear (slideUp)
```css
@keyframes slideUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.animate-slideUp {
  animation: slideUp 0.3s ease-out;
}
```

**Usage**: Deep views, suggestions popup
**Effect**: Bottom sheet slide-up
**Purpose**: Mobile-native feel, clear origin

#### 3. Typing Indicator (bounce)
```css
/* Three dots with staggered animation */
.animate-bounce {
  animation: bounce 1s infinite;
}

/* Stagger delays: 0ms, 150ms, 300ms */
<div style={{animationDelay: '150ms'}}></div>
```

**Usage**: When Chitta is "typing"
**Effect**: Three white dots bounce in sequence
**Purpose**: Indicates AI is thinking, creates anticipation

#### 4. Button Hover (shadow-lg)
```css
/* Tailwind utility - box-shadow transition */
hover:shadow-lg

/* Rendered as: */
transition: box-shadow 150ms ease;
```

**Usage**: Send button, action buttons
**Effect**: Shadow grows on hover
**Purpose**: Tactile feedback, feels "clickable"

#### 5. Card Hover (opacity + shadow)
```css
/* Card click target */
hover:shadow-md
group-hover:opacity-100

/* Chevron fades in */
<ChevronRight className="opacity-50 group-hover:opacity-100 transition" />
```

**Usage**: Context cards with actions
**Effect**: Shadow + chevron appears
**Purpose**: Reveals card is interactive

#### 6. Input Focus (ring)
```css
focus:outline-none
focus:ring-2
focus:ring-indigo-500

transition: box-shadow 200ms;
```

**Usage**: Text inputs, textareas
**Effect**: Indigo ring appears around input
**Purpose**: Clear focus state for accessibility

#### 7. Icon Button Hover (background)
```css
hover:bg-gray-100
hover:bg-white
hover:bg-opacity-20

transition: background-color 150ms;
```

**Usage**: Close buttons, icon-only buttons
**Effect**: Subtle background color on hover
**Purpose**: Gentle feedback without overwhelming

---

## 🎯 Micro-Interactions

### 1. Auto-Scroll on New Message

```javascript
const chatEndRef = useRef(null);

useEffect(() => {
  chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, [messages, isTyping]);
```

**Effect**: Chat smoothly scrolls to bottom
**Why Magical**: User never has to manually scroll
**Timing**: Triggered on every new message or typing state change

---

### 2. Message Replay with Delays

```javascript
data.messages.forEach((msg) => {
  setTimeout(() => {
    if (msg.sender === 'chitta') {
      setIsTyping(true);
    }
    setTimeout(() => {
      setMessages(prev => [...prev, msg]);
      setIsTyping(false);
    }, msg.sender === 'chitta' ? 800 : 0);
  }, msg.delay);
});
```

**Effect**: Messages appear one-by-one with realistic timing
**Why Magical**: Feels like a real conversation unfolding
**Timing**:
- User messages: instant
- Chitta messages: 800ms typing indicator, then appear

---

### 3. Backdrop Dismiss

```jsx
<div className="fixed inset-0 bg-black bg-opacity-30" onClick={onClose}>
  <div onClick={(e) => e.stopPropagation()}>
    {/* Modal content */}
  </div>
</div>
```

**Effect**: Click outside modal to close
**Why Magical**: Intuitive, no need for explicit "Cancel" button
**Timing**: Instant dismiss

---

### 4. Enter Key to Send

```javascript
const handleKeyPress = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
};
```

**Effect**: Press Enter to send message
**Why Magical**: Natural desktop behavior, no mouse needed
**Note**: Shift+Enter for line break (standard pattern)

---

### 5. Suggestion Click → Send

```javascript
const handleSuggestionClick = (suggestionText) => {
  handleSend(suggestionText);
  setShowSuggestions(false);
};
```

**Effect**: Clicking suggestion sends it as a message
**Why Magical**: Shortcuts typing, suggestions feel like quick replies
**Timing**: Immediate send + popup dismiss

---

### 6. Card Click → Deep View

```javascript
onClick={() => card.action && onCardClick(card.action)}
```

**Effect**: Tapping card opens full-screen detail
**Why Magical**: Direct manipulation, no intermediate steps
**Animation**: Slide-up from bottom

---

### 7. Lightbulb Pulse (Conditional)

```jsx
{hasSuggestions && (
  <button className="bg-amber-100 text-amber-600 hover:bg-amber-200 transition">
    <Lightbulb />
  </button>
)}
```

**Effect**: Lightbulb button appears when suggestions available
**Why Magical**: Appears contextually, hints at help without forcing it
**Color**: Warm amber (inviting, not urgent)

---

## 🎨 Component Patterns

### Message Bubble Pattern

**User Messages** (Right-aligned)
```jsx
<div className="flex justify-start">
  <div className="max-w-[80%] rounded-2xl px-4 py-3 shadow-sm
                  bg-white text-gray-800 border border-gray-200">
    {text}
  </div>
</div>
```

**Chitta Messages** (Left-aligned)
```jsx
<div className="flex justify-end">
  <div className="max-w-[80%] rounded-2xl px-4 py-3 shadow-sm
                  bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
    {text}
  </div>
</div>
```

**Why This Works**:
- Max 80% width: Prevents overly wide bubbles
- Rounded corners: Friendly, modern
- User = Plain white: Clarity
- Chitta = Gradient: Visually distinctive, warm
- Shadow: Subtle depth

---

### Context Card Pattern

```jsx
<div className={`${statusColor} border rounded-xl p-3
                 flex items-center justify-between
                 ${card.action ? 'cursor-pointer hover:shadow-md' : ''}
                 transition group`}>
  <div className="flex items-center gap-3">
    <div className="p-2 bg-white rounded-lg shadow-sm">
      <Icon className="w-5 h-5" />
    </div>
    <div>
      <div className="font-semibold text-sm">{title}</div>
      <div className="text-xs opacity-80">{subtitle}</div>
    </div>
  </div>
  {card.action && (
    <ChevronRight className="w-5 h-5 opacity-50 group-hover:opacity-100 transition" />
  )}
</div>
```

**Anatomy**:
1. **Outer Container**: Status color, rounded-xl, padding
2. **Icon Box**: White rounded square, contains icon
3. **Text Stack**: Title (bold) + subtitle (smaller)
4. **Chevron**: Only if actionable, fades in on hover

**Why This Works**:
- **Icon in box**: Draws attention, separates from text
- **Two-line text**: Title = what, subtitle = context
- **Chevron on hover**: Progressive disclosure
- **Status color**: Immediate visual categorization

---

### Deep View Modal Pattern

```jsx
<div className="fixed inset-0 bg-black bg-opacity-50 z-50
                flex items-end md:items-center justify-center p-4"
     onClick={onClose}>

  <div className="bg-white rounded-t-3xl md:rounded-3xl
                  w-full max-w-2xl max-h-[85vh]
                  overflow-hidden flex flex-col animate-slideUp"
       onClick={(e) => e.stopPropagation()}>

    {/* Header */}
    <div className="bg-gradient-to-r from-indigo-500 to-purple-500
                    text-white p-5 flex items-center justify-between">
      <h3 className="text-lg font-bold">{title}</h3>
      <button onClick={onClose}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
        <X />
      </button>
    </div>

    {/* Scrollable Content */}
    <div className="flex-1 overflow-y-auto p-5 space-y-4">
      {children}
    </div>

  </div>
</div>
```

**Anatomy**:
1. **Backdrop**: Full-screen dark overlay, dismissible
2. **Modal**: White card, rounded top corners (mobile) or all corners (desktop)
3. **Header**: Gradient, fixed at top, close button
4. **Content**: Scrollable, spacious padding

**Responsive**:
- Mobile: `items-end` (bottom sheet), `rounded-t-3xl` (top corners only)
- Desktop: `md:items-center` (centered), `md:rounded-3xl` (all corners)

**Why This Works**:
- **Bottom sheet on mobile**: Native mobile pattern, thumb-friendly
- **Centered on desktop**: Traditional modal, more balanced
- **Gradient header**: Brand consistency, matches Chitta's messages
- **Scroll container**: Content can be unlimited length

---

### Input Area Pattern

```jsx
<div className="bg-white border-t border-gray-200 p-4">
  <div className="flex gap-2">
    {/* Lightbulb (conditional) */}
    <button className="p-3 bg-amber-100 text-amber-600 rounded-full
                       hover:bg-amber-200 transition flex-shrink-0">
      <Lightbulb />
    </button>

    {/* Text Input */}
    <input className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200
                      rounded-full focus:outline-none focus:ring-2
                      focus:ring-indigo-500 transition"
           placeholder="שאלי אותי משהו..." />

    {/* Send Button */}
    <button className="p-3 bg-gradient-to-r from-indigo-500 to-purple-500
                       text-white rounded-full hover:shadow-lg transition
                       flex-shrink-0">
      <ArrowRight />
    </button>
  </div>
</div>
```

**Why This Works**:
- **Pills**: Rounded-full creates cohesive pill shape
- **Gradient send**: Matches Chitta's personality
- **Amber lightbulb**: Warm, inviting
- **Gray input bg**: Soft, not stark white
- **Flex-shrink-0**: Buttons never collapse on long text

---

### Suggestions Popup Pattern

```jsx
<div className="fixed inset-0 bg-black bg-opacity-30 z-40
                flex items-end justify-center"
     onClick={onClose}>

  <div className="bg-white rounded-t-3xl w-full max-w-2xl p-5
                  shadow-2xl animate-slideUp"
       onClick={(e) => e.stopPropagation()}>

    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-2">
        <Lightbulb className="text-amber-500" />
        <h4 className="font-bold">הצעות</h4>
      </div>
      <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
        <X />
      </button>
    </div>

    <div className="space-y-2">
      {suggestions.map(s => (
        <button className={`w-full ${s.color} text-white px-4 py-3
                            rounded-xl font-semibold flex items-center gap-3
                            hover:shadow-lg transition`}>
          <Icon /> {s.text}
        </button>
      ))}
    </div>

  </div>
</div>
```

**Why This Works**:
- **Bottom sheet**: Mobile-native pattern
- **Color-coded buttons**: Each suggestion has personality
- **Full-width**: Easy tap targets
- **Icon + text**: Visual + verbal
- **Hover shadow**: Tactile feedback

---

## 🎨 Advanced Styling Techniques

### Gradients

**Primary Gradient** (Most Common)
```css
bg-gradient-to-r from-indigo-500 to-purple-500
```

**Subtle Background Gradient**
```css
bg-gradient-to-br from-blue-50 to-indigo-50
```

**Content Highlight Gradients**
```css
/* Purple accent */
bg-gradient-to-r from-purple-50 to-indigo-50

/* Amber warmth */
bg-gradient-to-r from-amber-50 to-orange-50
```

**Why Gradients?**
- Adds depth without heavy shadows
- Creates visual interest in flat UI
- Reinforces brand colors

---

### Shadows

```css
/* Subtle elevation */
shadow-sm   → 0 1px 2px rgba(0,0,0,0.05)

/* Card depth */
shadow-md   → 0 4px 6px rgba(0,0,0,0.1)

/* Floating buttons */
shadow-lg   → 0 10px 15px rgba(0,0,0,0.1)

/* Modal prominence */
shadow-2xl  → 0 25px 50px rgba(0,0,0,0.25)
```

**Usage Guidelines**:
- Message bubbles: shadow-sm
- Context cards: shadow-md on hover
- Buttons: shadow-lg on hover
- Modals: shadow-2xl (backdrop creates depth)

---

### Opacity & Transparency

```css
/* Backdrop overlays */
bg-opacity-30   (suggestions)
bg-opacity-50   (deep views)

/* Secondary text */
opacity-80      (card subtitles)

/* Hidden chevrons */
opacity-50      (default state)
opacity-100     (hover reveal)
```

**Why Layered Opacity?**
- Suggestions are less critical → lighter backdrop
- Deep views are primary focus → darker backdrop
- Secondary text recedes → 80% opacity
- Interactive hints → fade in on hover

---

### Borders

```css
/* Dividers */
border-t border-gray-200

/* Card outlines */
border border-{color}-200

/* Thick accent */
border-l-4 border-{color}-400
```

**Border Strategy**:
- **Horizontal dividers**: Top border on sections
- **Card borders**: Match status color at 200 level (subtle)
- **Accent borders**: Left side, 4px thick, 400 level (stronger)

---

## 🎭 Interaction States

### Buttons

```css
/* Default */
bg-gradient-to-r from-indigo-500 to-purple-500 text-white

/* Hover */
hover:shadow-lg transition

/* Active (click) */
active:scale-95

/* Disabled */
opacity-50 cursor-not-allowed
```

### Inputs

```css
/* Default */
bg-gray-50 border border-gray-200

/* Focus */
focus:outline-none focus:ring-2 focus:ring-indigo-500

/* Error */
border-red-300 focus:ring-red-500
```

### Cards

```css
/* Default */
bg-{color}-50 border border-{color}-200

/* Hover (actionable) */
hover:shadow-md cursor-pointer

/* Active (viewing) */
border-2 border-{color}-400
```

---

## 📱 Responsive Design

### Breakpoints
```css
sm:   640px   (Large phones)
md:   768px   (Tablets)
lg:   1024px  (Desktop)
xl:   1280px  (Large desktop)
```

### Mobile-First Patterns

**Deep Views**
```css
/* Mobile: Bottom sheet */
items-end rounded-t-3xl

/* Desktop: Centered modal */
md:items-center md:rounded-3xl
```

**Content Padding**
```css
/* Mobile: Tight */
p-4

/* Desktop: Spacious */
md:p-6
```

**Text Sizing**
```css
/* Mobile: Base */
text-base

/* Desktop: Slightly larger */
md:text-lg
```

---

## ♿ Accessibility

### Color Contrast

All text/background combinations meet **WCAG AA** (4.5:1 for normal text, 3:1 for large)

Verified combinations:
- White text on indigo-500 ✓
- Gray-800 text on white ✓
- {Color}-700 text on {Color}-50 ✓

### Focus States

All interactive elements have visible focus:
```css
focus:outline-none focus:ring-2 focus:ring-indigo-500
```

### Keyboard Navigation

- Enter to send messages
- Escape to close modals
- Tab navigation works throughout

### Screen Readers

- Semantic HTML (`<button>`, `<input>`)
- `aria-label` on icon-only buttons
- `role="dialog"` on modals
- `aria-live` regions for new messages

---

## 🎨 Animation Guidelines

### When to Animate

✅ **Do Animate**:
- New content appearing (messages, cards)
- Modals opening/closing
- State changes (hover, focus)
- Loading states

❌ **Don't Animate**:
- Scrolling (auto-scroll is smooth, but no extra animation)
- Layout shifts
- Text changes
- Background colors (use `transition` for smooth fade)

### Duration Guidelines

```css
150ms → Micro-interactions (hover, focus)
300ms → Content appearing (fadeIn, slideUp)
500ms → Complex transitions (page changes)
800ms → Typing indicator delay (feels natural)
```

### Easing Functions

```css
ease-out     → Most animations (deceleration feels natural)
ease-in-out  → Reversible animations (modal open/close)
linear       → Loading spinners, progress bars
```

---

## 🎨 Icon System

### Icon Library

**Lucide React** - Consistent, modern, lightweight

**Icon Sizes**:
```css
w-4 h-4  → 16px  (Small badges, inline)
w-5 h-5  → 20px  (Standard buttons, cards)
w-6 h-6  → 24px  (Large buttons, headers)
```

### Icon Usage

**In Cards**: White rounded box background
```jsx
<div className="p-2 bg-white rounded-lg shadow-sm">
  <Icon className="w-5 h-5" />
</div>
```

**In Buttons**: Inline with text
```jsx
<button>
  <Icon className="w-5 h-5" />
  <span>Label</span>
</button>
```

**Icon-Only Buttons**: Rounded-full containers
```jsx
<button className="p-3 bg-amber-100 rounded-full">
  <Lightbulb className="w-5 h-5" />
</button>
```

---

## 🎨 RTL (Right-to-Left) Support

### Implementation

```jsx
<div dir="rtl">
  {/* All content */}
</div>
```

### RTL-Specific Styles

```css
/* Text alignment */
[dir="rtl"] {
  text-align: right;
}

/* Flexbox reversal (automatic) */
flex-row → reverses automatically

/* Chevrons */
ChevronRight in RTL → points left visually ✓
```

### Arabic/Hebrew Typography

- System fonts include Hebrew glyphs
- Line-height: 1.625 (extra space for diacritics)
- No custom web fonts (faster, better support)

---

## 🎨 Scrollbar Styling

```css
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}
```

**Why Custom Scrollbars?**
- Default scrollbars are chunky
- Custom: Subtle, matches aesthetic
- Still accessible (click/drag works)

---

## 🎯 Design Tokens (Future)

For scalability, consider extracting to design tokens:

```javascript
// tokens/colors.js
export const colors = {
  primary: {
    gradient: 'linear-gradient(to right, #6366f1, #a855f7)',
    indigo: '#6366f1',
    purple: '#a855f7'
  },
  status: {
    completed: { bg: '#f0fdf4', border: '#86efac', text: '#15803d' },
    // ... more
  }
};

// tokens/spacing.js
export const spacing = {
  xs: '0.5rem',
  sm: '0.75rem',
  md: '1rem',
  lg: '1.25rem',
  xl: '1.5rem'
};

// tokens/animations.js
export const animations = {
  durations: {
    fast: '150ms',
    normal: '300ms',
    slow: '500ms'
  },
  easings: {
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)'
  }
};
```

---

## ✨ Creating a "Magical" Experience

### The Details Matter

1. **Message Delays**: Stagger AI messages (800ms feels like thinking)
2. **Auto-Scroll**: User never manually scrolls
3. **Typing Dots**: Three dots bounce in sequence (feels alive)
4. **Backdrop Dismiss**: Click outside → instant close (intuitive)
5. **Enter to Send**: Desktop users don't reach for mouse
6. **Hover Reveals**: Chevrons appear on hover (progressive disclosure)
7. **Smooth Transitions**: All state changes fade (no jarring jumps)
8. **Contextual Suggestions**: Lightbulb appears only when relevant

### Why It Feels Good

- **Anticipation**: Typing indicator creates suspense
- **Feedback**: Every action has immediate visual response
- **Delight**: Subtle animations surprise and please
- **Clarity**: Status colors instantly communicate state
- **Ease**: Shortcuts (Enter, suggestions) reduce friction
- **Warmth**: Gradients, rounded corners, soft colors feel friendly

---

## 🎨 Customization Guide

### Rebranding Chitta

**1. Change Color Palette**
```css
/* Find and replace */
from-indigo-500 to-purple-500  →  from-{your}-500 to-{your}-500
```

**2. Update Logo/Avatar**
```jsx
<div className="w-10 h-10 bg-gradient-to-br from-{your}-500 to-{your}-500 rounded-full">
  <YourIcon />
</div>
```

**3. Adjust Typography**
```css
/* Install custom font */
@import url('https://fonts.googleapis.com/css2?family=YourFont');

body {
  font-family: 'YourFont', sans-serif;
}
```

**4. Custom Animations**
```css
@keyframes yourAnimation {
  from { /* ... */ }
  to { /* ... */ }
}
```

**5. Domain-Specific Icons**
```javascript
// Replace lucide-react icons
import { YourIcon } from 'your-icon-library';
```

---

## 📚 Related Documentation

- **ARCHITECTURE_V2.md** - Complete technical architecture
- **GRAPHITI_INTEGRATION_GUIDE.md** - Backend integration
- **CORE_INNOVATION_DETAILED.md** - Design philosophy deep dive

---

**This design system creates a warm, supportive, magical experience that makes complex interactions feel effortless.**
