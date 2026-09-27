---
name: Campus Conquest Arena
description: A cartographic operations table for reproducible bot matches.
colors:
  survey-paper: "#eef3f6"
  instrument-surface: "#f8fbfc"
  ink: "#172735"
  muted-ink: "#5c6c78"
  survey-line: "#c7d3da"
  operations-navy: "#173a59"
  deep-navy: "#0d2a43"
  yonsei-blue: "#1467b3"
  korea-crimson: "#be3b4b"
  timing-amber: "#b56a06"
  ready-green: "#16805a"
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "clamp(24px, 3vw, 38px)"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  data:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.4
rounded:
  control: "10px"
  surface: "14px"
spacing:
  compact: "8px"
  control: "12px"
  section: "22px"
  canvas: "36px"
components:
  button-primary:
    backgroundColor: "{colors.operations-navy}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
    padding: "12px 20px"
  input:
    backgroundColor: "#ffffff"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "11px 12px"
---

# Design System: Campus Conquest Arena

## Overview

**Creative North Star: "The Cartographic Operations Table"**

The interface treats each experiment as a planned maneuver: conditions are set on one side, the campus grid is the shared field, and evidence accumulates in a disciplined run ledger. It is an operational surface rather than a promotional dashboard, with calm density and immediate distinctions between the two teams, neutral terrain, timing risk, and valid engine state.

**Key Characteristics:**

- Map-first spatial reasoning
- Restrained cool neutral field
- Blue and crimson reserved for team identity
- Monospaced type only for IDs, turns, commands, and measurements
- Responsive controls that preserve the run workflow

## Colors

The palette is restrained: cool survey neutrals carry most of the interface while navy provides operational authority.

### Primary

- **Operations Navy** (`#173a59`): primary actions, selected timing mode, and the run ledger.
- **Deep Navy** (`#0d2a43`): persistent navigation and event logs.

### Secondary

- **Yonsei Blue** (`#1467b3`): Y team ownership and units only.
- **Korea Crimson** (`#be3b4b`): K team ownership and units only.
- **Timing Amber** (`#b56a06`): timing risk or pending engine health, never general decoration.

### Neutral

- **Survey Paper** (`#eef3f6`): application ground.
- **Instrument Surface** (`#f8fbfc`): controls and focused work regions.
- **Ink** (`#172735`): primary text.
- **Muted Ink** (`#5c6c78`): secondary explanation.
- **Survey Line** (`#c7d3da`): dividers and control outlines.

**The Territory Rule.** Team colors encode team ownership; they do not decorate unrelated controls.

## Typography

The system uses the platform UI sans for operational clarity and a native monospaced stack for machine-identifying data.

### Hierarchy

- **Display:** 700 weight, `clamp(24px, 3vw, 38px)`, tight tracking for the application title.
- **Headline:** 21–30px with tight tracking for task regions.
- **Body:** regular platform sans, comfortable 1.5 line height, with explanations limited to readable measures.
- **Label:** 13px semibold for form labels; uppercase is reserved for compact table headings.
- **Data:** 12–13px monospaced for IDs, turns, commands, and event JSON.

**The Data Voice Rule.** Monospace signals exact machine data, never generic technical atmosphere.

## Layout

Desktop uses a persistent 220px navigation rail and a fluid main canvas. The primary run view pairs a larger launch panel with a map field; below 1040px the map follows the controls. Below 720px navigation becomes a horizontal strip and all form grids collapse to one column. The surface supports widths down to 320px without horizontal page overflow.

## Elevation & Depth

Large work surfaces use a low ambient shadow (`0 12px 30px rgba(28,54,74,.06–.08)`) to separate them from survey paper. Navigation, tables, and the map rely primarily on tonal layering and lines. Controls do not stack border and shadow treatments.

## Shapes

Work surfaces use 14px corners. Controls use 10–11px corners and remain clearly rectangular; pills are limited to the compact segmented timing selector. The rotated two-color brand mark and square 15x15 map cells provide the system's recurring geometry.

## Components

### Buttons

- Primary actions use operations navy, white text, 10–11px corners, and `12px 20px` padding.
- Quiet actions are transparent with a survey-line outline.
- Focus uses a visible three-pixel translucent Yonsei-blue ring.

### Cards / Containers

- Only bounded work regions such as the launch panel and map field receive a surface and ambient shadow.
- Repeated records remain rows divided by survey lines rather than becoming card grids.

### Inputs / Fields

- White field, one-pixel survey-line stroke, 10px corner, and a minimum 44px target.
- Labels sit directly above controls and name concrete inputs.

### Navigation

- Deep navy rail with quiet inactive labels and a low-contrast filled active state.
- At narrow widths it becomes a horizontally scrollable strip without changing the information architecture.

### Campus Map

- A fixed 15x15 grid dominates replay interpretation.
- Buildings use compact inset squares; ownership changes their fill.
- Y and K units occupy opposing corners of a cell so both remain visible during conflict.

## Do's and Don'ts

### Do:

- **Do** keep official, timing, and run status visible beside the action that changes it.
- **Do** use team colors consistently on map evidence and team identity.
- **Do** preserve the same task order on desktop and narrow layouts.

### Don't:

- **Don't** turn every metric or record into a rounded card.
- **Don't** use amber, blue, or crimson as arbitrary decoration.
- **Don't** use monospaced type for prose or headings.
- **Don't** hide non-official settings behind neutral styling.

