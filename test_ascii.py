#!/usr/bin/env python3
"""
Test script to preview ASCII art headers
"""

from rich.console import Console
from ascii_art import *

def main():
    console = Console()
    
    console.print("\n[bold cyan]=== ASCII Art Preview ===[/bold cyan]\n")
    
    # Show different headers based on width
    console.print("[bold]Wide Terminal Header:[/bold]")
    console.print(COMBINED_HEADER)
    
    console.print("\n[bold]Medium Terminal Header:[/bold]")  
    console.print(MINIMAL_HEADER)
    
    console.print("\n[bold]Small Terminal (App Icon):[/bold]")
    console.print(APP_ICON_SMALL)
    
    console.print("\n[bold]Large App Icon:[/bold]")
    console.print(APP_ICON_LARGE)
    
    console.print("\n[bold]Asahi Logo Variations:[/bold]")
    console.print("Small:")
    console.print(ASAHI_LOGO_SMALL)
    console.print("Large:")
    console.print(ASAHI_LOGO_LARGE)
    
    console.print("\n[bold]Status Icons:[/bold]")
    for status, icon in STATUS_ICONS.items():
        console.print(f"  {status}: {icon}")
    
    console.print(f"\n[bold]Current terminal width:[/bold] {get_terminal_width()} columns")
    console.print(f"[bold]Recommended header:[/bold]")
    console.print(get_header_for_width())

if __name__ == "__main__":
    main()