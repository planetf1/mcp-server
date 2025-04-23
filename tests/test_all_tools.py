import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Add the project root to the Python path
# This allows importing modules from the 'tools' directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the tools that will be used in the tests
from tools.tool_calculator import calculator
# from tools.tool_github import github_get_file # Assuming this might be used elsewhere or later
from tools.tool_wikipedia import wikipedia_search
from tools.tool_long_task import long_task
from tools.tool_calculate_bmi import calculate_bmi

# Mock the mcp instance and its decorator to avoid dependency issues
# In a real scenario, you might have a shared mock setup in conftest.py
class MockMCP:
    def tool(self):
        def decorator(func):
            return func
        return decorator

# Apply the mock globally if mcp is imported at module level in tools
# If mcp is only used inside functions, this might not be strictly necessary
# but it's safer for testing in isolation.
# Note: Adjust the patch target if 'mcp_instance' is imported differently in tools
# Example: If a tool does 'from mcp_instance import mcp', patch 'tools.tool_xyz.mcp'
# For now, assuming a central 'mcp_instance' module might be used (adjust if needed)
# try:
#     patcher = patch('mcp_instance.mcp', MockMCP()).start()
# except ModuleNotFoundError:
#     print("Note: 'mcp_instance' module not found for patching. Ensure tools don't depend on it directly at module level for these tests.")
#     pass # Allow tests to run if mcp_instance isn't structured this way


@pytest.fixture
def mock_context():
    """Provides a mock context object for tool functions."""
    # Add 'read_resource' to the spec list
    context = AsyncMock(spec=['info', 'debug', 'warning', 'error', 'report_progress', 'read_resource'])
    context.info = AsyncMock()
    context.debug = AsyncMock()
    context.warning = AsyncMock()
    context.error = AsyncMock()
    context.report_progress = AsyncMock()
    # Configure read_resource to be an AsyncMock returning dummy data
    context.read_resource = AsyncMock(return_value=(b'dummy file content', 'text/plain'))
    return context

class TestAllTools:
    """Tests involving sequences or combinations of multiple tools."""

    # Add the asyncio marker (only once)
    @pytest.mark.asyncio
    # Add async keyword
    async def test_calculator_basic(self):
        """Test the calculator tool directly."""
        # Assuming calculator takes a single string expression and is async
        # and returns a dictionary like {'expression': ..., 'result': ...}
        result_dict = await calculator("5 + 3")
        assert isinstance(result_dict, dict) # Optional: Check if it's a dict
        assert result_dict['result'] == 8    # Check the 'result' key

        result_dict = await calculator("10 / 2")
        assert isinstance(result_dict, dict)
        assert result_dict['result'] == 5

        result_dict = await calculator("6 * 7")
        assert isinstance(result_dict, dict)
        assert result_dict['result'] == 42

        result_dict = await calculator("10 - 4")
        assert isinstance(result_dict, dict)
        assert result_dict['result'] == 6

    # --- Corrected Indentation: This method belongs to the class TestAllTools ---
    @pytest.mark.asyncio
    async def test_multiple_tools_sequence(self, mock_context):
        """
        Test a sequence involving Wikipedia search, BMI calculation, and a long task.
        This test verifies the integration and mocking for these specific tools.
        """
        # --- Mocking Setup for httpx used by wikipedia_search ---

        # 1. Mock the response object for the Wikipedia *search* API call
        search_response_mock = AsyncMock()
        search_response_mock.status_code = 200
        search_response_mock.json = AsyncMock(return_value={
            "query": {
                "search": [
                    {
                        "title": "Body mass index", # The title we expect
                        "pageid": 123
                    }
                ]
            }
        })

        # 2. Mock the response object for the Wikipedia *extract* API call
        extract_response_mock = AsyncMock()
        extract_response_mock.status_code = 200
        extract_response_mock.json = AsyncMock(return_value={
            "query": {
                "pages": {
                    "123": {
                        "title": "Body mass index",
                        "fullurl": "https://en.wikipedia.org/wiki/Body_mass_index",
                        "extract": "BMI is calculated by dividing weight by height squared."
                    }
                }
            }
        })

        # 3. Mock the httpx client instance that will be returned by the context manager
        mock_client_instance = AsyncMock()
        # Set the side_effect: the first client.get() gets search_response, the second gets extract_response
        mock_client_instance.get.side_effect = [search_response_mock, extract_response_mock]

        # 4. Mock the async context manager returned when httpx.AsyncClient() is called
        mock_async_cm = AsyncMock()
        # Configure its __aenter__ to return our mock client instance
        mock_async_cm.__aenter__.return_value = mock_client_instance

        # --- Patch httpx.AsyncClient where it's used by wikipedia_search ---
        # Adjust the patch target if httpx is imported differently in tool_wikipedia.py
        patch_target = 'tools.tool_wikipedia.httpx.AsyncClient'
        try:
            # Verify the target exists before patching if needed (optional)
            from tools.tool_wikipedia import httpx as wiki_httpx
            assert hasattr(wiki_httpx, 'AsyncClient')
        except (ImportError, AttributeError, AssertionError):
            # Fallback if the import structure is different (e.g., just 'import httpx')
            print(f"Warning: Patch target '{patch_target}' might be incorrect. Falling back to 'httpx.AsyncClient'. Check imports in tool_wikipedia.py.")
            patch_target = 'httpx.AsyncClient'


        with patch(patch_target, return_value=mock_async_cm) as MockHttpxClientConstructor:

            # --- Test Execution ---

            # Step 1: Get info about BMI from Wikipedia using the mocked httpx calls
            wiki_result = await wikipedia_search("BMI calculation", limit=1)

            # --- Assertions for Step 1 ---
            assert wiki_result is not None, "Wikipedia search returned None"
            assert "results" in wiki_result, "Missing 'results' key in Wikipedia response"
            assert len(wiki_result["results"]) == 1, "Expected exactly one Wikipedia result"
            assert "title" in wiki_result["results"][0], "Missing 'title' key in Wikipedia result"

            # Get the title and perform the check that was previously failing
            title = wiki_result["results"][0]["title"]
            assert isinstance(title, str), f"Expected title to be a string, but got {type(title)}"
            title_lower = title.lower()

            # Use find() as a more robust check if 'in' operator was problematic
            # find() returns -1 if the substring is not found, otherwise the starting index (>= 0)
            # --- CORRECTED ASSERTION: Check for 'index' instead of 'bmi' ---
            assert title_lower.find("index") != -1, f"Expected 'index' to be in '{title_lower}'"

            # Optional: Verify the extract was also present if needed
            assert "extract" in wiki_result["results"][0], "Missing 'extract' key"
            assert "BMI" in wiki_result["results"][0]["extract"], "Expected 'BMI' in extract"


            # Step 2: Calculate BMI using a separate tool
            weight_kg = 80
            height_m = 1.8
            bmi_value = calculate_bmi(weight_kg, height_m)

            # --- Assertions for Step 2 ---
            assert bmi_value is not None
            assert isinstance(bmi_value, (float, int))
            assert round(bmi_value, 1) == 24.7, "BMI calculation result is incorrect"


            # Step 3: Simulate processing results using the long_task tool and mock context
            files_to_process = ["bmi_results.txt"]
            task_result = await long_task(files_to_process, mock_context)

            # --- Assertions for Step 3 ---
            assert task_result == "Processing complete"

            # Verify that context methods were called as expected by long_task
            mock_context.info.assert_called_with("Processing bmi_results.txt")
            # Check progress reporting (adjust numbers if long_task logic changes)
            mock_context.report_progress.assert_called_with(0, 1) # Assuming progress from 0 to 1 for 1 file
            # Verify read_resource was called
            mock_context.read_resource.assert_awaited_once_with("file://bmi_results.txt")


            # --- Final Mock Verification ---
            # Verify the httpx.AsyncClient constructor was called once
            MockHttpxClientConstructor.assert_called_once()
            # Verify the client's get method was called twice (once for search, once for extract)
            assert mock_client_instance.get.call_count == 2

# Example of how to stop the patcher if it was started globally (e.g., in a teardown)
# def teardown_module(module):
#     try:
#         patcher.stop()
#     except NameError:
#         pass # Patcher wasn't started