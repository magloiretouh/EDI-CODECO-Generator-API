"""
Unit tests for SFTP Client service.
Tests async SFTP upload with mocking to avoid real connections.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
from services.sftp_client import SFTPClient, upload_edi_file


class TestSFTPClient:
    """Test cases for SFTP Client functionality."""

    @pytest.fixture
    def sftp_client(self):
        """Fixture providing an SFTP client instance."""
        return SFTPClient(
            host='127.0.0.1',
            port=22,
            username='testuser',
            password='testpass',
            remote_dir='/',
            max_retries=3,
            retry_delay=1
        )

    @pytest.fixture
    def temp_file(self):
        """Fixture providing a temporary test file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.edi') as f:
            f.write('TEST EDI CONTENT')
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    def test_sftp_client_initialization(self, sftp_client):
        """Test SFTP client initialization."""
        assert sftp_client.host == '127.0.0.1'
        assert sftp_client.port == 22
        assert sftp_client.username == 'testuser'
        assert sftp_client.password == 'testpass'
        # Remote dir strips trailing slash, so '/' becomes empty
        assert sftp_client.remote_dir == '' or sftp_client.remote_dir == '/'
        assert sftp_client.max_retries == 3
        assert sftp_client.retry_delay == 1

    def test_sftp_client_with_custom_remote_dir(self):
        """Test SFTP client with custom remote directory."""
        client = SFTPClient(
            host='127.0.0.1',
            port=22,
            username='testuser',
            password='testpass',
            remote_dir='/incoming/edi/'
        )
        assert client.remote_dir == '/incoming/edi'

    def test_sftp_client_remote_dir_trailing_slash_removed(self):
        """Test that trailing slashes are removed from remote directory."""
        client = SFTPClient(
            host='127.0.0.1',
            port=22,
            username='testuser',
            password='testpass',
            remote_dir='/incoming/edi/'
        )
        assert not client.remote_dir.endswith('/')

    @pytest.mark.asyncio
    async def test_upload_file_nonexistent_file_raises_error(self, sftp_client):
        """Test that uploading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            await sftp_client.upload_file('/nonexistent/path/file.edi')

    @pytest.mark.asyncio
    async def test_upload_file_with_custom_remote_name(self, sftp_client, temp_file):
        """Test uploading file with custom remote filename."""
        with patch('services.sftp_client.paramiko.Transport') as mock_transport_class:
            # Mock SFTP client
            mock_sftp = MagicMock()
            mock_sftp.put = MagicMock()

            # Mock transport
            mock_transport = MagicMock()
            mock_transport_class.return_value = mock_transport

            # Setup paramiko SFTP client creation
            with patch('services.sftp_client.paramiko.SFTPClient.from_transport', return_value=mock_sftp):
                # Upload file with custom remote name
                result = await sftp_client.upload_file(temp_file, 'custom_name.edi')

                assert result is True
                mock_sftp.put.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_uses_basename_when_no_custom_name(self, sftp_client, temp_file):
        """Test that upload uses basename of local file when no custom name provided."""
        with patch('services.sftp_client.paramiko.Transport') as mock_transport_class:
            # Mock SFTP client
            mock_sftp = MagicMock()
            mock_sftp.put = MagicMock()

            # Mock transport
            mock_transport = MagicMock()
            mock_transport_class.return_value = mock_transport

            # Setup paramiko SFTP client creation
            with patch('services.sftp_client.paramiko.SFTPClient.from_transport', return_value=mock_sftp):
                # Upload file without custom name
                result = await sftp_client.upload_file(temp_file)

                assert result is True
                # Verify put was called with correct remote path
                call_args = mock_sftp.put.call_args
                assert Path(temp_file).name in call_args[0][1]

    @pytest.mark.asyncio
    async def test_upload_file_connection_error_retries(self, sftp_client, temp_file):
        """Test that connection errors trigger retry logic."""
        with patch('services.sftp_client.paramiko.Transport') as mock_transport_class:
            # Simulate connection error
            mock_transport_class.side_effect = Exception("Connection refused")

            with pytest.raises(IOError) as exc_info:
                await sftp_client.upload_file(temp_file)

            assert "Connection refused" in str(exc_info.value)
            # Should have attempted max_retries times
            assert mock_transport_class.call_count == sftp_client.max_retries

    @pytest.mark.asyncio
    async def test_upload_file_retry_with_exponential_backoff(self, sftp_client, temp_file):
        """Test that retries use exponential backoff."""
        with patch('services.sftp_client.paramiko.Transport') as mock_transport_class:
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                # Simulate connection error
                mock_transport_class.side_effect = Exception("Connection refused")

                try:
                    await sftp_client.upload_file(temp_file)
                except IOError:
                    pass

                # Should have called sleep with exponential backoff
                # retry_delay * (2 ^ attempt)
                assert mock_sleep.call_count == sftp_client.max_retries - 1

                # Check backoff values
                sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
                assert sleep_calls[0] == 1  # 1 * (2^0) = 1
                assert sleep_calls[1] == 2  # 1 * (2^1) = 2

    @pytest.mark.asyncio
    async def test_upload_file_success_on_retry(self, sftp_client, temp_file):
        """Test that upload succeeds on a retry attempt."""
        with patch('services.sftp_client.paramiko.Transport') as mock_transport_class:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                # Mock SFTP client
                mock_sftp = MagicMock()
                mock_sftp.put = MagicMock()

                # Mock transport
                mock_transport = MagicMock()

                # Setup paramiko SFTP client creation
                def _create_sftp(*args, **kwargs):
                    return mock_sftp

                with patch('services.sftp_client.paramiko.SFTPClient.from_transport', side_effect=_create_sftp):
                    # Fail first attempt, succeed on second
                    mock_transport_class.side_effect = [
                        Exception("Connection refused"),
                        mock_transport
                    ]

                    result = await sftp_client.upload_file(temp_file)

                    # Should have succeeded on retry
                    assert result is True
                    # Should have attempted twice
                    assert mock_transport_class.call_count == 2

    @pytest.mark.asyncio
    async def test_upload_edi_file_function(self, temp_file):
        """Test the standalone upload_edi_file function."""
        with patch('services.sftp_client.paramiko.Transport') as mock_transport_class:
            # Mock SFTP client
            mock_sftp = MagicMock()
            mock_sftp.put = MagicMock()

            # Mock transport
            mock_transport = MagicMock()
            mock_transport_class.return_value = mock_transport

            # Setup paramiko SFTP client creation
            with patch('services.sftp_client.paramiko.SFTPClient.from_transport', return_value=mock_sftp):
                # Call standalone function
                result = await upload_edi_file(
                    temp_file,
                    '127.0.0.1',
                    22,
                    'testuser',
                    'testpass',
                    '/'
                )

                assert result is True


class TestSFTPClientIntegration:
    """Integration tests for SFTP client (with mocks)."""

    @pytest.mark.asyncio
    async def test_full_upload_workflow(self):
        """Test complete upload workflow from file creation to transfer."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.edi') as f:
            f.write('UNB+UNOC:3+SENDER+RECEIVER+240425+0400+123456789\'')
            temp_path = f.name

        try:
            with patch('services.sftp_client.paramiko.Transport') as mock_transport_class:
                # Mock SFTP client
                mock_sftp = MagicMock()
                mock_sftp.put = MagicMock()

                # Mock transport
                mock_transport = MagicMock()
                mock_transport_class.return_value = mock_transport

                # Setup paramiko SFTP client creation
                with patch('services.sftp_client.paramiko.SFTPClient.from_transport', return_value=mock_sftp):
                    client = SFTPClient(
                        host='sftp.example.com',
                        port=22,
                        username='user',
                        password='pass',
                        remote_dir='/incoming'
                    )

                    result = await client.upload_file(temp_path)

                    assert result is True
                    mock_sftp.put.assert_called_once()

        finally:
            Path(temp_path).unlink(missing_ok=True)
