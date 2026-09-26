import cv2, os

videos = {
    'S1': 'output/solution1/sample1_annotated_hud.mp4',
    'S2': 'output/solution2/sample1_annotated_hud.mp4',
    'S3': 'output/solution3/sample1_annotated_hud.mp4',
    'S4': 'output/solution4/sample1_annotated_hud.mp4',
    'S5': 'output/solution5/sample1_annotated_hud.mp4',
    'ALL': 'output/sample1_all_solutions_comparison_hud.mp4',
}

os.makedirs('output/white_presentation', exist_ok=True)

# Let's extract frame 540 (18.0s) and frame 450 (15.0s)
for target_frame in [450, 540]:
    for name, vpath in videos.items():
        cap = cv2.VideoCapture(vpath)
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        if ret:
            out_path = f'output/white_presentation/{name}_frame_{target_frame}.jpg'
            cv2.imwrite(out_path, frame)
            print(f'Saved {out_path} ({frame.shape})')
        cap.release()
