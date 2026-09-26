import cv2

for target_frame in [462, 512]:
    for name, vpath in [
        ('S3', 'output/solution3/sample1_annotated_hud.mp4'),
        ('S5', 'output/solution5/sample1_annotated_hud.mp4'),
        ('ALL', 'output/sample1_all_solutions_comparison_hud.mp4'),
    ]:
        cap = cv2.VideoCapture(vpath)
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        if ret:
            out_path = f'output/white_presentation/{name}_frame_{target_frame}.jpg'
            cv2.imwrite(out_path, frame)
            print(f'Saved {out_path}')
        cap.release()
