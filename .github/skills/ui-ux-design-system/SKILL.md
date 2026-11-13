---
name: ui-ux-design-system
description: Improve Agent_Banca UI/UX and accessibility using its TCS palette and a centralized Streamlit stylesheet.
---

# UI/UX design system

Use this skill when changing Agent_Banca interfaces, dashboards, forms, or
uploads. Preserve the existing product behavior, financial controls, and
privacy notices.

## Project conventions

- Read `CONTEXT.md`, the affected app, and tests before editing.
- For Streamlit, inject `src/assets/global.css` once from `src/copilot_app.py`.
- Keep custom colors and component styles in `global.css`; do not scatter CSS
  blocks or HTML style attributes across components.
- Streamlit does not apply Tailwind utilities without a Tailwind build.
  Prefer native Streamlit components and only use equivalent classes defined
  in the global stylesheet; do not add a build system just for utility CSS.
- Keep `.streamlit/config.toml` theme colors aligned with the global tokens.

## TCS design tokens

Define colors only in `:root` of `src/assets/global.css`:

- Surfaces: `--color-tcs-white: #FFFFFF`,
  `--color-surface-subtle: #F5F7FA`.
- Structure: `--color-tcs-black-900: #101828`,
  `--color-tcs-gray-700: #595959`, `--color-tcs-gray-100: #D9D9D9`.
- Actions: `--color-tcs-blue: #3D6EA7`,
  `--color-tcs-yellow: #F9B233`.
- Semantic states: `--color-tcs-green: #4CB050`,
  `--color-tcs-red: #E53935`, `--color-tcs-orange: #F25C2A`.

Use dark text over yellow, green, and orange backgrounds. Do not rely on red
text alone for an error state.

## UX and accessibility

- Use at most three typographic levels per section: title, body, metadata.
- Give uploads and async work clear next steps and immediate status feedback.
- Keep normal text contrast at least 4.5:1 and provide visible keyboard focus.
- Group related controls with consistent spacing and support narrow windows.
- Hide raw JSON, logs, and technical details behind expanders when possible.
- Do not hide failures, imply success after errors, or weaken privacy notices.

## Validation

- Run focused UI tests and the relevant project test suite.
- Smoke-test the Streamlit page and the key upload flow.
- Do not claim accessibility certification without a measured audit.