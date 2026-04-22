# -*- coding: utf-8 -*-
import cv2
import numpy as np

def undistort_img(dist,mtx,cv2_bgr_img):
    """FOnction qui corrige les distortion sur une image(rétablie à nouveau les lignes transformées en arcs)"""
    try :
        height,width = cv2_bgr_img.shape[:2]
        camMatrixNew,roi = cv2.getOptimalNewCameraMatrix(mtx,dist,(width,height),1,(width,height))
        imgUndist = cv2.undistort(cv2_bgr_img,mtx,dist,None,camMatrixNew)
        #x, y, w, h = roi si on veut une auto adaptation de la coupure après correction
        x, y, w, h = 411, 328, 1340, 630
        croppedUndist = imgUndist[y:y+h, x:x+w]
        return croppedUndist
    
    except Exception as e:
        print(f"Erreur undistort: {e}")
        return cv2_bgr_img


def homo_and_pixel_conversion(cv2_bgr_undistort_img, homo_matrix, thersh_cutting=100):
    try:
        if cv2_bgr_undistort_img is None or homo_matrix is None:
            return cv2_bgr_undistort_img
        
        dst = cv2.warpPerspective(
            cv2_bgr_undistort_img,
            homo_matrix,
            (
                int(cv2_bgr_undistort_img.shape[1] * 1.5),
                int(cv2_bgr_undistort_img.shape[0] * 1.5)
            )
        )

        gray = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            cnt = max(contours, key=cv2.contourArea)
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)

            dx = box[1, 0] - box[0, 0]
            dy = box[1, 1] - box[0, 1]

            angle = np.degrees(np.arctan2(dy, dx))

            M = cv2.getRotationMatrix2D((dx/2, dy/2), angle, 1)
            dst_rot = cv2.warpAffine(dst, M, (dst.shape[1], dst.shape[0]))

            gray2 = cv2.cvtColor(dst_rot, cv2.COLOR_BGR2GRAY)
            mask = gray2 > thersh_cutting
            coords = np.argwhere(mask)

            if len(coords) > 0:
                y_min, x_min = coords.min(axis=0)
                y_max, x_max = coords.max(axis=0)
                return dst_rot[y_min:y_max+1, x_min:x_max+1]

        return dst

    except Exception as e:
        print(f"Erreur homographie: {e}")
        return cv2_bgr_undistort_img