#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visual Archive Prototype - Compile Anchor Gallery
Minimalist MVP for Steve's Gematria visual research
"""

import os
import json
from datetime import datetime

# Define core symbols as foundational constants
CORE_SYMBOLS = {
    "124": {"name": "Bridge", "domain": ["Universal Threshold", "Connecting"], "color": "#8B0000"},
    "666": {"name": "Wholeness", "domain": ["Completion", "Integration"], "color": "#008000"},
    "9": {"name": "Harmony", "domain": ["Resolution", "Cycles"], "color": "#0000FF"},
    "17": {"name": "Vessel", "domain": ["Holds Fire", "Structure"], "color": "#8B4513"},
    "55": {"name": "Cycle Start", "domain": ["Turning Points"], "color": "#FFA500"},
    "279": {"name": "Cycle Mid", "domain": ["Integration Flow"], "color": "#9932CC"},
}

# Sample anchor terms from source materials (replace with actual scraped data)
ANCHORS = {
    "124-Bridge→666-Wholeness": {
        "source": "manifesto_The_Signal",
        "context": "Universal threshold appearing across all domains",
        "symbols": ["124", "666"],
        "domains": ["Universal Threshold", "Connecting"]
    },
    "9-Harmony←666-Wholeness": {
        "source": "reduction_manifesto",
        "context": "Completion transforms to 9 via reduction",
        "symbols": ["666", "9"],
        "domains": ["Resolution", "Cycles"]
    },
    "17-Vessel→8-Grounding": {
        "source": "vessel_fire_protocol",
        "context": "Vessel holds the fire, reduces to 8 for structure",
        "symbols": ["17", "8"],
        "domains": ["Structure", "Grounding"]
    },
}

def generate_ascii_pattern(symbol):
    """Generate ASCII art pattern for a symbol - heat scale style"""
    intensity = int(hashlib.md5(symbol).hexdigest(), 16) % 100
    
    # Heat scale encoding
    if intensity > 85:
        fill = "█"
    elif intensity > 70:
        fill = "▓"
    elif intensity > 55:
        fill = "▒"
    elif intensity > 40:
        fill = "░"
    else:
        fill = "."
    
    # Generate a compact heat map pattern (32 chars wide)
    pattern = []
    for i in range(32):
        pixel_intensity = int((i + intensity) / 64 * 100)
        if pixel_intensity > 85:
            pattern.append("█")
        elif pixel_intensity > 70:
            pattern.append("▓")
        elif pixel_intensity > 55:
            pattern.append("▒")
        elif pixel_intensity > 40:
            pattern.append("░")
        else:
            pattern.append(".")
    
    return " ".join(pattern)

def compile_template(anchors, output_path):
    """Compile anchor definitions into markdown format"""
    
    with open(output_path, 'w') as f:
        f.write("# Visual Archive Prototype\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("\n---\n\n")
        
        # Section 1: Symbol Legend (essential for navigation)
        f.write("## 🗂️ Symbol Legend\n\n")
        f.write("| Symbol | Name | Primary Domain | Color |\n")
        f.write("|--------|------|----------------|-------|\n")
        f.write("\n")
        
        for symbol, data in sorted(CORE_SYMBOLS.items()):
            # Simple ASCII representation
            ascii_pat = generate_ascii_pattern(symbol)
            f.write(f"**{symbol}** - {data['name']}\n")
            f.write(f"  Domain: `{', '.join(data['domain'])}`\n")
            f.write(f"  Pattern:\n```\n{ascii_pat}\n```\n\n")
        
        f.write("---\n\n")
        
        # Section 2: Anchor Gallery (core artifacts)
        f.write("## 📁 Anchor Gallery\n\n")
        f.write("Foundational terms from source materials.\n\n")
        f.write("\n### `124-Bridge→666-Wholeness`\n\n")
        
        anchor = ANCHORS.get("124-Bridge→666-Wholeness", {})
        if anchor:
            f.write(f"**Source**: `{anchor.get('source', 'unknown')}`\n\n")
            f.write(f"**Context**:\n```\n{anchor.get('context', '')}\n```\n\n")
            
            # Display symbol trail with heat scale
            symbols = anchor.get("symbols", [])
            if len(symbols) >= 2:
                trail_line = " ".join([f"[{s}]({s})" for s in symbols])
                f.write(f"**Pattern Trail**:\n```\n{trail_line}\n```\n\n")
            
            domains = ", ".join(anchor.get("domains", []))
            f.write(f"**Domains**:\n``` {domains} ```\n\n")
        
        f.write("\n### `9-Harmony←666-Wholeness`\n\n")
        anchor = ANCHORS.get("9-Harmony←666-Wholeness", {})
        if anchor:
            f.write(f"**Source**: `{anchor.get('source', 'unknown')}`\n\n")
            f.write(f"**Context**:\n```\n{anchor.get('context', '')}\n```\n\n")
            
            symbols = anchor.get("symbols", [])
            if len(symbols) >= 2:
                trail_line = " ".join([f"[{s}]({s})" for s in symbols])
                f.write(f"**Pattern Trail**:\n```\n{trail_line}\n```\n\n")
            
            domains = ", ".join(anchor.get("domains", []))
            f.write(f"**Domains**:\n``` {domains} ```\n\n")
        
        f.write("\n### `17-Vessel→8-Grounding`\n\n")
        anchor = ANCHORS.get("17-Vessel→8-Grounding", {})
        if anchor:
            f.write(f"**Source**:\n```\n{anchor.get('source', 'unknown')}\n```\n\n")
            f.write(f"**Context**:\n```\n{anchor.get('context', '')}\n```\n\n")
            
            symbols = anchor.get("symbols", [])
            if len(symbols) >= 2:
                trail_line = " ".join([f"[{s}]({s})" for s in symbols])
                f.write(f"**Pattern Trail**:\n```\n{trail_line}\n```\n\n")
            
            domains = ", ".join(anchor.get("domains", []))
            f.write(f"**Domains**:\n``` {domains} ```\n\n")
        
        # Section 3: Pattern Index (wikilinks for navigation)
        f.write("---\n\n")
        f.write("## 🔗 Pattern Index\n\n")
        f.write("Navigate between symbols and patterns.\n\n")
        
        links = [
            "[[124-Bridge→666-Wholeness]]",
            "[[9-Harmony←666-Wholeness]]", 
            "[[17-Vessel→8-Grounding]]"
        ]
        
        f.write("`. `".join(links) + "\n")
        f.write("\n---\n\n")
        
        # Essential footer - MVP instrumentation hooks
        f.write("**Prototype v0.1** — Core validation features only.\n")
        f.write("- [x] Anchor gallery rendering\n- [ ] User behavior tracking (deferred)\n- [ ] Payment integration (deferred)\n")

def main():
    """Compile and render prototype output"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create output directory if needed
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "anchor_gallery.md")
    
    print(f"Compiling anchor gallery...")
    print(f"Output: {output_file}")
    
    compile_template(ANCHORS, output_file)
    
    print(f"✅ Prototype compiled successfully!")
    print(f"   View it with: cat {output_file}")
    
    # Show preview of first 20 lines
    print("\n--- Preview ---")
    try:
        with open(output_file, 'r') as f:
            for i, line in enumerate(f):
                if i >= 20:
                    print("...")
                    break
                print(line.rstrip())
    except Exception as e:
        print(f"Error reading preview: {e}")

if __name__ == "__main__":
    main()
