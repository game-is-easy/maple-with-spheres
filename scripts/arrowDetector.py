import matplotlib
import matplotlib.pyplot as plt
import cv2
import numpy as np
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt
from pathlib import Path


class ArrowDirectionClassifier:
    """Classifies arrow direction and provides confidence scores"""

    def __init__(self):
        self.directions = ['up', 'down', 'left', 'right']

    def analyze_hue_gradient_direction(self, arrow_region: np.ndarray) -> Dict:
        """Analyze hue gradient direction to determine arrow direction"""
        # Convert to HSV
        hsv = cv2.cvtColor(arrow_region, cv2.COLOR_BGR2HSV)
        hue = hsv[:, :, 0].astype(np.float32)

        # Calculate gradients
        grad_x = cv2.Sobel(hue, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(hue, cv2.CV_32F, 0, 1, ksize=3)

        # Calculate gradient magnitude and direction
        magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
        angle = np.arctan2(grad_y, grad_x) * 180 / np.pi

        # Only consider pixels with significant gradients
        significant_mask = magnitude > np.percentile(magnitude,
                                                     70)  # Top 30% of gradients

        if np.sum(significant_mask) < 10:  # Not enough gradient information
            return {'direction': None, 'confidence': 0.0,
                    'method': 'hue_gradient'}

        significant_angles = angle[significant_mask]

        # Bin angles into 4 directions (with some tolerance)
        direction_votes = {
            'right': np.sum(
                (significant_angles >= -30) & (significant_angles <= 30)),
            'down': np.sum(
                (significant_angles >= 60) & (significant_angles <= 120)),
            'left': np.sum(
                (significant_angles >= 150) | (significant_angles <= -150)),
            'up': np.sum(
                (significant_angles >= -120) & (significant_angles <= -60))
        }

        total_votes = sum(direction_votes.values())
        if total_votes == 0:
            return {'direction': None, 'confidence': 0.0,
                    'method': 'hue_gradient'}

        # Find dominant direction
        best_direction = max(direction_votes.keys(),
                             key=lambda k: direction_votes[k])
        confidence = direction_votes[best_direction] / total_votes

        return {
            'direction': best_direction,
            'confidence': confidence,
            'method': 'hue_gradient',
            'votes': direction_votes
        }

    def analyze_shape_features(self, arrow_region: np.ndarray) -> Dict:
        """Analyze shape features to determine if this looks like an arrow"""
        gray = cv2.cvtColor(arrow_region, cv2.COLOR_BGR2GRAY)

        # Edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return {'is_arrow_like': False, 'shape_confidence': 0.0}

        # Analyze the largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Basic shape metrics
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)

        if area < 50 or perimeter < 20:
            return {'is_arrow_like': False, 'shape_confidence': 0.0}

        # Convex hull and solidity
        hull = cv2.convexHull(largest_contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0

        # Aspect ratio
        x, y, w, h = cv2.boundingRect(largest_contour)
        aspect_ratio = w / h if h > 0 else 0

        # Arrow-like features scoring
        shape_score = 0.0

        # Solidity: arrows should be reasonably solid (0.4-0.9)
        if 0.4 <= solidity <= 0.9:
            shape_score += 0.3

        # Aspect ratio: arrows shouldn't be too extreme
        if 0.3 <= aspect_ratio <= 3.0:
            shape_score += 0.3

        # Size: reasonable size for an arrow
        if 300 <= area <= 3000:
            shape_score += 0.2

        # Compactness: perimeter^2 / area should be reasonable
        compactness = (perimeter ** 2) / area if area > 0 else 1000
        if 10 <= compactness <= 100:
            shape_score += 0.2

        return {
            'is_arrow_like': shape_score > 0.5,
            'shape_confidence': shape_score,
            'solidity': solidity,
            'aspect_ratio': aspect_ratio,
            'area': area,
            'compactness': compactness
        }

    def classify_arrow_region(self, arrow_region: np.ndarray) -> Dict:
        """Full classification of an arrow region"""
        if arrow_region.size == 0 or arrow_region.shape[0] < 10 or \
                arrow_region.shape[1] < 10:
            return {
                'direction': None,
                'confidence': 0.0,
                'is_arrow': False,
                'overall_confidence': 0.0
            }

        # Analyze hue gradients for direction
        gradient_result = self.analyze_hue_gradient_direction(arrow_region)

        # Analyze shape features
        shape_result = self.analyze_shape_features(arrow_region)

        # Combine results
        direction_confidence = gradient_result.get('confidence', 0.0)
        shape_confidence = shape_result.get('shape_confidence', 0.0)

        # Overall confidence is weighted combination
        overall_confidence = (
                    direction_confidence * 0.7 + shape_confidence * 0.3)

        # Determine if this is likely an arrow
        is_arrow = (overall_confidence > 0.3 and
                    shape_result.get('is_arrow_like', False) and
                    gradient_result.get('direction') is not None)

        return {
            'direction': gradient_result.get('direction'),
            'confidence': direction_confidence,
            'is_arrow': is_arrow,
            'overall_confidence': overall_confidence,
            'shape_analysis': shape_result,
            'gradient_analysis': gradient_result
        }


class ArrowDetector:
    def __init__(self):
        self.arrow_size_range = (30, 70)  # Expected arrow size range
        self.expected_arrow_count = 4
        self.classifier = ArrowDirectionClassifier()

    def classify_all_candidates(self, image: np.ndarray,
                                candidates: List[Tuple]) -> List[Dict]:
        """Classify all arrow candidates and return with confidence scores"""
        classified_arrows = []

        for i, candidate in enumerate(candidates):
            x, y, w, h = candidate[:4]
            method = candidate[4] if len(candidate) > 4 else 'unknown'

            # Extract arrow region
            arrow_region = image[y:y + h, x:x + w]

            # Classify this region
            classification = self.classifier.classify_arrow_region(
                arrow_region)

            # Add metadata
            classification.update({
                'id': i,
                'bbox': (x, y, w, h),
                'center': (x + w // 2, y + h // 2),
                'detection_method': method,
                'region': arrow_region
            })

            classified_arrows.append(classification)

        return classified_arrows

    def filter_by_confidence(self, classified_arrows: List[Dict],
                             min_confidence: float = 0.3) -> List[Dict]:
        """Filter arrows by confidence threshold and spatial constraints"""

        # Filter by confidence
        confident_arrows = [arrow for arrow in classified_arrows
                            if
                            arrow['overall_confidence'] >= min_confidence and
                            arrow['is_arrow']]

        print(
            f"After confidence filtering ({min_confidence}): {len(confident_arrows)} arrows")

        if not confident_arrows:
            print("No arrows passed confidence filter, lowering threshold...")
            # Try lower threshold
            confident_arrows = [arrow for arrow in classified_arrows
                                if arrow['overall_confidence'] >= 0.2]

        # Sort by overall confidence (descending)
        confident_arrows.sort(key=lambda x: x['overall_confidence'],
                              reverse=True)

        # Apply spatial filtering - prefer arrows that are horizontally distributed
        if len(confident_arrows) > 4:
            # Group by y-coordinate to find horizontally aligned arrows
            y_positions = [arrow['center'][1] for arrow in confident_arrows]

            if len(y_positions) > 1:
                median_y = np.median(y_positions)
                y_tolerance = 40

                # Prefer arrows near the median y position
                spatially_filtered = []
                for arrow in confident_arrows:
                    if abs(arrow['center'][1] - median_y) <= y_tolerance:
                        spatially_filtered.append(arrow)

                if len(spatially_filtered) >= 2:  # Need at least 2 arrows
                    confident_arrows = spatially_filtered

        # Take top 4 by confidence, sorted by x-position
        if len(confident_arrows) > 4:
            confident_arrows = confident_arrows[:4]

        # Sort by x-position for final output
        confident_arrows.sort(key=lambda x: x['center'][0])

        return confident_arrows

    def preprocess_image(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """Apply various preprocessing techniques to enhance arrow detection"""
        # Convert to different color spaces
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(image, (3, 3), 0)

        return {
            'original': image,
            'hsv': hsv,
            'lab': lab,
            'blurred': blurred
        }

    def detect_background_change(self, before_images: List[np.ndarray],
                                 after_images: List[np.ndarray]) -> Tuple[
        np.ndarray, np.ndarray]:
        """Detect regions that changed between before/after sequences"""
        # Average the before and after images
        before_avg = np.mean(before_images, axis=0).astype(np.uint8)
        after_avg = np.mean(after_images, axis=0).astype(np.uint8)

        # Calculate difference
        diff = cv2.absdiff(before_avg, after_avg)

        # Convert to grayscale and threshold
        if len(diff.shape) == 3:
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        else:
            diff_gray = diff

        # Apply threshold to find significant changes
        _, change_mask = cv2.threshold(diff_gray, 20, 255, cv2.THRESH_BINARY)

        # Morphological operations to clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        change_mask = cv2.morphologyEx(change_mask, cv2.MORPH_CLOSE, kernel)
        change_mask = cv2.morphologyEx(change_mask, cv2.MORPH_OPEN, kernel)

        return change_mask, after_avg

    def detect_hue_gradients(self, image: np.ndarray,
                             roi_mask: np.ndarray = None) -> np.ndarray:
        """Detect areas with strong hue gradients (arrow characteristic)"""
        processed = self.preprocess_image(image)
        hsv = processed['hsv']

        # Extract hue channel
        hue = hsv[:, :, 0].astype(np.float32)

        # Calculate gradients in both directions
        grad_x = cv2.Sobel(hue, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(hue, cv2.CV_32F, 0, 1, ksize=3)

        # Calculate gradient magnitude
        grad_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

        # Apply ROI mask if provided
        if roi_mask is not None:
            grad_magnitude = cv2.bitwise_and(grad_magnitude, grad_magnitude,
                                             mask=roi_mask)

        # Normalize and convert to uint8
        grad_magnitude = cv2.normalize(grad_magnitude, None, 0, 255,
                                       cv2.NORM_MINMAX)
        return grad_magnitude.astype(np.uint8), grad_x, grad_y

    def find_arrow_candidates(self, image: np.ndarray,
                              change_mask: np.ndarray) -> List[Tuple]:
        """Find potential arrow regions using multiple methods"""
        candidates = []

        # Method 1: Use hue gradient detection (PRIMARY METHOD)
        hue_gradients, _, _ = self.detect_hue_gradients(image)

        # Try a single, more targeted threshold
        _, hue_thresh = cv2.threshold(hue_gradients, 25, 255,
                                      cv2.THRESH_BINARY)

        # More aggressive morphological operations to separate individual arrows
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

        hue_thresh = cv2.morphologyEx(hue_thresh, cv2.MORPH_CLOSE,
                                      kernel_close)
        hue_thresh = cv2.morphologyEx(hue_thresh, cv2.MORPH_OPEN, kernel_open)

        # Find contours
        hue_contours, _ = cv2.findContours(hue_thresh, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)

        for contour in hue_contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)

            # Stricter size filtering to focus on arrows
            min_area = 400  # Minimum arrow area
            max_area = 4000  # Maximum arrow area
            min_dim = 20  # Minimum dimension
            max_dim = 80  # Maximum dimension

            if (min_area < area < max_area and
                    min_dim < w < max_dim and
                    min_dim < h < max_dim and
                    0.5 < w / h < 2.0):  # Reasonable aspect ratio for arrows

                candidates.append((x, y, w, h, 'hue_gradient', area))

        # SPATIAL FILTERING: Focus on horizontally arranged arrows
        if candidates:
            # Filter by y-coordinate - arrows should be at similar height
            y_centers = [y + h // 2 for x, y, w, h, method, area in candidates]

            if len(y_centers) > 1:
                median_y = np.median(y_centers)
                y_tolerance = 30  # pixels

                # Keep only candidates near the median y-position
                spatial_filtered = []
                for candidate in candidates:
                    x, y, w, h = candidate[:4]
                    y_center = y + h // 2
                    if abs(y_center - median_y) <= y_tolerance:
                        spatial_filtered.append(candidate)

                candidates = spatial_filtered

            # Additional filtering: ensure horizontal distribution
            if len(candidates) > 1:
                x_positions = [x + w // 2 for x, y, w, h, method, area in
                               candidates]
                x_span = max(x_positions) - min(x_positions)

                # Arrows should span a reasonable horizontal distance
                if x_span < image.shape[
                    1] * 0.3:  # Less than 30% of image width
                    # Try to find better distributed candidates
                    pass  # Keep current candidates for now

    def detect_pad_region(self, image: np.ndarray) -> Tuple[np.ndarray, Tuple]:
        """Detect the semi-transparent pad that contains the arrows"""
        # Convert to HSV for better color detection
        hsv = image.astype(np.float32)
        hsv = cv2.cvtColor((hsv * 255).astype(np.uint8), cv2.COLOR_BGR2HSV)

        # Look for the semi-transparent pad - it should have consistent saturation/brightness
        saturation = hsv[:, :, 1]

        # The pad often appears as a region with moderate saturation
        pad_mask = cv2.inRange(saturation, 30, 200)

        # Find the largest connected component (should be the pad)
        contours, _ = cv2.findContours(pad_mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Get the largest contour (likely the pad)
            largest_contour = max(contours, key=cv2.contourArea)

            # Get bounding rectangle of the pad
            pad_x, pad_y, pad_w, pad_h = cv2.boundingRect(largest_contour)

            # Create a mask for just the pad region
            pad_region_mask = np.zeros(image.shape[:2], dtype=np.uint8)
            cv2.fillPoly(pad_region_mask, [largest_contour], 255)

            return pad_region_mask, (pad_x, pad_y, pad_w, pad_h)

        return None, None

    def filter_and_rank_candidates(self, candidates: List[Tuple],
                                   image: np.ndarray) -> List[Tuple]:
        """Filter and rank arrow candidates"""
        if not candidates:
            return []

        # Remove duplicates (candidates that overlap significantly)
        filtered_candidates = []
        for candidate in candidates:
            x1, y1, w1, h1 = candidate[:4]
            is_duplicate = False

            for existing in filtered_candidates:
                x2, y2, w2, h2 = existing[:4]

                # Calculate overlap
                overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                overlap_area = overlap_x * overlap_y

                # If overlap is more than 50% of either candidate, consider it duplicate
                area1 = w1 * h1
                area2 = w2 * h2
                if overlap_area > 0.5 * min(area1, area2):
                    # Keep the one from hue gradient detection if there's a choice
                    if 'hue_gradient' in candidate[4] and 'hue_gradient' not in \
                            existing[4]:
                        # Replace existing with current (hue gradient is better)
                        filtered_candidates.remove(existing)
                        break
                    else:
                        is_duplicate = True
                        break

            if not is_duplicate:
                filtered_candidates.append(candidate)

        # Prefer hue gradient detections, then sort by x-coordinate (left to right)
        filtered_candidates.sort(
            key=lambda x: (0 if 'hue_gradient' in x[4] else 1, x[0]))

        # Take top candidates if we have too many
        if len(filtered_candidates) > self.expected_arrow_count:
            filtered_candidates = filtered_candidates[
                                  :self.expected_arrow_count]

        return filtered_candidates

    def extract_arrow_regions(self, image: np.ndarray,
                              candidates: List[Tuple]) -> List[Dict]:
        """Extract arrow regions from the image"""
        arrows = []

        for i, candidate in enumerate(candidates):
            x, y, w, h = candidate[:4]
            method = candidate[4] if len(candidate) > 4 else 'unknown'

            # Add some padding around the detected region
            padding = 5
            x_start = max(0, x - padding)
            y_start = max(0, y - padding)
            x_end = min(image.shape[1], x + w + padding)
            y_end = min(image.shape[0], y + h + padding)

            # Extract the arrow region
            arrow_region = image[y_start:y_end, x_start:x_end]

            arrows.append({
                'id': i,
                'region': arrow_region,
                'bbox': (x_start, y_start, x_end - x_start, y_end - y_start),
                'center': (x + w // 2, y + h // 2),
                'detection_method': method,
                'original_bbox': (x, y, w, h)
            })

        return arrows

    def process_image_sequence(self, image_paths: List[str]) -> Dict:
        """Process a sequence of images to detect and classify arrows"""
        # Load all images
        images = []
        for path in image_paths:
            img = cv2.imread(path)
            if img is not None:
                images.append(img)

        if len(images) < 2:
            raise ValueError("Need at least 2 images to detect changes")

        # Split into before and after (assuming arrows appear in later images)
        mid_point = len(images) // 2
        before_images = images[:mid_point]
        after_images = images[mid_point:]

        # Detect background changes
        change_mask, representative_image = self.detect_background_change(
            before_images, after_images
        )

        # Find arrow candidates (more permissive now)
        candidates = self.find_arrow_candidates(representative_image,
                                                change_mask)

        # Classify all candidates with confidence scoring
        classified_arrows = self.classify_all_candidates(representative_image,
                                                         candidates)

        # Filter by confidence and spatial constraints
        final_arrows = self.filter_by_confidence(classified_arrows,
                                                 min_confidence=0.3)

        # Print classification results for debugging
        print("\nClassification Results:")
        for i, arrow in enumerate(classified_arrows):
            print(f"Candidate {i}: Direction={arrow.get('direction')}, "
                  f"Overall Confidence={arrow.get('overall_confidence', 0):.2f}, "
                  f"Is Arrow={arrow.get('is_arrow')}")

        print(f"\nFinal arrows after filtering: {len(final_arrows)}")
        for i, arrow in enumerate(final_arrows):
            print(f"Arrow {i}: Direction={arrow.get('direction')}, "
                  f"Confidence={arrow.get('overall_confidence', 0):.2f}")

        return {
            'arrows': final_arrows,
            'all_candidates': classified_arrows,
            'change_mask': change_mask,
            'representative_image': representative_image,
            'raw_candidates': candidates
        }

    def visualize_detection(self, result: Dict):
        """Visualize the detection and classification results"""
        fig, axes = plt.subplots(3, 4, figsize=(20, 15))

        # Row 1: Detection overview
        # Original image with all candidates
        img_with_all = result['representative_image'].copy()
        for i, candidate in enumerate(result['all_candidates']):
            x, y, w, h = candidate['bbox']
            confidence = candidate.get('overall_confidence', 0)

            # Color code by confidence: red=low, yellow=medium, green=high
            if confidence < 0.3:
                color = (0, 0, 255)  # Red
            elif confidence < 0.6:
                color = (0, 255, 255)  # Yellow
            else:
                color = (0, 255, 0)  # Green

            cv2.rectangle(img_with_all, (x, y), (x + w, y + h), color, 2)
            cv2.putText(img_with_all, f"{confidence:.2f}",
                        (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        axes[0, 0].imshow(cv2.cvtColor(img_with_all, cv2.COLOR_BGR2RGB))
        axes[0, 0].set_title(
            'All Candidates (Red=Low, Yellow=Med, Green=High Confidence)')
        axes[0, 0].axis('off')

        # Final arrows only
        img_with_final = result['representative_image'].copy()
        for i, arrow in enumerate(result['arrows']):
            x, y, w, h = arrow['bbox']
            direction = arrow.get('direction', 'unknown')
            confidence = arrow.get('overall_confidence', 0)

            cv2.rectangle(img_with_final, (x, y), (x + w, y + h), (0, 255, 0),
                          2)
            cv2.putText(img_with_final, f"{direction} {confidence:.2f}",
                        (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),
                        1)

        axes[0, 1].imshow(cv2.cvtColor(img_with_final, cv2.COLOR_BGR2RGB))
        axes[0, 1].set_title('Final Classified Arrows')
        axes[0, 1].axis('off')

        # Change mask and hue gradients
        axes[0, 2].imshow(result['change_mask'], cmap='gray')
        axes[0, 2].set_title('Change Detection Mask')
        axes[0, 2].axis('off')

        hue_grad, _, _ = self.detect_hue_gradients(
            result['representative_image'])
        axes[0, 3].imshow(hue_grad, cmap='hot')
        axes[0, 3].set_title('Hue Gradients')
        axes[0, 3].axis('off')

        # Row 2 & 3: Individual arrow regions (up to 8)
        for i in range(8):
            row = 1 + i // 4
            col = i % 4

            if i < len(result['all_candidates']):
                candidate = result['all_candidates'][i]
                arrow_region = candidate.get('region')
                direction = candidate.get('direction', 'unknown')
                confidence = candidate.get('overall_confidence', 0)
                is_arrow = candidate.get('is_arrow', False)

                if arrow_region is not None and arrow_region.size > 0:
                    axes[row, col].imshow(
                        cv2.cvtColor(arrow_region, cv2.COLOR_BGR2RGB))
                    status = "✓" if is_arrow else "✗"
                    axes[row, col].set_title(
                        f'{status} {direction} ({confidence:.2f})')
                else:
                    axes[row, col].axis('off')
            else:
                axes[row, col].axis('off')
            axes[row, col].axis('off')

        plt.tight_layout()
        plt.show()

        # Print detailed analysis
        print(f"\n=== DETECTION SUMMARY ===")
        print(f"Total candidates found: {len(result['all_candidates'])}")
        print(f"Candidates passing confidence filter: {len(result['arrows'])}")
        print(
            f"Detected directions: {[arrow.get('direction') for arrow in result['arrows']]}")

        return result


# Example usage
def test_arrow_detection():
    detector = ArrowDetector()

    # Example with your image paths (adjust as needed)
    # image_paths = ['image1.png', 'image2.png', ...]  # Your sequence

    # For testing, you would call:
    # result = detector.process_image_sequence(image_paths)
    # detector.visualize_detection(result)

    print("Arrow detector framework ready!")
    print("Key methods:")
    print("- process_image_sequence(): Main detection pipeline")
    print("- visualize_detection(): Show detection results")
    print("- extract_arrow_regions(): Get individual arrow images")

    return detector


if __name__ == "__main__":
    detector = test_arrow_detection()


# Example usage
def test_arrow_detection():
    detector = ArrowDetector()

    # Example with your image paths (adjust as needed)
    arrow_image_name = '08091434_4'
    # arrow_image_name = '08082349_4'
    base_image_name = arrow_image_name[:-1] + str(int(arrow_image_name[-1]) + 1)
    image_paths = [f'../training/{base_image_name}.png', f'../training/{arrow_image_name}.png']  # Your sequence

    # For testing, you would call:
    result = detector.process_image_sequence(image_paths)
    detector.visualize_detection(result)

    print("Arrow detector framework ready!")
    print("Key methods:")
    print("- process_image_sequence(): Main detection pipeline")
    print("- visualize_detection(): Show detection results")
    print("- extract_arrow_regions(): Get individual arrow images")

    return detector


if __name__ == "__main__":
    detector = test_arrow_detection()