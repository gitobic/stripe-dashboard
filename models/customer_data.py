import json
import streamlit as st
from pathlib import Path
from datetime import datetime
from config.settings import DATA_DIR, TAGS_FILE

def get_tags_file_path():
    """Get the path to the tags storage file"""
    return Path(TAGS_FILE)

def ensure_data_directory():
    """Ensure the data directory exists"""
    Path(DATA_DIR).mkdir(exist_ok=True)

def load_tags_and_notes():
    """Load tags and notes from JSON file"""
    ensure_data_directory()
    tags_file = get_tags_file_path()
    
    if tags_file.exists():
        try:
            with open(tags_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    return {
        "customer_tags": {},
        "customer_notes": {},
        "transaction_tags": {},
        "transaction_notes": {},
        "tag_definitions": {
            "VIP": {"color": "green", "description": "High-value customer"},
            "Refund Risk": {"color": "red", "description": "Customer with refund history"},
            "New Customer": {"color": "blue", "description": "Recently acquired customer"},
            "Payment Issues": {"color": "orange", "description": "Has payment problems"}
        }
    }

def save_tags_and_notes(data):
    """Save tags and notes to JSON file"""
    ensure_data_directory()
    tags_file = get_tags_file_path()
    
    try:
        with open(tags_file, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving tags: {str(e)}")
        return False

def add_customer_tag(customer_id, tag):
    """Add a tag to a customer"""
    data = load_tags_and_notes()
    if customer_id not in data["customer_tags"]:
        data["customer_tags"][customer_id] = []
    
    if tag not in data["customer_tags"][customer_id]:
        data["customer_tags"][customer_id].append(tag)
    
    # Always save to ensure consistency
    save_tags_and_notes(data)

def remove_customer_tag(customer_id, tag):
    """Remove a tag from a customer"""
    data = load_tags_and_notes()
    if customer_id in data["customer_tags"] and tag in data["customer_tags"][customer_id]:
        data["customer_tags"][customer_id].remove(tag)
        save_tags_and_notes(data)

def add_customer_note(customer_id, note):
    """Add a note to a customer"""
    data = load_tags_and_notes()
    if customer_id not in data["customer_notes"]:
        data["customer_notes"][customer_id] = []
    
    note_entry = {
        "note": note,
        "timestamp": datetime.now().isoformat(),
        "user": "Dashboard User"
    }
    data["customer_notes"][customer_id].append(note_entry)
    save_tags_and_notes(data)

def get_customer_tags(customer_id):
    """Get all tags for a customer"""
    data = load_tags_and_notes()
    return data["customer_tags"].get(customer_id, [])

def get_customer_notes(customer_id):
    """Get all notes for a customer"""
    data = load_tags_and_notes()
    return data["customer_notes"].get(customer_id, [])

def search_customers_by_tag(tag):
    """Find all customers with a specific tag"""
    data = load_tags_and_notes()
    customers_with_tag = []
    for customer_id, tags in data["customer_tags"].items():
        if tag in tags:
            customers_with_tag.append(customer_id)
    return customers_with_tag