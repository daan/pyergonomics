# Development Notebooks

Internal notebooks for debugging, testing, and development. Not intended for end users.

## Notebooks

### xsens_skeleton.ipynb
Compare BVH forward kinematics implementations:
- **Cell 1**: Reference FK implementation (per-frame, manual computation)
- **Cell 2**: Compare with `pyergonomics.importers.from_bvh` output

Use this to debug import issues - red and blue points should overlap exactly.
