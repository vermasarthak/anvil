import pytest
import os
from sol.tools.file_ops import ReadFileTool, CreateFileTool, EditFileTool

@pytest.mark.asyncio
async def test_file_ops_tools(tmp_path):
    test_file = str(tmp_path / "test.py")
    
    # Test Create
    create_tool = CreateFileTool()
    res = await create_tool.execute(path=test_file, content="def foo():\n    return 42\n")
    assert res.success is True
    assert os.path.exists(test_file)
    
    # Test Read
    read_tool = ReadFileTool()
    res_read = await read_tool.execute(path=test_file)
    assert res_read.success is True
    assert "return 42" in res_read.output

    # Test Edit
    edit_tool = EditFileTool()
    res_edit = await edit_tool.execute(path=test_file, old_string="return 42", new_string="return 100")
    assert res_edit.success is True
    
    res_read2 = await read_tool.execute(path=test_file)
    assert "return 100" in res_read2.output
