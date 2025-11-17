# Global Design System - Available Everywhere

## Overview

This document describes the global CSS classes and components available throughout the Flask-Basecoat application, following shadcn/ui design patterns.

## CSS Classes Available Globally

All these classes are defined in [app/assets/styles/input.css](app/assets/styles/input.css) and compiled to [app/static/styles/app.css](app/static/styles/app.css), making them available on every page.

### 1. Buttons (`.btn`)

#### Base Button
```html
<button class="btn">Click me</button>
<input type="submit" class="btn" value="Submit">
```

**Styling:**
- Dark background (slate-900) with white text
- Rounded corners (0.375rem)
- Height: 2.5rem (h-10)
- Padding: 0.5rem 1rem
- Smooth transitions
- Focus ring on keyboard navigation

#### Button Variants

**Ghost Button** - Transparent background
```html
<a class="btn btn--ghost" href="#">Back to dashboard</a>
```
- Transparent background
- Hover: light gray background
- Perfect for secondary actions and links

**Outline Button** - Border with transparent background
```html
<button class="btn btn--outline">Cancel</button>
```
- 1px border
- Transparent background
- Hover: light gray background

**Secondary Button** - Light gray background
```html
<button class="btn btn--secondary">Secondary</button>
```
- Light gray background (slate-100)
- Darker gray on hover

#### Button Sizes

**Small Button**
```html
<button class="btn btn--sm">Small</button>
```
- Height: 2rem
- Smaller padding and text

**Large Button**
```html
<button class="btn btn--lg">Large</button>
```
- Height: 3rem
- Larger padding and text

#### Combining Variants
```html
<button class="btn btn--ghost btn--sm">Small Ghost</button>
<button class="btn btn--outline btn--lg">Large Outline</button>
```

### 2. Input Fields (`.input`)

```html
<input type="text" class="input" placeholder="Enter text...">
<input type="email" class="input" placeholder="Email">
<input type="password" class="input" placeholder="Password">
<select class="input">
    <option>Option 1</option>
    <option>Option 2</option>
</select>
<textarea class="input" rows="4"></textarea>
```

**Styling:**
- White background with slate-300 border
- Rounded corners
- Height: 2.5rem
- Focus ring (2px solid slate-950)
- Placeholder text: slate-500
- Full dark mode support

**Fixed width variant:**
```html
<input type="text" class="input w-64" placeholder="Fixed width">
```

### 3. Card Component (`.card`)

Cards provide visual containers with borders and shadows.

#### Basic Card
```html
<div class="card">
    <div class="card-header">
        <h2 class="text-2xl font-semibold">Title</h2>
        <p class="text-sm text-slate-600">Description</p>
    </div>
    <div class="card-content">
        <!-- Your content here -->
    </div>
</div>
```

**Styling:**
- White background with subtle border
- Rounded corners (0.5rem)
- Subtle shadow for depth
- Dark mode: dark background with dark border

#### Card Header
```html
<div class="card-header">
    <h2>Title</h2>
    <p class="text-sm text-slate-600">Subtitle or description</p>
</div>
```
- Padding: 1.5rem
- Flexbox column layout
- Space between child elements

#### Card Content
```html
<div class="card-content">
    <!-- Form fields, tables, etc. -->
</div>
```
- Padding: 1.5rem (top padding removed to align with header)

### 4. Utility Classes

These Tailwind utilities are commonly used:

**Spacing:**
- `px-4` - Horizontal padding
- `py-8` - Vertical padding
- `mt-6` - Top margin
- `mb-4` - Bottom margin
- `gap-3` - Gap in flex/grid

**Layout:**
- `flex` - Flexbox
- `items-center` - Align items center
- `justify-between` - Space between
- `grid grid-cols-2` - 2-column grid
- `container mx-auto` - Centered container
- `max-w-md` - Max width medium

**Text:**
- `text-2xl font-semibold` - Large bold heading
- `text-sm text-slate-600` - Small muted text
- `dark:text-slate-400` - Dark mode text color

**Interactive:**
- `cursor-pointer` - Pointer cursor
- `hover:bg-slate-50` - Hover background
- `overflow-x-auto` - Horizontal scroll

## Usage Examples

### Login/Register Forms

```html
<div class="container mx-auto px-4 py-8">
    <div class="max-w-md mx-auto w-full">
        <div class="card">
            <div class="card-header">
                <h2 class="text-2xl font-semibold">Log in</h2>
            </div>
            <div class="card-content">
                <form>
                    <input type="email" class="input" placeholder="Email">
                    <input type="password" class="input" placeholder="Password">
                    <button type="submit" class="btn">Log in</button>
                </form>
            </div>
        </div>
    </div>
</div>
```

### Admin Tables with Filters

```html
<div class="container mx-auto px-4 py-8">
    <a class="btn btn--ghost" href="/admin">← Back to dashboard</a>

    <div class="card mt-6">
        <div class="card-header">
            <h2 class="text-2xl font-semibold">Registered Users</h2>
            <p class="text-sm text-slate-600">Manage users</p>
        </div>
        <div class="card-content">
            <div class="flex items-center gap-3 mb-4">
                <select class="input w-64">
                    <option>All account types</option>
                </select>
                <input type="text" class="input w-64" placeholder="Search...">
            </div>

            <div class="overflow-x-auto">
                <table class="table w-full">
                    <!-- Table content -->
                </table>
            </div>
        </div>
    </div>
</div>
```

### Action Buttons

```html
<!-- Primary action -->
<button class="btn">Create New</button>

<!-- Secondary actions -->
<button class="btn btn--secondary">Save Draft</button>
<button class="btn btn--outline">Cancel</button>

<!-- Link-style button -->
<a class="btn btn--ghost" href="#">Go Back</a>

<!-- Small buttons for compact spaces -->
<button class="btn btn--sm">Edit</button>
<button class="btn btn--sm btn--outline">Delete</button>
```

### Form with Multiple Fields

```html
<div class="card">
    <div class="card-header">
        <h2 class="text-2xl font-semibold">User Information</h2>
    </div>
    <div class="card-content">
        <form class="grid gap-6">
            <div class="grid grid-cols-2 gap-4">
                <input type="text" class="input" placeholder="First name">
                <input type="text" class="input" placeholder="Last name">
            </div>

            <input type="email" class="input" placeholder="Email">

            <select class="input">
                <option>Select role...</option>
                <option>Admin</option>
                <option>User</option>
            </select>

            <div class="flex gap-3">
                <button type="submit" class="btn">Save</button>
                <button type="button" class="btn btn--outline">Cancel</button>
            </div>
        </form>
    </div>
</div>
```

## Color Palette

All components use Tailwind's slate color scale for consistency:

- **Text:** slate-900 (light mode), slate-100 (dark mode)
- **Muted text:** slate-600 (light), slate-400 (dark)
- **Borders:** slate-200 (light), slate-800 (dark)
- **Backgrounds:** white (light), slate-950 (dark)
- **Hover states:** slate-50/100 (light), slate-800/900 (dark)

## Dark Mode Support

All components have full dark mode support via `dark:` variants:

```html
<!-- Automatically adapts to system preference -->
<div class="bg-white dark:bg-slate-950">
    <p class="text-slate-900 dark:text-slate-100">Content</p>
</div>
```

## Accessibility Features

All components include:

- ✅ Keyboard navigation support
- ✅ Focus indicators (rings)
- ✅ ARIA attributes where needed
- ✅ Proper semantic HTML
- ✅ Screen reader labels (`sr-only` class)

```html
<!-- Example with accessibility -->
<label for="search" class="sr-only">Search users</label>
<input id="search" type="text" class="input" placeholder="Search...">
```

## Migration Guide

### Old → New Button Classes

| Old Class | New Class | Notes |
|-----------|-----------|-------|
| `.ui.button` | `.btn` | Base button |
| `.ui.primary.button` | `.btn` | Default is now primary |
| `.ui.secondary.button` | `.btn btn--secondary` | Light gray background |
| `.ui.basic.button` | `.btn btn--outline` | Outline variant |
| `.ui.ghost.button` | `.btn btn--ghost` | Transparent background |
| `.ui.small.button` | `.btn btn--sm` | Small size |
| `.ui.large.button` | `.btn btn--lg` | Large size |

### Old → New Input Classes

| Old Class | New Class |
|-----------|-----------|
| `.ui.input input` | `.input` |
| `.ui.form .field input` | `.input` |
| `.ui.form select` | `.input` |

### Old → New Card/Segment Classes

| Old Class | New Class |
|-----------|-----------|
| `.ui.segment` | `.card` |
| `.ui.segment .header` | `.card-header` |
| `.ui.segment .content` | `.card-content` |

## Best Practices

1. **Always use cards for content sections**
   ```html
   <div class="card">
       <div class="card-header">...</div>
       <div class="card-content">...</div>
   </div>
   ```

2. **Use consistent spacing**
   - Page padding: `px-4 py-8`
   - Card margin: `mt-6`
   - Form gap: `gap-6`
   - Element gap: `gap-3` or `gap-4`

3. **Button hierarchy**
   - Primary action: `.btn`
   - Secondary actions: `.btn btn--secondary` or `.btn btn--outline`
   - Navigation/Back: `.btn btn--ghost`

4. **Input widths**
   - Search fields: `w-64` (16rem)
   - Form fields: Full width by default
   - Short fields: `w-32` or `w-48`

5. **Responsive design**
   - Always use `overflow-x-auto` for tables
   - Use grid for multi-column layouts
   - Add `container mx-auto` for centered content

## Files Modified

1. **[app/assets/styles/input.css](app/assets/styles/input.css)**
   - Button base + variants
   - Input styling
   - Card components

2. **[app/static/styles/app.css](app/static/styles/app.css)**
   - Compiled production CSS

3. **Templates updated:**
   - [app/templates/account/login.html](app/templates/account/login.html)
   - [app/templates/account/register.html](app/templates/account/register.html)
   - [app/templates/admin/registered_users.html](app/templates/admin/registered_users.html)

## Testing

All components have been tested with:
- ✅ Browser automation (Selenium)
- ✅ Dark mode
- ✅ Keyboard navigation
- ✅ Responsive layouts

## Support

For issues or questions:
1. Check this document first
2. Review [FORM_IMPROVEMENTS.md](FORM_IMPROVEMENTS.md) for form-specific details
3. Review [SIDEBAR_IMPLEMENTATION.md](SIDEBAR_IMPLEMENTATION.md) for sidebar usage

---

**Status:** ✅ Production Ready
**Last Updated:** 2025-11-15
**Version:** 1.0.0
