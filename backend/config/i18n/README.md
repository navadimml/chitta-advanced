# Internationalization (i18n) Guide

## Structure

```
i18n/
├── README.md           # This file
├── _schema.yaml        # Defines ALL keys (source of truth)
├── he.yaml             # Hebrew translations (default, RTL)
└── en.yaml             # English translations (add more as needed, LTR)
```

## How It Works

1. **`_schema.yaml`** defines every translation key with:
   - Description of when/where it's used
   - Required placeholders
   - Context for translators

2. **Language files** (`he.yaml`, `en.yaml`) implement the schema:
   - Must have all keys from schema
   - Must include language metadata (direction, locale, etc.)
   - Can add language-specific formatting

## Language Metadata (Required)

Every language file must start with metadata:

```yaml
# Required fields
language: he              # ISO 639-1 code
direction: rtl            # "rtl" or "ltr"
name: "עברית"             # Native language name

# Optional fields
locale: he-IL             # Full locale for formatting
font_family: Heebo        # Recommended font
```

### RTL vs LTR Languages

| Direction | Languages |
|-----------|-----------|
| RTL | Hebrew (he), Arabic (ar), Persian (fa), Urdu (ur) |
| LTR | English (en), Spanish (es), French (fr), Russian (ru) |

## Using Direction in Code

```python
from app.services.i18n_service import get_language_config, is_rtl

# Get full language config for API/frontend
config = get_language_config()
# Returns: {"code": "he", "direction": "rtl", "is_rtl": true, ...}

# Quick RTL check
if is_rtl():
    # Apply RTL-specific logic
```

### Frontend Integration

Include language config in API responses for the frontend:

```python
# In your API response
response = {
    "data": {...},
    "language": get_language_config()
}
```

Frontend can then apply:
```jsx
<div dir={language.direction} style={{ fontFamily: language.font_family }}>
  {content}
</div>
```

## Adding a New Language

1. Copy `he.yaml` to `{language_code}.yaml`
2. Update metadata at the top:
   ```yaml
   language: ar
   direction: rtl  # or ltr
   name: "العربية"
   locale: ar-SA
   font_family: Noto Sans Arabic
   ```
3. Translate all values (keep keys and `{placeholders}` intact)
4. Set `CHITTA_LANGUAGE=ar` environment variable

## Adding a New Translation Key

1. **First**: Add to `_schema.yaml` with description and placeholders
2. **Then**: Add to ALL language files

## Placeholder Syntax

Use `{placeholder_name}` for dynamic values:

```yaml
greeting: "Hello {child_name}, you are {age} years old"
```

Available placeholders depend on context - see schema for each key.

## Key Naming Convention

Hierarchical, dot-separated, describing location and purpose:

```
{category}.{subcategory}.{specific_context}
```

Examples:
- `greetings.first_visit` - First time user greeting
- `greetings.returning.short_absence` - Returning after 1-7 days
- `cards.returning_user.title` - Card title for returning users
- `domain.concerns.speech` - Label for "speech" concern type

## Categories

| Category | Purpose |
|----------|---------|
| `greetings` | User-facing greetings based on context |
| `cards` | UI card content (title, body, footer) |
| `moments` | Moment-triggered messages |
| `domain` | Domain value labels (concerns, stages, etc.) |
| `milestones` | Conversation progress milestones |
| `errors` | Error messages |
| `ui` | General UI text (buttons, labels) |
| `time` | Time-related expressions |

## Best Practices

1. **Keep text in YAML, logic in Python**
2. **Use descriptive keys** - the key should explain the context
3. **Document placeholders** - list what's available for each key
4. **Test all languages** - missing keys cause runtime errors
5. **LLM prompts stay in English** - better model performance
6. **Always include direction** - for proper UI layout
