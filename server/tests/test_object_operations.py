import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils import (
    draw_objects_masks_on_frame,
    serialize_mask,
    deserialize_mask,
    create_point,
)
from src.inference import InferenceAPI


# Test drawing objects on a frame
def test_draw_objects_masks_on_frame(db, test_video, test_object, test_frame):
    # Create a mask for the object
    from src.models import Mask

    # Create a simple binary mask
    mask = np.zeros((480, 640), dtype=bool)
    mask[100:300, 100:300] = True  # Square mask

    # Serialize the mask
    mask_blob = serialize_mask(mask)

    # Create a mask record in the database
    db_mask = Mask(
        object_id=test_object.id,
        mask=mask_blob
    )
    db.add(db_mask)
    db.commit()

    # Mock cv2.imread to return a test image
    with patch('cv2.imread') as mock_imread, \
            patch('cv2.imwrite') as mock_imwrite, \
            patch('src.utils.public_video_thumbnail_dir_with_video_name') as mock_thumbnail_dir, \
            patch('pathlib.Path.exists') as mock_path_exists:  # Add this patch

        # Create a dummy image
        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_imread.return_value = dummy_img

        # Mock the file existence check
        mock_path_exists.return_value = True

        # Mock the thumbnail directory
        mock_dir = MagicMock()
        mock_dir.__str__.return_value = "mocked_path"
        mock_dir.__truediv__.return_value = Path("mocked_path/inference.jpg")
        mock_thumbnail_dir.return_value = mock_dir

        # Call the function
        result = draw_objects_masks_on_frame(test_video.id, db)

        # Verify the result
        assert Path(result) == Path("mocked_path/inference.jpg")

        # Verify cv2.imread was called
        mock_imread.assert_called_once()

        # Verify cv2.imwrite was called
        mock_imwrite.assert_called_once()


# Test segmenting an object
@patch('src.inference.build_sam2_video_predictor')
def test_segment_object(mock_build_predictor, db, test_object, test_point, test_frame, test_video):
    # Mock the SAM2 predictor
    mock_predictor = MagicMock()
    mock_build_predictor.return_value = mock_predictor

    # Mock the add_new_points_or_box method to return dummy mask logits
    mock_mask_logits = MagicMock()

    # Create a properly structured mock for the comparison operation
    mock_tensor = MagicMock()
    mock_numpy_obj = MagicMock()
    mock_numpy_obj.squeeze.return_value = np.ones((480, 640), dtype=bool)
    mock_tensor.cpu.return_value.numpy.return_value = mock_numpy_obj

    # Create a custom implementation for __getitem__ that handles comparison
    def mock_getitem(self, idx):
        result_mock = MagicMock()
        # Make the '> 0.0' operation return a mock with proper cpu() method
        result_mock.__gt__ = lambda *args: mock_tensor
        return result_mock

    mock_mask_logits.__getitem__ = mock_getitem

    mock_predictor.add_new_points_or_box.return_value = (
        None, None, mock_mask_logits)

    # Initialize InferenceAPI
    with patch('src.inference.Path') as mock_path, \
            patch('src.inference.public_frames_base_dir_with_video_name') as mock_frames_dir, \
            patch('os.path.dirname') as mock_dirname, \
            patch('os.path.abspath') as mock_abspath:

        # Mock path and directory existence checks
        mock_path.return_value.parent = Path("mocked_parent")
        mock_path.return_value.exists.return_value = True
        mock_dirname.return_value = "mocked_dir"
        mock_abspath.return_value = "mocked_abs_path"

        # Mock frames directory
        mock_dir = MagicMock()
        mock_dir.__str__.return_value = "mocked_frames_dir"
        mock_frames_dir.return_value = mock_dir

        # Create InferenceAPI instance
        api = InferenceAPI(checkpoint="tiny")

        # Mock initialize_state
        api.initialize_state = MagicMock()
        api.inference_state = MagicMock()

        # Call segment_object
        result = api.segment_object(test_object.id, db)

        # Verify the result
        assert result is not None

        # Check if a mask was created in the database
        from src.models import Mask
        mask = db.query(Mask).filter_by(object_id=test_object.id).first()
        assert mask is not None

        # Deserialize and check the mask
        deserialized_mask = deserialize_mask(mask.mask)
        assert isinstance(deserialized_mask, np.ndarray)


# Test creating a point for an object
def test_create_point(db, test_object):
    # Define point coordinates
    x, y = 200, 150
    label = 1  # positive point

    # Create a point
    point = create_point(x, y, label, test_object.id, db)

    # Verify the point was created
    assert point is not None
    assert point.x == x
    assert point.y == y
    assert point.label == label
    assert point.object_id == test_object.id

    # Check if the point exists in the database
    from src.models import Point
    db_point = db.query(Point).filter_by(
        object_id=test_object.id,
        x=x,
        y=y
    ).first()

    assert db_point is not None
    assert db_point.id == point.id
