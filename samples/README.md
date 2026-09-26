# 📁 Samples Directory

This directory is kept lightweight for public git distribution.

- Raw original videos (`sample1.mp4`, full `sample2.mp4`) are stored locally in `local/samples/` (git-ignored to protect athlete privacy and keep repository size minimal).
- A 5-second privacy-anonymized annotated sample is provided in [`output/solution2/sample2_5s_annotated.mp4`](../output/solution2/sample2_5s_annotated.mp4) and [`docs/assets/demo.gif`](../docs/assets/demo.gif).

### Adding Your Own Videos
Place any `.mp4`, `.avi`, or `.mov` workout video into `local/samples/`:
```bash
mkdir -p local/samples
cp /path/to/video.mp4 local/samples/my_workout.mp4
uv run stairmaster --video local/samples/my_workout.mp4 --solution 2 --save-video
```
