# 🔧 Visual Art Integration Guide

## 📦 Available Creative Skills

The gematria visual archive has access to these creative generation skills:

### ASCII & Pattern Generation
- **`gematria-symbol-cluster-art`** — Primary tool for generating ASCII/visual art from gematria symbol clusters using pattern trails as data source.

### Pixel Art Era Palettes  
- **`pixel-art`** — Pixel art with era palettes (NES, Game Boy, PICO-8)
  - NES palette: Classic 1-bit with limited color accents
  - Game Boy: Monochrome green/gray
  - PICO-8: 16-color retro palette

### Advanced Visualization
- **`architecture-diagram`** — Dark-themed SVG architecture/cloud/infra diagrams as HTML
- **`excalidraw`** — Hand-drawn Excalidraw JSON diagrams (arch, flow, seq)
- **`design-md`** — Google's DESIGN.md token spec files for design systems

### Specialized Tools
- **`ascii-art`** — pyfiglet, cowsay, boxes, image-to-ascii conversions
- **`baoyu-infographic`** — 21 layouts × 21 styles Chinese infographics (信息图，可视化)
- **`pretext`** — DOM-free text layout for ASCII art, typographic flow, kinetic typography

### Media & Animation
- **`ascii-video`** — Convert video/audio to colored ASCII MP4/GIF
- **`manim-video`** — 3Blue1Brown-style math/algo animations with Manim CE

---

## 🎯 Integration Workflow

### Step 1: Identify Source Material
```bash
# Check existing anchor gallery
cat /home/avalonas/.hermes/gematria-visual-archive/output/anchor_gallery.md

# Review recent gematria analysis
ls /home/avalonas/.hermes/gematria/
```

### Step 2: Select Appropriate Tool
**For ASCII heat maps from symbols**: Use `gematria-symbol-cluster-art`
**For pixel art**: Use `pixel-art` with era palette selection  
**For diagrams**: Use `architecture-diagram` or `excalidraw`

### Step 3: Generate & Route Output
```python
# Example workflow pattern
output_path = f"/home/avalonas/.hermes/gematria-visual-archive/output/art/{type}/{filename}"
```

---

## 🔍 Pattern Trail Examples

### From anchor_gallery.md Symbols

```markdown
[124-Bridge→666-Wholeness] 
  → Generates: ASCII heatmap showing intensity gradient from ░░ to ████
  
[[9-Harmony←666-Wholeness]]
  → Generates: Circular flow diagram with reduction visualization
```

### Wikilink Format
```markdown
[[124-Bridge→666-Wholeness]]. [[9-Harmony←666-Wholeness]]. [[17-Vessel→8-Grounding]]
```

---

## 📊 Heat Scale Reference

| Character | Value | Use Case |
|-----------|-------|----------|
| `░` | 20% | Emerging patterns, weak correlations |
| `▒` | 35% | Medium patterns, developing connections |
| `▓` | 50% | Strong patterns, established relationships |
| `█` | 70% | Core symbols, high intensity |
| `.` / `o` / `O` / `^` | Low/Med/High variants | Alternative encoding for texture |

---

## 🗂️ Output Organization

```bash
output/art/
├── ascii_patterns/      # ASCII heat maps and terminal outputs
│   ├── symbols/         # Individual symbol visualizations
│   └── trails/          # Pattern trail sequences
├── pixel_art/           # Era palette artworks
│   ├── NES/             # 1-bit with color accents
│   ├── GameBoy/         # Monochrome green/gray
│   └── PICO8/           # 16-color retro
├── collections/         # Symbol cluster galleries
│   ├── bridge_to_wholeness/
│   ├── reduction_cycles/
│   └── vessel_protocol/
```

---

## 🛠️ Quick Integration Commands

### Generate ASCII Pattern Trail
```bash
# Example: 124→666→9 cycle visualization
skill_view(name="gematria-symbol-cluster-art")
```

### Create Pixel Art from Concept
```bash
# Use pixel-art skill with era palette selection
skill_view(name="pixel-art")
```

### Generate SVG Diagram
```bash
skill_view(name="architecture-diagram")
```

---

## 📝 Status Tracking

Current status should be documented in:
- `output/status/processing.log` — Real-time generation logs
- `output/art/collections/.status` — Gallery completion indicators

Use ASCII heat scale for status encoding:
```bash
█ = Processing complete
▓ = In progress  
░ = Pending/Awaiting input
```

---

## 🔗 Hermes Skill System Integration

All visual art skills integrate with the Hermes skill library at:
```bash
/home/avalonas/.hermes/skills/creative/
```

Key gematria-specific skills also available:
- `gematria-analysis-workflow` — Multi-step image/text analysis
- `gematria-multi-domain-pattern-analysis` — Structured analysis docs
- `gematria-image-seed-overnight-research` — Image-to-event research pipeline
- `gematria-visualization-engine-setup` — ASCII/HTML dashboard creation

---

## 🎨 Example: Generating First Pattern Trail

```bash
# 1. View available creative skills
skills_list(category="creative")

# 2. Load specific skill for usage context
skill_view(name="gematria-symbol-cluster-art")

# 3. Generate visualization (via skill execution)
# Output will be written to output/art/ascii_patterns/symbols/
```

---

**Integration Ready** — Visual art tools can now generate content directly into this repository's `output/art/` directory.
