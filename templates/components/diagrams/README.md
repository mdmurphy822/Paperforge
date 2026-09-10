# Paperforge TikZ Diagram Templates

Reusable TikZ diagram templates for Paperforge documents. Designed with WCAG 2.2 AA accessibility compliance and cognitive load principles from the RAG library.

## Quick Start

```latex
% In document preamble
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc, decorations.pathreplacing}

% Load diagram components
\input{templates/components/diagrams/_colors}
\input{templates/components/diagrams/_styles}
\input{templates/components/diagrams/process_flow}

% In document body
\processflow{Input}{Process}{Output}
```

## Template Index

| File | Purpose | Key Macros |
|------|---------|------------|
| `_colors.tex` | Color palette (WCAG verified) | `diagramPrimary`, `diagramDarkBg` |
| `_styles.tex` | Shared TikZ styles | `diagram box`, `diagram arrow` |
| `process_flow.tex` | Flow diagrams | `\processflow`, `\processcycle` |
| `comparison.tex` | Side-by-side layouts | `\sidebyside`, `\proscons` |
| `timeline.tex` | Event timelines | `\timelinethree`, `\phasetimeline` |
| `hierarchy.tex` | Pyramids and trees | `\pyramid`, `\orgtree` |
| `network.tex` | Node-link diagrams | `\networktriad`, `\venndiagram` |
| `flowchart.tex` | Decision flows | `\decisiontree`, `\ifthenelse` |
| `bento_grid.tex` | Card grids | `\bentogrid`, `\bentohero` |
| `data_callout.tex` | Statistics/KPIs | `\herostat`, `\progressbar` |

---

## Process Flow (`process_flow.tex`)

### Three-Step Flow
```latex
\processflow{Claim}{Baseline}{Verdict}
```

### Four-Step Flow
```latex
\processflowfour{Plan}{Design}{Build}{Deploy}
```

### Flow with Labels
```latex
\processflowlabeled{Input}{validate}{Process}{transform}{Output}
```

### Vertical Flow
```latex
\processflowvertical{Top}{Middle}{Bottom}
```

### Cyclic Flow
```latex
\processcycle{Plan}{Do}{Review}
```

### Feedback Loop
```latex
\processfeedback{Process}{Feedback}{Output}
```

### Dark Theme
```latex
\processflowdark{Step 1}{Step 2}{Step 3}
\processflowdarklabeled{A}{label1}{B}{label2}{C}
```

---

## Comparison (`comparison.tex`)

### Side-by-Side
```latex
\sidebyside{Option A}{Content for A}{Option B}{Content for B}
```

### Before/After
```latex
\beforeafter{Before}{Old state description}{After}{New state description}
```

### Pros and Cons
```latex
\proscons{Pro 1\\Pro 2\\Pro 3}{Con 1\\Con 2}
```

### Three-Column
```latex
\comparisonthree{Title1}{Content1}{Title2}{Content2}{Title3}{Content3}
```

### Versus
```latex
\versus{React}{Vue}
```

---

## Timeline (`timeline.tex`)

### Three-Event Timeline
```latex
\timelinethree{Event 1}{2020}{Event 2}{2022}{Event 3}{2024}
```

### Four-Event Timeline
```latex
\timelinefour{E1}{D1}{E2}{D2}{E3}{D3}{E4}{D4}
```

### Milestone Timeline
```latex
\milestonetimeline{Launch}{Q1}{Growth}{Q2}{Scale}{Q3}
```

### Phase Timeline
```latex
\phasetimeline{Research}{Development}{Deployment}
\phasetimelinefour{Plan}{Build}{Test}{Ship}
```

### Vertical Timeline
```latex
\timelinevertical{Start}{Jan}{Middle}{Jun}{End}{Dec}
```

---

## Hierarchy (`hierarchy.tex`)

### Three-Tier Pyramid
```latex
\pyramid{Leadership}{Management}{Operations}
```

### Four-Tier Pyramid
```latex
\pyramidfour{CEO}{Directors}{Managers}{Staff}
```

### Inverted Pyramid (Funnel)
```latex
\funnel{Awareness}{Consideration}{Conversion}
```

### Org Chart (2 children)
```latex
\orgtree{CEO}{CTO}{CFO}
```

### Org Chart (3 children)
```latex
\orgtreethree{CEO}{CTO}{CFO}{COO}
```

### Two-Level Org Chart
```latex
\orgcharttwolevel{CEO}{VP Eng}{VP Sales}{Dev1}{Dev2}{Rep1}{Rep2}
```

---

## Network (`network.tex`)

### Central Hub with 3 Nodes
```latex
\networktriad{Core}{Node A}{Node B}{Node C}
```

### Star Network (4 directions)
```latex
\networkstar{Hub}{North}{East}{South}{West}
```

### Linear Chain
```latex
\networkchain{A}{B}{C}{D}
```

### Fully Connected
```latex
\networkfully{Node 1}{Node 2}{Node 3}
```

### DAG (3 levels)
```latex
\dagthree{Root}{Mid1}{Mid2}{Leaf1}{Leaf2}{Leaf3}
```

### Two-Set Venn Diagram
```latex
\venndiagram{Set A}{Set B}{Both}
```

### Three-Set Venn Diagram
```latex
\venntriangle{A}{B}{C}{All Three}
```

### Hub and Spoke
```latex
\hubspoke{Core}{S1}{S2}{S3}{S4}{S5}{S6}
```

---

## Flowchart (`flowchart.tex`)

### Simple Flow (Start → Process → End)
```latex
\flowchartsimple{Start}{Process Data}{End}
```

### Binary Decision
```latex
\decisiontree{Is valid?}{Accept}{Reject}
```

### Two-Level Decision
```latex
\decisiontreetwo{Q1?}{Y1}{Q2?}{Y2}{N2}
```

### If-Then-Else
```latex
\ifthenelse{Condition?}{True Action}{False Action}
```

### Linear Flowchart (4 steps)
```latex
\flowchartlinear{Start}{Step 1}{Step 2}{End}
```

### Data Flow
```latex
\flowchartdata{Input File}{Transform}{Output File}
```

### Loop
```latex
\flowchartloop{i=0}{i<10?}{Process}{i++}
```

### Swimlane
```latex
\swimlane{Frontend}{Request\\Display}{Backend}{Validate\\Process}
```

---

## Bento Grid (`bento_grid.tex`)

### 2x2 Grid
```latex
\bentogrid{Card 1 content}{Card 2}{Card 3}{Card 4}
```

### Hero + 4 Cards
```latex
\bentohero{Main Feature}{Detail 1}{Detail 2}{Detail 3}{Detail 4}
```

### 2x3 Grid
```latex
\bentosix{C1}{C2}{C3}{C4}{C5}{C6}
```

### Vertical Card Stack
```latex
\cardstack{Title 1}{Content 1}{Title 2}{Content 2}{Title 3}{Content 3}
```

### Icon Grid
```latex
\icongrid{Icon1}{Label1}{Icon2}{Label2}{Icon3}{Label3}{Icon4}{Label4}
```

### Feature Card
```latex
\featurecard{Feature Name}{Description text here}{Highlight Value}
```

---

## Data Callout (`data_callout.tex`)

### Hero Statistic
```latex
\herostat{42\%}{Conversion Rate}
```

### Stat with Unit
```latex
\herostatunit{3.2}{M}{Active Users}
```

### KPI Card
```latex
\kpicard{Revenue}{\$1.2M}{up}{+12\%}
\kpicard{Churn}{5.2\%}{down}{-0.8\%}
\kpicard{Users}{10K}{stable}{0\%}
```

### Progress Bar
```latex
\progressbar{75}{Project Completion}
```

### Stacked Progress Bars
```latex
\progressstack{Design}{90}{Development}{65}{Testing}{30}
```

### Two-Stat Comparison
```latex
\statcompare{Before}{150}{After}{320}
```

### Gauge
```latex
\gauge{75}{Performance Score}
```

### Inline Badge
```latex
Growth rate: \metricbadge{+12\%}{success}
Decline: \metricbadge{-5\%}{error}
```

---

## Color Reference

### Light Theme
| Color | Hex | Use |
|-------|-----|-----|
| `diagramPrimary` | #004C93 | Primary actions |
| `diagramSecondary` | #5B9BD5 | Secondary elements |
| `diagramAccent` | #FFC72C | Highlights |
| `diagramSuccess` | #1E8449 | Positive/complete |
| `diagramWarning` | #F39C12 | Caution |
| `diagramError` | #E74C3C | Negative/error |

### Dark Theme
| Color | Hex | Use |
|-------|-----|-----|
| `diagramDarkBg` | #242424 | Background |
| `diagramDarkText` | #F0F0F0 | Primary text |
| `diagramDarkPrimary` | #5DADE2 | Accent |
| `diagramDarkBorder` | #B0B0B8 | Borders |

---

## Accessibility Guidelines

1. **Contrast**: All colors verified for WCAG 2.2 AA (4.5:1 minimum)
2. **Redundancy**: Use shape + color, never color alone
3. **Cognitive load**: Maximum 4 elements per diagram
4. **Alt text**: Always add `\caption{}` for figures
5. **Theme support**: Dark variants for all major macros

---

## Integration Example

```latex
\documentclass{book}
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, calc}

% Load all diagram templates
\input{templates/components/diagrams/_colors}
\input{templates/components/diagrams/_styles}
\input{templates/components/diagrams/process_flow}
\input{templates/components/diagrams/comparison}
\input{templates/components/diagrams/timeline}
\input{templates/components/diagrams/hierarchy}
\input{templates/components/diagrams/network}
\input{templates/components/diagrams/flowchart}
\input{templates/components/diagrams/bento_grid}
\input{templates/components/diagrams/data_callout}

\begin{document}

\chapter{Analysis}

The following workflow illustrates our methodology:

\processflowlabeled{Data}{collect}{Analysis}{synthesize}{Insights}

\section{Results}

\herostat{87\%}{Accuracy Achieved}

\end{document}
```

---

## Math & Physics Diagrams (`math_diagrams.tex`)

Scientific and mathematical concept visualization for technical documents.

### Force & Stress Diagrams

```latex
% Two forces at specified angles
\forcediagram{Satellite}{$F_g$}{270}{$F_c$}{90}

% Balanced forces in cardinal directions
\equilibriumforces{Structure}{$T$}{$T$}{$F_{lift}$}{$mg$}

% Pressure vessel cross-section with stress formula
\pressurevesselcross{$R$}{$t$}{$P_{int}$}

% Shell element showing hoop/meridional stress
\shellstressdiagram{$R$}{$t$}{hoop}    % or {meridional} or {both}
```

### Orbital Mechanics

```latex
% Elliptical orbit with periapsis/apoapsis
\orbitellipse{Earth}{Transfer orbit}{$r_p$}{$r_a$}

% Five Lagrange points for two-body system
\lagrangepoints{Sun}{Earth}

% Hohmann-style transfer trajectory
\transferorbit{Earth orbit}{Mars orbit}{Hohmann transfer}
```

### Operating Envelopes

```latex
% 2D state space with safe/danger regions
\statespaceenvelope{Stress $\sigma$}{Cycles $N$}{Safe}{Fatigue failure}

% Simplified rectangular envelope
\envelopebounds{Velocity}{Altitude}{Entry corridor}{Current state}
```

### Scaling & Proportions

```latex
% Geometric scaling comparison
\scalingcubes{$r$}{$2r$}{Mass $\propto r^3$}

% Proportional bar comparison
\proportionbar{Surface Area}{4}{Volume}{8}
```

### Physics Concepts

```latex
% Centripetal acceleration diagram
\rotatingframe{Axis}{$r = 500$ m}{$\omega$}{$a_c = \omega^2 r$}

% Radiation attenuation through shielding
\radiationshield{3}{$x$ cm}{$I = I_0 e^{-\mu x}$}

% Stress-strain curve with yield/ultimate points
\stressstrain{$\sigma_y = 250$ MPa}{$\sigma_u = 400$ MPa}
```

### Dark Theme Variants

All math diagram macros have dark theme variants by adding `dark` suffix:

```latex
\forcediagramdark{...}
\pressurevesselcrossdark{...}
\orbitellipsedark{...}
\rotatingframedark{...}
```
