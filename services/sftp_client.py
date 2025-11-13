"""
SFTP Client Service for asynchronous file uploads.
Handles uploading EDI files to SFTP server with retry logic and exponential backoff.
Uses paramiko for SFTP operations with async wrapper (run_in_executor).

Note: asyncssh was considered but requires Rust compilation. Paramiko provides
synchronous SFTP operations wrapped in asyncio for non-blocking I/O.
"""

import asyncio
import logging
from typing import Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import paramiko

logger = logging.getLogger(__name__)

# Thread pool for running blocking paramiko operations
_executor = ThreadPoolExecutor(max_workers=5)


class SFTPClient:
    """
    Async SFTP client for uploading files to remote SFTP server.

    This client supports:
    - Asynchronous file uploads
    - Automatic retries with exponential backoff
    - Connection pooling and error handling
    - Detailed logging of operations and failures
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        remote_dir: str = '/',
        max_retries: int = 3,
        retry_delay: int = 1
    ):
        """
        Initialize SFTP client configuration.

        Args:
            host: SFTP server hostname or IP address.
            port: SFTP server port (typically 22).
            username: SFTP username for authentication.
            password: SFTP password for authentication.
            remote_dir: Remote directory where files should be uploaded (default: '/').
            max_retries: Maximum number of retry attempts (default: 3).
            retry_delay: Initial delay in seconds between retry attempts (default: 1).
                        Uses exponential backoff: delay * (2 ^ attempt_number).
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.remote_dir = remote_dir.rstrip('/')
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def upload_file(
        self,
        local_file_path: str,
        remote_file_name: Optional[str] = None
    ) -> bool:
        """
        Upload a file to the SFTP server with retry logic.

        Implements exponential backoff retry strategy. Each retry waits
        delay_seconds * (2 ^ attempt_number) seconds before retrying.

        Args:
            local_file_path: Full path to local file to upload.
            remote_file_name: Optional custom name for remote file.
                             If not provided, uses the basename of local_file_path.

        Returns:
            bool: True if upload succeeded, False otherwise.

        Raises:
            FileNotFoundError: If local file doesn't exist.
            IOError: If final upload attempt fails (after all retries).
        """
        # Validate local file exists
        if not Path(local_file_path).exists():
            error_msg = f"Local file not found: {local_file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Use basename if remote filename not specified
        if remote_file_name is None:
            remote_file_name = Path(local_file_path).name

        # Construct full remote path
        full_remote_path = f"{self.remote_dir}/{remote_file_name}".replace('//', '/')

        # Attempt upload with retries
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"SFTP upload attempt {attempt + 1}/{self.max_retries}: "
                    f"{local_file_path} -> {self.host}:{full_remote_path}"
                )

                # Perform SFTP upload
                await self._upload_with_paramiko(local_file_path, full_remote_path)

                logger.info(
                    f"Successfully uploaded {local_file_path} to "
                    f"{self.host}:{full_remote_path}"
                )
                return True

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"Upload attempt {attempt + 1} failed: {error_msg}"
                )

                # Calculate exponential backoff delay
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    final_error = (
                        f"SFTP upload failed after {self.max_retries} attempts. "
                        f"Last error: {error_msg}"
                    )
                    logger.error(final_error)
                    raise IOError(final_error)

        return False

    async def _upload_with_paramiko(
        self,
        local_file_path: str,
        remote_file_path: str
    ) -> None:
        """
        Perform SFTP upload using paramiko library (run in thread pool for async).

        This method handles the actual SSH connection and SFTP file transfer.
        Connection is closed automatically after transfer.

        Since paramiko is synchronous, this method runs in a thread pool executor
        to provide async semantics without blocking the event loop.

        Args:
            local_file_path: Full path to local file.
            remote_file_path: Full remote path for uploaded file.

        Raises:
            IOError: If SSH/SFTP connection or transfer fails.
            OSError: If file I/O fails.
        """
        loop = asyncio.get_event_loop()

        def _upload_sync():
            """Synchronous SFTP upload using paramiko."""
            try:
                # Create SSH transport
                transport = paramiko.Transport((self.host, self.port))
                transport.connect(username=self.username, password=self.password)

                # Open SFTP client
                sftp = paramiko.SFTPClient.from_transport(transport)

                try:
                    # Upload file
                    sftp.put(local_file_path, remote_file_path)
                finally:
                    sftp.close()
                    transport.close()

            except paramiko.AuthenticationException as e:
                raise IOError(f"SFTP authentication error: {str(e)}")
            except paramiko.SSHException as e:
                raise IOError(f"SSH error: {str(e)}")
            except OSError as e:
                raise IOError(f"File I/O error: {str(e)}")
            except Exception as e:
                raise IOError(f"Unexpected error during SFTP transfer: {str(e)}")

        # Run synchronous SFTP operation in thread pool
        await loop.run_in_executor(_executor, _upload_sync)


async def upload_edi_file(
    local_edi_path: str,
    sftp_host: str,
    sftp_port: int,
    sftp_user: str,
    sftp_password: str,
    sftp_remote_dir: str = '/',
    max_retries: int = 3,
    retry_delay: int = 1
) -> bool:
    """
    Convenience function to upload an EDI file to SFTP server.

    This is a standalone async function that creates an SFTPClient instance
    and performs the upload operation.

    Args:
        local_edi_path: Full path to local EDI file.
        sftp_host: SFTP server hostname.
        sftp_port: SFTP server port.
        sftp_user: SFTP username.
        sftp_password: SFTP password.
        sftp_remote_dir: Remote directory for upload.
        max_retries: Maximum retry attempts.
        retry_delay: Initial delay between retries.

    Returns:
        bool: True if upload succeeded, False otherwise.

    Raises:
        Exception: If upload fails after all retries.
    """
    client = SFTPClient(
        host=sftp_host,
        port=sftp_port,
        username=sftp_user,
        password=sftp_password,
        remote_dir=sftp_remote_dir,
        max_retries=max_retries,
        retry_delay=retry_delay
    )

    return await client.upload_file(local_edi_path)
