import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import numpy as np

from src.utils import (
    extract_frames_at_fps,
    get_frames_list,
)


# Test uploading a video (via FastAPI endpoint)
@pytest.mark.asyncio
@patch('src.main.extract_video_metadata')
@patch('src.main.extract_frames_at_fps')
async def test_upload_video(mock_extract_frames, mock_extract_metadata, db, test_project):
    from fastapi import UploadFile
    from src.main import upload_video

    # Create a mock file instead of a real temporary file
    mock_file = MagicMock()
    mock_file.read = MagicMock(return_value=b'dummy video content')

    # Create a mock UploadFile instead of using a real file
    upload_file = MagicMock(spec=UploadFile)
    upload_file.filename = "test_video.mp4"
    upload_file.content_type = "video/mp4"
    upload_file.file = mock_file

    # Mock video metadata
    mock_extract_metadata.return_value = {
        "width": 640,
        "height": 480,
        "fps": 30.0,
        "duration": 10.0,
        "file_size": 1000
    }

    # Mock frame extraction
    mock_extract_frames.return_value = Path("mocked_frames_dir")

    # Mock directory creation and file operations
    with patch('pathlib.Path.mkdir') as mock_mkdir, \
            patch('src.main.public_videos_dir_with_video_name') as mock_videos_dir, \
            patch('src.main.public_frames_base_dir_with_video_name') as mock_frames_dir, \
            patch('src.main.public_frames_inference_dir_with_video_name') as mock_inference_dir, \
            patch('src.main.public_video_thumbnail_dir_with_video_name') as mock_thumbnail_dir, \
            patch('builtins.open', mock_open()), \
            patch('subprocess.run') as mock_subprocess:

        # Mock directory paths
        mock_dir = MagicMock()
        mock_dir.__truediv__.return_value = Path("mocked_path")
        mock_videos_dir.return_value = mock_dir
        mock_frames_dir.return_value = mock_dir
        mock_inference_dir.return_value = mock_dir
        mock_thumbnail_dir.return_value = mock_dir

        # Call the upload_video endpoint
        response = await upload_video(
            file=upload_file,
            project_id=test_project.id,
            resolution=None,
            target_fps=None,
            db=db
        )

        # Check response
        assert response is not None
        assert "id" in response
        assert "file_name" in response
        assert response["project_id"] == test_project.id

        # Verify the video was added to the database
        from src.models import Video
        video = db.query(Video).filter_by(
            project_id=test_project.id).first()
        assert video is not None
        assert video.file_name.endswith(".mp4")


# Test extracting frames from a video
@patch('subprocess.run')
@patch('pathlib.Path.glob')
@patch('pathlib.Path.mkdir')
@patch('src.utils.get_frames_list')
def test_extract_frames_at_fps(mock_get_frames, mock_mkdir, mock_glob, mock_subprocess, db, test_video):
    # Mock the frames list
    mock_frame_paths = [Path("mocked_frames_dir/00001.jpg")]
    mock_get_frames.return_value = mock_frame_paths

    # Mock glob to return some frames
    mock_glob.return_value = mock_frame_paths

    # Mock subprocess.run
    mock_subprocess.return_value = MagicMock(returncode=0)

    # Mock directory existence checks and file operations
    with patch('pathlib.Path.exists') as mock_exists, \
            patch('os.path.exists') as mock_os_exists, \
            patch('src.utils.public_frames_base_dir_with_video_name') as mock_frames_dir, \
            patch('src.utils.public_video_thumbnail_dir_with_video_name') as mock_thumbnail_dir, \
            patch('shutil.copy') as mock_copy, \
            patch('pathlib.Path.unlink') as mock_unlink, \
            patch('pathlib.Path.iterdir') as mock_iterdir:

        mock_exists.return_value = True
        mock_os_exists.return_value = True
        mock_unlink.return_value = None  # Don't actually delete files
        mock_iterdir.return_value = []  # Return empty list for directory iteration

        # Mock directory paths
        mock_dir = MagicMock()
        mock_dir.glob.return_value = mock_frame_paths
        mock_frames_dir.return_value = mock_dir
        mock_thumbnail_dir.return_value = mock_dir

        # Call extract_frames_at_fps
        result = extract_frames_at_fps(test_video.file_path, db)

        # Verify result
        assert result is not None

        # Check if frame was added to database
        from src.models import Frame
        frame = db.query(Frame).filter_by(video_id=test_video.id).first()
        assert frame is not None


# Test getting the list of frames
def test_get_frames_list():
    # Create a temporary directory with some test frames
    with tempfile.TemporaryDirectory() as temp_dir:
        frames_dir = Path(temp_dir)

        # Create some test frame files
        for i in range(1, 6):
            frame_path = frames_dir / f"{i:05d}.jpg"
            # Create an empty file
            with open(frame_path, 'w') as f:
                pass

        # Get the frames list
        frames = get_frames_list(frames_dir)

        # Verify the result
        assert len(frames) == 5
        assert all(frame.suffix == '.jpg' for frame in frames)
        assert frames[0].name == "00001.jpg"
        assert frames[-1].name == "00005.jpg"
        assert all(frame.suffix == '.jpg' for frame in frames)
        assert frames[0].name == "00001.jpg"
        assert frames[-1].name == "00005.jpg"
