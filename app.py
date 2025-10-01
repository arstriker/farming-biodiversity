from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io
from datetime import datetime, timedelta
import uuid
import shutil
import glob
from werkzeug.utils import secure_filename

# Import logging system
try:
    from diary_logger import diary_logger, log_errors, log_performance
    LOGGING_ENABLED = True
except ImportError:
    print("Warning: Diary logging system not available")
    LOGGING_ENABLED = False
    
    # Create dummy decorators if logging not available
    def log_errors(func):
        return func
    
    def log_performance(operation_name=None):
        def decorator(func):
            return func
        return decorator

# Load environment variables from .env file
# Try to load from current directory first
load_dotenv('.env')
# Also try the default behavior
load_dotenv()

app = Flask(__name__)

# --- Gemini API Configuration ---
api_key = os.getenv("GEMINI_API_KEY")

if not api_key or api_key == "YOUR_API_KEY_HERE":
    print("WARNING: GEMINI_API_KEY not found or not set. Please set it in your .env file.")
else:
    print("✅ Gemini API configured successfully!")
    genai.configure(api_key=api_key)

# --- Historical Data ---
try:
    with open('history.json', 'r') as f:
        historical_data = json.load(f)
except FileNotFoundError:
    historical_data = {"history": "No historical data found. Please create a history.json file."}
except json.JSONDecodeError:
    historical_data = {"history": "Error decoding history.json."}

# --- Plant Database ---
try:
    with open('plant_database.json', 'r') as f:
        plant_database = json.load(f)
except FileNotFoundError:
    plant_database = {"plants": {}, "error": "Plant database not found."}
except json.JSONDecodeError:
    plant_database = {"plants": {}, "error": "Error decoding plant database."}

# --- Crop and Growth Stage Categories ---
CROP_CATEGORIES = {
    "vegetables": {
        "name": "Vegetables",
        "icon": "fas fa-carrot",
        "color": "#22c55e",
        "crops": ["tomato", "potato", "onion", "carrot", "lettuce", "cucumber", "pepper", "broccoli", "spinach", "cabbage"]
    },
    "fruits": {
        "name": "Fruits", 
        "icon": "fas fa-apple-alt",
        "color": "#f59e0b",
        "crops": ["apple", "orange", "banana", "strawberry", "grape", "peach", "pear", "cherry", "plum", "blueberry"]
    },
    "grains": {
        "name": "Grains",
        "icon": "fas fa-seedling",
        "color": "#8b5cf6", 
        "crops": ["rice", "wheat", "corn", "barley", "oats", "quinoa", "millet", "sorghum", "rye", "buckwheat"]
    },
    "herbs": {
        "name": "Herbs",
        "icon": "fas fa-leaf",
        "color": "#10b981",
        "crops": ["basil", "mint", "cilantro", "parsley", "oregano", "thyme", "rosemary", "sage", "dill", "chives"]
    },
    "legumes": {
        "name": "Legumes",
        "icon": "fas fa-circle",
        "color": "#ef4444",
        "crops": ["beans", "peas", "lentils", "chickpeas", "soybeans", "peanuts", "alfalfa", "clover"]
    }
}

GROWTH_STAGES = {
    "seed": {
        "name": "Seed/Planting",
        "icon": "fas fa-circle",
        "color": "#8b5cf6",
        "description": "Initial planting stage"
    },
    "germination": {
        "name": "Germination", 
        "icon": "fas fa-seedling",
        "color": "#06b6d4",
        "description": "Seeds sprouting and emerging"
    },
    "seedling": {
        "name": "Seedling",
        "icon": "fas fa-sprout",
        "color": "#10b981",
        "description": "Young plants with first leaves"
    },
    "vegetative": {
        "name": "Vegetative Growth",
        "icon": "fas fa-leaf",
        "color": "#22c55e",
        "description": "Active leaf and stem growth"
    },
    "flowering": {
        "name": "Flowering",
        "icon": "fas fa-flower",
        "color": "#f59e0b",
        "description": "Flower development and blooming"
    },
    "fruit": {
        "name": "Fruit Development",
        "icon": "fas fa-apple-alt",
        "color": "#ef4444",
        "description": "Fruit formation and development"
    },
    "harvest": {
        "name": "Harvest",
        "icon": "fas fa-cut",
        "color": "#8b5cf6",
        "description": "Ready for harvesting"
    },
    "post-harvest": {
        "name": "Post-Harvest",
        "icon": "fas fa-archive",
        "color": "#6b7280",
        "description": "After harvest activities"
    }
}

def get_crop_category(crop_name):
    """Get the category information for a given crop."""
    crop_lower = crop_name.lower()
    for category_key, category_data in CROP_CATEGORIES.items():
        if crop_lower in category_data["crops"]:
            return {
                "key": category_key,
                "name": category_data["name"],
                "icon": category_data["icon"],
                "color": category_data["color"]
            }
    return {
        "key": "custom",
        "name": "Custom",
        "icon": "fas fa-question-circle",
        "color": "#6b7280"
    }

def get_growth_stage_info(stage_key):
    """Get the information for a given growth stage."""
    stage_lower = stage_key.lower()
    if stage_lower in GROWTH_STAGES:
        return GROWTH_STAGES[stage_lower]
    return {
        "name": stage_key.title(),
        "icon": "fas fa-question-circle",
        "color": "#6b7280",
        "description": "Custom growth stage"
    }

def load_custom_categories():
    """Load custom crop categories from file."""
    try:
        with open('custom_categories.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"custom_crops": [], "custom_stages": []}
    except json.JSONDecodeError:
        return {"custom_crops": [], "custom_stages": []}

def save_custom_categories(custom_data):
    """Save custom crop categories to file."""
    try:
        with open('custom_categories.json', 'w') as f:
            json.dump(custom_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving custom categories: {e}")
        return False

# --- User Data Storage ---
def save_user_data(user_data):
    """Save user input data to JSON file for analysis and improvement."""
    try:
        # Load existing data
        try:
            with open('user_data.json', 'r') as f:
                existing_data = json.load(f)
        except FileNotFoundError:
            existing_data = {"sessions": []}
        except json.JSONDecodeError:
            existing_data = {"sessions": []}
        
        # Add new session data
        existing_data["sessions"].append(user_data)
        
        # Keep only last 100 sessions to prevent file from growing too large
        if len(existing_data["sessions"]) > 100:
            existing_data["sessions"] = existing_data["sessions"][-100:]
        
        # Save updated data
        with open('user_data.json', 'w') as f:
            json.dump(existing_data, f, indent=2)
            
    except Exception as e:
        print(f"Error saving user data: {e}")
        # Don't fail the main request if logging fails

# --- Diary Data Storage with Caching ---
# Simple in-memory cache for diary data
_diary_cache = {
    'data': None,
    'last_modified': None,
    'cache_time': None
}

CACHE_DURATION = 30  # Cache for 30 seconds

def get_file_modified_time(filepath):
    """Get the last modified time of a file."""
    try:
        return os.path.getmtime(filepath)
    except OSError:
        return None

@log_errors
@log_performance('load_diary_entries')
def load_diary_entries():
    """Load diary entries from JSON file with caching."""
    global _diary_cache
    
    try:
        # Check if cache is valid
        current_time = datetime.now().timestamp()
        file_modified = get_file_modified_time('diary_data.json')
        
        # Use cache if it's fresh and file hasn't been modified
        if (_diary_cache['data'] is not None and 
            _diary_cache['cache_time'] is not None and
            current_time - _diary_cache['cache_time'] < CACHE_DURATION and
            _diary_cache['last_modified'] == file_modified):
            return _diary_cache['data']
        
        # Load fresh data from file
        with open('diary_data.json', 'r') as f:
            diary_data = json.load(f)
        
        # Update cache
        _diary_cache['data'] = diary_data
        _diary_cache['last_modified'] = file_modified
        _diary_cache['cache_time'] = current_time
        
        return diary_data
    except FileNotFoundError:
        # Create initial diary data structure if file doesn't exist
        initial_data = {
            "entries": [],
            "metadata": {
                "total_entries": 0,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        # Create the file
        try:
            with open('diary_data.json', 'w') as f:
                json.dump(initial_data, f, indent=2)
        except Exception as e:
            print(f"Error creating diary_data.json: {e}")
        return initial_data
    except json.JSONDecodeError:
        print("Error: diary_data.json contains invalid JSON - attempting recovery")
        
        # Attempt automatic recovery from backup
        recovery_result = recover_from_backup('diary_data.json')
        if recovery_result["success"]:
            print("Successfully recovered diary data from backup")
            # Try loading again after recovery
            try:
                with open('diary_data.json', 'r') as f:
                    diary_data = json.load(f)
                return diary_data
            except:
                pass
        
        # If recovery failed, return error structure
        return {
            "entries": [],
            "metadata": {
                "total_entries": 0,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
                "error": "JSON decode error - file may be corrupted",
                "recovery_attempted": True,
                "recovery_success": recovery_result["success"]
            }
        }
    except Exception as e:
        print(f"Error loading diary entries: {e}")
        return {
            "entries": [],
            "metadata": {
                "total_entries": 0,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
                "error": str(e)
            }
        }

def invalidate_diary_cache():
    """Invalidate the diary data cache."""
    global _diary_cache
    _diary_cache['data'] = None
    _diary_cache['last_modified'] = None
    _diary_cache['cache_time'] = None

@log_errors
@log_performance('save_diary_entry')
def save_diary_entry(entry_data):
    """Save a diary entry to JSON file with proper error handling."""
    try:
        # Validate entry data structure
        if not isinstance(entry_data, dict):
            return {"success": False, "error": "Invalid entry data format", "message": "Entry data must be a dictionary"}
        
        # Load existing diary data
        diary_data = load_diary_entries()
        
        # Check if loading failed
        if "error" in diary_data.get("metadata", {}):
            return {"success": False, "error": "Data storage error", "message": "Failed to load existing diary data"}
        
        # Generate unique ID for the entry
        entry_id = str(uuid.uuid4())
        
        # Get category information for the crop
        crop_category = get_crop_category(entry_data.get('crop_type', ''))
        growth_stage_info = get_growth_stage_info(entry_data.get('growth_stage', ''))
        
        # Create the entry with required fields and validation
        new_entry = {
            "id": entry_id,
            "timestamp": datetime.now().isoformat(),
            "date": entry_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            "crop_type": entry_data.get('crop_type', ''),
            "crop_category": crop_category,
            "growth_stage": entry_data.get('growth_stage', ''),
            "growth_stage_info": growth_stage_info,
            "observations": entry_data.get('observations', ''),
            "photos": entry_data.get('photos', []),
            "weather": entry_data.get('weather', ''),
            "actions_taken": entry_data.get('actions_taken', []),
            "location": entry_data.get('location', ''),
            "user_notes": entry_data.get('user_notes', '')
        }
        
        # Validate entry data
        validation_errors = validate_entry_data(new_entry)
        if validation_errors:
            return {
                "success": False, 
                "error": "Validation failed", 
                "message": "Entry validation failed",
                "validation_errors": validation_errors
            }
        
        # Add the new entry to the list
        diary_data["entries"].append(new_entry)
        
        # Update metadata
        diary_data["metadata"]["total_entries"] = len(diary_data["entries"])
        diary_data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Save to file with backup and error handling
        backup_success = create_backup_file('diary_data.json')
        timestamped_backup = create_timestamped_backup('diary_data.json')
        if not backup_success:
            print("Warning: Could not create backup file")
        if not timestamped_backup:
            print("Warning: Could not create timestamped backup file")
        
        # Attempt to save with atomic write
        temp_filename = 'diary_data.json.tmp'
        try:
            with open(temp_filename, 'w') as f:
                json.dump(diary_data, f, indent=2)
            
            # Atomic move
            if os.path.exists('diary_data.json'):
                os.replace(temp_filename, 'diary_data.json')
            else:
                os.rename(temp_filename, 'diary_data.json')
                
        except Exception as save_error:
            # Clean up temp file if it exists
            if os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                except:
                    pass
            raise save_error
        
        # Invalidate cache after successful save
        invalidate_diary_cache()
        
        return {"success": True, "entry_id": entry_id, "message": "Diary entry saved successfully"}
        
    except PermissionError as e:
        print(f"Permission error saving diary entry: {e}")
        return {"success": False, "error": "Permission denied", "message": "Unable to save diary entry due to file permissions"}
    except OSError as e:
        print(f"OS error saving diary entry: {e}")
        return {"success": False, "error": "File system error", "message": "Unable to save diary entry due to storage issues"}
    except (ValueError, TypeError) as e:
        print(f"JSON encoding error saving diary entry: {e}")
        return {"success": False, "error": "Data encoding error", "message": "Failed to encode diary entry data"}
    except Exception as e:
        print(f"Unexpected error saving diary entry: {e}")
        return {"success": False, "error": str(e), "message": "An unexpected error occurred while saving diary entry"}

def validate_entry_data(entry):
    """Validate diary entry data and return list of errors."""
    errors = []
    
    # Required fields validation
    if not entry.get('crop_type', '').strip():
        errors.append("Crop type is required")
    
    if not entry.get('observations', '').strip():
        errors.append("Observations are required")
    
    # Date validation
    date_str = entry.get('date', '')
    if date_str:
        try:
            entry_date = datetime.fromisoformat(date_str).date()
            today = datetime.now().date()
            if entry_date > today:
                errors.append("Entry date cannot be in the future")
        except ValueError:
            errors.append("Invalid date format")
    
    # Length validations
    if len(entry.get('crop_type', '')) > 100:
        errors.append("Crop type must be 100 characters or less")
    
    if len(entry.get('growth_stage', '')) > 50:
        errors.append("Growth stage must be 50 characters or less")
    
    if len(entry.get('observations', '')) > 2000:
        errors.append("Observations must be 2000 characters or less")
    
    if len(entry.get('weather', '')) > 200:
        errors.append("Weather description must be 200 characters or less")
    
    if len(entry.get('location', '')) > 200:
        errors.append("Location must be 200 characters or less")
    
    if len(entry.get('user_notes', '')) > 1000:
        errors.append("User notes must be 1000 characters or less")
    
    # Actions validation
    actions = entry.get('actions_taken', [])
    if not isinstance(actions, list):
        errors.append("Actions taken must be a list")
    elif len(actions) > 20:
        errors.append("Maximum 20 actions allowed per entry")
    else:
        for action in actions:
            if not isinstance(action, str) or len(action) > 100:
                errors.append("Each action must be a string of 100 characters or less")
    
    # Photos validation
    photos = entry.get('photos', [])
    if not isinstance(photos, list):
        errors.append("Photos must be a list")
    elif len(photos) > 10:
        errors.append("Maximum 10 photos allowed per entry")
    else:
        for photo in photos:
            if not isinstance(photo, str) or len(photo) > 500:
                errors.append("Each photo path must be a string of 500 characters or less")
    
    return errors

def create_backup_file(filename):
    """Create a backup of the specified file."""
    try:
        if os.path.exists(filename):
            backup_filename = f"{filename}.backup"
            shutil.copy2(filename, backup_filename)
            return True
    except Exception as e:
        print(f"Failed to create backup of {filename}: {e}")
        return False

def create_timestamped_backup(filename):
    """Create a timestamped backup of the specified file."""
    try:
        if os.path.exists(filename):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{filename}.backup_{timestamp}"
            shutil.copy2(filename, backup_filename)
            
            # Keep only the last 10 timestamped backups to prevent disk space issues
            cleanup_old_backups(filename)
            
            return backup_filename
    except Exception as e:
        print(f"Failed to create timestamped backup of {filename}: {e}")
        return None

def cleanup_old_backups(filename, max_backups=10):
    """Clean up old backup files, keeping only the most recent ones."""
    try:
        backup_pattern = f"{filename}.backup_*"
        backup_files = []
        
        # Find all backup files
        import glob
        for backup_file in glob.glob(backup_pattern):
            try:
                stat = os.stat(backup_file)
                backup_files.append((backup_file, stat.st_mtime))
            except OSError:
                continue
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old backups beyond the limit
        for backup_file, _ in backup_files[max_backups:]:
            try:
                os.remove(backup_file)
                print(f"Removed old backup: {backup_file}")
            except OSError as e:
                print(f"Failed to remove old backup {backup_file}: {e}")
                
    except Exception as e:
        print(f"Error cleaning up old backups: {e}")

def validate_json_file(filename):
    """Validate that a JSON file is properly formatted and contains expected structure."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # For diary data, validate expected structure
        if filename == 'diary_data.json':
            return validate_diary_data_structure(data)
        
        # For other JSON files, basic validation
        return {"valid": True, "errors": []}
        
    except FileNotFoundError:
        return {"valid": False, "errors": ["File not found"]}
    except json.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON format: {str(e)}"]}
    except Exception as e:
        return {"valid": False, "errors": [f"Validation error: {str(e)}"]}

def validate_diary_data_structure(data):
    """Validate the structure of diary data."""
    errors = []
    
    # Check top-level structure
    if not isinstance(data, dict):
        errors.append("Data must be a dictionary")
        return {"valid": False, "errors": errors}
    
    # Check required keys
    if "entries" not in data:
        errors.append("Missing 'entries' key")
    elif not isinstance(data["entries"], list):
        errors.append("'entries' must be a list")
    
    if "metadata" in data and not isinstance(data["metadata"], dict):
        errors.append("'metadata' must be a dictionary")
    
    # Validate individual entries
    if isinstance(data.get("entries"), list):
        for i, entry in enumerate(data["entries"]):
            entry_errors = validate_single_entry_structure(entry, i)
            errors.extend(entry_errors)
    
    return {"valid": len(errors) == 0, "errors": errors}

def validate_single_entry_structure(entry, index):
    """Validate the structure of a single diary entry."""
    errors = []
    prefix = f"Entry {index}: "
    
    if not isinstance(entry, dict):
        errors.append(f"{prefix}Entry must be a dictionary")
        return errors
    
    # Required fields
    required_fields = ["id", "timestamp", "date", "crop_type", "observations"]
    for field in required_fields:
        if field not in entry:
            errors.append(f"{prefix}Missing required field '{field}'")
        elif not isinstance(entry[field], str) or not entry[field].strip():
            errors.append(f"{prefix}Field '{field}' must be a non-empty string")
    
    # Optional list fields
    list_fields = ["photos", "actions_taken"]
    for field in list_fields:
        if field in entry and not isinstance(entry[field], list):
            errors.append(f"{prefix}Field '{field}' must be a list")
    
    # Validate timestamp format
    if "timestamp" in entry:
        try:
            datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            errors.append(f"{prefix}Invalid timestamp format")
    
    # Validate date format
    if "date" in entry:
        try:
            datetime.strptime(entry["date"], '%Y-%m-%d')
        except ValueError:
            errors.append(f"{prefix}Invalid date format (should be YYYY-MM-DD)")
    
    return errors

def recover_from_backup(filename):
    """Attempt to recover a file from its backup."""
    try:
        backup_filename = f"{filename}.backup"
        
        if not os.path.exists(backup_filename):
            return {"success": False, "error": "No backup file found"}
        
        # Validate the backup file first
        validation = validate_json_file(backup_filename)
        if not validation["valid"]:
            return {
                "success": False, 
                "error": "Backup file is also corrupted",
                "validation_errors": validation["errors"]
            }
        
        # Create a backup of the corrupted file before recovery
        if os.path.exists(filename):
            corrupted_backup = f"{filename}.corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(filename, corrupted_backup)
        
        # Restore from backup
        shutil.copy2(backup_filename, filename)
        
        # Invalidate cache if this is diary data
        if filename == 'diary_data.json':
            invalidate_diary_cache()
        
        return {"success": True, "message": "File recovered from backup successfully"}
        
    except Exception as e:
        return {"success": False, "error": f"Recovery failed: {str(e)}"}

def recover_from_timestamped_backup(filename, backup_timestamp=None):
    """Recover from a specific timestamped backup or the most recent one."""
    try:
        import glob
        
        if backup_timestamp:
            backup_filename = f"{filename}.backup_{backup_timestamp}"
            if not os.path.exists(backup_filename):
                return {"success": False, "error": f"Backup with timestamp {backup_timestamp} not found"}
        else:
            # Find the most recent timestamped backup
            backup_pattern = f"{filename}.backup_*"
            backup_files = []
            
            for backup_file in glob.glob(backup_pattern):
                try:
                    stat = os.stat(backup_file)
                    backup_files.append((backup_file, stat.st_mtime))
                except OSError:
                    continue
            
            if not backup_files:
                return {"success": False, "error": "No timestamped backups found"}
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            backup_filename = backup_files[0][0]
        
        # Validate the backup file
        validation = validate_json_file(backup_filename)
        if not validation["valid"]:
            return {
                "success": False,
                "error": "Selected backup file is corrupted",
                "validation_errors": validation["errors"]
            }
        
        # Create a backup of the current file before recovery
        if os.path.exists(filename):
            corrupted_backup = f"{filename}.corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(filename, corrupted_backup)
        
        # Restore from backup
        shutil.copy2(backup_filename, filename)
        
        # Invalidate cache if this is diary data
        if filename == 'diary_data.json':
            invalidate_diary_cache()
        
        return {
            "success": True, 
            "message": f"File recovered from backup {os.path.basename(backup_filename)} successfully"
        }
        
    except Exception as e:
        return {"success": False, "error": f"Recovery failed: {str(e)}"}

def export_diary_data(format_type='json', include_metadata=True):
    """Export diary data in various formats for user data portability."""
    try:
        diary_data = load_diary_entries()
        
        if "error" in diary_data.get("metadata", {}):
            return {"success": False, "error": "Cannot export corrupted data"}
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "export_format": format_type,
            "total_entries": len(diary_data.get("entries", [])),
            "entries": diary_data.get("entries", [])
        }
        
        if include_metadata:
            export_data["metadata"] = diary_data.get("metadata", {})
            export_data["custom_crops"] = diary_data.get("custom_crops", [])
            export_data["custom_stages"] = diary_data.get("custom_stages", [])
        
        if format_type.lower() == 'json':
            return {
                "success": True,
                "data": export_data,
                "filename": f"diary_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        elif format_type.lower() == 'csv':
            return export_diary_to_csv(export_data)
        else:
            return {"success": False, "error": f"Unsupported export format: {format_type}"}
            
    except Exception as e:
        return {"success": False, "error": f"Export failed: {str(e)}"}

def export_diary_to_csv(export_data):
    """Convert diary data to CSV format."""
    try:
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = [
            'ID', 'Timestamp', 'Date', 'Crop Type', 'Growth Stage', 
            'Observations', 'Weather', 'Location', 'Actions Taken', 'User Notes'
        ]
        writer.writerow(headers)
        
        # Write data rows
        for entry in export_data.get("entries", []):
            row = [
                entry.get('id', ''),
                entry.get('timestamp', ''),
                entry.get('date', ''),
                entry.get('crop_type', ''),
                entry.get('growth_stage', ''),
                entry.get('observations', ''),
                entry.get('weather', ''),
                entry.get('location', ''),
                ', '.join(entry.get('actions_taken', [])),
                entry.get('user_notes', '')
            ]
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return {
            "success": True,
            "data": csv_content,
            "filename": f"diary_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
        
    except Exception as e:
        return {"success": False, "error": f"CSV export failed: {str(e)}"}

def check_data_integrity():
    """Check the integrity of all data files and return a comprehensive report."""
    integrity_report = {
        "timestamp": datetime.now().isoformat(),
        "files_checked": [],
        "overall_status": "healthy",
        "issues_found": []
    }
    
    # Files to check
    files_to_check = [
        'diary_data.json',
        'user_data.json', 
        'plant_database.json',
        'custom_categories.json'
    ]
    
    for filename in files_to_check:
        file_report = {
            "filename": filename,
            "exists": os.path.exists(filename),
            "readable": False,
            "valid_json": False,
            "structure_valid": False,
            "size_bytes": 0,
            "last_modified": None,
            "backup_exists": os.path.exists(f"{filename}.backup"),
            "errors": []
        }
        
        try:
            if file_report["exists"]:
                # Check file stats
                stat = os.stat(filename)
                file_report["size_bytes"] = stat.st_size
                file_report["last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                # Check if readable
                try:
                    with open(filename, 'r') as f:
                        content = f.read()
                    file_report["readable"] = True
                    
                    # Check JSON validity
                    try:
                        data = json.loads(content)
                        file_report["valid_json"] = True
                        
                        # Structure validation
                        validation = validate_json_file(filename)
                        file_report["structure_valid"] = validation["valid"]
                        if not validation["valid"]:
                            file_report["errors"].extend(validation["errors"])
                            
                    except json.JSONDecodeError as e:
                        file_report["errors"].append(f"JSON decode error: {str(e)}")
                        
                except IOError as e:
                    file_report["errors"].append(f"File read error: {str(e)}")
            else:
                file_report["errors"].append("File does not exist")
                
        except Exception as e:
            file_report["errors"].append(f"Unexpected error: {str(e)}")
        
        # Determine if this file has issues
        if file_report["errors"] or not file_report["structure_valid"]:
            integrity_report["overall_status"] = "issues_found"
            integrity_report["issues_found"].extend([
                f"{filename}: {error}" for error in file_report["errors"]
            ])
        
        integrity_report["files_checked"].append(file_report)
    
    return integrity_report

def generate_unique_id():
    """Generate a unique identifier for diary entries."""
    return str(uuid.uuid4())

def get_climate_info_from_gps(gps_coordinates):
    """
    Get climate zone and growing information based on GPS coordinates.
    This is a simplified version - in production, you'd use a proper climate API.
    """
    if not gps_coordinates:
        return ""
    
    try:
        lat = gps_coordinates.get('latitude', 0)
        lon = gps_coordinates.get('longitude', 0)
        
        # Basic climate zone estimation based on latitude
        climate_info = []
        
        if abs(lat) <= 23.5:  # Tropical zone
            climate_info.append("Tropical climate zone - year-round growing season")
        elif abs(lat) <= 35:  # Subtropical
            climate_info.append("Subtropical climate - long growing season")
        elif abs(lat) <= 50:  # Temperate
            climate_info.append("Temperate climate - seasonal growing patterns")
        else:  # Cold/Arctic
            climate_info.append("Cold climate - short growing season")
        
        # Add hemisphere information
        if lat >= 0:
            climate_info.append("Northern hemisphere")
        else:
            climate_info.append("Southern hemisphere")
        
        return ". ".join(climate_info) + "."
        
    except Exception as e:
        print(f"Error getting climate info: {e}")
        return ""

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/admin')
def admin():
    """Renders the admin interface for managing plant database."""
    return render_template('admin.html')

@app.route('/diary')
def diary():
    """Renders the farming diary page for tracking crop growth and activities."""
    try:
        return render_template('diary.html')
    except Exception as e:
        print(f"Error rendering diary template: {e}")
        return jsonify({"error": "Failed to load diary page"}), 500

@app.route('/api/plants', methods=['GET'])
def get_plants():
    """Get all plants from the database."""
    return jsonify(plant_database)

@app.route('/api/plants/<plant_id>', methods=['GET'])
def get_plant(plant_id):
    """Get a specific plant by ID."""
    if plant_id in plant_database['plants']:
        return jsonify(plant_database['plants'][plant_id])
    return jsonify({"error": "Plant not found"}), 404

@app.route('/api/plants/<plant_id>', methods=['PUT'])
def update_plant(plant_id):
    """Update a specific plant."""
    try:
        data = request.get_json()
        plant_database['plants'][plant_id] = data
        
        # Save to file
        with open('plant_database.json', 'w') as f:
            json.dump(plant_database, f, indent=2)
        
        return jsonify({"message": "Plant updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/plants/<plant_id>', methods=['DELETE'])
def delete_plant(plant_id):
    """Delete a specific plant."""
    try:
        if plant_id in plant_database['plants']:
            del plant_database['plants'][plant_id]
            
            # Save to file
            with open('plant_database.json', 'w') as f:
                json.dump(plant_database, f, indent=2)
            
            return jsonify({"message": "Plant deleted successfully"})
        return jsonify({"error": "Plant not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/plants', methods=['POST'])
def add_plant():
    """Add a new plant to the database."""
    try:
        data = request.get_json()
        plant_id = data.get('id', '').lower().replace(' ', '_')
        
        if not plant_id:
            return jsonify({"error": "Plant ID is required"}), 400
        
        if plant_id in plant_database['plants']:
            return jsonify({"error": "Plant already exists"}), 400
        
        # Remove the ID from the data before storing
        plant_data = {k: v for k, v in data.items() if k != 'id'}
        plant_database['plants'][plant_id] = plant_data
        
        # Save to file
        with open('plant_database.json', 'w') as f:
            json.dump(plant_database, f, indent=2)
        
        return jsonify({"message": "Plant added successfully", "id": plant_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/plants/import', methods=['POST'])
def import_plants():
    """Import plants database from JSON."""
    try:
        data = request.get_json()
        
        if not data or 'plants' not in data:
            return jsonify({"error": "Invalid data format"}), 400
        
        # Replace the entire plants database
        plant_database['plants'] = data['plants']
        
        # Save to file
        with open('plant_database.json', 'w') as f:
            json.dump(plant_database, f, indent=2)
        
        return jsonify({"message": "Database imported successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/diary/categories', methods=['GET'])
def get_diary_categories():
    """Get all crop categories and growth stages for the diary."""
    try:
        # Load custom categories
        custom_data = load_custom_categories()
        
        # Prepare response data
        response_data = {
            "crop_categories": CROP_CATEGORIES,
            "growth_stages": GROWTH_STAGES,
            "custom_crops": custom_data.get("custom_crops", []),
            "custom_stages": custom_data.get("custom_stages", [])
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error getting diary categories: {e}")
        return jsonify({"error": "Failed to get categories", "details": str(e)}), 500

@app.route('/api/diary/categories/crop', methods=['POST'])
def add_custom_crop():
    """Add a custom crop category."""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({"error": "Crop name is required"}), 400
        
        crop_name = data.get('name', '').strip().lower()
        category = data.get('category', 'custom').lower()
        
        if len(crop_name) > 50:
            return jsonify({"error": "Crop name must be 50 characters or less"}), 400
        
        # Load existing custom categories
        custom_data = load_custom_categories()
        
        # Check if crop already exists
        existing_crop = next((crop for crop in custom_data.get("custom_crops", []) 
                            if crop["name"].lower() == crop_name), None)
        
        if existing_crop:
            return jsonify({"error": "Crop already exists in custom categories"}), 400
        
        # Check if crop exists in predefined categories
        for cat_data in CROP_CATEGORIES.values():
            if crop_name in cat_data["crops"]:
                return jsonify({"error": "Crop already exists in predefined categories"}), 400
        
        # Add new custom crop
        new_crop = {
            "name": crop_name,
            "category": category,
            "added_date": datetime.now().isoformat()
        }
        
        if "custom_crops" not in custom_data:
            custom_data["custom_crops"] = []
        
        custom_data["custom_crops"].append(new_crop)
        
        # Save to file
        if save_custom_categories(custom_data):
            return jsonify({
                "success": True,
                "message": "Custom crop added successfully",
                "crop": new_crop
            }), 201
        else:
            return jsonify({"error": "Failed to save custom crop"}), 500
            
    except Exception as e:
        print(f"Error adding custom crop: {e}")
        return jsonify({"error": "Failed to add custom crop", "details": str(e)}), 500

@app.route('/api/diary/categories/stage', methods=['POST'])
def add_custom_growth_stage():
    """Add a custom growth stage."""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({"error": "Growth stage name is required"}), 400
        
        stage_name = data.get('name', '').strip().lower()
        description = data.get('description', '').strip()
        
        if len(stage_name) > 50:
            return jsonify({"error": "Growth stage name must be 50 characters or less"}), 400
        
        if len(description) > 200:
            return jsonify({"error": "Description must be 200 characters or less"}), 400
        
        # Load existing custom categories
        custom_data = load_custom_categories()
        
        # Check if stage already exists
        existing_stage = next((stage for stage in custom_data.get("custom_stages", []) 
                             if stage["name"].lower() == stage_name), None)
        
        if existing_stage:
            return jsonify({"error": "Growth stage already exists in custom categories"}), 400
        
        # Check if stage exists in predefined stages
        if stage_name in GROWTH_STAGES:
            return jsonify({"error": "Growth stage already exists in predefined stages"}), 400
        
        # Add new custom growth stage
        new_stage = {
            "name": stage_name,
            "description": description,
            "added_date": datetime.now().isoformat()
        }
        
        if "custom_stages" not in custom_data:
            custom_data["custom_stages"] = []
        
        custom_data["custom_stages"].append(new_stage)
        
        # Save to file
        if save_custom_categories(custom_data):
            return jsonify({
                "success": True,
                "message": "Custom growth stage added successfully",
                "stage": new_stage
            }), 201
        else:
            return jsonify({"error": "Failed to save custom growth stage"}), 500
            
    except Exception as e:
        print(f"Error adding custom growth stage: {e}")
        return jsonify({"error": "Failed to add custom growth stage", "details": str(e)}), 500

@app.route('/api/diary/categories/crop/<crop_name>', methods=['DELETE'])
def delete_custom_crop(crop_name):
    """Delete a custom crop category."""
    try:
        crop_name_lower = crop_name.lower()
        
        # Load existing custom categories
        custom_data = load_custom_categories()
        
        # Find and remove the crop
        custom_crops = custom_data.get("custom_crops", [])
        updated_crops = [crop for crop in custom_crops if crop["name"].lower() != crop_name_lower]
        
        if len(updated_crops) == len(custom_crops):
            return jsonify({"error": "Custom crop not found"}), 404
        
        custom_data["custom_crops"] = updated_crops
        
        # Save to file
        if save_custom_categories(custom_data):
            return jsonify({
                "success": True,
                "message": "Custom crop deleted successfully"
            }), 200
        else:
            return jsonify({"error": "Failed to delete custom crop"}), 500
            
    except Exception as e:
        print(f"Error deleting custom crop: {e}")
        return jsonify({"error": "Failed to delete custom crop", "details": str(e)}), 500

@app.route('/api/diary/backup', methods=['POST'])
def create_diary_backup():
    """Create a manual backup of diary data."""
    try:
        # Create both regular and timestamped backups
        backup_success = create_backup_file('diary_data.json')
        timestamped_backup = create_timestamped_backup('diary_data.json')
        
        if backup_success or timestamped_backup:
            return jsonify({
                "success": True,
                "message": "Backup created successfully",
                "regular_backup": backup_success,
                "timestamped_backup": timestamped_backup is not None,
                "timestamped_filename": os.path.basename(timestamped_backup) if timestamped_backup else None
            }), 200
        else:
            return jsonify({"error": "Failed to create backup"}), 500
            
    except Exception as e:
        print(f"Error creating backup: {e}")
        return jsonify({"error": "Failed to create backup", "details": str(e)}), 500

@app.route('/api/diary/recover', methods=['POST'])
def recover_diary_data():
    """Recover diary data from backup."""
    try:
        data = request.get_json() or {}
        backup_timestamp = data.get('backup_timestamp')
        
        if backup_timestamp:
            result = recover_from_timestamped_backup('diary_data.json', backup_timestamp)
        else:
            result = recover_from_backup('diary_data.json')
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Error recovering data: {e}")
        return jsonify({"error": "Recovery failed", "details": str(e)}), 500

@app.route('/api/diary/export', methods=['GET'])
def export_diary():
    """Export diary data for user data portability."""
    try:
        format_type = request.args.get('format', 'json').lower()
        include_metadata = request.args.get('include_metadata', 'true').lower() == 'true'
        
        result = export_diary_data(format_type, include_metadata)
        
        if result["success"]:
            if format_type == 'json':
                response = jsonify(result["data"])
                response.headers['Content-Disposition'] = f'attachment; filename={result["filename"]}'
                return response
            elif format_type == 'csv':
                from flask import Response
                response = Response(
                    result["data"],
                    mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename={result["filename"]}'}
                )
                return response
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Error exporting data: {e}")
        return jsonify({"error": "Export failed", "details": str(e)}), 500

@app.route('/api/diary/integrity', methods=['GET'])
def check_diary_integrity():
    """Check data integrity and return a comprehensive report."""
    try:
        integrity_report = check_data_integrity()
        
        # Return appropriate status code based on integrity
        if integrity_report["overall_status"] == "healthy":
            return jsonify(integrity_report), 200
        else:
            return jsonify(integrity_report), 206  # Partial Content - issues found but not critical
            
    except Exception as e:
        print(f"Error checking integrity: {e}")
        return jsonify({"error": "Integrity check failed", "details": str(e)}), 500

@app.route('/api/diary/validate', methods=['POST'])
def validate_diary_file():
    """Validate a specific diary data file or uploaded data."""
    try:
        # Check if data is provided in request body
        if request.is_json:
            data = request.get_json()
            validation = validate_diary_data_structure(data)
        else:
            # Validate the current diary_data.json file
            validation = validate_json_file('diary_data.json')
        
        if validation["valid"]:
            return jsonify({
                "valid": True,
                "message": "Data structure is valid",
                "errors": []
            }), 200
        else:
            return jsonify({
                "valid": False,
                "message": "Data structure validation failed",
                "errors": validation["errors"]
            }), 400
            
    except Exception as e:
        print(f"Error validating data: {e}")
        return jsonify({"error": "Validation failed", "details": str(e)}), 500

@app.route('/api/diary/backups', methods=['GET'])
def list_diary_backups():
    """List available backup files for diary data."""
    try:
        import glob
        
        backups = []
        
        # Check for regular backup
        if os.path.exists('diary_data.json.backup'):
            stat = os.stat('diary_data.json.backup')
            backups.append({
                "type": "regular",
                "filename": "diary_data.json.backup",
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size_bytes": stat.st_size
            })
        
        # Check for timestamped backups
        backup_pattern = "diary_data.json.backup_*"
        for backup_file in glob.glob(backup_pattern):
            try:
                stat = os.stat(backup_file)
                timestamp = backup_file.split('_')[-2] + '_' + backup_file.split('_')[-1]
                backups.append({
                    "type": "timestamped",
                    "filename": os.path.basename(backup_file),
                    "timestamp": timestamp,
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size_bytes": stat.st_size
                })
            except (OSError, IndexError):
                continue
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created"], reverse=True)
        
        return jsonify({
            "success": True,
            "backups": backups,
            "total_backups": len(backups)
        }), 200
        
    except Exception as e:
        print(f"Error listing backups: {e}")
        return jsonify({"error": "Failed to list backups", "details": str(e)}), 500

@app.route('/api/diary/entries', methods=['GET'])
def get_diary_entries():
    """Get diary entries with optional filtering and pagination."""
    try:
        # Load diary data
        diary_data = load_diary_entries()
        entries = diary_data.get("entries", [])
        
        # Get query parameters for filtering and pagination
        crop_type = request.args.get('crop_type', '').strip()
        growth_stage = request.args.get('growth_stage', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        search = request.args.get('search', '').strip()
        
        # Pagination parameters
        try:
            page = max(1, int(request.args.get('page', '1')))
            per_page = min(100, max(1, int(request.args.get('per_page', '10'))))
        except (ValueError, TypeError):
            page = 1
            per_page = 10
        
        # Legacy support for limit/offset
        limit = request.args.get('limit', '').strip()
        offset = request.args.get('offset', '0').strip()
        if limit:
            try:
                per_page = min(100, max(1, int(limit)))
                page = max(1, int(offset) // per_page + 1)
            except (ValueError, TypeError):
                pass
        
        # Apply filters
        filtered_entries = entries.copy()
        
        # Filter by crop type
        if crop_type:
            filtered_entries = [entry for entry in filtered_entries 
                              if entry.get('crop_type', '').lower() == crop_type.lower()]
        
        # Filter by growth stage
        if growth_stage:
            filtered_entries = [entry for entry in filtered_entries 
                              if entry.get('growth_stage', '').lower() == growth_stage.lower()]
        
        # Filter by date range
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from).date()
                filtered_entries = [entry for entry in filtered_entries 
                                  if datetime.fromisoformat(entry.get('date', '')).date() >= from_date]
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid date_from format. Use YYYY-MM-DD"}), 400
        
        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to).date()
                filtered_entries = [entry for entry in filtered_entries 
                                  if datetime.fromisoformat(entry.get('date', '')).date() <= to_date]
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid date_to format. Use YYYY-MM-DD"}), 400
        
        # Search in observations and user notes
        if search:
            search_lower = search.lower()
            filtered_entries = [entry for entry in filtered_entries 
                              if search_lower in entry.get('observations', '').lower() or 
                                 search_lower in entry.get('user_notes', '').lower() or
                                 search_lower in entry.get('crop_type', '').lower()]
        
        # Sort entries by date (newest first)
        filtered_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Calculate pagination
        total_entries = len(filtered_entries)
        total_pages = (total_entries + per_page - 1) // per_page if total_entries > 0 else 1
        
        # Validate page number
        if page > total_pages and total_entries > 0:
            return jsonify({"error": f"Page {page} does not exist. Total pages: {total_pages}"}), 400
        
        # Apply pagination
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_entries = filtered_entries[start_index:end_index]
        
        # Calculate pagination metadata
        has_next = page < total_pages
        has_prev = page > 1
        next_page = page + 1 if has_next else None
        prev_page = page - 1 if has_prev else None
        
        # Return response with comprehensive metadata
        response_data = {
            "entries": paginated_entries,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_entries": total_entries,
                "total_pages": total_pages,
                "returned_entries": len(paginated_entries),
                "has_next": has_next,
                "has_prev": has_prev,
                "next_page": next_page,
                "prev_page": prev_page,
                "start_index": start_index + 1 if paginated_entries else 0,
                "end_index": start_index + len(paginated_entries) if paginated_entries else 0
            },
            "filters_applied": {
                "crop_type": crop_type if crop_type else None,
                "growth_stage": growth_stage if growth_stage else None,
                "date_from": date_from if date_from else None,
                "date_to": date_to if date_to else None,
                "search": search if search else None
            },
            # Legacy metadata for backward compatibility
            "metadata": {
                "total_entries": total_entries,
                "returned_entries": len(paginated_entries),
                "offset": start_index,
                "limit": per_page
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error retrieving diary entries: {e}")
        return jsonify({"error": "Failed to retrieve diary entries", "details": str(e)}), 500

@app.route('/api/diary/entries/stats', methods=['GET'])
def get_diary_stats():
    """Get diary statistics and counts for performance optimization."""
    try:
        # Load diary data
        diary_data = load_diary_entries()
        entries = diary_data.get("entries", [])
        
        # Calculate basic statistics
        total_entries = len(entries)
        
        if total_entries == 0:
            return jsonify({
                "total_entries": 0,
                "crop_counts": {},
                "stage_counts": {},
                "recent_entries": 0,
                "date_range": None
            }), 200
        
        # Count entries by crop type
        crop_counts = {}
        stage_counts = {}
        dates = []
        
        for entry in entries:
            # Count crops
            crop = entry.get('crop_type', '').lower()
            if crop:
                crop_counts[crop] = crop_counts.get(crop, 0) + 1
            
            # Count growth stages
            stage = entry.get('growth_stage', '').lower()
            if stage:
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
            
            # Collect dates
            entry_date = entry.get('date', '')
            if entry_date:
                dates.append(entry_date)
        
        # Calculate date range
        dates.sort()
        date_range = {
            "earliest": dates[0] if dates else None,
            "latest": dates[-1] if dates else None
        }
        
        # Count recent entries (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).date()
        recent_entries = sum(1 for entry in entries 
                           if entry.get('date') and 
                           datetime.fromisoformat(entry.get('date')).date() >= thirty_days_ago)
        
        return jsonify({
            "total_entries": total_entries,
            "crop_counts": crop_counts,
            "stage_counts": stage_counts,
            "recent_entries": recent_entries,
            "date_range": date_range
        }), 200
        
    except Exception as e:
        print(f"Error retrieving diary statistics: {e}")
        return jsonify({"error": "Failed to retrieve diary statistics", "details": str(e)}), 500

@app.route('/api/diary/entries', methods=['POST'])
def create_diary_entry():
    """Create a new diary entry with validation and sanitization."""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ['crop_type', 'observations']
        missing_fields = [field for field in required_fields if not data.get(field, '').strip()]
        
        if missing_fields:
            return jsonify({
                "error": "Missing required fields", 
                "missing_fields": missing_fields
            }), 400
        
        # Sanitize and validate input data
        sanitized_data = {}
        
        # Date validation and sanitization
        entry_date = data.get('date', '').strip()
        if entry_date:
            try:
                # Validate date format and ensure it's not in the future
                parsed_date = datetime.fromisoformat(entry_date).date()
                today = datetime.now().date()
                if parsed_date > today:
                    return jsonify({"error": "Entry date cannot be in the future"}), 400
                sanitized_data['date'] = entry_date
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        else:
            # Default to today's date
            sanitized_data['date'] = datetime.now().strftime('%Y-%m-%d')
        
        # Crop type validation (required, max 100 chars)
        crop_type = data.get('crop_type', '').strip()
        if len(crop_type) > 100:
            return jsonify({"error": "Crop type must be 100 characters or less"}), 400
        sanitized_data['crop_type'] = crop_type
        
        # Growth stage validation (optional, max 50 chars)
        growth_stage = data.get('growth_stage', '').strip()
        if len(growth_stage) > 50:
            return jsonify({"error": "Growth stage must be 50 characters or less"}), 400
        sanitized_data['growth_stage'] = growth_stage
        
        # Observations validation (required, max 2000 chars)
        observations = data.get('observations', '').strip()
        if len(observations) > 2000:
            return jsonify({"error": "Observations must be 2000 characters or less"}), 400
        sanitized_data['observations'] = observations
        
        # Optional fields with validation
        weather = data.get('weather', '').strip()
        if len(weather) > 200:
            return jsonify({"error": "Weather description must be 200 characters or less"}), 400
        sanitized_data['weather'] = weather
        
        location = data.get('location', '').strip()
        if len(location) > 200:
            return jsonify({"error": "Location must be 200 characters or less"}), 400
        sanitized_data['location'] = location
        
        user_notes = data.get('user_notes', '').strip()
        if len(user_notes) > 1000:
            return jsonify({"error": "User notes must be 1000 characters or less"}), 400
        sanitized_data['user_notes'] = user_notes
        
        # Actions taken validation (should be a list)
        actions_taken = data.get('actions_taken', [])
        if not isinstance(actions_taken, list):
            return jsonify({"error": "Actions taken must be a list"}), 400
        
        # Validate each action and limit to 20 actions max
        if len(actions_taken) > 20:
            return jsonify({"error": "Maximum 20 actions allowed per entry"}), 400
        
        sanitized_actions = []
        for action in actions_taken:
            if isinstance(action, str) and action.strip():
                action_clean = action.strip()
                if len(action_clean) > 100:
                    return jsonify({"error": "Each action must be 100 characters or less"}), 400
                sanitized_actions.append(action_clean)
        
        sanitized_data['actions_taken'] = sanitized_actions
        
        # Photos validation (should be a list, will be handled by separate upload endpoint)
        photos = data.get('photos', [])
        if not isinstance(photos, list):
            return jsonify({"error": "Photos must be a list"}), 400
        
        # Limit to 10 photos max and validate each photo path
        if len(photos) > 10:
            return jsonify({"error": "Maximum 10 photos allowed per entry"}), 400
        
        sanitized_photos = []
        for photo in photos:
            if isinstance(photo, str) and photo.strip():
                photo_clean = photo.strip()
                if len(photo_clean) > 500:
                    return jsonify({"error": "Photo path must be 500 characters or less"}), 400
                sanitized_photos.append(photo_clean)
        
        sanitized_data['photos'] = sanitized_photos
        
        # Save the diary entry
        result = save_diary_entry(sanitized_data)
        
        if result.get('success'):
            # Return success response with entry details
            response_data = {
                "success": True,
                "message": result.get('message', 'Entry created successfully'),
                "entry_id": result.get('entry_id'),
                "entry": {
                    "id": result.get('entry_id'),
                    "date": sanitized_data['date'],
                    "crop_type": sanitized_data['crop_type'],
                    "growth_stage": sanitized_data['growth_stage'],
                    "observations": sanitized_data['observations']
                }
            }
            return jsonify(response_data), 201
        else:
            return jsonify({
                "error": result.get('message', 'Failed to create entry'),
                "details": result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        print(f"Error creating diary entry: {e}")
        return jsonify({
            "error": "Failed to create diary entry", 
            "details": str(e)
        }), 500

@app.route('/api/diary/entries/<entry_id>', methods=['PUT'])
def update_diary_entry(entry_id):
    """Update an existing diary entry with validation and sanitization."""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Load existing diary data
        diary_data = load_diary_entries()
        entries = diary_data.get("entries", [])
        
        # Find the entry to update
        entry_index = None
        for i, entry in enumerate(entries):
            if entry.get('id') == entry_id:
                entry_index = i
                break
        
        if entry_index is None:
            return jsonify({"error": "Entry not found"}), 404
        
        # Validate required fields
        required_fields = ['crop_type', 'observations']
        missing_fields = [field for field in required_fields if not data.get(field, '').strip()]
        
        if missing_fields:
            return jsonify({
                "error": "Missing required fields", 
                "missing_fields": missing_fields
            }), 400
        
        # Sanitize and validate input data (same validation as create)
        sanitized_data = {}
        
        # Date validation and sanitization
        entry_date = data.get('date', '').strip()
        if entry_date:
            try:
                # Validate date format and ensure it's not in the future
                parsed_date = datetime.fromisoformat(entry_date).date()
                today = datetime.now().date()
                if parsed_date > today:
                    return jsonify({"error": "Entry date cannot be in the future"}), 400
                sanitized_data['date'] = entry_date
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        else:
            # Keep existing date if not provided
            sanitized_data['date'] = entries[entry_index].get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Crop type validation (required, max 100 chars)
        crop_type = data.get('crop_type', '').strip()
        if len(crop_type) > 100:
            return jsonify({"error": "Crop type must be 100 characters or less"}), 400
        sanitized_data['crop_type'] = crop_type
        
        # Growth stage validation (optional, max 50 chars)
        growth_stage = data.get('growth_stage', '').strip()
        if len(growth_stage) > 50:
            return jsonify({"error": "Growth stage must be 50 characters or less"}), 400
        sanitized_data['growth_stage'] = growth_stage
        
        # Observations validation (required, max 2000 chars)
        observations = data.get('observations', '').strip()
        if len(observations) > 2000:
            return jsonify({"error": "Observations must be 2000 characters or less"}), 400
        sanitized_data['observations'] = observations
        
        # Optional fields with validation
        weather = data.get('weather', '').strip()
        if len(weather) > 200:
            return jsonify({"error": "Weather description must be 200 characters or less"}), 400
        sanitized_data['weather'] = weather
        
        location = data.get('location', '').strip()
        if len(location) > 200:
            return jsonify({"error": "Location must be 200 characters or less"}), 400
        sanitized_data['location'] = location
        
        user_notes = data.get('user_notes', '').strip()
        if len(user_notes) > 1000:
            return jsonify({"error": "User notes must be 1000 characters or less"}), 400
        sanitized_data['user_notes'] = user_notes
        
        # Actions taken validation (should be a list)
        actions_taken = data.get('actions_taken', [])
        if not isinstance(actions_taken, list):
            return jsonify({"error": "Actions taken must be a list"}), 400
        
        # Validate each action and limit to 20 actions max
        if len(actions_taken) > 20:
            return jsonify({"error": "Maximum 20 actions allowed per entry"}), 400
        
        sanitized_actions = []
        for action in actions_taken:
            if isinstance(action, str) and action.strip():
                action_clean = action.strip()
                if len(action_clean) > 100:
                    return jsonify({"error": "Each action must be 100 characters or less"}), 400
                sanitized_actions.append(action_clean)
        
        sanitized_data['actions_taken'] = sanitized_actions
        
        # Photos validation (should be a list)
        photos = data.get('photos', [])
        if not isinstance(photos, list):
            return jsonify({"error": "Photos must be a list"}), 400
        
        # Limit to 10 photos max and validate each photo path
        if len(photos) > 10:
            return jsonify({"error": "Maximum 10 photos allowed per entry"}), 400
        
        sanitized_photos = []
        for photo in photos:
            if isinstance(photo, str) and photo.strip():
                photo_clean = photo.strip()
                if len(photo_clean) > 500:
                    return jsonify({"error": "Photo path must be 500 characters or less"}), 400
                sanitized_photos.append(photo_clean)
        
        sanitized_data['photos'] = sanitized_photos
        
        # Update the entry while preserving id and original timestamp
        updated_entry = {
            "id": entry_id,
            "timestamp": entries[entry_index].get('timestamp'),  # Keep original timestamp
            "last_modified": datetime.now().isoformat(),  # Add modification timestamp
            **sanitized_data
        }
        
        # Replace the entry in the list
        entries[entry_index] = updated_entry
        
        # Update metadata
        diary_data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Create backup before saving
        try:
            if os.path.exists('diary_data.json'):
                import shutil
                shutil.copy2('diary_data.json', 'diary_data.json.backup')
        except Exception as backup_error:
            print(f"Warning: Could not create backup: {backup_error}")
        
        # Save the updated data
        with open('diary_data.json', 'w') as f:
            json.dump(diary_data, f, indent=2)
        
        # Return success response with updated entry details
        response_data = {
            "success": True,
            "message": "Entry updated successfully",
            "entry": updated_entry
        }
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error updating diary entry: {e}")
        return jsonify({
            "error": "Failed to update diary entry", 
            "details": str(e)
        }), 500

@app.route('/api/diary/entries/<entry_id>', methods=['DELETE'])
def delete_diary_entry(entry_id):
    """Delete a diary entry with proper confirmation handling."""
    try:
        # Load existing diary data
        diary_data = load_diary_entries()
        entries = diary_data.get("entries", [])
        
        # Find the entry to delete
        entry_index = None
        entry_to_delete = None
        for i, entry in enumerate(entries):
            if entry.get('id') == entry_id:
                entry_index = i
                entry_to_delete = entry
                break
        
        if entry_index is None:
            return jsonify({"error": "Entry not found"}), 404
        
        # Create backup before deletion
        try:
            if os.path.exists('diary_data.json'):
                import shutil
                shutil.copy2('diary_data.json', 'diary_data.json.backup')
        except Exception as backup_error:
            print(f"Warning: Could not create backup: {backup_error}")
        
        # Remove the entry from the list
        deleted_entry = entries.pop(entry_index)
        
        # Update metadata
        diary_data["metadata"]["total_entries"] = len(entries)
        diary_data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Save the updated data
        with open('diary_data.json', 'w') as f:
            json.dump(diary_data, f, indent=2)
        
        # Return success response with deleted entry info
        response_data = {
            "success": True,
            "message": "Entry deleted successfully",
            "deleted_entry": {
                "id": deleted_entry.get('id'),
                "date": deleted_entry.get('date'),
                "crop_type": deleted_entry.get('crop_type'),
                "observations": deleted_entry.get('observations', '')[:50] + "..." if len(deleted_entry.get('observations', '')) > 50 else deleted_entry.get('observations', '')
            }
        }
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error deleting diary entry: {e}")
        return jsonify({
            "error": "Failed to delete diary entry", 
            "details": str(e)
        }), 500

@app.route('/api/diary/upload', methods=['POST'])
def upload_diary_photo():
    """Handle photo uploads for diary entries with validation and storage."""
    try:
        # Check if files were uploaded
        if 'photos' not in request.files:
            return jsonify({"error": "No photos provided"}), 400
        
        files = request.files.getlist('photos')
        
        if not files or all(file.filename == '' for file in files):
            return jsonify({"error": "No photos selected"}), 400
        
        # Configuration
        UPLOAD_FOLDER = 'static/uploads/diary'
        ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
        MAX_FILES = 10  # Maximum 10 photos per upload
        
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Validate number of files
        if len(files) > MAX_FILES:
            return jsonify({"error": f"Maximum {MAX_FILES} photos allowed per upload"}), 400
        
        def allowed_file(filename):
            return '.' in filename and \
                   filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        
        uploaded_photos = []
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
                
            # Validate file extension
            if not allowed_file(file.filename):
                errors.append(f"File '{file.filename}' has unsupported format. Use JPG, PNG, or WebP.")
                continue
            
            # Read file to check size and validate it's actually an image
            try:
                file_content = file.read()
                file.seek(0)  # Reset file pointer
                
                # Check file size
                if len(file_content) > MAX_FILE_SIZE:
                    errors.append(f"File '{file.filename}' is too large (max 5MB)")
                    continue
                
                # Validate it's actually an image by trying to open it
                try:
                    img = Image.open(io.BytesIO(file_content))
                    img.verify()  # Verify it's a valid image
                    file.seek(0)  # Reset file pointer again
                except Exception:
                    errors.append(f"File '{file.filename}' is not a valid image")
                    continue
                
                # Generate unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_id = str(uuid.uuid4())[:8]
                original_extension = file.filename.rsplit('.', 1)[1].lower()
                secure_name = secure_filename(file.filename.rsplit('.', 1)[0])[:20]  # Limit filename length
                
                new_filename = f"diary_{timestamp}_{unique_id}_{secure_name}.{original_extension}"
                file_path = os.path.join(UPLOAD_FOLDER, new_filename)
                
                # Save the file
                file.save(file_path)
                
                # Optimize image if it's too large (resize to max 1920x1080 while maintaining aspect ratio)
                try:
                    with Image.open(file_path) as img:
                        # Convert RGBA to RGB if necessary (for JPEG compatibility)
                        if img.mode in ('RGBA', 'LA', 'P'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                            img = background
                        
                        # Resize if too large
                        max_size = (1920, 1080)
                        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                            img.thumbnail(max_size, Image.Resampling.LANCZOS)
                            img.save(file_path, optimize=True, quality=85)
                
                except Exception as resize_error:
                    print(f"Warning: Could not optimize image {new_filename}: {resize_error}")
                    # Continue anyway - the original file is still saved
                
                # Store relative path for database
                relative_path = f"/static/uploads/diary/{new_filename}"
                uploaded_photos.append({
                    "filename": new_filename,
                    "original_name": file.filename,
                    "path": relative_path,
                    "size": len(file_content)
                })
                
            except Exception as e:
                errors.append(f"Error processing file '{file.filename}': {str(e)}")
                continue
        
        # Prepare response
        response_data = {
            "success": len(uploaded_photos) > 0,
            "uploaded_photos": uploaded_photos,
            "total_uploaded": len(uploaded_photos)
        }
        
        if errors:
            response_data["errors"] = errors
            response_data["total_errors"] = len(errors)
        
        if len(uploaded_photos) > 0:
            response_data["message"] = f"Successfully uploaded {len(uploaded_photos)} photo(s)"
            status_code = 201
        else:
            response_data["message"] = "No photos were uploaded"
            response_data["error"] = "All files failed validation"
            status_code = 400
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        print(f"Error in photo upload: {e}")
        return jsonify({
            "error": "Failed to upload photos",
            "details": str(e)
        }), 500

@app.route('/static/uploads/diary/<filename>')
def uploaded_file(filename):
    """Serve uploaded diary photos."""
    try:
        upload_folder = 'static/uploads/diary'
        return send_from_directory(upload_folder, filename)
    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        return jsonify({"error": "File not found"}), 404

def get_companion_recommendations(confirmed_crops, soil_type='', soil_ph=''):
    """
    Get companion plant recommendations based on the plant database with soil filtering
    """
    recommendations = []
    all_companions = set()
    
    # Normalize crop names to lowercase for matching
    normalized_crops = [crop.lower().replace(' ', '_') for crop in confirmed_crops]
    
    # Collect all companion plants for the confirmed crops
    for crop in normalized_crops:
        if crop in plant_database['plants']:
            plant_info = plant_database['plants'][crop]
            companions = plant_info.get('companion_plants', [])
            all_companions.update(companions)
    
    # Remove crops that are already planted
    all_companions = all_companions - set(normalized_crops)
    
    # Filter companions based on soil compatibility if soil info is provided
    if soil_type or soil_ph:
        compatible_companions = set()
        for companion in all_companions:
            if companion in plant_database['plants']:
                plant_info = plant_database['plants'][companion]
                soil_requirements = plant_info.get('soil_requirements', {})
                
                # Check soil type compatibility
                soil_compatible = True
                if soil_type and 'type' in soil_requirements:
                    plant_soil_types = [t.lower() for t in soil_requirements['type']]
                    if soil_type.lower() not in plant_soil_types and 'mixed' not in plant_soil_types:
                        soil_compatible = False
                
                # Check pH compatibility
                ph_compatible = True
                if soil_ph and 'ph_range' in soil_requirements:
                    try:
                        user_ph = float(soil_ph)
                        ph_range = soil_requirements['ph_range']
                        if len(ph_range) >= 2:
                            min_ph, max_ph = ph_range[0], ph_range[1]
                            # Allow some tolerance (±0.5 pH units)
                            if not (min_ph - 0.5 <= user_ph <= max_ph + 0.5):
                                ph_compatible = False
                    except (ValueError, TypeError):
                        pass  # If pH parsing fails, don't filter based on pH
                
                if soil_compatible and ph_compatible:
                    compatible_companions.add(companion)
        
        all_companions = compatible_companions
    
    # Create recommendations with detailed information
    for companion in list(all_companions)[:5]:  # Limit to top 5 recommendations
        if companion in plant_database['plants']:
            plant_info = plant_database['plants'][companion]
            
            # Build recommendation reason
            benefits = plant_info.get('benefits_provided', [])
            harvest_info = plant_info.get('harvest_time', {})
            soil_info = plant_info.get('soil_requirements', {})
            
            reason_parts = []
            
            # Add companion benefits
            if benefits:
                reason_parts.append(f"Benefits: {', '.join(benefits[:2])}")
            
            # Add harvest timing
            if 'days_to_maturity' in harvest_info:
                reason_parts.append(f"Harvest in {harvest_info['days_to_maturity']} days")
            
            # Add soil compatibility info
            if 'type' in soil_info:
                soil_types = ', '.join(soil_info['type'])
                reason_parts.append(f"Thrives in {soil_types} soil")
            
            # Add pH compatibility if available
            if 'ph_range' in soil_info and len(soil_info['ph_range']) >= 2:
                ph_min, ph_max = soil_info['ph_range'][0], soil_info['ph_range'][1]
                reason_parts.append(f"Prefers pH {ph_min}-{ph_max}")
            
            # Add specific companion relationships
            compatible_with = []
            for crop in normalized_crops:
                if crop in plant_database['plants']:
                    if companion in plant_database['plants'][crop].get('companion_plants', []):
                        compatible_with.append(plant_database['plants'][crop]['name'])
            
            if compatible_with:
                reason_parts.append(f"Excellent companion for {', '.join(compatible_with[:2])}")
            
            # Add soil compatibility note if filtering was applied
            if soil_type or soil_ph:
                reason_parts.append("Compatible with your soil conditions")
            
            recommendation = {
                'plant': plant_info['name'],
                'reason': '. '.join(reason_parts) + '.'
            }
            recommendations.append(recommendation)
    
    return recommendations

def parse_gemini_response_to_json(response_text, expected_keys):
    """
    A more robust parser for Gemini responses that are expected to be in a JSON-like format.
    It tries to find a JSON block and parse it.
    """
    try:
        # Find the start and end of the JSON block
        json_start = response_text.find('```json')
        if json_start == -1:
            json_start = response_text.find('{')
        else:
            json_start += len('```json')
        json_end = response_text.rfind('```')
        if json_end == -1:
            json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end != -1:
            json_str = response_text[json_start:json_end].strip()
            # Let's try to parse it
            data = json.loads(json_str)
            # Basic validation
            if all(key in data for key in expected_keys):
                return data
    except json.JSONDecodeError:
        print("Failed to decode JSON from Gemini response.")
        return None # Indicate failure
    
    print("Could not find a valid JSON block in the response.")
    return None

@app.route('/analyze', methods=['POST'])
def analyze():
    if not api_key or api_key == "YOUR_API_KEY_HERE":
         return jsonify({"error": "API key is not configured on the server."}), 500

    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']
    text_input = request.form.get('text', '')
    soil_type = request.form.get('soilType', '')
    soil_ph = request.form.get('soilPH', '')
    location = request.form.get('location', '')
    gps_coordinates_str = request.form.get('gpsCoordinates', '')
    
    # Parse GPS coordinates
    gps_coordinates = None
    if gps_coordinates_str and gps_coordinates_str != 'null':
        try:
            gps_coordinates = json.loads(gps_coordinates_str)
        except json.JSONDecodeError:
            gps_coordinates = None

    # Save user input data to JSON file
    user_data = {
        'timestamp': datetime.now().isoformat(),
        'text_input': text_input,
        'soil_type': soil_type,
        'soil_ph': soil_ph,
        'location': location,
        'gps_coordinates': gps_coordinates
    }
    
    save_user_data(user_data)

    try:
        image = Image.open(image_file.stream)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Enhanced prompt with soil and location context
        context_info = []
        if soil_type:
            context_info.append(f"Soil type: {soil_type}")
        if soil_ph:
            context_info.append(f"Soil pH: {soil_ph}")
        if location:
            context_info.append(f"Location: {location}")
        
        context_str = ". ".join(context_info) if context_info else "No additional context provided"

        prompt_parts = [
            f"You are an expert in agricultural science. Analyze the image and notes to identify plants. List them one per line. Do not add other text. If unsure, use 'Unknown Plant'.\n"
            f"User's notes: {text_input if text_input else 'None'}\n"
            f"Additional context: {context_str}",
            image,
        ]

        response = model.generate_content(prompt_parts)
        
        if not response.parts:
             return jsonify({"error": "Model response was blocked or empty."}), 500

        crops = []
        lines = response.text.strip().split('\n')
        for i, line in enumerate(lines):
            clean_line = line.strip().lstrip('*-123456789. ').strip()
            if clean_line:
                crops.append({"name": clean_line, "id": f"crop_{i}"})
        
        if not crops:
             return jsonify({"error": "Could not identify any crops."}), 500

        # Update user data with identified crops
        user_data['identified_crops'] = [crop['name'] for crop in crops]
        save_user_data(user_data)

        return jsonify({"identified_crops": crops})

    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    if not data or 'crops' not in data:
        return jsonify({"error": "No confirmed crops provided."}), 400

    confirmed_crops = data['crops']
    soil_type = data.get('soilType', '')
    soil_ph = data.get('soilPH', '')
    location = data.get('location', '')
    gps_coordinates = data.get('gpsCoordinates')
    
    try:
        # First, get recommendations from our plant database with soil filtering
        database_recommendations = get_companion_recommendations(confirmed_crops, soil_type, soil_ph)
        
        # If we have database recommendations, use them
        if database_recommendations:
            # Save recommendation data
            recommendation_data = {
                'timestamp': datetime.now().isoformat(),
                'confirmed_crops': confirmed_crops,
                'soil_type': soil_type,
                'soil_ph': soil_ph,
                'location': location,
                'gps_coordinates': gps_coordinates,
                'recommendations': database_recommendations,
                'source': 'database'
            }
            save_user_data(recommendation_data)
            return jsonify({"recommendations": database_recommendations})
        
        # Fallback to AI if database doesn't have enough info
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            return jsonify({"error": "API key is not configured and no database recommendations available."}), 500
            
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Enhanced prompt with database and soil context
        database_info = ""
        if plant_database.get('plants'):
            database_info = f"\n**Available Plant Database Info:**\n{json.dumps(plant_database, indent=2)}\n"
        
        soil_context = ""
        if soil_type or soil_ph or location or gps_coordinates:
            soil_context = f"\n**Soil & Location Context:**\n"
            if soil_type:
                soil_context += f"- Soil Type: {soil_type}\n"
            if soil_ph:
                soil_context += f"- Soil pH: {soil_ph}\n"
            if location:
                soil_context += f"- Location: {location}\n"
            if gps_coordinates:
                soil_context += f"- GPS Coordinates: {gps_coordinates['latitude']:.6f}, {gps_coordinates['longitude']:.6f}\n"
                climate_info = get_climate_info_from_gps(gps_coordinates)
                if climate_info:
                    soil_context += f"- Climate Zone: {climate_info}\n"
        
        prompt = (
            "You are an expert in agricultural biodiversity, polyculture, and sustainable farming.\n"
            "Based on the following information, recommend a list of compatible companion plants.\n\n"
            "**Current Confirmed Crops:**\n"
            f"- {', '.join(confirmed_crops)}\n\n"
            f"{soil_context}"
            "**Historical Data for this Farmland Area:**\n"
            f"{json.dumps(historical_data, indent=2)}\n"
            f"{database_info}\n"
            "**Task:**\n"
            "Provide a list of 3-5 recommended companion plants. For each plant, provide a brief, practical explanation (2-3 sentences) of why it's a good companion, focusing on benefits like pest deterrence, soil health, structural support, harvest timing, and soil compatibility.\n"
            "Consider the soil type and pH when making recommendations - suggest plants that will thrive in the given conditions.\n"
            "Include specific details about days to maturity, soil requirements, and companion benefits when possible.\n"
            "Format the response as a JSON object with a single key 'recommendations', which is a list of objects. Each object should have two keys: 'plant' (the name of the plant) and 'reason' (the explanation).\n"
            "Example format:\n"
            "```json\n"
            "{\n"
            '  "recommendations": [\n'
            '    {\n'
            '      "plant": "Example Plant",\n'
            '      "reason": "This is an example reason with specific benefits and timing."\n'
            '    }\n'
            '  ]\n'
            '}\n'
            "```"
        )
        
        response = model.generate_content(prompt)
        
        if not response.parts:
            return jsonify({"error": "Model response was blocked or empty."}), 500
        
        # Use the JSON parser function
        recommendations_data = parse_gemini_response_to_json(response.text, ['recommendations'])
        if recommendations_data:
            # Save AI recommendation data
            recommendation_data = {
                'timestamp': datetime.now().isoformat(),
                'confirmed_crops': confirmed_crops,
                'soil_type': soil_type,
                'soil_ph': soil_ph,
                'location': location,
                'gps_coordinates': gps_coordinates,
                'recommendations': recommendations_data['recommendations'],
                'source': 'ai'
            }
            save_user_data(recommendation_data)
            return jsonify(recommendations_data)
        else:
            # Final fallback with basic recommendations
            fallback_recommendations = [
                {"plant": "Marigold", "reason": "Natural pest deterrent that repels nematodes and attracts beneficial insects. Easy to grow and blooms continuously."},
                {"plant": "Basil", "reason": "Improves flavor of nearby plants and repels aphids. Harvest in 60 days with continuous picking."},
                {"plant": "Lettuce", "reason": "Fast-growing ground cover that can be harvested in 45 days. Provides living mulch for taller plants."}
            ]
            
            # Save fallback recommendation data
            recommendation_data = {
                'timestamp': datetime.now().isoformat(),
                'confirmed_crops': confirmed_crops,
                'soil_type': soil_type,
                'soil_ph': soil_ph,
                'location': location,
                'gps_coordinates': gps_coordinates,
                'recommendations': fallback_recommendations,
                'source': 'fallback'
            }
            save_user_data(recommendation_data)
            return jsonify({"recommendations": fallback_recommendations})

    except Exception as e:
        print(f"An error occurred during recommendation: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

# --- Missing Diary Routes ---

@app.route('/diary')
def diary_page():
    """Render the diary page"""
    return render_template('diary.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)