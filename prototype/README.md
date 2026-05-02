# Visual Archive Prototype 📁

**Prototype Phase**: MVP validation for Steve's Gematria visual research system.  
**Goal**: Validate core artifact capture → pattern display → linking flow at low fidelity.

---

## 🎯 Essential MVP Features (What We're Building Now)

### ✅ Core Functionality
1. **Anchor Gallery Rendering** — Display foundational terms from source materials
2. **Pattern Trail Visualization** — Show connections between symbols using wikilinks  
3. **Symbol Legend** — Reference guide for quick navigation

### 📦 Deferred to Iteration 2+ (Not in MVP)
- User behavior tracking / analytics
- Payment integration for premium features
- Multi-platform sync (Obsidian, web, mobile)
- Advanced AI-powered pattern discovery

---

## 🚀 Quick Start

```bash
# Navigate to prototype directory
cd ~/gematria/visual_archive/prototype

# Compile anchor gallery from templates
python compile.py

# Preview output
cat output/anchor_gallery.md
```

**Expected Output Structure:**
```
output/
└── anchor_gallery.md
    ├── Symbol Legend (reference table)
    ├── Anchor Gallery (artifacts with wikilinks)
    └── Pattern Index (navigation links)
```

---

## 📖 Prototype Documentation

### `compile.py` — Core Engine

**What it does**: Compiles anchor definitions into rendered markdown format.  
**How it works**: 
- Reads anchor JSON/YAML data → renders to ASCII art + wikilinks
- Applies heat scale encoding (░ ▒ ▓ █ . o O) for symbol patterns
- Generates domain clusters and connection trails

**Features**:
- ✅ Core artifact capture from sources
- ✅ Pattern trail rendering with `[[wikilink]]` notation
- ✅ Heat scale ASCII patterns for terminal/Obsidian compatibility
- ✅ Essential footer with instrumentation hooks (MVP tracking placeholders)

---

## 🎨 Visual Style

### ASCII Art Outputs ✓
All visualizations use **character-based diagrams** rather than images:
- Heat scales (`░ ▒ ▓ █ . o O`)
- Pattern trails (`[[symbol1]]→[[symbol2]]`)
- Domain clusters (backtick code blocks)

**Why**: Matches Steve's Gematria "digital monastery" aesthetic and integrates with Obsidian/terminal workflows.

### Color Palette
```
█ Red:  High intensity (completion, wholeness)  
▓ Orange: Medium-high (bridge patterns)  
▒ Yellow: Medium-low (transitional cycles)  
░ Blue: Low intensity (grounding phases)  
. White: Minimal (empty/neutral)
```

---

## 🔧 Development Workflow

### Adding New Anchor Terms
1. Edit `anchors.json` with new source artifacts
2. Run `python compile.py` to regenerate markdown
3. Preview in Obsidian or terminal

### Sample JSON Structure
```json
{
  "anchor_id": "124-Bridge→666-Wholeness",
  "source": "manifesto_The_Signal",
  "context": "Universal threshold appearing across all domains",
  "symbols": ["124", "666"],
  "domains": ["Universal Threshold", "Connecting"]
}
```

---

## 📊 Prototype Success Metrics (What We're Validating)

- [ ] **Clarity**: Can users understand pattern connections quickly?
- [ ] **Flow**: Is the wikilink navigation intuitive?
- [ ] **Value Perception**: Does visualizing anchors add research value?

**MVP Threshold**: ≥3 researchers use anchor gallery within 2 weeks.

---

## 📁 Output Files

| File | Purpose | Format |
|------|---------|--------|
| `output/anchor_gallery.md` | Rendered prototype | Markdown (Obsidian-compatible) |
| `anchors.json` | Source definitions | JSON/YAML |

---

## 🔗 Integration with Gematria Research

### Obsidian Workflow
```
gematria vault/
└── visual-archive/
    ├── output/anchor_gallery.md  ← Opens here in graph view
    └── prototype/compile.py       ← Compile anchor gallery
```

**Usage in Obsidian**: 
- Open `anchor_gallery.md` → See patterns emerge
- Click wikilinks (`[[symbol]]`) → Navigate between related concepts
- Use heat scales to identify high-priority symbols at a glance

---

## 🛠️ Troubleshooting

**Pattern not rendering?**  
→ Ensure Python 3.8+ with `obsidian` plugin installed for markdown parsing

**Heat scale missing?**  
→ Check terminal font supports box drawing characters

---

## 🔜 Iteration 2 Features (Deferred)
- User behavior tracking (anonymous analytics)
- Payment integration (Obsidian vault upgrades)
- Multi-platform sync (web dashboard, mobile app)
- Advanced AI pattern discovery

---

**Version**: 0.1 — MVP Prototype  
**Status**: Core rendering validation ready ✅

---

*Visual Archive for Steve's Gematria © 2026 — A digital monastery in the terminal.*
