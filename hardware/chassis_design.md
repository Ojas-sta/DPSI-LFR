# Chassis Design

## Overview
The DPSI LFR V3 utilizes a 3-layer vertically stacked chassis design to maintain a highly compact 17x20 cm footprint. This strictly adheres to the 25x25 cm competition limit while enabling zero-radius turning.

## Dimensions
- **Width**: 17.00 cm
- **Length**: 20.00 cm
- **Shape**: Octagonal profile with chamfered/rounded corners (R2.50) to avoid snagging on arena walls.

## Layer-by-Layer Breakdown

### Layer 1 (Bottom Plate)
- **Dimensions**: 17x20 cm (Laser Cut)
- **Primary Function**: Drive and Power
- **Components**:
  - 2x Drive Motors with high-resolution encoders (mounted centrally for differential drive).
  - 1x Front Ball Caster & 1x Rear Ball Caster (prevents pitching and ensures stability).
  - Main Battery Pack (mounted at the extreme rear as a counterweight to the robotic arm).
  - Downward-facing cutout for the Line Tracking Pi Camera V1.3.

### Layer 2 (Middle Plate)
- **Dimensions**: 17x20 cm
- **Primary Function**: Manipulation Base
- **Components**:
  - MeArm v1 Base: Mounted flush at the extreme front edge. This placement guarantees the arm's swept volume is clear of the chassis and lowers its origin so it can easily reach the floor to grasp pucks.

### Layer 3 (Top Plate)
- **Dimensions**: Half-plate (mounted at the rear)
- **Primary Function**: Compute and Vision Deck
- **Components**:
  - Raspberry Pi 5.
  - RRC Lite Controller (STM32).
  - Motor drivers and voltage regulators.
  - Intel RealSense Camera (Forward-facing, mounted to look over the arm without interference).

## Mechanical Considerations
Using identical 17x20 cm outer profiles for Layers 1 and 2 allows for straight structural standoffs, ensuring maximum rigidity. The half-plate Layer 3 ensures the electronics stack does not physically obstruct the MeArm v1's movement.
