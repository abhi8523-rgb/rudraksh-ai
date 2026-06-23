"""
Neel AI — Trident Verification & Self-Correction
======================================================
Post-execution outcome checking, LLM-powered assessment,
error classification, and automatic plan adjustment.
"""

from typing import Optional
from llm.ollama_client import OllamaClient
from config.settings import get_settings


VERIFICATION_SYSTEM = """You are the Trident verification engine. You assess whether a task 
was completed successfully and provide structured feedback.

Given:
- The task description (what was intended)
- The task result (what actually happened)

You must determine:
1. SUCCESS: Did the task achieve its goal?
2. QUALITY: How well was it done? (1-10)
3. ISSUES: Any problems, errors, or incomplete aspects
4. SUGGESTIONS: If failed, what should be tried differently

RESPONSE FORMAT (strict JSON):
{
    "verdict": "success" | "partial" | "failure",
    "quality_score": 1-10,
    "explanation": "Brief explanation of the assessment",
    "issues": ["list of specific issues found"],
    "retry_suggestion": "What to do differently if retrying, or null if successful",
    "needs_replan": true/false
}

RULES:
- Be strict but fair in assessment
- "partial" means the core goal was met but with issues
- Set needs_replan=true only if the entire approach is wrong
- Always respond with ONLY valid JSON"""


class Verifier:
    """Verifies task execution results and provides corrective feedback."""

    def __init__(self):
        self._client = OllamaClient()

    async def verify(
        self,
        task_name: str,
        task_description: str,
        task_result: str,
        tool_name: str = "",
        was_success: bool = True,
    ) -> dict:
        """Verify whether a task was completed successfully.
        
        Args:
            task_name: Name of the task
            task_description: What the task was supposed to do
            task_result: The actual output/result
            tool_name: Which tool was used
            was_success: Whether the tool reported success
            
        Returns:
            Verification result dict with verdict, score, issues, suggestions
        """
        settings = get_settings()

        user_prompt = f"""Verify this task execution:

Task Name: {task_name}
Task Description: {task_description}
Tool Used: {tool_name}
Tool Reported Success: {was_success}

Task Result:
{task_result[:3000]}"""

        messages = [
            {"role": "system", "content": VERIFICATION_SYSTEM},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self._client.chat(
                model=settings.default_model,
                messages=messages,
            )
            content = response.get("message", {}).get("content", "")
            
            # Parse JSON response
            import json
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            
            result = json.loads(content)
            
            # Ensure required fields
            result.setdefault("verdict", "failure" if not was_success else "success")
            result.setdefault("quality_score", 5)
            result.setdefault("explanation", "")
            result.setdefault("issues", [])
            result.setdefault("retry_suggestion", None)
            result.setdefault("needs_replan", False)
            
            return result

        except Exception as e:
            # If verification itself fails, use a simple heuristic
            return {
                "verdict": "success" if was_success else "failure",
                "quality_score": 7 if was_success else 3,
                "explanation": f"Automated verification (LLM verification failed: {e})",
                "issues": [] if was_success else [str(task_result[:200])],
                "retry_suggestion": None if was_success else "Retry with different parameters",
                "needs_replan": False,
            }

    async def should_retry(self, verification_result: dict, current_retries: int, max_retries: int) -> bool:
        """Determine if a failed task should be retried.
        
        Args:
            verification_result: Result from verify()
            current_retries: Number of retries so far
            max_retries: Maximum allowed retries
            
        Returns:
            True if the task should be retried
        """
        if current_retries >= max_retries:
            return False
        
        verdict = verification_result.get("verdict", "failure")
        
        # Don't retry successes
        if verdict == "success":
            return False
        
        # Don't retry if a full replan is needed
        if verification_result.get("needs_replan", False):
            return False
        
        # Retry partial successes and failures
        return True

    async def generate_retry_context(self, task_name: str, previous_result: str, verification: dict) -> str:
        """Generate context for a retry attempt.
        
        Args:
            task_name: Name of the task being retried
            previous_result: Output from the failed attempt
            verification: Verification result from the failed attempt
            
        Returns:
            Context string to prepend to the retry
        """
        suggestion = verification.get("retry_suggestion", "")
        issues = verification.get("issues", [])
        
        context = f"""RETRY CONTEXT for '{task_name}':
Previous attempt failed with issues:
{chr(10).join(f'  - {issue}' for issue in issues)}

Suggestion for this retry:
{suggestion}

Previous output (for reference):
{previous_result[:1000]}"""
        
        return context
