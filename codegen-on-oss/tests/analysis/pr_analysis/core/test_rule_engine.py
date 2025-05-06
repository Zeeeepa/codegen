"""
Tests for the Rule Engine
"""

import unittest
from unittest.mock import Mock
from codegen_on_oss.analysis.pr_analysis.core.rule_engine import RuleEngine
from codegen_on_oss.analysis.pr_analysis.rules.base_rule import AnalysisResult


class TestRuleEngine(unittest.TestCase):
    def setUp(self):
        self.rule1 = Mock()
        self.rule1.rule_id = "rule1"
        self.rule1.category = "category1"
        self.rule1.apply.return_value = [AnalysisResult("rule1", "error", "Error message")]
        
        self.rule2 = Mock()
        self.rule2.rule_id = "rule2"
        self.rule2.category = "category2"
        self.rule2.apply.return_value = [
            AnalysisResult("rule2", "warning", "Warning message"),
            AnalysisResult("rule2", "info", "Info message")
        ]
        
        self.engine = RuleEngine([self.rule1, self.rule2])
        
    def test_apply_rules(self):
        # Mock context
        context = Mock()
        
        # Call the method under test
        results = self.engine.apply_rules(context)
        
        # Verify the results
        self.rule1.apply.assert_called_once_with(context)
        self.rule2.apply.assert_called_once_with(context)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].rule_id, "rule1")
        self.assertEqual(results[0].severity, "error")
        self.assertEqual(results[1].rule_id, "rule2")
        self.assertEqual(results[1].severity, "warning")
        self.assertEqual(results[2].rule_id, "rule2")
        self.assertEqual(results[2].severity, "info")
    
    def test_get_rule_by_id(self):
        # Call the method under test
        rule = self.engine.get_rule_by_id("rule1")
        
        # Verify the results
        self.assertEqual(rule, self.rule1)
        
        # Test with non-existent rule
        rule = self.engine.get_rule_by_id("non-existent")
        self.assertIsNone(rule)
    
    def test_get_rules_by_category(self):
        # Call the method under test
        rules = self.engine.get_rules_by_category("category1")
        
        # Verify the results
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0], self.rule1)
        
        # Test with non-existent category
        rules = self.engine.get_rules_by_category("non-existent")
        self.assertEqual(len(rules), 0)
    
    def test_get_all_rules(self):
        # Call the method under test
        rules = self.engine.get_all_rules()
        
        # Verify the results
        self.assertEqual(len(rules), 2)
        self.assertEqual(rules[0], self.rule1)
        self.assertEqual(rules[1], self.rule2)
    
    def test_get_rule_categories(self):
        # Call the method under test
        categories = self.engine.get_rule_categories()
        
        # Verify the results
        self.assertEqual(len(categories), 2)
        self.assertIn("category1", categories)
        self.assertIn("category2", categories)
    
    def test_rule_error_handling(self):
        # Create a rule that raises an exception
        rule3 = Mock()
        rule3.rule_id = "rule3"
        rule3.apply.side_effect = Exception("Test exception")
        
        # Add the rule to the engine
        self.engine.register_rule(rule3)
        
        # Mock context
        context = Mock()
        
        # Call the method under test
        results = self.engine.apply_rules(context)
        
        # Verify the results
        self.assertEqual(len(results), 4)  # 3 from the first two rules, 1 error from rule3
        self.assertEqual(results[3].rule_id, "rule3")
        self.assertEqual(results[3].severity, "error")
        self.assertTrue("Test exception" in results[3].message)

