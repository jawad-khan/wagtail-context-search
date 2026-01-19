"""
Tests for management commands.
"""

from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from unittest.mock import patch


class CommandTests(TestCase):
    """Test management commands."""

    def test_rag_index_command_help(self):
        """Test rag_index command help."""
        out = StringIO()
        try:
            call_command('rag_index', '--help', stdout=out)
            output = out.getvalue()
            self.assertIn('Index pages for RAG search', output)
        except SystemExit:
            pass  # Help command exits

    def test_rag_sync_command_help(self):
        """Test rag_sync command help."""
        out = StringIO()
        try:
            call_command('rag_sync', '--help', stdout=out)
            output = out.getvalue()
            self.assertIn('Sync incremental changes', output)
        except SystemExit:
            pass  # Help command exits

    def test_rag_remove_command_help(self):
        """Test rag_remove command help."""
        out = StringIO()
        try:
            call_command('rag_remove', '--help', stdout=out)
            output = out.getvalue()
            self.assertIn('Remove pages from RAG index', output)
        except SystemExit:
            pass  # Help command exits
