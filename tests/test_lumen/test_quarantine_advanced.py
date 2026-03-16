"""Phase Lumen L62 — Advanced quarantine and ClamAV scan tests.

Tests ClamAV import failures, socket fallback, scan results,
and quarantine_file edge cases.
— Scout (QA Lead)
"""

import sys
from unittest.mock import MagicMock, patch

# ══════════════════════════════════════════════════════════════════════════════
# SCAN WITH CLAMAV — IMPORT MISSING
# ══════════════════════════════════════════════════════════════════════════════


class TestScanWithClamavImportMissing:
    """Test scan_with_clamav when clamd is not installed."""

    def test_returns_not_scanned_when_clamd_missing(self):
        """When clamd import fails: returns scanned=False, clean=True, threat=None."""
        from app.services.quarantine import scan_with_clamav

        # Ensure clamd is not importable
        with patch.dict(sys.modules, {"clamd": None}):
            # Force reimport to hit ImportError
            # Just call the function — it does `import clamd` inside
            result = scan_with_clamav("/fake/file.txt")

        assert result["scanned"] is False
        assert result["clean"] is True
        assert result["threat"] is None


# ══════════════════════════════════════════════════════════════════════════════
# SCAN WITH CLAMAV — SOCKET FAILURES
# ══════════════════════════════════════════════════════════════════════════════


class TestScanWithClamavSocketFailures:
    """Test socket fallback behavior."""

    def _make_mock_clamd(self, unix_ping_ok=False, tcp_ping_ok=False):
        """Create a mock clamd module with configurable socket behavior."""
        mock_clamd = MagicMock()

        unix_socket = MagicMock()
        if not unix_ping_ok:
            unix_socket.ping.side_effect = ConnectionError("unix down")
        mock_clamd.ClamdUnixSocket.return_value = unix_socket

        tcp_socket = MagicMock()
        if not tcp_ping_ok:
            tcp_socket.ping.side_effect = ConnectionError("tcp down")
        else:
            tcp_socket.scan.return_value = None
        mock_clamd.ClamdNetworkSocket.return_value = tcp_socket

        return mock_clamd, unix_socket, tcp_socket

    def test_unix_fails_tcp_succeeds(self):
        """Unix socket ping fails, TCP succeeds: uses ClamdNetworkSocket."""
        mock_clamd, unix_sock, tcp_sock = self._make_mock_clamd(unix_ping_ok=False, tcp_ping_ok=True)
        tcp_sock.scan.return_value = None  # clean

        with patch.dict(sys.modules, {"clamd": mock_clamd}):
            from app.services.quarantine import scan_with_clamav

            result = scan_with_clamav("/fake/file.txt")

        assert result["scanned"] is True
        assert result["clean"] is True
        tcp_sock.scan.assert_called_once_with("/fake/file.txt")

    def test_both_sockets_unreachable(self):
        """Both sockets unreachable: returns scanned=False, clean=True."""
        mock_clamd, _, _ = self._make_mock_clamd(unix_ping_ok=False, tcp_ping_ok=False)

        with patch.dict(sys.modules, {"clamd": mock_clamd}):
            from app.services.quarantine import scan_with_clamav

            result = scan_with_clamav("/fake/file.txt")

        assert result["scanned"] is False
        assert result["clean"] is True
        assert result["threat"] is None


# ══════════════════════════════════════════════════════════════════════════════
# SCAN WITH CLAMAV — RESULTS
# ══════════════════════════════════════════════════════════════════════════════


class TestScanWithClamavResults:
    """Test various ClamAV scan result scenarios."""

    def _make_connected_clamd(self, scan_return=None, scan_raises=None):
        """Create a mock clamd with a connected TCP socket."""
        mock_clamd = MagicMock()

        # Unix fails
        unix_socket = MagicMock()
        unix_socket.ping.side_effect = ConnectionError("unix down")
        mock_clamd.ClamdUnixSocket.return_value = unix_socket

        # TCP succeeds
        tcp_socket = MagicMock()
        if scan_raises:
            tcp_socket.scan.side_effect = scan_raises
        else:
            tcp_socket.scan.return_value = scan_return
        mock_clamd.ClamdNetworkSocket.return_value = tcp_socket

        return mock_clamd

    def test_scan_returns_none_is_clean(self):
        """scan returns None: scanned=True, clean=True."""
        mock_clamd = self._make_connected_clamd(scan_return=None)

        with patch.dict(sys.modules, {"clamd": mock_clamd}):
            from app.services.quarantine import scan_with_clamav

            result = scan_with_clamav("/fake/file.txt")

        assert result == {"scanned": True, "clean": True, "threat": None}

    def test_scan_returns_ok(self):
        """scan returns ('OK', ...): clean=True."""
        filepath = "/fake/file.txt"
        mock_clamd = self._make_connected_clamd(scan_return={filepath: ("OK", None)})

        with patch.dict(sys.modules, {"clamd": mock_clamd}):
            from app.services.quarantine import scan_with_clamav

            result = scan_with_clamav(filepath)

        assert result["scanned"] is True
        assert result["clean"] is True
        assert result["threat"] is None

    def test_scan_returns_found_threat(self):
        """scan returns ('FOUND', 'Eicar'): clean=False, threat='Eicar'."""
        filepath = "/fake/file.txt"
        mock_clamd = self._make_connected_clamd(scan_return={filepath: ("FOUND", "Eicar")})

        with patch.dict(sys.modules, {"clamd": mock_clamd}):
            from app.services.quarantine import scan_with_clamav

            result = scan_with_clamav(filepath)

        assert result["scanned"] is True
        assert result["clean"] is False
        assert result["threat"] == "Eicar"

    def test_scan_raises_exception(self):
        """scan raises exception: scanned=False, clean=True."""
        mock_clamd = self._make_connected_clamd(scan_raises=RuntimeError("scan crashed"))

        with patch.dict(sys.modules, {"clamd": mock_clamd}):
            from app.services.quarantine import scan_with_clamav

            result = scan_with_clamav("/fake/file.txt")

        assert result["scanned"] is False
        assert result["clean"] is True
        assert result["threat"] is None


# ══════════════════════════════════════════════════════════════════════════════
# QUARANTINE FILE EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════


class TestQuarantineFileEdgeCases:
    """Test quarantine_file edge cases."""

    def test_quarantine_file_logs_audit_event(self, tmp_path):
        """quarantine_file logs audit event."""
        # Create a file to quarantine
        src = tmp_path / "malware.exe"
        src.write_bytes(b"evil content")

        with (
            patch("app.services.quarantine.QUARANTINE_DIR", tmp_path / "quarantine"),
            patch("app.services.quarantine.log_audit_event") as mock_audit,
        ):
            from app.services.quarantine import quarantine_file

            result = quarantine_file(src, reason="virus detected", threat="Eicar")

        assert result is not None
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args
        assert call_args[0][0] == "file_quarantined"
        assert call_args[1]["reason"] == "virus detected"
        assert call_args[1]["filename"] == "malware.exe"

    def test_quarantine_file_returns_none_when_source_missing(self, tmp_path):
        """quarantine_file returns None when source doesn't exist."""
        nonexistent = tmp_path / "does_not_exist.txt"

        with patch("app.services.quarantine.QUARANTINE_DIR", tmp_path / "quarantine"):
            from app.services.quarantine import quarantine_file

            result = quarantine_file(nonexistent, reason="test")

        assert result is None
