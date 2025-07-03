import tempfile
import json
from pathlib import Path
import numpy as np

from src.utils import (
    create_coco_annotations_structure,
    save_coco_annotations,
    mask_to_yolo_bbox,
    save_yolo_annotations,
    create_yolo_data_yaml,
)


# Test creating COCO annotations
def test_create_coco_annotations(db, test_video, test_object):
    # Create a temporary directory to simulate frames
    with tempfile.TemporaryDirectory() as temp_dir:
        frames_dir = Path(temp_dir)

        # Create test frame files
        frame_path1 = frames_dir / "00001.jpg"
        frame_path2 = frames_dir / "00002.jpg"

        # Create dummy image content
        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        import cv2
        cv2.imwrite(str(frame_path1), dummy_img)
        cv2.imwrite(str(frame_path2), dummy_img)

        # List of frames
        frames = [frame_path1, frame_path2]

        # Create COCO annotations structure
        coco_data = create_coco_annotations_structure([test_object], frames)

        # Verify structure
        assert 'images' in coco_data
        assert 'categories' in coco_data
        assert 'annotations' in coco_data
        assert len(coco_data['images']) == 2
        assert len(coco_data['categories']) == 1
        assert coco_data['categories'][0]['name'] == test_object.name

        # Create a temporary directory to save annotations
        coco_dir = frames_dir / "coco"
        coco_dir.mkdir()

        # Save COCO annotations
        video_name = Path(test_video.file_path).stem
        save_coco_annotations(coco_data, coco_dir, video_name)

        # Check if file was created
        json_file = coco_dir / f"{video_name}_coco.json"
        assert json_file.exists()

        # Load the JSON file and check content
        with open(json_file, 'r') as f:
            saved_data = json.load(f)

        assert 'images' in saved_data
        assert 'categories' in saved_data
        assert len(saved_data['images']) == 2
        assert len(saved_data['categories']) == 1


# Test creating YOLO annotations
def test_create_yolo_annotations(db, test_video, test_object):
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Create a frame file path
        frame_path = temp_dir_path / "00001.jpg"

        # Create dummy image
        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        import cv2
        cv2.imwrite(str(frame_path), dummy_img)

        # Create a mask
        mask = np.zeros((480, 640), dtype=bool)
        mask[100:200, 100:200] = True  # Square mask

        # Get YOLO bbox
        yolo_bbox = mask_to_yolo_bbox(mask, 640, 480)

        # Create output directory
        yolo_dir = temp_dir_path / "yolo"
        yolo_dir.mkdir()

        # Save YOLO annotations
        objects_data = [(0, *yolo_bbox)]  # class_id 0
        save_yolo_annotations(frame_path, objects_data, yolo_dir)

        # Check if annotation file was created
        ann_file = yolo_dir / "00001.txt"
        assert ann_file.exists()

        # Read the annotation file and check content
        with open(ann_file, 'r') as f:
            content = f.read().strip()

        # Split the content into parts and check format
        parts = content.split()
        assert len(parts) == 5  # class_id, x_center, y_center, width, height
        assert parts[0] == "0"  # class_id

        # Create data.yml file
        create_yolo_data_yaml([test_object], yolo_dir)

        # Check if data.yml was created
        data_yml = yolo_dir / "data.yml"
        assert data_yml.exists()

        # Read data.yml and check content
        import yaml
        with open(data_yml, 'r') as f:
            data = yaml.safe_load(f)

        assert 'classes' in data
        assert 'names' in data
        assert data['classes'] == 1
        # Changed from '0' to 0 - keys are integers, not strings
        assert 0 in data['names']
        assert data['names'][0] == test_object.name
