---
name: JobSentinel
description: AI-powered job monitoring system with a focused, developer-grade interface
colors:
  primary: "#3b82f6"
  primary-light: "#60a5fa"
  primary-dark: "#2563eb"
  primary-alpha: "rgba(59, 130, 246, 0.12)"
  sidebar-bg: "#0f172a"
  sidebar-text: "#94a3b8"
  sidebar-text-active: "#ffffff"
  page-bg: "#f1f5f9"
  card-bg: "#ffffff"
  card-border: "#e2e8f0"
  header-bg: "#ffffff"
  header-border: "#e2e8f0"
  text-primary: "#1e293b"
  text-secondary: "#64748b"
  text-tertiary: "#94a3b8"
  success: "#10b981"
  warning: "#f59e0b"
  danger: "#ef4444"
  info: "#6366f1"
typography:
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  heading:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.02em"
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.01em"
  card-title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  nav-text:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.4
  nav-icon:
    fontSize: "18px"
  group-label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    fontSize: "10px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.08em"
rounded:
  xs: "3px"
  sm: "6px"
  md: "10px"
  lg: "14px"
  xl: "20px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "10px 18px"
  button-primary-hover:
    backgroundColor: "{colors.primary-light}"
  card:
    backgroundColor: "{colors.card-bg}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
---

# Design System: JobSentinel

## Overview

**Creative North Star: "Night Watch"**

JobSentinel's interface draws from the atmosphere of a technical operations room during the night shift—dark navigation, bright data signals, and deliberate restraint. The deep slate sidebar (#0f172a) creates a commanding backdrop where information pops with clinical precision. The modern blue accent (#3b82f6) serves as the signal color: scan results, active states, interactive targets. The system never decorates; every visual decision earns its weight by clarifying the task.

This is a monitoring tool built for developers who self-host. The interface respects that context: tight information density where it matters (tables, task lists), generous breathing room where the eye needs rest (dashboard cards, settings), and zero tolerance for gratuitous decoration. Hover states respond crisply. Transitions are fast. The color palette is narrow by design—neutral grays dominate, the primary blue punctuates, status colors (green/amber/red) trigger only on meaningful state.

The typography is system-native throughout, leaning on platform defaults rather than custom display faces. Weight and size carry hierarchy; letter-spacing tightens on headings to keep them compact. The result reads as tool-grade: legible at a glance, never precious, built to be scanned rather than admired.

**Key Characteristics:**
- Deep sidebar creates focus, not decoration
- Blue accent used decisively, never scattered
- Low shadow vocabulary (dual-layer soft shadows, no dramatic offset)
- Tight spacing in data-dense regions, generous in promotional surfaces
- Status dots glow; tags round fully; buttons lift on hover

## Colors

The palette is restrained: one blue accent, four neutrals, four semantic states.

### Primary
- **Modern Blue** (#3b82f6): The signal color. Used for primary actions, active navigation, links, and selected states. Appears on ~10-15% of any screen—common enough to guide, rare enough to command attention. Hover lightens to #60a5fa; pressed state darkens to #2563eb.
- **Blue Alpha** (rgba(59, 130, 246, 0.12)): Tinted backgrounds for selected rows, focused inputs, and accent surfaces that need subtlety.

### Neutral
- **Sidebar Night** (#0f172a): The commanding left rail. Deep slate, not pure black, so text stays legible without harsh contrast.
- **Page Ground** (#f1f5f9): Extremely pale cool gray. The main content area sits here; white cards float above it.
- **Card Surface** (#ffffff): Pure white. Every card, dialog, and elevated surface.
- **Hairline Border** (#e2e8f0): Soft gray used for all dividers, card edges, and table rules. Never pure #ddd.
- **Text Primary** (#1e293b): Body copy and active elements.
- **Text Secondary** (#64748b): Labels, metadata, table headers.
- **Text Tertiary** (#94a3b8): Placeholder text, disabled states, de-emphasized UI.

### Semantic States
- **Success Green** (#10b981): Enabled/active status, completed tasks, positive metrics.
- **Warning Amber** (#f59e0b): In-progress states, attention needed, caution signals.
- **Danger Red** (#ef4444): Errors, delete actions, failed tasks.
- **Info Indigo** (#6366f1): Informational highlights, supplementary context.

**The Signal Discipline Rule.** The primary blue is used only on interactive targets and active states. Decorative blue (blue text on static content, blue backgrounds with no action) is banned. If it's blue, you can click it or it's showing you're here.

## Typography

**System Stack Only:** `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`

**Character:** Utilitarian and cross-platform. No custom display faces; weight and size carry all hierarchy. The system respects what the OS already optimized.

### Hierarchy
- **Page Title** (700 weight, 20px, 1.3 line-height, -0.02em tracking): Top-of-page landmarks. Dashboard, Company Management, etc.
- **Card Title** (700 weight, 16px, 1.3 line-height, -0.01em tracking): Section headers inside cards.
- **Body** (400 weight, 14px, 1.5 line-height): All running text, table cells, form fields.
- **Stat Value** (700 weight, 28px, 1.1 line-height, -0.02em tracking): Dashboard metric numbers.
- **Label** (500-600 weight, 12-13px, 1.4 line-height, 0.01-0.04em tracking): Form labels, table column headers, metadata captions. Often uppercase on table headers.
- **Nav Text** (500 weight, 13px, 1.4 line-height): Sidebar navigation item labels. Tighter than body to keep the rail compact.
- **Nav Icon** (18px): Sidebar and topbar icon size. Sits inline with nav text; scales no further than 16px in collapsed-density variants.
- **Group Label** (600 weight, 10px, 1.4 line-height, 0.08em tracking, uppercase): Sidebar section dividers (监测/配置/运行/系统). The only positive-tracking text in the system; reads as a micro-caption, not a heading.

**The Tight Tracking Rule.** Headings use negative letter-spacing (-0.01em to -0.02em) to keep them compact. Body text stays at normal tracking. Never positive tracking except on uppercase labels (group labels at 0.08em).

## Layout

Single-column centered layouts with a max-width of 800-1200px depending on surface density. Dashboard stats use a 4-column grid (collapses to 2-col on tablet, 1-col on mobile). Tables and lists run full-width within their card container.

**Spacing rhythm:** 4px base unit. Common intervals are 8px, 12px, 16px, 20px, 24px, 32px. Tight groupings (input + label) use 4-8px; card internal padding is 20-24px; section gaps are 24-32px.

**Responsive behavior:** The sidebar is 240px wide on desktop, collapses to 72px icon-only on user toggle. On mobile (<768px), it becomes a slide-out drawer. Content padding reduces from 24px to 16px on small screens. Stat grids and action chips reflow to single column.

**Density:** Data tables are snug (compact row height, tight cell padding) because scanning is the job. Dashboard cards are airy (generous internal padding, breathing room between elements) because they're promotional, not operational.

## Elevation & Depth

**Philosophy:** Low ambient shadows. Surfaces float with soft dual-layer shadows rather than hard offset. Hover adds depth; rest state is nearly flat.

### Shadow Vocabulary
- **Card Resting** (`0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)`): The default for all cards and elevated surfaces. Barely perceptible; establishes layer separation without drama.
- **Card Hover** (`0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)`): Soft lift on interactive cards. Signals "you can click this."
- **Primary Action Hover** (`0 4px 12px rgba(59, 130, 246, 0.3)`): Blue-tinted glow under the primary CTA button on hover. The only colored shadow in the system.

**The Flat-By-Default Rule.** Surfaces are flat at rest. Shadows appear only to signal interactivity (hover) or establish clear layer separation (modals over page). Zero-offset hard shadows are banned.

## Shapes

**Corner Strategy:** Fully rounded corners on all interactive elements and containers. Extra-small radius (3px) on micro-indicators like the active-nav left-edge bar; small (6px) on buttons and inputs; medium (10px) on chips and small cards; large (14px) on main cards and dialogs.

**Borders:** Hairline borders (#e2e8f0, 1px) separate cards from the page ground and divide table rows. No thick borders, no colored left-edge accents (a common B2B trope we reject).

**Clipping:** Status tags are fully rounded (border-radius: 999px) to read as pills. Navigation items in the sidebar use 10px radius. The primary action button on Dashboard uses 6px for crispness. The active-nav left-edge glow indicator uses 3px radius (`0 3px 3px 0`) so it reads as a slim signal bar rather than a soft pill.

## Components

### Buttons
- **Shape:** 6px radius, crisp corners.
- **Primary:** Blue solid (#3b82f6), white text, 10px vertical × 18px horizontal padding. Hover lightens to #60a5fa and lifts 1px (`transform: translateY(-1px)`). Font weight 600.
- **Secondary / Ghost:** Transparent background, 1px border in #e2e8f0, primary text color. Hover fills with page-bg gray.
- **Icon-only:** 28-36px square, 6px radius, transparent at rest, gray bg on hover. Used in table action columns.

### Status Indicators
- **Dot + Label:** 8px circular dot with a subtle glow (`box-shadow: 0 0 6px <color>`). Green dot for active/enabled, gray for inactive, amber for in-progress, red for failed. Dot sits inline with 13px label text.
- **Pills:** Fully rounded background with matching text color. Used for tags (keywords, cities, status). 2px vertical × 8px horizontal padding, 12px font size, 500 weight.

### Cards
- **Corner Style:** 14px radius.
- **Background:** Pure white (#ffffff).
- **Shadow:** Resting shadow as default; hover shadow on interactive cards only.
- **Border:** 1px solid #e2e8f0.
- **Internal Padding:** 20-24px. Tight (16px) on dense data cards, generous (24px) on promotional dashboard cards.

### Inputs & Fields
- **Style:** 1px border (#e2e8f0 inset as box-shadow), 6px radius, white background, 14px text.
- **Focus:** 2px blue glow (box-shadow: 0 0 0 2px rgba(59,130,246,0.12) inset, 0 0 0 2px #3b82f6 inset). Border disappears into the glow.
- **Hover:** Border shifts to primary-light (#60a5fa).
- **Disabled:** Gray text, gray background, no pointer events.

### Navigation (Sidebar)
- **Default State:** 10px radius nav items, sidebar-text gray (#94a3b8), transparent background.
- **Hover:** Semi-transparent white overlay (rgba(255,255,255,0.06)).
- **Active:** Semi-transparent blue background (rgba(59,130,246,0.18)), white text, 3px blue left-edge glow indicator (position: absolute, height: 20px, width: 3px, border-radius: 0 3px 3px 0, background: #3b82f6, box-shadow: 0 0 8px #3b82f6).
- **Mobile:** Sidebar becomes a slide-out drawer; otherwise identical treatment.

### Tables
- **Header Row:** Light gray background (#f8fafc), 12px uppercase text with 0.04em tracking, 600 weight, secondary text color.
- **Body Rows:** Zebra striping with extremely subtle #fafbfc on alternates. Hover row gets blue alpha tint (rgba(59,130,246,0.12)).
- **Borders:** 1px hairline (#e2e8f0) between rows and columns.

### Stat Cards (Dashboard)
- **Structure:** Icon + value + label. 52px icon container (rounded, white bg, subtle border, colored icon inside), 28px value (700 weight), 13px label (500 weight, secondary color).
- **Background Accent:** Gradient shape in top-right corner at 10% opacity (from CSS variable --js-gradient-blue/green/orange/purple). Purely atmospheric; never obscures content.
- **Hover:** Card lifts with hover shadow, translates up 2px.

## Do's and Don'ts

### Do:
- **Do** use the primary blue (#3b82f6) only on clickable elements and active states. If it's blue, it's interactive.
- **Do** keep table row height snug (compact padding) so users can scan 20+ rows without scrolling.
- **Do** add the 3px glowing left-edge indicator on active sidebar nav items. It's the signature active-state marker.
- **Do** use 6px radius on buttons and inputs, 10px on chips and nav, 14px on cards. Consistency matters.
- **Do** pair every status color with its semantic meaning: green = success/enabled, amber = in-progress/warning, red = error/delete, blue = active/primary.

### Don't:
- **Don't** use gradient text. Emphasis comes from weight (700) or size, never gradient fills.
- **Don't** add decorative blue backgrounds or blue text on static content. Blue signals interactivity.
- **Don't** use hard-offset shadows (e.g. `box-shadow: 4px 4px 0 #000`). All shadows are soft dual-layer.
- **Don't** scatter the primary blue across the interface. The Signal Discipline Rule: blue appears on ≤15% of any screen.
- **Don't** use colored left-edge bars on cards or list items. We rejected that B2B visual trope deliberately.
- **Don't** add eyebrow labels or kickers above headings. Headings carry their own weight.
