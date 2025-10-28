# Chitta Cards Reference - Color Coding & Icons
*Exact match with main branch*

## Color Coding System

```javascript
const colors = {
  completed: 'bg-green-50 border-green-200 text-green-700',
  pending: 'bg-orange-50 border-orange-200 text-orange-700',
  action: 'bg-blue-50 border-blue-200 text-blue-700',
  new: 'bg-purple-50 border-purple-200 text-purple-700',
  processing: 'bg-yellow-50 border-yellow-200 text-yellow-700',
  instruction: 'bg-indigo-50 border-indigo-200 text-indigo-700',
  expert: 'bg-teal-50 border-teal-200 text-teal-700',
  upcoming: 'bg-pink-50 border-pink-200 text-pink-700',
  active: 'bg-violet-50 border-violet-200 text-violet-700',
  progress: 'bg-cyan-50 border-cyan-200 text-cyan-700'
};
```

---

## Interview Stage (welcome)

Cards appear progressively as conversation develops:

### Card 1: Interview Status
**When:** After first message (num_messages > 0)
```json
{
  "icon": "MessageCircle",
  "title": "מתנהל ראיון",
  "subtitle": "התקדמות: מידע בסיסי | תובנות עמוקות | סיכום",
  "status": "processing",
  "action": null
}
```
**Color:** Yellow (processing)

### Card 2: Topics Discussed
**When:** After 2+ messages (num_messages >= 2)
```json
{
  "icon": "CheckCircle",
  "title": "נושאים שנדונו",
  "subtitle": "גיל, דיבור, תקשורת",
  "status": "progress",
  "action": null
}
```
**Color:** Cyan (progress)

### Card 3: Estimated Time
**When:** After 3-6 messages (num_messages >= 3 && < 7)
```json
{
  "icon": "Clock",
  "title": "זמן משוער",
  "subtitle": "עוד 10-15 דקות",
  "status": "pending",
  "action": null
}
```
**Color:** Orange (pending)

---

## Video Upload Stage (video_upload)

### Card 1: Guidelines Summary
```json
{
  "icon": "Video",
  "title": "הוראות צילום",
  "subtitle": "3 תרחישים",
  "status": "pending",
  "action": "view_all_guidelines"
}
```
**Color:** Orange (pending)

### Card 2: Overall Progress
```json
{
  "icon": "CheckCircle",
  "title": "ההתקדמות שלך",
  "subtitle": "ראיון ✓ | סרטונים (0/3)",
  "status": "progress",
  "action": null,
  "journey_step": 2,
  "journey_total": 5
}
```
**Color:** Cyan (progress)
**Special:** Includes breadcrumbs navigation

### Card 3: Upload Video
```json
{
  "icon": "Upload",
  "title": "העלאת סרטון",
  "subtitle": "לחצי כדי להעלות",
  "status": "action",
  "action": "upload"
}
```
**Color:** Blue (action)

### Cards 4-6: Individual Guidelines
```json
{
  "icon": "Video",
  "title": "משחק חופשי",
  "subtitle": "עם ילדים אחרים, 3-5 דקות",
  "status": "instruction",
  "action": "view_guideline_0"
}
```
**Color:** Indigo (instruction)

---

## Analysis Stage (video_analysis)

### Card 1: Analysis In Progress
```json
{
  "icon": "Clock",
  "title": "ניתוח בתהליך",
  "subtitle": "משוער: 24 שעות",
  "status": "processing",
  "action": null
}
```
**Color:** Yellow (processing)

### Card 2: Video Gallery
```json
{
  "icon": "Video",
  "title": "צפייה בסרטונים",
  "subtitle": "3 סרטונים",
  "status": "action",
  "action": "videoGallery"
}
```
**Color:** Blue (action)

### Card 3: Journal
```json
{
  "icon": "MessageCircle",
  "title": "יומן יוני",
  "subtitle": "הוסיפי הערות מהימים האחרונים",
  "status": "action",
  "action": "journal"
}
```
**Color:** Blue (action)
**Note:** Uses MessageCircle icon in analysis stage

---

## Report Generation Stage (report_generation)

### Card 1: Parent Report
```json
{
  "icon": "FileText",
  "title": "מדריך להורים",
  "subtitle": "הסברים ברורים עבורך",
  "status": "new",
  "action": "parentReport"
}
```
**Color:** Purple (new)

### Card 2: Professional Report
```json
{
  "icon": "FileText",
  "title": "דוח מקצועי",
  "subtitle": "לשיתוף עם מומחים",
  "status": "new",
  "action": "proReport"
}
```
**Color:** Purple (new)

### Card 3: Find Experts
```json
{
  "icon": "Search",
  "title": "מציאת מומחים",
  "subtitle": "מבוסס על הממצאים",
  "status": "action",
  "action": "experts"
}
```
**Color:** Blue (action)

---

## Consultation Stage (consultation)

### Card 1: Consultation Mode
```json
{
  "icon": "Brain",
  "title": "מצב התייעצות",
  "subtitle": "שאלי כל שאלה",
  "status": "processing",
  "action": "consultDoc"
}
```
**Color:** Yellow (processing)

### Card 2: Upload Documents
```json
{
  "icon": "FileText",
  "title": "העלאת מסמכים",
  "subtitle": "אבחונים, סיכומים, דוחות",
  "status": "action",
  "action": "uploadDoc"
}
```
**Color:** Blue (action)

### Card 3: Journal
```json
{
  "icon": "Book",
  "title": "יומן יוני",
  "subtitle": "הערות והתבוננויות",
  "status": "action",
  "action": "journal"
}
```
**Color:** Blue (action)
**Note:** Uses Book icon in consultation stage (different from analysis)

---

## Icon Usage Summary

### Frequently Used Icons:
- **Video** - Video-related actions (guidelines, gallery)
- **CheckCircle** - Progress indicators (NOT CheckCircle2!)
- **MessageCircle** - Interview status, journal (in analysis stage)
- **Book** - Journal (in consultation stage)
- **FileText** - Reports and documents
- **Clock** - Time estimates and processing
- **Upload** - File/video upload
- **Brain** - Consultation mode
- **Search** - Finding experts

### Icon Variations by Context:
- **Journal** card uses **MessageCircle** in analysis stage
- **Journal** card uses **Book** in consultation stage

---

## Status Color Usage by Stage

| Stage | Statuses Used |
|-------|--------------|
| Interview | processing, progress, pending |
| Video Upload | pending, progress, action, instruction |
| Analysis | processing, action |
| Reports | new, action |
| Consultation | processing, action |

---

## Common Mistakes to Avoid

❌ Using "CheckCircle2" instead of "CheckCircle"
❌ Using wrong journal icon for stage context
❌ Missing journey_step/journey_total on progress cards
❌ Wrong status for card type (e.g., "pending" for action button)

✅ Use exact icon names from lucide-react
✅ Match colors to card purpose (action=blue, processing=yellow, etc.)
✅ Include journey breadcrumbs on overall progress cards
✅ Set action=null for non-clickable status cards

---

End of Cards Reference
