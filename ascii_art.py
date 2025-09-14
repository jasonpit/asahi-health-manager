#!/usr/bin/env python3
"""
ASCII Art definitions for Asahi Health Manager
"""

# App Icon ASCII Art (based on the chip design with circuit pattern)
APP_ICON_SMALL = """
    ╭─────╮
  ╭─│ ◉ ◉ │─╮
  │ │ ┼ ┼ │ │
  │ │ ◉ ◉ │ ▼
  ╰─│ ┼ ┼ │─╯
    ╰─────╯
"""

APP_ICON_LARGE = """
       ╭─────────────╮
     ╭─│  ◉   ◉   ◉  │─╮
   ╭─│ │  │   │   │  │ │─╮
  ╱  │ │  ┼───┼───┼  │ │  ╲
 ╱   │ │  │   │   │  │ │   ╲
│    │ │  ◉   ◉   ◉  │ │ ▼  │
│    │ │  │   │   │  │ │    │
 ╲   │ │  ┼───┼───┼  │ │   ╱
  ╲  │ │  │   │   │  │ │  ╱
   ╰─│ │  ◉   ◉   ◉  │ │─╯
     ╰─│             │─╯
       ╰─────────────╯
"""

# Asahi Linux Logo ASCII Art (inspired by the mountain/volcano design)
ASAHI_LOGO_SMALL = """
      /\    /\
     /  \  /  \
    /    \/    \
   /  ASAHI  \
  /__________\
"""

ASAHI_LOGO_LARGE = """
           /\      /\
          /  \    /  \
         /    \  /    \
        /      \/      \
       /                \
      /    A S A H I     \
     /      L I N U X     \
    /                      \
   /________________________\
  /__________________________\
"""

# Combined header with both logos
COMBINED_HEADER = """
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                  ║
║        ╭─────────╮          A S A H I   H E A L T H   M A N A G E R            ║
║      ╭─│ ◉  ◉  ◉ │─╮                                                           ║
║     ╱  │ ┼  ┼  ┼ │  ╲       Advanced System Management for Apple Silicon      ║
║    ╱   │ ◉  ◉  ◉ │ ▼ ╲                                                         ║
║   ╱    │ ┼  ┼  ┼ │    ╲              /\      /\                               ║
║  ╱     ╰─────────╯     ╲            /  \    /  \                              ║
║                         ╲          /    \  /    \                             ║
║                                   /   ASAHI LINUX  \                          ║
║                                  /__________________ \                         ║
║                                                                                ║
║  AI-Powered • Cloud Sync • Hardware Detection • Performance Optimization      ║
║                                                                                ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

# Minimal header for smaller terminals
MINIMAL_HEADER = """
╔═══════════════════════════════════════════════╗
║  [◉◉◉]  A S A H I   H E A L T H   M G R  /\  ║
║  [┼┼┼]  System Management for Apple   /ASAHI\ ║
║  [◉◉◉]  Silicon Macs                /_______\ ║
╚═══════════════════════════════════════════════╝
"""

# Loading/progress animations
LOADING_FRAMES = [
    "[    ] Loading...",
    "[=   ] Loading...", 
    "[==  ] Loading...",
    "[=== ] Loading...",
    "[====] Loading...",
    "[ ===] Loading...",
    "[  ==] Loading...",
    "[   =] Loading...",
]

CHIP_LOADING_FRAMES = [
    "◉ ◯ ◯",
    "◯ ◉ ◯", 
    "◯ ◯ ◉",
    "◯ ◉ ◯",
]

# Status indicators
STATUS_ICONS = {
    'good': '[+]',
    'warning': '[!]',
    'error': '[!]',
    'critical': '[!]',
    'info': '[>]',
    'question': '[?]',
    'processing': '[~]'
}

def get_terminal_width():
    """Get terminal width for responsive design"""
    import shutil
    return shutil.get_terminal_size().columns

def get_header_for_width(width=None):
    """Get appropriate header based on terminal width"""
    if width is None:
        width = get_terminal_width()
    
    if width >= 86:
        return COMBINED_HEADER
    elif width >= 47:
        return MINIMAL_HEADER
    else:
        return APP_ICON_SMALL + "\nAsahi Health Manager"

def animate_loading(message="Loading", frames=None):
    """Generator for loading animation"""
    import itertools
    if frames is None:
        frames = LOADING_FRAMES
    
    for frame in itertools.cycle(frames):
        yield f"\r{frame} {message}"