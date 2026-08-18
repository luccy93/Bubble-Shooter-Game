# Bubble Shooter Game

This repository contains the Bubble Shooter game. This branch (enhance/ui-readme) starts a non-destructive enhancement pass to polish the UI and mobile experience while preserving all existing gameplay functionality.

## Summary of this branch
- Project title updated to "Bubble Shooter Game".
- Added quick testing notes for reviewers so changes can be validated safely and incrementally.

I will only make incremental, reversible changes on this branch. Major gameplay or history-rewriting operations will NOT be performed on master.

## How to test the web build locally
1. Open `bubble_shooter_web.html` in a modern browser (Chrome, Edge, Firefox).
   - Right-click the file in your file manager and choose "Open with" → your browser, or drag the file into a browser window.
2. From the main menu, press "PLAY" to start the game.
3. Verify core gameplay remains unchanged:
   - Aim mechanic
   - Shooting and collision
   - Matching and bubble dropping
   - Scoring and level progression
4. Check the console for unexpected errors (for debugging only). Do not expose raw errors in release builds.

## What's next (planned safe changes)
1. Small visual polish to the main menu (buttons, typography, gentle background motion).
2. HUD layout improvements (top bar for level/progress, bottom launcher visuals).
3. Cosmetic bubble visuals (shadows, highlights) using CSS only.
4. Add animation helpers (CSS + small JS wrappers) but do not wire them into core gameplay until validated.

If you'd like me to proceed, I will update `bubble_shooter_web.html` with non-destructive UI changes on this branch and open a PR for your review.
