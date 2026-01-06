"""Execute Amplifier recipes via CLI subprocess and stream progress to SSE queue."""

import asyncio
import json
import logging
import shutil
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # Will handle gracefully

logger = logging.getLogger(__name__)


class RecipeExecutor:
    """Execute Amplifier recipes via CLI and stream progress to SSE queue.
    
    This module wraps the Amplifier CLI in a subprocess, parses recipe stages,
    and streams progress updates to the web UI's MessageQueue for real-time display.
    """
    
    # Map recipe stage names to UI display names and indices
    STAGE_MAPPING = {
        "style-analysis": ("Style Extraction", 0),
        "draft-creation": ("Draft Generation", 1),
        "review": ("Review", 2),
        "revision": ("Revision", 3),
        "illustration": ("Illustration", 4),
    }
    
    def __init__(self, recipe_path: Path):
        """Initialize executor with recipe file.
        
        Args:
            recipe_path: Path to recipe YAML file
        """
        self.recipe_path = Path(recipe_path)
        self.stage_map = self._load_stage_map()
        self.amplifier_path = self._find_amplifier_cli()
    
    def _find_amplifier_cli(self) -> str:
        """Find amplifier CLI executable path.
        
        Returns:
            Path to amplifier executable
            
        Raises:
            RuntimeError: If amplifier CLI not found
        """
        # Try which command first
        amplifier = shutil.which("amplifier")
        if amplifier:
            return amplifier
        
        # Fallback to common locations
        common_paths = [
            Path.home() / ".local" / "bin" / "amplifier",
            Path("/usr/local/bin/amplifier"),
            Path("/usr/bin/amplifier"),
        ]
        
        for path in common_paths:
            if path.exists():
                return str(path)
        
        raise RuntimeError(
            "Amplifier CLI not found. Ensure 'amplifier' is installed and in PATH."
        )
    
    def _load_stage_map(self) -> dict[str, tuple[str, int]]:
        """Load recipe stages and build stage mapping.
        
        Parses the recipe YAML to extract stage names and maps them to
        UI indices based on STAGE_MAPPING.
        
        Returns:
            Dictionary mapping stage names to (display_name, index) tuples
        """
        if not self.recipe_path.exists():
            logger.warning(f"Recipe file not found: {self.recipe_path}")
            return self.STAGE_MAPPING
        
        # Try to parse with PyYAML if available
        if yaml:
            try:
                with open(self.recipe_path) as f:
                    recipe_data = yaml.safe_load(f)
                    stages = recipe_data.get("stages", [])
                    
                    # Build map from recipe stage names
                    stage_map = {}
                    for idx, stage in enumerate(stages):
                        stage_name = stage.get("name", "")
                        if stage_name in self.STAGE_MAPPING:
                            stage_map[stage_name] = self.STAGE_MAPPING[stage_name]
                        else:
                            # Unknown stage - use name as display and assign index
                            logger.warning(f"Unknown stage in recipe: {stage_name}")
                            stage_map[stage_name] = (stage_name.title(), idx)
                    
                    return stage_map if stage_map else self.STAGE_MAPPING
                    
            except Exception as e:
                logger.warning(f"Failed to parse recipe YAML: {e}")
        
        # Fallback to default mapping
        logger.info("Using default stage mapping")
        return self.STAGE_MAPPING
    
    def _build_command(
        self, context: dict[str, Any], session_dir: Path
    ) -> list[str]:
        """Build amplifier CLI command for recipe execution.
        
        Args:
            context: Recipe context variables (topic, style_samples_dir, etc.)
            session_dir: Output directory for recipe artifacts
            
        Returns:
            Command array for subprocess execution
        """
        # Serialize context to JSON
        context_json = json.dumps(context)
        
        # Build command
        cmd = [
            self.amplifier_path,
            "tool",
            "invoke",
            "recipes",
            "operation=execute",
            f"recipe_path={self.recipe_path}",
            f"context={context_json}",
        ]
        
        logger.debug(f"Built command: {' '.join(cmd)}")
        return cmd
    
    def _detect_stage(self, line: str) -> tuple[str, int] | None:
        """Parse line for stage information.
        
        Looks for patterns indicating stage transitions in CLI output.
        
        Args:
            line: Output line from subprocess
            
        Returns:
            (stage_name, stage_index) tuple if stage detected, None otherwise
        """
        line_lower = line.lower()
        
        # Common patterns in recipe execution output
        # Look for: "Starting stage: <name>", "Running stage <name>", etc.
        stage_indicators = [
            "starting stage:",
            "running stage:",
            "stage:",
            "executing stage:",
        ]
        
        for indicator in stage_indicators:
            if indicator in line_lower:
                # Extract stage name after indicator
                idx = line_lower.index(indicator) + len(indicator)
                stage_name = line[idx:].strip().split()[0].strip("'\":")
                
                # Look up in our mapping
                if stage_name in self.stage_map:
                    display_name, stage_idx = self.stage_map[stage_name]
                    logger.debug(f"Detected stage: {stage_name} -> {display_name} (index {stage_idx})")
                    return (stage_name, stage_idx)
        
        # Also check if line starts with stage name
        for stage_name in self.stage_map:
            if line_lower.startswith(stage_name):
                display_name, stage_idx = self.stage_map[stage_name]
                return (stage_name, stage_idx)
        
        return None
    
    async def _stream_output(self, proc: asyncio.subprocess.Process, queue) -> bool:
        """Stream subprocess output to message queue.
        
        Reads stdout/stderr line-by-line, detects stage transitions,
        and puts progress updates in the queue.
        
        Args:
            proc: Subprocess process object
            queue: MessageQueue for progress updates
            
        Returns:
            True if subprocess completed successfully, False on error
        """
        current_stage = None
        current_stage_idx = -1
        
        async def read_stream(stream, stream_name):
            """Read from a stream line by line."""
            nonlocal current_stage, current_stage_idx
            
            while True:
                try:
                    line_bytes = await stream.readline()
                    if not line_bytes:
                        break
                    
                    line = line_bytes.decode('utf-8', errors='replace').rstrip()
                    if not line:
                        continue
                    
                    # Log all output at DEBUG level
                    logger.debug(f"[{stream_name}] {line}")
                    
                    # Detect stage transitions
                    stage_info = self._detect_stage(line)
                    if stage_info:
                        stage_name, stage_idx = stage_info
                        current_stage = stage_name
                        current_stage_idx = stage_idx
                        
                        # Get display name
                        display_name, _ = self.stage_map.get(stage_name, (stage_name, stage_idx))
                        
                        # Send stage transition message
                        await queue.put(
                            f"Starting: {display_name}",
                            stage=stage_name,
                            stage_index=stage_idx
                        )
                    else:
                        # Send regular progress message with current stage context
                        await queue.put(
                            line,
                            stage=current_stage,
                            stage_index=current_stage_idx if current_stage_idx >= 0 else None
                        )
                
                except Exception as e:
                    logger.error(f"Error reading {stream_name}: {e}")
                    break
        
        # Read both stdout and stderr concurrently
        try:
            await asyncio.gather(
                read_stream(proc.stdout, "stdout"),
                read_stream(proc.stderr, "stderr"),
            )
        except Exception as e:
            logger.error(f"Error streaming output: {e}")
            await queue.put(f"Error streaming output: {str(e)}")
            return False
        
        # Wait for process to complete
        return_code = await proc.wait()
        
        if return_code != 0:
            logger.error(f"Process exited with code {return_code}")
            await queue.put(f"Recipe execution failed with exit code {return_code}")
            return False
        
        return True
    
    async def execute(
        self,
        context: dict[str, Any],
        session_dir: Path,
        queue,
    ) -> bool:
        """Execute recipe with context and stream progress.
        
        Main entry point for recipe execution. Builds command, spawns subprocess,
        streams output to queue, and handles errors.
        
        Args:
            context: Recipe context variables (topic, style_samples_dir, etc.)
            session_dir: Output directory for recipe artifacts
            queue: MessageQueue for progress updates
            
        Returns:
            True if execution successful, False on error
            
        Example:
            >>> executor = RecipeExecutor(Path("recipes/create-blog-post.yaml"))
            >>> success = await executor.execute(
            ...     context={"topic": "...", "style_samples_dir": "/path/to/samples"},
            ...     session_dir=Path(".data/blog_creator/session-123"),
            ...     queue=message_queue
            ... )
        """
        try:
            # Ensure session directory exists
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Build command
            cmd = self._build_command(context, session_dir)
            
            # Initial message
            await queue.put("Initializing recipe execution...")
            logger.info(f"Starting recipe execution: {self.recipe_path}")
            
            # Create subprocess
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(session_dir),
            )
            
            # Stream output with timeout
            try:
                success = await asyncio.wait_for(
                    self._stream_output(proc, queue),
                    timeout=1800.0  # 30 minute timeout
                )
                
                if success:
                    await queue.put("Recipe execution completed successfully!")
                    logger.info("Recipe execution completed successfully")
                else:
                    logger.error("Recipe execution failed")
                
                return success
                
            except asyncio.TimeoutError:
                logger.error("Recipe execution timed out after 30 minutes")
                await queue.put("Error: Recipe execution timed out (30 minute limit)")
                
                # Terminate the process
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                
                return False
        
        except Exception as e:
            logger.error(f"Recipe execution error: {e}", exc_info=True)
            await queue.put(f"Error: {str(e)}")
            return False
