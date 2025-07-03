from src.models import Base
import sys
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))


# Create an in-memory SQLite database for testing
@pytest.fixture(scope="function")
def db():
    # Create an in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create a session
    db = TestingSessionLocal()

    # Override the get_db function to use our test database
    def _get_db_override():
        try:
            yield db
        finally:
            pass

    # Use the test database for all tests
    import src.db
    src.db.get_db = _get_db_override

    yield db

    # Clean up
    db.close()
    Base.metadata.drop_all(bind=engine)


# Create test project fixture
@pytest.fixture(scope="function")
def test_project(db):
    from src.models import Project
    project = Project(id=1, name="Test Project",
                      description="Test Description")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

# Create test video fixture


@pytest.fixture(scope="function")
def test_video(db, test_project):
    from src.models import Video
    video = Video(
        id=1,
        project_id=test_project.id,
        file_path="test_video_path.mp4",
        file_name="test_video.mp4",
        file_size=1000,
        width=640,
        height=480,
        fps=30.0,
        duration=10.0,
        type="base"
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video

# Create test object fixture


@pytest.fixture(scope="function")
def test_object(db, test_video):
    from src.models import Object
    obj = Object(
        id=1,
        video_id=test_video.id,
        name="Test Object",
        color="#FF0000"
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

# Create test frame fixture


@pytest.fixture(scope="function")
def test_frame(db, test_video):
    from src.models import Frame
    frame = Frame(
        id=1,
        video_id=test_video.id,
        file_path="test_frame_path.jpg"
    )
    db.add(frame)
    db.commit()
    db.refresh(frame)
    return frame

# Create test point fixture


@pytest.fixture(scope="function")
def test_point(db, test_object):
    from src.models import Point
    point = Point(
        id=1,
        object_id=test_object.id,
        x=100,
        y=100,
        label=1
    )
    db.add(point)
    db.commit()
    db.refresh(point)
    return point
