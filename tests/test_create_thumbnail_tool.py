import pytest
import sys
import os
from unittest.mock import patch, MagicMock
# Removed AsyncMock as the tool is synchronous
# Removed io as we are mocking open directly

# Import necessary types from PIL and MCP
from PIL import Image as PILImage_real # Use alias to avoid conflict if needed
from PIL import UnidentifiedImageError
from mcp.server.fastmcp import Image as MCPImageType # Import the specific return type

# Add the parent directory to path so we can import modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the tool function
from tools.tool_create_thumbnail import create_thumbnail

# --- Fixtures ---
# No context fixture needed as the tool doesn't use it
# No mock_image_bytes fixture needed as we mock PILImage.open directly

# --- Test Class ---

class TestCreateThumbnailTool:
    """Test cases for the create thumbnail tool."""

    def test_create_thumbnail_success(self):
        """Test successful thumbnail creation."""
        # Mock the Image object returned by PILImage.open
        mock_img_instance = MagicMock(spec=PILImage_real.Image)
        mock_img_instance.size = (200, 150) # Example original size
        # Mock the tobytes method which is called by the tool
        mock_img_instance.tobytes.return_value = b'dummy_thumbnail_bytes'

        # Patch PILImage.open used within the tool's module scope
        # Use the correct target based on 'from PIL import Image as PILImage'
        with patch('tools.tool_create_thumbnail.PILImage.open', return_value=mock_img_instance) as mock_pil_open, \
            patch.object(mock_img_instance, 'thumbnail') as mock_thumbnail:
            # No need to patch save as the tool doesn't save to file

            image_path = "images/source_image.png"

            # Call the synchronous tool function directly with the path
            result = create_thumbnail(image_path)

            # --- Assertions ---
            # Verify PILImage.open usage
            mock_pil_open.assert_called_once_with(image_path)

            # Verify thumbnail calculation (Tool hardcodes 100x100)
            mock_thumbnail.assert_called_once_with((100, 100))

            # Verify tobytes was called to get the data
            mock_img_instance.tobytes.assert_called_once()

            # Verify return value (MCP Image type)
            assert isinstance(result, MCPImageType)
            assert result.data == b'dummy_thumbnail_bytes'
            # Removed assertion for result.format as the attribute doesn't exist

    def test_error_image_open_file_not_found(self):
        """Test error handling when the image file is not found."""
        image_path = "images/nonexistent.png"

        # Patch PILImage.open to raise FileNotFoundError
        with patch('tools.tool_create_thumbnail.PILImage.open', side_effect=FileNotFoundError(f"No such file: {image_path}")) as mock_pil_open:
            # Use pytest.raises to check if the expected exception is raised
            with pytest.raises(FileNotFoundError) as excinfo:
                create_thumbnail(image_path)

            # Verify PILImage.open was called
            mock_pil_open.assert_called_once_with(image_path)
            # Optionally check the exception message
            assert image_path in str(excinfo.value)

    def test_error_image_open_unidentified_image(self):
        """Test error handling when the file is not a valid image."""
        image_path = "images/corrupt_or_not_image.txt"

        # Patch PILImage.open to raise UnidentifiedImageError
        with patch('tools.tool_create_thumbnail.PILImage.open', side_effect=UnidentifiedImageError("Cannot identify image file")) as mock_pil_open:
            # Use pytest.raises to check if the expected exception is raised
            with pytest.raises(UnidentifiedImageError) as excinfo:
                create_thumbnail(image_path)

            # Verify PILImage.open was called
            mock_pil_open.assert_called_once_with(image_path)
            # Optionally check the exception message
            assert "Cannot identify image file" in str(excinfo.value)

    def test_error_thumbnail_processing_exception(self):
        """Test error handling if PIL's thumbnail method raises an exception."""
        # Mock the Image object returned by PILImage.open
        mock_img_instance = MagicMock(spec=PILImage_real.Image)
        mock_img_instance.size = (200, 150)
        # Configure the thumbnail method to raise an error
        mock_img_instance.thumbnail.side_effect = Exception("Internal PIL thumbnail error")

        image_path = "images/problematic_image.png"

        # Patch PILImage.open and the thumbnail method
        with patch('tools.tool_create_thumbnail.PILImage.open', return_value=mock_img_instance) as mock_pil_open, \
            patch.object(mock_img_instance, 'thumbnail', side_effect=Exception("Internal PIL thumbnail error")) as mock_thumbnail:

            # Use pytest.raises to check if the expected exception is raised
            with pytest.raises(Exception) as excinfo:
                create_thumbnail(image_path)

            # Verify PILImage.open was called
            mock_pil_open.assert_called_once_with(image_path)
            # Verify thumbnail was called
            mock_thumbnail.assert_called_once_with((100, 100))
            # Check the exception message
            assert "Internal PIL thumbnail error" in str(excinfo.value)
            # Verify tobytes was NOT called if thumbnail failed
            mock_img_instance.tobytes.assert_not_called()