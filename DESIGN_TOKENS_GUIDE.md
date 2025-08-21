# Design Tokens & Utility Classes Guide

## Overview
This guide documents the reusable utility classes and design tokens created to eliminate repeated CSS values and improve maintainability across the trading system.

## Background Utilities

### Glass Effects
- `.bg-glass` - Light glass effect with backdrop blur
- `.bg-glass-dark` - Dark glass effect with backdrop blur

### Hover Effects
- `.bg-hover-light` - Light background on hover
- `.bg-hover-dark` - Dark background on hover

## Text Utilities

### Muted Text with Size
- `.text-muted-sm` - Muted text at 0.875rem
- `.text-muted-xs` - Muted text at 0.75rem

### White Text Variants
- `.text-white-85` - White text at 85% opacity
- `.text-white-75` - White text at 75% opacity

## Font Size Utilities
- `.fs-xxs` - 0.65rem
- `.fs-xs` - 0.75rem (replaces .text-xs)
- `.fs-sm` - 0.875rem
- `.fs-lg` - 1.125rem
- `.fs-xl` - 1.25rem

## Spacing Utilities

### Padding
- `.p-xs` - 0.25rem padding
- `.p-sm` - 0.5rem padding
- `.p-md` - 0.75rem padding
- `.p-lg` - 1rem padding

### Margin
- `.m-xs` - 0.25rem margin
- `.m-sm` - 0.5rem margin
- `.m-md` - 0.75rem margin

## Shadow Utilities
- `.shadow-sm` - Small shadow (0 2px 4px rgba(0,0,0,0.1))
- `.shadow-md` - Medium shadow (0 4px 8px rgba(0,0,0,0.15))
- `.shadow-lg` - Large shadow (0 8px 16px rgba(0,0,0,0.2))

## Border Radius Utilities
- `.rounded-sm` - 0.25rem border radius
- `.rounded-md` - 0.375rem border radius
- `.rounded-lg` - 0.5rem border radius
- `.rounded-pill` - 50rem border radius (fully rounded)

## Trading-Specific Utilities

### PnL/Trade Status
- `.trade-positive` - Success color with 600 font weight
- `.trade-negative` - Danger color with 600 font weight
- `.trade-neutral` - Muted color with 500 font weight

### Price Display
- `.price-highlight` - Green background highlight with monospace font
- `.crypto-symbol` - Bold, letter-spaced crypto symbol styling

## Status Utilities
- `.status-online` - Green status with light background
- `.status-offline` - Red status with light background  
- `.status-warning` - Yellow status with light background

## Interactive Utilities
- `.hover-lift` - Lifts element on hover with shadow
- `.hover-scale` - Scales element to 1.05 on hover
- `.clickable` - Adds pointer cursor and transition

## Table Utilities

### Alignment
- `.col-left` - Left align table columns
- `.col-right` - Right align table columns
- `.col-center` - Center align table columns

### Width Classes
- `.w-5` through `.w-15` - Percentage width classes

### Trading Table Classes
- `.numeric`, `.price`, `.amount` - Right-aligned numeric columns
- `.status`, `.action` - Center-aligned status columns

## Chart Utilities
- `.chart-container-sm` - 200px height
- `.chart-container-md` - 300px height
- `.chart-container-lg` - 400px height

## Animation Utilities
- `.fade-in` - 0.5s fade in animation
- `.slide-up` - 0.3s slide up animation

## Migration Guide

### Before (Repeated Values)
```css
.my-element {
    color: #6c757d;
    font-size: 0.875rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-radius: 0.375rem;
}
```

### After (Design Tokens)
```html
<div class="my-element text-muted-sm shadow-sm rounded-md">
```

### Legacy Class Replacements
- `.text-xxs` → `.fs-xxs`
- `.text-xs` → `.fs-xs`
- `.pnl-positive` → `.trade-positive`
- `.pnl-negative` → `.trade-negative`
- `.trade-buy` → `.trade-positive`
- `.trade-sell` → `.trade-negative`

## Font Stacks

### System Fonts
The system uses modern CSS custom properties for font stacks:

- `--font-family-system` - Comprehensive system UI font stack
  - `system-ui, -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, 'Noto Sans', sans-serif`
  - Includes emoji fonts: `'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji'`

- `--font-family-mono` - Modern monospace font stack
  - `ui-monospace, 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Courier New', monospace`

### Usage
```css
.my-element {
    font-family: var(--font-family-system);
}

.code-display {
    font-family: var(--font-family-mono);
}
```

## Benefits
1. **Consistency** - Standardized values across the application
2. **Maintainability** - Single source of truth for design values
3. **Performance** - Reduced CSS file size through reusability
4. **Developer Experience** - Faster styling with utility classes
5. **Design System** - Foundation for scalable UI development
6. **Cross-Platform Compatibility** - Modern system font stacks for optimal display

## Usage Examples

### Price Display
```html
<span class="price-highlight crypto-symbol">$0.00001000</span>
```

### Status Badge
```html
<span class="status-online p-xs rounded-md">Online</span>
```

### Interactive Card
```html
<div class="card hover-lift shadow-sm rounded-lg">
    <div class="p-md">
        <h6 class="text-muted-sm">Total Value</h6>
        <h4 class="trade-positive">$60.16</h4>
    </div>
</div>
```

### Responsive Table
```html
<td class="col-right price-highlight">$0.00001000</td>
<td class="col-center status-online">Active</td>
```