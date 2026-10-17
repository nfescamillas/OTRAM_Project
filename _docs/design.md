# Codex Task: Complete UI/UX Refinement — OT Asset & Risk Management

## Objective

Redesign and refine the existing frontend of my **OT Asset Inventory & Risk Management Tool** to create a polished, distinctive, professional application.

The current application needs a more intentional, personally crafted visual identity. I want it to look like a mature industrial software product developed by an experienced engineering team, rather than a generic AI-generated SaaS dashboard.

**The primary visual theme must be grayscale**, using carefully selected shades of white, silver, gray, charcoal, and graphite.

This is a frontend and user-experience improvement task. Preserve the existing backend, application features, data models, APIs, calculations, and business logic.

## 1. Design Philosophy

Follow these principles:

- **Industrial precision:** Reflect the character of operational technology, industrial asset management, reliability engineering, and cybersecurity.
- **Minimalism with purpose:** Every visual element must contribute to navigation, comprehension, or decision-making.
- **Human-crafted appearance:** Use deliberate typography, spacing, alignment, hierarchy, and distinctive component details instead of repetitive template styling.
- **Professional restraint:** Avoid flashy gradients, excessive shadows, oversized rounded cards, unnecessary animations, and decorative graphics.
- **Information density:** This is an engineering application. Users should be able to inspect meaningful operational information without excessive scrolling.
- **Visual consistency:** Establish a coherent design language across the entire application.

The finished product should feel like a serious industrial engineering workstation, not a marketing website.

## 2. Color System — Graphite Industrial

Use the following palette as a starting point, refining it where necessary:

| Element | Suggested Color |
|---|---|
| Primary background | `#F5F5F4` |
| Main surfaces | `#FFFFFF` |
| Secondary surfaces | `#ECEDEB` |
| Sidebar background | `#242628` |
| Sidebar active state | `#3A3D40` |
| Primary text | `#202224` |
| Secondary text | `#666A6D` |
| Muted text | `#85898C` |
| Borders and separators | `#D9DCDE` |
| Primary buttons | `#303336` |
| Hover surfaces | `#E5E7E7` |

Requirements:

- Use grayscale for the overwhelming majority of the interface.
- Create reusable design tokens or CSS variables.
- Maintain accessible contrast and readable text.
- Avoid blue or purple as generic primary accent colors.
- Critical risk information may use extremely restrained semantic colors where necessary for safety and recognition, but never rely on color alone. Always use severity text, icons, and distinct visual treatments.
- Keep the overall appearance neutral, clean, technical, and sophisticated.

## 3. Typography and Visual Hierarchy

Introduce a deliberate typography system.

Use a modern, professional sans-serif font such as Inter or IBM Plex Sans, depending on which best suits the existing application.

Use a monospaced font selectively for technical information, including IP addresses, firmware versions, asset identifiers, model numbers, and network addresses.

Improve the hierarchy of:

- Page titles and section headings
- Navigation labels
- Dashboard metrics
- Table headings and values
- Asset information
- Risk classifications and remediation priorities

Avoid unnecessarily large headings, excessive bold text, and inconsistent font sizes.

## 4. Application Layout

Redesign the layout around a cohesive enterprise application shell.

**Sidebar**

Create a visually refined dark graphite sidebar with clear navigation groups, consistent icons, subtle active-state indicators, and compact, professional spacing.

Navigation should reflect the application's actual implemented modules, such as Dashboard, Asset Inventory, Risk Assessment, Remediation, and Settings. Do not create nonfunctional placeholder modules.

**Top Bar**

Implement a minimal top navigation area with page context, useful actions, and consistent alignment. Avoid unnecessary decorative elements.

**Main Content**

Use a consistent content grid, controlled spacing, clean section boundaries, and an intentional information hierarchy.

Use whitespace strategically without making the interface feel empty.

## 5. Dashboard Redesign

Make the dashboard resemble an engineering risk-management console.

Clearly communicate actual available metrics, such as:

- Total OT assets
- Assets by type
- Assets with identified risks
- Risk severity distribution
- Firmware or lifecycle concerns
- Outstanding remediation actions
- Asset health and risk trends, where historical data exists

Improve KPI presentation using restrained typography, compact metrics, subtle separators, and contextual information.

Use meaningful visualizations, including horizontal bar charts, severity distribution charts, and prioritized risk lists where supported by existing data.

Avoid oversized donut charts, excessive colored cards, and charts that do not help users make decisions.

Never fabricate values or trends to fill visual space.

## 6. Asset Inventory Experience

Treat the Asset Inventory as one of the application's most important workflows.

Improve the asset table with:

- Clear column hierarchy and alignment
- Compact but readable rows
- Consistent sorting and filtering interactions
- Search integrated naturally with the table
- Meaningful asset-type icons
- Distinct but restrained status indicators
- Readable technical values
- Clear row actions and selection states
- Well-designed pagination where appropriate

Optimize presentation of PLCs, DCS servers, industrial switches, firewalls, HMIs, engineering workstations, and other OT equipment.

The table should resemble a professional technical asset register, not a generic spreadsheet embedded in a website.

## 7. Asset Details and Risk Assessment

Refine asset detail views to make technical information easy to scan.

Group information logically into sections such as Identity, Technical Specifications, Network Information, Firmware and Lifecycle, Risk Assessment, and Related Remediation Actions, using only fields supported by the application.

Present technical data using structured key-value layouts rather than excessive cards.

Give the Risk Assessment interface a structured engineering appearance. Make the distinction between severity, likelihood, impact, rationale, and recommended mitigation immediately understandable wherever those fields exist.

High-priority risks should be visually prominent without turning the page into a collection of bright warning banners.

## 8. Remediation Experience

Make the remediation workflow feel like an actionable engineering work register.

Clearly communicate priority, status, asset relationship, ownership, and due dates wherever supported.

Use intentional layouts that help users identify what requires action, what is in progress, and what has been completed.

Do not introduce fake workflow states or unsupported data fields.

## 9. Component Design and Microinteractions

Establish consistent reusable patterns for buttons, inputs, dropdowns, tables, dialogs, panels, status indicators, and navigation.

Use subtle hover and focus treatments and brief functional transitions.

Avoid generic AI-generated UI patterns such as:

- Endless identical rounded cards
- Excessive pill-shaped buttons and badges
- Large decorative gradients
- Gratuitous glow effects
- Oversized spacing and empty hero sections
- Inconsistent icon styles
- Multiple competing accent colors
- Heavy shadows around every component
- Unnecessary animations

Prefer understated borders, careful alignment, subtle surface contrast, thoughtful typography, and distinctive details.

Add polished empty, loading, error, and success states. Ensure keyboard accessibility and responsive behavior.

## 10. Implementation Instructions

First, inspect the existing repository to understand the frontend framework, application structure, styling approach, component library, routing, and implemented functionality.

Then:

1. Audit the current UI and identify the main visual and usability weaknesses.
2. Establish a coherent grayscale design system with reusable tokens.
3. Refine shared components and the main application layout.
4. Apply the design system consistently across all existing screens.
5. Improve tables, filters, forms, charts, dialogs, and navigation interactions.
6. Remove redundant styling and unnecessary visual complexity.
7. Preserve all working features, permissions, routes, API integrations, and business logic.
8. Test the frontend for build errors, broken navigation, layout regressions, and accessibility issues.
9. Run the application and inspect actual rendered screens where the environment supports it. Fix visual inconsistencies rather than relying only on code review.

Prefer the existing frontend stack and libraries. Do not introduce major dependencies or rewrite working components without a clear benefit.

Do not stop after producing a design proposal or mockup. **Implement the improvements directly in the codebase.**

## 11. Acceptance Criteria

The task is complete when:

- All existing application screens share a consistent grayscale visual identity.
- The layout feels intentionally designed and professional.
- Technical information is easier to read and navigate.
- Dashboards communicate operational priorities clearly.
- Asset tables and risk-management workflows remain practical and information-dense.
- The interface works across desktop and smaller screen sizes.
- No existing application functionality is broken.
- The application builds and available tests pass.
- Loading, empty, error, hover, and focus states are visually coherent.

## Final Deliverables

After implementation, provide a concise summary of the design changes, major files modified, components improved, tests performed, and any remaining limitations.

Where possible, include screenshots of the updated Dashboard, Asset Inventory, Asset Details, and Risk Assessment screens.

**Final design directive:** Make this feel like a bespoke industrial OT management product. Prioritize engineering clarity, thoughtful restraint, and a mature graphite-gray visual identity over fashionable UI trends.
