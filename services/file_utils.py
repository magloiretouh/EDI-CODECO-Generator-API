"""
File utilities for asynchronous file I/O operations.
Provides async functions for reading and writing files to support non-blocking operations.
"""

import aiofiles
import os
from pathlib import Path
from typing import Optional


async def write_file_async(file_path: str, content: str) -> None:
    """
    Asynchronously write content to a file.

    Creates the directory structure if it doesn't exist and writes the file content
    in a non-blocking manner using aiofiles.

    Args:
        file_path: Full path where the file should be written.
        content: String content to write to the file.

    Raises:
        IOError: If file write operation fails.
        OSError: If directory creation fails.
    """
    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            Path(parent_dir).mkdir(parents=True, exist_ok=True)

        # Write file asynchronously
        async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
            await f.write(content)
    except Exception as e:
        raise IOError(f"Failed to write file {file_path}: {str(e)}")


async def read_file_async(file_path: str) -> str:
    """
    Asynchronously read content from a file.

    Args:
        file_path: Path to the file to read.

    Returns:
        str: File content as string.

    Raises:
        IOError: If file read operation fails.
        FileNotFoundError: If file doesn't exist.
    """
    try:
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
        return content
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise IOError(f"Failed to read file {file_path}: {str(e)}")


async def write_binary_file_async(file_path: str, content: bytes) -> None:
    """
    Asynchronously write binary content to a file.

    Args:
        file_path: Full path where the file should be written.
        content: Binary content to write to the file.

    Raises:
        IOError: If file write operation fails.
        OSError: If directory creation fails.
    """
    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            Path(parent_dir).mkdir(parents=True, exist_ok=True)

        # Write file asynchronously
        async with aiofiles.open(file_path, mode='wb') as f:
            await f.write(content)
    except Exception as e:
        raise IOError(f"Failed to write binary file {file_path}: {str(e)}")


def file_exists(file_path: str) -> bool:
    """
    Check if a file exists.

    Args:
        file_path: Path to the file.

    Returns:
        bool: True if file exists, False otherwise.
    """
    return os.path.isfile(file_path)
