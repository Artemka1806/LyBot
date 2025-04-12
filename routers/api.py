import re

from fastapi import APIRouter
from pydantic import BaseModel

from models.user import User

# Initialize the API router
router = APIRouter()

# Access Redis from main.py
redis_client = None

def init_redis(client):
    global redis_client
    redis_client = client


@router.head("/")
@router.get("/")
async def index():
    """
    Why not?
    """
    return {"text": "I don't think you're supposed to be here."}


@router.get("/attendance")
async def get_attendance(timestamp: float = -1.0):
    # Query users with updated status after the given timestamp
    data = []
    for doc in await User.find({"status_updated_at": {"$gt": timestamp}}).to_list(length=None):
        d = doc.to_mongo()
        data.append(d)

    # Sort by ztu_name if available, otherwise by family_name + given_name
    data = sorted(data, key=lambda x: x.get('ztu_name') or f"{x.get('family_name', '')} {x.get('given_name', '')}")
    result = {}

    for entry in data:
        # Get group information
        group = entry.get("group")
        if group is None:
            continue
            
        # Get class number (first part of group) and subgroup (full group name)
        class_num = group.split('-')[0]
        subgroup = group
        
        # Create nested dictionaries for classes and groups if they don't exist
        if class_num not in result:
            result[class_num] = {}
        if subgroup not in result[class_num]:
            result[class_num][subgroup] = {}
        
        full_name = entry.get("ztu_name") or f"{entry.get('family_name', '')} {entry.get('given_name', '')}"
        
        # Create object for each student using dictionary attributes
        # Store with full_name as the key for backward compatibility
        result[class_num][subgroup][full_name] = {
            "name": full_name,
            "avatar_url": entry.get("avatar_url", ""),
            "status_updated_at": entry.get("status_updated_at"),
            "status": entry.get("status", 3),
            "message": entry.get("status_message", "")
        }
    
    # Function for sorting subgroups by numerical and alphabetical parts
    def sort_key(subgroup):
        match = re.match(r"(\d+)-([А-Яа-я])", subgroup)
        if match:
            return (int(match.group(1)), match.group(2))
        return (0, subgroup)
    
    # Sort classes and subgroups
    sorted_result = {
        class_num: dict(sorted(result[class_num].items(), key=lambda x: sort_key(x[0])))
        for class_num in sorted(result.keys(), key=int)
    }
    
    return sorted_result