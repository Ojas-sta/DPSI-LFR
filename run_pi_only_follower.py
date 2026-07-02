#!/usr/bin/env python3
"""Convenience launcher for the Pi-only DPSI-LFR controller."""

from rpi_line_follower.pi_only_follower import main


if __name__ == "__main__":
    raise SystemExit(main())

