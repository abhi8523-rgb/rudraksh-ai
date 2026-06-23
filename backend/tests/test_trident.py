"""
Neel AI — Trident Engine Tests
=====================================
Tests for DAG planning, sandbox security, tool execution, and verification.
"""

import pytest
from trident.dag import DAGPlanner, TaskNode, TaskStatus
from trident.sandbox import Sandbox, SandboxViolation


class TestDAGPlanner:
    """Tests for the DAG task planner."""

    def test_task_node_creation(self):
        """Test TaskNode can be created with defaults."""
        node = TaskNode(name="Test Task", description="A test")
        assert node.name == "Test Task"
        assert node.status == TaskStatus.PENDING
        assert node.dependencies == []

    def test_task_node_serialization(self):
        """Test TaskNode serializes to dict correctly."""
        node = TaskNode(id="t1", name="Test", description="Desc")
        data = node.to_dict()
        assert data["id"] == "t1"
        assert data["name"] == "Test"
        assert data["status"] == "pending"

    def test_planner_creation(self):
        """Test DAGPlanner can be instantiated."""
        planner = DAGPlanner()
        assert planner.tasks == {}

    def test_planner_progress_empty(self):
        """Test progress on empty planner."""
        planner = DAGPlanner()
        progress = planner.get_progress()
        assert progress["total"] == 0

    def test_planner_is_complete_empty(self):
        """Test is_complete on empty planner."""
        planner = DAGPlanner()
        assert planner.is_complete()

    def test_mark_completed(self):
        """Test marking a task as completed."""
        planner = DAGPlanner()
        node = TaskNode(id="t1", name="Test")
        planner.tasks["t1"] = node
        planner.mark_completed("t1", "Result data")
        assert planner.tasks["t1"].status == TaskStatus.COMPLETED
        assert planner.tasks["t1"].result == "Result data"

    def test_mark_failed(self):
        """Test marking a task as failed."""
        planner = DAGPlanner()
        node = TaskNode(id="t1", name="Test")
        planner.tasks["t1"] = node
        planner.mark_failed("t1", "Error occurred")
        assert planner.tasks["t1"].status == TaskStatus.FAILED


class TestSandbox:
    """Tests for the security sandbox."""

    def setup_method(self):
        import tempfile
        self._tmpdir = tempfile.mkdtemp()
        self.sandbox = Sandbox(sandbox_dir=self._tmpdir)

    def test_sandbox_creation(self):
        """Test sandbox initializes correctly."""
        assert self.sandbox.root.exists()

    def test_valid_path_within_sandbox(self):
        """Test valid paths within sandbox are accepted."""
        path = self.sandbox.validate_path("test.txt")
        assert str(self.sandbox.root) in str(path)

    def test_path_traversal_blocked(self):
        """Test that path traversal attempts are blocked."""
        with pytest.raises(SandboxViolation):
            self.sandbox.validate_path("../../etc/passwd")

    def test_dangerous_command_blocked(self):
        """Test that dangerous commands are blocked."""
        with pytest.raises(SandboxViolation):
            self.sandbox.validate_command("rm -rf /")

    def test_sudo_blocked(self):
        """Test that privilege escalation is blocked."""
        with pytest.raises(SandboxViolation):
            self.sandbox.validate_command("sudo rm -rf /tmp")

    def test_safe_command_allowed(self):
        """Test that safe commands pass validation."""
        result = self.sandbox.validate_command("echo hello")
        assert result == "echo hello"

    def test_dangerous_extension_blocked(self):
        """Test that writing executable files is blocked."""
        with pytest.raises(SandboxViolation):
            self.sandbox.validate_file_write("malware.exe", "bad content")

    def test_output_truncation(self):
        """Test that very long output is truncated."""
        long_output = "x" * 200000
        truncated = self.sandbox.truncate_output(long_output)
        assert len(truncated) < len(long_output)
        assert "TRUNCATED" in truncated

    def test_sandbox_info(self):
        """Test get_info returns expected structure."""
        info = self.sandbox.get_info()
        assert "root" in info
        assert "exists" in info
        assert info["exists"] is True


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_status_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
