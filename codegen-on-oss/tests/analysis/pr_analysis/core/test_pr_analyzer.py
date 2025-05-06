"""
Tests for the PR Analyzer
"""

import unittest
from unittest.mock import Mock, patch
from codegen_on_oss.analysis.pr_analysis.core.pr_analyzer import PRAnalyzer


class TestPRAnalyzer(unittest.TestCase):
    def setUp(self):
        self.github_client = Mock()
        self.rule_engine = Mock()
        self.report_generator = Mock()
        self.analyzer = PRAnalyzer(self.github_client, self.rule_engine, self.report_generator)
        
    def test_analyze_pr(self):
        # Mock PR data
        pr_data = Mock()
        pr_data.base = Mock()
        pr_data.head = Mock()
        
        # Mock GitHub client
        self.github_client.get_pr.return_value = pr_data
        
        # Mock rule engine
        self.rule_engine.apply_rules.return_value = ["result1", "result2"]
        
        # Mock report generator
        self.report_generator.generate_report.return_value = {"report": "data"}
        
        # Mock _create_analysis_context
        self.analyzer._create_analysis_context = Mock()
        self.analyzer._create_analysis_context.side_effect = lambda x: x
        
        # Call the method under test
        results = self.analyzer.analyze_pr(123, "repo")
        
        # Verify the results
        self.github_client.get_pr.assert_called_once_with(123, "repo")
        self.rule_engine.apply_rules.assert_called_once()
        self.report_generator.generate_report.assert_called_once_with(["result1", "result2"], pr_data)
        self.assertEqual(results, {"report": "data"})
    
    @patch('codegen_on_oss.analysis.pr_analysis.core.pr_analyzer.tempfile.mkdtemp')
    @patch('codegen_on_oss.analysis.pr_analysis.core.pr_analyzer.subprocess.run')
    @patch('codegen_on_oss.analysis.pr_analysis.utils.integration.create_codebase_context')
    def test_create_analysis_context(self, mock_create_codebase_context, mock_run, mock_mkdtemp):
        # Mock tempfile.mkdtemp
        mock_mkdtemp.return_value = "/tmp/test"
        
        # Mock subprocess.run
        mock_run.return_value = Mock()
        
        # Mock create_codebase_context
        mock_codebase = Mock()
        mock_create_codebase_context.return_value = mock_codebase
        
        # Mock PR part context
        pr_part = Mock()
        pr_part.repo_name = "owner/repo"
        pr_part.ref = "main"
        
        # Call the method under test
        context = self.analyzer._create_analysis_context(pr_part)
        
        # Verify the results
        mock_mkdtemp.assert_called_once()
        self.assertEqual(mock_run.call_count, 2)  # One for clone, one for checkout
        mock_create_codebase_context.assert_called_once_with("/tmp/test")
        self.assertEqual(context.codebase, mock_codebase)
        self.assertEqual(context.pr_data, pr_part)
    
    def test_comment_on_pr(self):
        # Mock report generator
        self.report_generator.format_report_as_markdown.return_value = "markdown"
        
        # Call the method under test
        self.analyzer.comment_on_pr(123, "repo", {"report": "data"})
        
        # Verify the results
        self.report_generator.format_report_as_markdown.assert_called_once_with({"report": "data"})
        self.github_client.comment_on_pr.assert_called_once_with(123, "repo", "markdown")

