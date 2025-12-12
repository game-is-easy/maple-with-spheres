import argparse, os
import numpy as np
import cv2
# from math import degrees
# from sklearn.cluster import KMeans

def align_translation(imgA, imgB):
    h = min(imgA.shape[0], imgB.shape[0]); w = min(imgA.shape[1], imgB.shape[1])
    imgA = imgA[:h,:w].copy(); imgB = imgB[:h,:w].copy()
    gA = cv2.cvtColor(imgA, cv2.COLOR_BGR2GRAY); gB = cv2.cvtColor(imgB, cv2.COLOR_BGR2GRAY)
    warp_mode = cv2.MOTION_TRANSLATION; warp_matrix = np.eye(2,3,dtype=np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-6)
    try:
        _, warp_matrix = cv2.findTransformECC(gA, gB, warp_matrix, warp_mode, criteria, None, 5)
        imgB_al = cv2.warpAffine(imgB, warp_matrix, (w,h), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
    except cv2.error:
        (sx, sy), _ = cv2.phaseCorrelate(np.float32(gA), np.float32(gB))
        M = np.float32([[1,0,-sx],[0,1,-sy]])
        imgB_al = cv2.warpAffine(imgB, M, (w,h), flags=cv2.INTER_LINEAR)
    return imgA, imgB_al

def difference_gate(imgA, imgB_al, dilate_iters=2):
    diff = cv2.absdiff(imgA, imgB_al)
    g = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(g,(5,5),0)
    _, b = cv2.threshold(g,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
    return cv2.dilate(b, k3, iterations=dilate_iters)

def vivid_mask(img, sv_min=70):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return hsv, cv2.inRange(hsv, (0, sv_min, sv_min), (179,255,255))

def find_band(gate, band_height=80):
    row_score = gate.sum(axis=1).astype(np.float32)
    band_center = int(np.argmax(cv2.GaussianBlur(row_score.reshape(-1,1),(1,21),0)))
    H = gate.shape[0]
    y0 = max(0, band_center - band_height//2)
    y1 = min(H, y0 + band_height)
    return y0, y1

def unwrap_along_axis(h_vals, order_idx):
    # OpenCV hue is 0..179; scale to [0..360) for unwrapping
    a = h_vals.astype(np.float32) * 2.0
    a_ord = a[order_idx]
    unwrapped = np.zeros_like(a_ord, dtype=np.float32)
    unwrapped[0] = a_ord[0]
    for i in range(1, len(a_ord)):
        prev = unwrapped[i-1]; cur = a_ord[i]
        k = round((prev - cur)/360.0)
        unwrapped[i] = cur + 360.0*k
    out = np.zeros_like(a, dtype=np.float32)
    out[order_idx] = unwrapped
    return out

def apex_angle(contour, idx, step):
    n = len(contour); i = idx % n
    p = contour[i,0].astype(np.float32)
    a = contour[(i-step)%n,0].astype(np.float32) - p
    b = contour[(i+step)%n,0].astype(np.float32) - p
    if np.linalg.norm(a)<1e-6 or np.linalg.norm(b)<1e-6: return 180.0
    cosang = float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)))
    cosang = max(-1.0, min(1.0, cosang))
    return float(np.degrees(np.arccos(cosang)))

def nms(boxes, iou_thresh=0.3):
    boxes = sorted(boxes, key=lambda r: r[0], reverse=True)  # sort by score
    keep = []
    def iou(b1, b2):
        x1,y1,w1,h1 = b1; x2,y2,w2,h2 = b2
        xa=max(x1,x2); ya=max(y1,y2); xb=min(x1+w1,x2+w2); yb=min(y1+h1,y2+h2)
        inter=max(0,xb-xa)*max(0,yb-ya); union=w1*h1 + w2*h2 - inter
        return inter/union if union>0 else 0.0
    for row in boxes:
        _, x,y,w,h, *_ = row
        if all(iou((x,y,w,h),(r[1],r[2],r[3],r[4])) <= iou_thresh for r in keep):
            keep.append(row)
    return keep

def dynamic_select(cands, K=4, min_dx=20, max_dy_adj=22, target_size=50.0, size_w=0.5, drift_w=0.5):
    # Sort by x center
    c = np.array(cands, dtype=float)
    xc = c[:,1] + c[:,3]/2
    order = np.argsort(xc)
    c = c[order]; n = len(c)
    dp = -1e9*np.ones((K, n), dtype=float)
    prev = -np.ones((K, n), dtype=int)
    ys, xs, ws, hs = c[:,2], c[:,1], c[:,3], c[:,4]

    for i in range(n):
        size_pen = size_w * abs((ws[i]+hs[i])/2 - target_size) / target_size
        dp[0,i] = c[i,0] - size_pen

    for k in range(1,K):
        for i in range(n):
            for j in range(i):
                dx = (xs[i]+ws[i]/2) - (xs[j]+ws[j]/2)
                dy = (ys[i]+hs[i]/2) - (ys[j]+hs[j]/2)
                if dx < min_dx or abs(dy) > max_dy_adj:
                    continue
                size_pen = size_w * abs((ws[i]+hs[i])/2 - target_size) / target_size
                drift_pen = drift_w * (abs(dy)/max_dy_adj)
                score = dp[k-1,j] + c[i,0] - size_pen - drift_pen
                if score > dp[k,i]:
                    dp[k,i] = score; prev[k,i] = j

    end_idx = int(np.argmax(dp[K-1]))
    seq_idx = [end_idx]
    for k in range(K-1,0,-1):
        end_idx = int(prev[k,end_idx])
        if end_idx < 0: break
        seq_idx.append(end_idx)
    seq_idx = list(reversed(seq_idx))
    return c[seq_idx]

def detect_with_size_row(
    base_path, arrows_path, outdir, prefix="run",
    band_height=80, size_min=44, size_max=64, size_step=4,
    stride=6, vivid_sv=70, hue_tol=40.0,
    inlier_min=0.35, slope_min=3.0,
    nms_iou=0.3, min_dx=20, max_dy_adj=22,
    target_size=50.0
):
    imgA = cv2.imread(base_path, cv2.IMREAD_COLOR)
    imgB = cv2.imread(arrows_path, cv2.IMREAD_COLOR)
    if imgA is None or imgB is None:
        raise FileNotFoundError("Could not read input images.")
    imgA, imgB_al = align_translation(imgA, imgB)
    H, W = imgB_al.shape[:2]
    gate = difference_gate(imgA, imgB_al, dilate_iters=2)
    hsv, vivid = vivid_mask(imgB_al, sv_min=vivid_sv)
    Hh = hsv[:,:,0].astype(np.float32); S = hsv[:,:,1]; V = hsv[:,:,2]
    y0,y1 = find_band(gate, band_height=band_height)

    cands = []
    for win in range(size_min, size_max+1, size_step):
        for y in range(y0, max(y0, y1 - win), max(4, win//8)):
            for x in range(0, max(0, W - win), stride):
                g_patch = gate[y:y+win, x:x+win]
                v_patch = vivid[y:y+win, x:x+win]
                area = win*win
                frac_gate = float(g_patch.sum())/(255*area)
                frac_vivid = float(v_patch.sum())/(255*area)
                if frac_gate < 0.02 or frac_vivid < 0.02:
                    continue
                mask = cv2.bitwise_and(g_patch, v_patch)
                ys, xs = np.where(mask>0)
                if len(xs) < 80:
                    continue
                pts = np.column_stack([xs, ys]).astype(np.float32)
                mean = pts.mean(axis=0)
                cov = np.cov((pts-mean).T)
                eigvals, eigvecs = np.linalg.eig(cov)
                v = eigvecs[:, np.argmax(eigvals)].real
                v = v/(np.linalg.norm(v)+1e-8)
                t = (pts-mean) @ v
                order = np.argsort(t)
                h_patch = Hh[y:y+win, x:x+win][ys, xs]
                h_unw = unwrap_along_axis(h_patch, order)
                t_norm = (t - t.min())/(t.max()-t.min()+1e-8)
                A = np.column_stack([t_norm, np.ones_like(t_norm)]).astype(np.float32)
                sol, _, _, _ = np.linalg.lstsq(A, h_unw, rcond=None)
                a = float(sol[0])
                pred = a*t_norm + float(sol[1])
                resid = np.abs(h_unw - pred)
                inlier_ratio = float(np.mean(resid <= hue_tol))

                # build contour for apex angles
                mask_bin = np.zeros((win,win), np.uint8); mask_bin[ys, xs] = 255
                cnts,_ = cv2.findContours(mask_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if not cnts: continue
                contour = max(cnts, key=cv2.contourArea)
                cont_pts = contour[:,0,:].astype(np.float32)
                t_cont = (cont_pts - mean) @ v
                idx_min = int(np.argmin(t_cont)); idx_max = int(np.argmax(t_cont))
                step = max(2, len(contour)//25)
                ang_min = apex_angle(contour, idx_min, step)
                ang_max = apex_angle(contour, idx_max, step)

                # score combines gradient fit, slope, vividness, diff, and tip sharpness
                tip_sharp = max(0.0, (min(ang_min, ang_max) - 30.0))
                score = (inlier_ratio * 2.0) + (min(abs(a), 50.0)/50.0) + (frac_vivid*0.5) + (frac_gate*0.5) + (1.2 - min(1.2, tip_sharp/90.0))
                if inlier_ratio < inlier_min or abs(a) < slope_min:
                    continue
                cands.append([score, x, y, win, win, a, inlier_ratio, ang_min, ang_max, float(v[0]), float(v[1])])

    # NMS then DP choose 4
    cands_nms = nms(cands, iou_thresh=nms_iou)
    if len(cands_nms) >= 4:
        chosen = dynamic_select(cands_nms, K=4, min_dx=min_dx, max_dy_adj=max_dy_adj, target_size=target_size)
    else:
        chosen = cands_nms[:4]

    # Build outputs
    os.makedirs(outdir, exist_ok=True)
    overlay = imgB_al.copy()
    mask_total = np.zeros((H,W), np.uint8)
    directions = []

    # left->right order
    chosen = sorted(chosen, key=lambda r: r[1])

    for sc,x,y,ww,hh,a,inlier,ang_min,ang_max,vx,vy in chosen:
        x,y,ww,hh = int(x),int(y),int(ww),int(hh)
        x0 = max(0, min(W-1, x)); y0 = max(0, min(H-1, y))
        x1 = max(0, min(W, x+ww)); y1 = max(0, min(H, y+hh))
        if x1<=x0 or y1<=y0: continue
        # use vivid & diff within the box for the mask
        mask_total[y0:y1, x0:x1] = cv2.bitwise_or(mask_total[y0:y1, x0:x1], (gate[y0:y1, x0:x1] & (cv2.inRange(cv2.cvtColor(imgB_al[y0:y1, x0:x1], cv2.COLOR_BGR2HSV), (0, vivid_sv, vivid_sv), (179,255,255)))))

        tip_at_max = ang_max < ang_min
        if abs(vx) >= abs(vy):
            direction = "right" if (tip_at_max and vx > 0) or ((not tip_at_max) and vx < 0) else "left"
        else:
            direction = "down" if (tip_at_max and vy > 0) or ((not tip_at_max) and vy < 0) else "up"
        directions.append(direction)

        cv2.rectangle(overlay, (x0,y0), (x1,y1), (0,255,0), 2)
        (tw,th), _ = cv2.getTextSize(direction, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cx, cy = x0+(x1-x0)//2, y0+(y1-y0)//2
        tx = max(x0+2, min(x1-tw-2, cx-tw//2))
        ty = max(y0+th+2, min(y1-2, cy+th//2))
        cv2.putText(overlay, direction, (tx,ty), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2, cv2.LINE_AA)

    mask_path = os.path.join(outdir, f"{prefix}_mask.png"); cv2.imwrite(mask_path, mask_total)
    overlay_path = os.path.join(outdir, f"{prefix}_overlay.png")
    rgba = cv2.cvtColor(imgB_al, cv2.COLOR_BGR2BGRA); rgba[:,:,3] = mask_total; cv2.imwrite(overlay_path, rgba)
    annot_path = os.path.join(outdir, f"{prefix}_annotated.png"); cv2.imwrite(annot_path, overlay)

    return directions, {"mask": mask_path, "overlay": overlay_path, "annotated": annot_path}

# --------------------------- CLI ---------------------------

def main(base_im, arrow_im, output_path="out", prefix="sample", order="x"):
    ap = argparse.ArgumentParser(description="Detect arrow directions from a pair of images (baseline + with arrows).")
    ap.add_argument("--base", help="Path to the baseline image (without arrows).")
    ap.add_argument("--with_arrows", help="Path to the image with arrows.")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--prefix", default="run")
    ap.add_argument("--band-height", type=int, default=80)
    ap.add_argument("--size-min", type=int, default=44)
    ap.add_argument("--size-max", type=int, default=64)
    ap.add_argument("--size-step", type=int, default=4)
    ap.add_argument("--stride", type=int, default=6)
    ap.add_argument("--vivid-sv", type=int, default=70)
    ap.add_argument("--hue-tol", type=float, default=40.0)
    ap.add_argument("--inlier-min", type=float, default=0.35)
    ap.add_argument("--slope-min", type=float, default=3.0)
    ap.add_argument("--nms-iou", type=float, default=0.3)
    ap.add_argument("--min-dx", type=int, default=20)
    ap.add_argument("--max-dy-adj", type=int, default=22)
    ap.add_argument("--target-size", type=float, default=50.0)
    args = ap.parse_args()

    dirs, paths = detect_with_size_row(
        base_im, arrow_im, args.outdir, prefix=args.prefix,
        band_height=args.band_height, size_min=args.size_min,
        size_max=args.size_max, size_step=args.size_step,
        stride=args.stride, vivid_sv=args.vivid_sv, hue_tol=args.hue_tol,
        inlier_min=args.inlier_min, slope_min=args.slope_min,
        nms_iou=args.nms_iou,
        min_dx=args.min_dx, max_dy_adj=args.max_dy_adj,
        target_size=args.target_size
    )
    print(",".join(dirs))

if __name__ == "__main__":
    main("../training/08082300_3.png", "../training/08082300_4.png")
