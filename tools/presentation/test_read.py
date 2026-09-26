import cv2
for k, v in [
    ('S1', 'output/solution1/sample1_annotated_hud.mp4'),
    ('S2', 'output/solution2/sample1_annotated_hud.mp4'),
    ('S3', 'output/solution3/sample1_annotated_hud.mp4'),
    ('S4', 'output/solution4/sample1_annotated_hud.mp4'),
    ('S5', 'output/solution5/sample1_annotated_hud.mp4'),
    ('All', 'output/sample1_all_solutions_comparison_hud.mp4'),
]:
    cap = cv2.VideoCapture(v)
    ret, frame = cap.read()
    print(f'{k}: ret={ret}, shape={frame.shape if ret else None}, frames={int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}')
    cap.release()
