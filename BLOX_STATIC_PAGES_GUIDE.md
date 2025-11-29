# BLOX CMS Static Pages & Block Layout Guide
*SF Examiner Data Center Project - Lessons Learned*

---

## Overview

This guide documents the process of creating custom landing pages in BLOX CMS, specifically for the SF Examiner Data Center project. It covers the challenges encountered and working solutions for building responsive grid layouts with no right sidebar.

---

## Key Concepts

### The Three-Component System

BLOX uses three separate components that work together:

1. **Static Pages** (`Design → Static Pages`)
   - Creates the page entry and URL
   - Content editor that aggressively strips CSS and complex HTML
   - Best used for simple content or as a container for blocks

2. **HTML Blocks** (`Design → Blocks`)
   - Reusable HTML/CSS components
   - CSS survives intact (not stripped)
   - Can be inserted into layout regions

3. **URL Layout Customization** (`Design → Blocks → URL tree`)
   - Controls which template and blocks render for specific URLs
   - Allows per-URL customization without affecting other pages

---

## Creating a Custom Landing Page (Step-by-Step)

### Step 1: Create the HTML Block

**Location:** `Design → Blocks`

1. In the bottom-left "Blocks" panel, click **New** → **HTML block**
2. Give it a descriptive name (e.g., "Data Center Landing")
3. Paste your complete HTML markup including `<style>` tags
4. **Important:** Wrap everything in a unique class (e.g., `<div class="data-center-landing">`) to prevent CSS conflicts
5. Scope all CSS rules under that wrapper class:
   ```css
   .data-center-landing { ... }
   .data-center-landing .data-grid { ... }
   ```
6. Save the block

**Why this works:** Blocks preserve CSS and HTML structure, unlike Static Pages which strip styles.

### Step 2: Create URL Map Entry

**Location:** `Settings → URL maps`

1. Click **New → Create new URL**
2. Set **Parent URL** to `/` (for root-level) or `/site` (for subsection)
3. Set **Name** to your desired slug (e.g., `data_center`)
4. Leave other fields at defaults
5. Save

**Result:** Creates `/data_center` (or `/site/data_center`) as a customizable URL

### Step 3: Configure Layout for the URL

**Location:** `Design → Blocks`

1. In the left **URL tree**, select your new URL (e.g., `/data_center`)
2. In the right **Page customizations** panel, scroll to **Layout** section
3. Set **Side rail: False** to remove the right sidebar
4. Click **Save changes**

**Critical:** This only affects the specific URL you selected—other pages remain unchanged.

### Step 4: Assign Block to Layout Region

**Location:** `Design → Blocks` (with your URL selected)

1. In the middle **Layout** pane, find an appropriate content region:
   - `index-one-top` (usually main content area)
   - `global-container-top-fullscreen` (full-width top region)
   - Any empty region near the top of the page

2. **Drag your block** from the bottom-left Blocks list into that region
   - If dragging doesn't work, try double-clicking the block
   - Or right-click the region and look for "Add block"

3. Click **Save block layout changes** at the top of the Layout pane

### Step 5: Clear Static Page Content (If Applicable)

**Location:** `Design → Static Pages`

1. If you created a Static Page, open it
2. Delete all content in the body (leave it completely blank)
3. Save

**Why:** An empty Static Page body lets BLOX render the block layout you configured in Design → Blocks

### Step 6: Preview and Test

Visit your URL:
```
https://www.sfexaminer.com/data_center
```

Or with preview parameter if needed:
```
https://www.sfexaminer.com/data_center?preview=1
```

The page should now show:
- ✅ Your custom HTML block content
- ✅ Full CSS styling intact
- ✅ No right sidebar
- ✅ Responsive layout working

---

## Common Issues & Solutions

### Issue: Static Page Strips CSS

**Problem:** When you paste HTML with `<style>` tags directly into a Static Page, BLOX removes the styles.

**Solution:** Use an HTML Block instead. Blocks preserve CSS.

### Issue: Block Token Renders as Text

**Problem:** When you add `{{block type="html" name="..."}}` to a Static Page, it shows as literal text instead of rendering the block.

**Solution:** Static Pages in some BLOX installs don't parse template tokens. Use the block layout system instead (assign block through Design → Blocks).

### Issue: Right Sidebar Won't Disappear

**Problem:** Even with "Side rail: False" set, the right sidebar still appears.

**Solutions:**
1. Make sure you're previewing the correct URL (the one you customized in Design → Blocks)
2. Verify "Side rail: False" is saved in Page customizations
3. Clear browser cache and hard refresh (Cmd+Shift+R)
4. Check that you're not previewing a different page with a similar name

### Issue: Can't Add Blocks to Layout

**Problem:** Dragging blocks doesn't work, clicking regions does nothing.

**Solutions:**
1. Try **double-clicking** the block in the Blocks list
2. Try **right-clicking** the region for a context menu
3. Look for a **+ button** inside empty regions
4. Some BLOX versions require clicking "Edit" on the region first
5. As last resort, ask your BLOX admin to assign the block for you

### Issue: Changes Don't Appear on Preview

**Common causes:**
1. **Wrong URL:** You're customizing `/data_center` but previewing `/site/examiner_data_page`
2. **Cache:** Browser is showing old version (hard refresh)
3. **Block not assigned:** Block exists but isn't in any layout region
4. **Static Page has content:** Empty the Static Page body so BLOX uses the block layout

---

## Best Practices

### 1. Always Scope Your CSS

Wrap all custom CSS under a unique class:
```css
.my-custom-page { ... }
.my-custom-page .component { ... }
```

This prevents styles from affecting other pages, even if the CSS file accidentally loads elsewhere.

### 2. Use Inline Styles for Critical Layout

If BLOX strips external `<style>` blocks, use inline styles on elements:
```html
<div style="display:grid;gap:1.5rem;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));">
```

Inline styles always survive BLOX's sanitization.

### 3. Test Multiple URLs

BLOX can create confusing URL structures:
- `/data_center` (URL map entry)
- `/site/data_center` (section-based)
- `/site/examiner_data_page.html` (static page slug)

Always verify you're customizing and previewing the **same URL**.

### 4. Keep Blocks Simple and Focused

One block = one component (e.g., landing grid, hero banner, chart embed). Don't try to build entire complex pages in a single block—use multiple blocks and compose them in the layout.

### 5. Document Your Block Names

Use clear, descriptive names like "Data Center Landing" not "Block 47" or "Custom HTML 3". Future you will thank past you.

---

## Working Configuration for SF Examiner Data Center

### Final Setup

**URL:** `/data_center`

**Components:**
- **HTML Block:** "Data Center Landing"
- **Layout Region:** `index-one-top`
- **Template Setting:** Side rail: False
- **Static Page:** Empty (no content)

**Key CSS Classes:**
- `.data-center-landing` - Main wrapper
- `.data-grid` - Responsive grid container
- `.data-card` - Individual topic cards
- `.card-hero` - Colored image areas
- `.card-body` - Text content areas

**Responsive Breakpoints:**
- Desktop (>992px): 4 cards per row
- Tablet (680-992px): 2-3 cards per row
- Mobile (<680px): 1 card per row

---

## Quick Reference: Common BLOX Paths

| Task | Location | Notes |
|------|----------|-------|
| Create HTML block | Design → Blocks → New | CSS stays intact |
| Edit existing block | Design → Blocks → Click block → Edit | |
| Create URL map entry | Settings → URL maps → New | Enables layout customization |
| Assign blocks to URL | Design → Blocks → Select URL in tree | Drag blocks into regions |
| Remove sidebar | Design → Blocks → Page customizations → Side rail: False | Per-URL only |
| Preview page | Visit URL directly | May need `?preview=1` |
| Create Static Page | Design → Static Pages → Add | Strips CSS, use blocks instead |
| Check permissions | Settings → Users → Your account | See assigned roles |

---

## Troubleshooting Checklist

When something doesn't work:

- [ ] Am I previewing the correct URL?
- [ ] Is the block saved with the latest changes?
- [ ] Is the block assigned to a layout region?
- [ ] Is "Side rail: False" saved for this URL?
- [ ] Did I clear the Static Page body?
- [ ] Have I hard-refreshed the browser? (Cmd+Shift+R)
- [ ] Are all my CSS selectors scoped under a unique wrapper class?
- [ ] Is the layout region I'm using actually visible on the page?

---

## Future Improvements

### Potential Enhancements:
1. **Create reusable block templates** for common layouts
2. **Build topic-specific blocks** for each data category
3. **Implement lazy-loading** for Datawrapper embeds
4. **Add analytics tracking** to measure topic engagement
5. **Create mobile-optimized** chart embed blocks

### Known Limitations:
- BLOX blocks can't use external JavaScript libraries easily
- Some advanced CSS (grid, flexbox) may not preview correctly in editor
- Layout region names vary between BLOX versions
- Drag-and-drop block assignment isn't reliable in all installations

---

## Key Takeaways

### ✅ What Works:
- **HTML Blocks** preserve CSS and complex markup
- **URL-specific layout customization** doesn't affect other pages
- **Inline styles** survive BLOX sanitization
- **Side rail: False** removes sidebar when properly configured
- **Responsive CSS Grid** renders correctly in modern browsers

### ❌ What Doesn't Work:
- **Pasting CSS directly into Static Pages** - gets stripped
- **Block tokens** (`{{block ...}}`) - don't parse in Static Pages
- **Assuming preview URL matches what you're editing** - verify URLs
- **Global CSS changes** - always scope to a unique wrapper class

---

## Resources

- **BLOX Documentation:** (internal knowledge base)
- **SF Examiner brand colors:** 
  - Red: `#cf4236`
  - Gold: `#ffd74c`
  - Olive: `#7e883f`
  - Sky: `#80d0d8`
  - Stone: `#ccc9c8`
  - Sand: `#e3cbac`

---

*Last Updated: November 4, 2025*  
*Project: SF Examiner Data Center Landing Page*  
*Status: ✅ Working prototype deployed to `/data_center`*
