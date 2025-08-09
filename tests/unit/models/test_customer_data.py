"""Tests for customer_data model"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from models.customer_data import (
    load_tags_and_notes,
    save_tags_and_notes,
    add_customer_tag,
    remove_customer_tag,
    add_customer_note,
    get_customer_tags,
    get_customer_notes,
    search_customers_by_tag
)

class TestLoadTagsAndNotes:
    """Tests for load_tags_and_notes function"""
    
    @patch('models.customer_data.Path.exists')
    def test_load_default_structure_when_file_not_exists(self, mock_exists):
        """Test loading default structure when file doesn't exist"""
        mock_exists.return_value = False
        
        result = load_tags_and_notes()
        
        assert 'customer_tags' in result
        assert 'customer_notes' in result
        assert 'tag_definitions' in result
        assert isinstance(result['customer_tags'], dict)
        assert isinstance(result['customer_notes'], dict)
        assert 'VIP' in result['tag_definitions']
    
    @patch('models.customer_data.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_existing_data(self, mock_file, mock_exists):
        """Test loading existing data from file"""
        mock_exists.return_value = True
        test_data = {
            "customer_tags": {"cus_123": ["VIP"]},
            "customer_notes": {"cus_123": [{"note": "Good customer", "timestamp": "2023-01-01"}]},
            "tag_definitions": {"VIP": {"color": "green"}}
        }
        mock_file.return_value.read.return_value = json.dumps(test_data)
        
        result = load_tags_and_notes()
        
        assert result['customer_tags']['cus_123'] == ["VIP"]
        assert len(result['customer_notes']['cus_123']) == 1
    
    @patch('models.customer_data.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_corrupted_file_returns_default(self, mock_file, mock_exists):
        """Test that corrupted file returns default structure"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "invalid json"
        
        result = load_tags_and_notes()
        
        # Should return default structure when JSON is invalid
        assert 'customer_tags' in result
        assert result['customer_tags'] == {}

class TestSaveTagsAndNotes:
    """Tests for save_tags_and_notes function"""
    
    @patch('models.customer_data.ensure_data_directory')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_data_success(self, mock_file, mock_ensure_dir):
        """Test successful data saving"""
        test_data = {"customer_tags": {"cus_123": ["VIP"]}}
        
        result = save_tags_and_notes(test_data)
        
        assert result is True
        mock_file.assert_called_once()
        mock_ensure_dir.assert_called_once()
    
    @patch('models.customer_data.ensure_data_directory')
    @patch('builtins.open', side_effect=Exception("Write error"))
    @patch('streamlit.error')  # Mock streamlit error function
    def test_save_data_failure(self, mock_st_error, mock_file, mock_ensure_dir):
        """Test data saving failure handling"""
        test_data = {"customer_tags": {"cus_123": ["VIP"]}}
        
        result = save_tags_and_notes(test_data)
        
        assert result is False
        mock_st_error.assert_called_once()

class TestCustomerTagOperations:
    """Tests for customer tag operations"""
    
    @patch('models.customer_data.load_tags_and_notes')
    @patch('models.customer_data.save_tags_and_notes')
    def test_add_customer_tag_new_customer(self, mock_save, mock_load):
        """Test adding tag to new customer"""
        mock_load.return_value = {"customer_tags": {}}
        mock_save.return_value = True
        
        add_customer_tag("cus_123", "VIP")
        
        # Verify save was called with correct data
        mock_save.assert_called_once()
        saved_data = mock_save.call_args[0][0]
        assert "cus_123" in saved_data["customer_tags"]
        assert "VIP" in saved_data["customer_tags"]["cus_123"]
    
    @patch('models.customer_data.load_tags_and_notes')
    @patch('models.customer_data.save_tags_and_notes')
    def test_add_customer_tag_existing_customer(self, mock_save, mock_load):
        """Test adding tag to existing customer"""
        mock_load.return_value = {"customer_tags": {"cus_123": ["VIP"]}}
        mock_save.return_value = True
        
        add_customer_tag("cus_123", "New Customer")
        
        saved_data = mock_save.call_args[0][0]
        assert len(saved_data["customer_tags"]["cus_123"]) == 2
        assert "New Customer" in saved_data["customer_tags"]["cus_123"]
    
    @patch('models.customer_data.load_tags_and_notes')
    @patch('models.customer_data.save_tags_and_notes')
    def test_add_duplicate_tag_ignored(self, mock_save, mock_load):
        """Test that duplicate tags are ignored"""
        mock_load.return_value = {"customer_tags": {"cus_123": ["VIP"]}}
        mock_save.return_value = True
        
        add_customer_tag("cus_123", "VIP")  # Same tag again
        
        saved_data = mock_save.call_args[0][0]
        assert len(saved_data["customer_tags"]["cus_123"]) == 1
    
    @patch('models.customer_data.load_tags_and_notes')
    @patch('models.customer_data.save_tags_and_notes')
    def test_remove_customer_tag(self, mock_save, mock_load):
        """Test removing customer tag"""
        mock_load.return_value = {"customer_tags": {"cus_123": ["VIP", "New Customer"]}}
        mock_save.return_value = True
        
        remove_customer_tag("cus_123", "VIP")
        
        saved_data = mock_save.call_args[0][0]
        assert "VIP" not in saved_data["customer_tags"]["cus_123"]
        assert "New Customer" in saved_data["customer_tags"]["cus_123"]

class TestCustomerNoteOperations:
    """Tests for customer note operations"""
    
    @patch('models.customer_data.load_tags_and_notes')
    @patch('models.customer_data.save_tags_and_notes')
    @patch('models.customer_data.datetime')
    def test_add_customer_note(self, mock_datetime, mock_save, mock_load):
        """Test adding customer note"""
        mock_load.return_value = {"customer_notes": {}}
        mock_save.return_value = True
        mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T12:00:00"
        
        add_customer_note("cus_123", "Great customer service interaction")
        
        saved_data = mock_save.call_args[0][0]
        assert "cus_123" in saved_data["customer_notes"]
        note = saved_data["customer_notes"]["cus_123"][0]
        assert note["note"] == "Great customer service interaction"
        assert note["timestamp"] == "2023-01-01T12:00:00"
        assert note["user"] == "Dashboard User"

class TestCustomerDataRetrieval:
    """Tests for customer data retrieval functions"""
    
    @patch('models.customer_data.load_tags_and_notes')
    def test_get_customer_tags_existing(self, mock_load):
        """Test getting tags for existing customer"""
        mock_load.return_value = {"customer_tags": {"cus_123": ["VIP", "Premium"]}}
        
        result = get_customer_tags("cus_123")
        
        assert result == ["VIP", "Premium"]
    
    @patch('models.customer_data.load_tags_and_notes')
    def test_get_customer_tags_nonexistent(self, mock_load):
        """Test getting tags for non-existent customer"""
        mock_load.return_value = {"customer_tags": {}}
        
        result = get_customer_tags("cus_999")
        
        assert result == []
    
    @patch('models.customer_data.load_tags_and_notes')
    def test_get_customer_notes_existing(self, mock_load):
        """Test getting notes for existing customer"""
        notes = [{"note": "Test note", "timestamp": "2023-01-01"}]
        mock_load.return_value = {"customer_notes": {"cus_123": notes}}
        
        result = get_customer_notes("cus_123")
        
        assert result == notes
    
    @patch('models.customer_data.load_tags_and_notes')
    def test_search_customers_by_tag(self, mock_load):
        """Test searching customers by tag"""
        mock_load.return_value = {
            "customer_tags": {
                "cus_123": ["VIP", "Premium"],
                "cus_456": ["VIP"],
                "cus_789": ["Premium"]
            }
        }
        
        result = search_customers_by_tag("VIP")
        
        assert "cus_123" in result
        assert "cus_456" in result
        assert "cus_789" not in result
        assert len(result) == 2