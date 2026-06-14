"""
Rudraksh AI — Shivoham Security Sandbox
========================================
Restricts file system access, command execution, and resource usage
for the autonomous execution engine to prevent damage.
"""

import os
import re
from pathlib import Path
from typing import Optional
from config.settings import get_settings


class SandboxViolation(Exception):
    """Raised when a sandbox rule is violated."""
    pass


class Sandbox:
    """Security sandbox for Shivoham's autonomous execution.
    
    Enforces:
    - File system access restricted to sandbox directory
    - Command allowlist/denylist
    - Path traversal prevention
    - Resource limits
    """

    # Commands that are NEVER allowed
    COMMAND_DENYLIST = [
        "rm -rf /", "rm -rf /*", "mkfs", "dd if=",
        ":(){ :|:& };:", "chmod -R 777 /", "shutdown",
        "reboot", "halt", "poweroff", "init 0", "init 6",
        "format", "del /f /s /q C:\\", "rd /s /q C:\\",
        "> /dev/sda", "wget", "curl -o", "curl -O",
        "powershell -enc", "Invoke-WebRequest",
    ]

    # File extensions that cannot be executed
    DANGEROUS_EXTENSIONS = [
        ".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js",
        ".msi", ".scr", ".com", ".pif", ".reg",
    ]

    def __init__(self, sandbox_dir: Optional[str] = None):
        settings = get_settings()
        self._sandbox_root = Path(sandbox_dir or settings.shivoham_sandbox_dir).resolve()
        self._sandbox_root.mkdir(parents=True, exist_ok=True)
        self._max_file_size_mb = 50
        self._max_output_length = 100_000  # characters

    @property
    def root(self) -> Path:
        return self._sandbox_root

    def validate_path(self, file_path: str) -> Path:
        """Validate and resolve a file path within the sandbox.
        
        Args:
            file_path: Relative or absolute path to validate
            
        Returns:
            Resolved absolute Path within the sandbox
            
        Raises:
            SandboxViolation: If path escapes the sandbox
        """
        # Resolve the path
        target = Path(file_path)
        if not target.is_absolute():
            target = self._sandbox_root / target
        target = target.resolve()

        # Check it's within the sandbox
        try:
            target.relative_to(self._sandbox_root)
        except ValueError:
            raise SandboxViolation(
                f"Path '{file_path}' resolves to '{target}' which is outside "
                f"the sandbox directory '{self._sandbox_root}'"
            )

        # Check for suspicious patterns
        path_str = str(target)
        if ".." in file_path:
            raise SandboxViolation(f"Path traversal detected in '{file_path}'")

        return target

    def validate_command(self, command: str) -> str:
        """Validate a shell command against security rules.
        
        Args:
            command: Shell command to validate
            
        Returns:
            The validated command string
            
        Raises:
            SandboxViolation: If command violates security rules
        """
        cmd_lower = command.lower().strip()

        # Check denylist
        for denied in self.COMMAND_DENYLIST:
            if denied.lower() in cmd_lower:
                raise SandboxViolation(
                    f"Command contains denied pattern: '{denied}'"
                )

        # Check for dangerous redirections
        if re.search(r">\s*/dev/", cmd_lower):
            raise SandboxViolation("Writing to device files is not allowed")

        # Check for privilege escalation
        if cmd_lower.startswith("sudo ") or cmd_lower.startswith("runas "):
            raise SandboxViolation("Privilege escalation is not allowed in sandbox")

        # Check for network operations (strict mode)
        network_patterns = [
            r"\bnc\b", r"\bncat\b", r"\bnetcat\b",
            r"\bssh\b", r"\bscp\b", r"\bsftp\b",
            r"\btelnet\b", r"\bftp\b",
        ]
        for pattern in network_patterns:
            if re.search(pattern, cmd_lower):
                raise SandboxViolation(
                    f"Network command detected: matches pattern '{pattern}'"
                )

        return command

    def validate_file_write(self, path: str, content: str) -> Path:
        """Validate a file write operation.
        
        Args:
            path: Target file path
            content: Content to write
            
        Returns:
            Validated Path object
            
        Raises:
            SandboxViolation: If write violates sandbox rules
        """
        target = self.validate_path(path)

        # Check file extension
        if target.suffix.lower() in self.DANGEROUS_EXTENSIONS:
            raise SandboxViolation(
                f"Cannot write files with extension '{target.suffix}' in sandbox"
            )

        # Check content size
        content_size_mb = len(content.encode("utf-8")) / (1024 * 1024)
        if content_size_mb > self._max_file_size_mb:
            raise SandboxViolation(
                f"File size ({content_size_mb:.1f}MB) exceeds limit "
                f"({self._max_file_size_mb}MB)"
            )

        return target

    def validate_file_read(self, path: str) -> Path:
        """Validate a file read operation.
        
        Args:
            path: File path to read
            
        Returns:
            Validated Path object
            
        Raises:
            SandboxViolation: If read violates sandbox rules
        """
        target = self.validate_path(path)

        if not target.exists():
            raise SandboxViolation(f"File does not exist: '{path}'")

        if not target.is_file():
            raise SandboxViolation(f"Path is not a file: '{path}'")

        # Check file size
        file_size_mb = target.stat().st_size / (1024 * 1024)
        if file_size_mb > self._max_file_size_mb:
            raise SandboxViolation(
                f"File too large to read ({file_size_mb:.1f}MB > {self._max_file_size_mb}MB)"
            )

        return target

    def truncate_output(self, output: str) -> str:
        """Truncate command output to prevent memory issues."""
        if len(output) > self._max_output_length:
            return (
                output[:self._max_output_length // 2]
                + f"\n\n... [TRUNCATED: {len(output) - self._max_output_length} chars omitted] ...\n\n"
                + output[-self._max_output_length // 2:]
            )
        return output

    def get_info(self) -> dict:
        """Get sandbox configuration info."""
        return {
            "root": str(self._sandbox_root),
            "exists": self._sandbox_root.exists(),
            "max_file_size_mb": self._max_file_size_mb,
            "max_output_length": self._max_output_length,
            "denied_commands": len(self.COMMAND_DENYLIST),
            "dangerous_extensions": self.DANGEROUS_EXTENSIONS,
        }
