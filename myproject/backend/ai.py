from __future__ import annotations

import os
from typing import List, Tuple

import cv2
import numpy as np


def segment_polygon(image_path: str, seed_point: Tuple[int, int], tolerance: int = 15) -> List[List[int]]:
	"""
	Segment a region using OpenCV flood fill from a seed point, then polygonize the
	largest contour via Ramer-Douglas-Peucker approximation.

	Returns a list of [x, y] points in image coordinates. Empty list if failed.
	"""
	if not os.path.exists(image_path):
		return []

	image_bgr = cv2.imread(image_path, cv2.IMREAD_COLOR)
	if image_bgr is None:
		return []

	h, w = image_bgr.shape[:2]
	seed_x, seed_y = int(seed_point[0]), int(seed_point[1])
	if seed_x < 0 or seed_x >= w or seed_y < 0 or seed_y >= h:
		return []

	# Use grayscale for robust flood fill differences
	gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
	flood_img = gray.copy()

	# Mask must be 2 pixels larger than the image
	mask = np.zeros((h + 2, w + 2), dtype=np.uint8)

	lo_diff = int(max(0, tolerance))
	up_diff = int(max(0, tolerance))

	# Perform flood fill. We use a dummy new value that won't affect the mask extraction.
	flood_flags = 4 | (255 << 8) | cv2.FLOODFILL_FIXED_RANGE
	retval, flood_img, mask, rect = cv2.floodFill(
		flood_img,
		mask,
		(seed_x, seed_y),
		newVal=0,
		loDiff=(lo_diff,),
		upDiff=(up_diff,),
		flags=flood_flags,
	)

	# Remove the 1-pixel border added for the mask
	region_mask = (mask[1:-1, 1:-1] > 0).astype(np.uint8) * 255

	# Clean small noise
	kernel = np.ones((3, 3), np.uint8)
	region_mask = cv2.morphologyEx(region_mask, cv2.MORPH_OPEN, kernel, iterations=1)
	region_mask = cv2.morphologyEx(region_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

	contours, _ = cv2.findContours(region_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	if not contours:
		return []

	# Choose the largest contour by area
	areas = [cv2.contourArea(c) for c in contours]
	max_idx = int(np.argmax(areas))
	contour = contours[max_idx]

	perimeter = cv2.arcLength(contour, True)
	# Epsilon is 1% of perimeter; ensure minimum to avoid empty approx
	epsilon = max(1.0, 0.01 * perimeter)
	approx = cv2.approxPolyDP(contour, epsilon, True)

	points: List[List[int]] = []
	for p in approx.reshape(-1, 2):
		xi = int(p[0])
		yi = int(p[1])
		points.append([xi, yi])

	# Ensure polygon is at least a triangle
	if len(points) < 3:
		# fallback to the contour itself (downsample if too many points)
		contour_points = contour.reshape(-1, 2)
		if contour_points.shape[0] >= 3:
			step = max(1, contour_points.shape[0] // 100)
			points = [[int(x), int(y)] for x, y in contour_points[::step]]
		else:
			return []

	return points