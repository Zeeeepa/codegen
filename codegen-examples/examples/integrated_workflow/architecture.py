#!/usr/bin/env python3
"""
Generate an architecture diagram for the integrated workflow.
"""

import os
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.lines as lines
import numpy as np

# Set up the figure
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 10)
ax.set_ylim(0, 7)
ax.axis('off')

# Define colors
colors = {
    'github': '#333333',
    'slack': '#4A154B',
    'linear': '#5E6AD2',
    'event_handler': '#2D9CDB',
    'issue_solver': '#27AE60',
    'pr_review': '#F2994A',
    'knowledge_transfer': '#9B51E0',
    'arrow': '#718096',
    'background': '#F7FAFC',
    'box': '#E2E8F0',
    'text': '#1A202C'
}

# Draw the background
ax.add_patch(patches.Rectangle((0, 0), 10, 7, facecolor=colors['background'], edgecolor='none'))

# Draw the components
def draw_box(x, y, width, height, label, color, fontsize=12):
    ax.add_patch(patches.FancyBboxPatch(
        (x, y), width, height, 
        boxstyle=patches.BoxStyle("Round", pad=0.3, rounding_size=0.2),
        facecolor=color, edgecolor='none', alpha=0.8
    ))
    ax.text(x + width/2, y + height/2, label, ha='center', va='center', 
            color='white', fontsize=fontsize, fontweight='bold')

# External services
draw_box(0.5, 5.5, 2, 1, 'GitHub', colors['github'])
draw_box(3.0, 5.5, 2, 1, 'Slack', colors['slack'])
draw_box(5.5, 5.5, 2, 1, 'Linear', colors['linear'])

# Event handler
draw_box(3.0, 4.0, 4, 1, 'Event Handlers', colors['event_handler'])

# Agents
draw_box(1.0, 2.5, 2.5, 1, 'Issue Solver Agent', colors['issue_solver'])
draw_box(4.0, 2.5, 2.5, 1, 'PR Review Bot', colors['pr_review'])
draw_box(7.0, 2.5, 2.5, 1, 'Knowledge Transfer', colors['knowledge_transfer'])

# Codebase
draw_box(3.0, 0.5, 4, 1, 'Codebase', colors['github'])

# Draw arrows
def draw_arrow(x1, y1, x2, y2, color=colors['arrow'], width=0.01, style='-'):
    ax.add_line(lines.Line2D([x1, x2], [y1, y2], color=color, linewidth=2, linestyle=style))
    # Add arrowhead
    dx = x2 - x1
    dy = y2 - y1
    length = np.sqrt(dx**2 + dy**2)
    dx, dy = dx/length, dy/length
    ax.add_patch(patches.Polygon(
        [[x2, y2], [x2-0.2*dx-0.1*dy, y2-0.2*dy+0.1*dx], [x2-0.2*dx+0.1*dy, y2-0.2*dy-0.1*dx]],
        closed=True, color=color
    ))

# External services to event handler
draw_arrow(1.5, 5.5, 3.0, 4.5)
draw_arrow(4.0, 5.5, 4.0, 5.0)
draw_arrow(6.5, 5.5, 5.0, 4.5)

# Event handler to agents
draw_arrow(3.5, 4.0, 2.5, 3.5)
draw_arrow(5.0, 4.0, 5.0, 3.5)
draw_arrow(6.5, 4.0, 7.5, 3.5)

# Agents to codebase
draw_arrow(2.5, 2.5, 3.5, 1.5)
draw_arrow(5.0, 2.5, 5.0, 1.5)
draw_arrow(7.5, 2.5, 6.5, 1.5)

# Codebase to agents (feedback loop)
draw_arrow(4.0, 1.5, 2.0, 2.5, style='--')
draw_arrow(5.0, 1.5, 5.0, 2.5, style='--')
draw_arrow(6.0, 1.5, 8.0, 2.5, style='--')

# Add title
ax.text(5, 6.8, 'Integrated AI Development Workflow', ha='center', fontsize=16, fontweight='bold', color=colors['text'])

# Save the diagram
output_path = Path(__file__).parent / 'architecture.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Architecture diagram saved to {output_path}")

# Show the diagram
plt.show()
