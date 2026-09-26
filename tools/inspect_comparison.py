import cv2, os

cap = cv2.VideoCapture('output/sample2_all_solutions_comparison_hud.mp4')
print('comparison exists:', cap.isOpened())
if cap.isOpened():
    print('frames:', cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print('fps:', cap.get(cv2.CAP_PROP_FPS))
    print('w,h:', cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    ret, frame = cap.read()
    if ret:
        os.makedirs('output/inspect_s2', exist_ok=True)
        cv2.imwrite('output/inspect_s2/comparison_sample2_f0.jpg', frame)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 60)
        ret2, f2 = cap.read()
        if ret2:
            cv2.imwrite('output/inspect_s2/comparison_sample2_f60.jpg', f2)
        print('Saved comparison sample frames.')
cap.release()
