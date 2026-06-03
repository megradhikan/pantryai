# Design

## Theme

Mood: "Sunday farmer's market — brown paper bags, fresh herbs under warm kitchen light, a well-worn recipe card."

Color strategy: **Restrained** — tinted neutrals with a single accent for actions. The warmth lives in the brand color and typography, not in the surface.

## Color Palette

```css
:root {
  /* Primary — deep warm plum, the identity anchor */
  --primary: oklch(0.48 0.14 270);
  --primary-hover: oklch(0.42 0.16 270);
  --primary-light: oklch(0.92 0.03 270);

  /* Accent — sage green, natural and herbal */
  --accent: oklch(0.58 0.12 155);
  --accent-hover: oklch(0.52 0.14 155);
  --accent-light: oklch(0.93 0.03 155);

  /* Surfaces */
  --bg: oklch(1.000 0.000 0);
  --surface: oklch(0.970 0.003 270);
  --surface-raised: oklch(1.000 0.000 0);

  /* Text */
  --ink: oklch(0.18 0.02 270);
  --muted: oklch(0.50 0.01 270);
  --faint: oklch(0.72 0.005 270);

  /* Semantic */
  --success: oklch(0.60 0.15 145);
  --warning: oklch(0.75 0.15 80);
  --danger: oklch(0.55 0.18 25);
  --info: oklch(0.60 0.10 250);

  /* Status (inventory) */
  --status-fresh: oklch(0.60 0.15 145);
  --status-low: oklch(0.75 0.15 80);
  --status-expiring: oklch(0.68 0.16 55);
  --status-expired: oklch(0.55 0.18 25);
  --status-finished: oklch(0.65 0.01 270);
}
```

## Typography

- **Family:** System font stack — `-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', system-ui, sans-serif`. Native iOS feel, no external font loads.
- **Scale (fixed rem):**
  - Page title: 1.5rem / 600
  - Section heading: 1.125rem / 600
  - Body: 0.875rem / 400
  - Caption: 0.75rem / 500
  - Badge/label: 0.6875rem / 600

## Spacing

Base unit: 4px. Tokens: 4, 8, 12, 16, 20, 24, 32, 48.

## Radius

- Cards/containers: 16px (rounded-2xl)
- Buttons/inputs: 12px (rounded-xl)
- Badges/pills: 9999px (full rounding)
- Status dots: 50%

## Components

### Cards
- White background on gray-50 surface
- 16px radius, subtle shadow (`0 1px 3px oklch(0 0 0 / 0.06)`)
- 16px internal padding
- No nested cards

### Buttons
- Primary: filled with --primary, white text, 12px radius
- Secondary: --surface bg with --ink text, 1px border
- Destructive: --danger bg, white text
- All buttons: 44px minimum touch height, 14px font, 600 weight

### Form inputs
- --surface background
- 12px radius
- 14px padding vertical, 16px horizontal
- No visible border in default state, 2px --primary ring on focus

### Navigation
- Bottom tab bar, 56px height
- Backdrop blur, semi-transparent white
- Active tab: --primary color, inactive: --faint

### Status indicators
- 8px dots with status colors
- Paired with text label

## Layout

- Single column, max-width 428px (iPhone viewport)
- Page padding: 16px horizontal
- Section gaps: 16px
- Card gaps: 8px
- Content padded from bottom tab bar: 80px + safe area

## Motion

- Transitions: 150ms ease-out for state changes (hover, focus, toggle)
- No page transitions, no orchestrated reveals
- Reduced motion: instant transitions via `prefers-reduced-motion`

## iOS Patterns Used

- Large title at top of each screen
- Bottom tab bar navigation
- Grouped list rows (inventory items)
- Swipe-implied interactions (future)
- Safe area respect (notch, home indicator)
- Native date picker for date inputs
