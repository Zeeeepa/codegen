"""
API routes for Slack integration.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from projector.backend.slack_manager import SlackManager
from projector.api.main import get_slack_manager

router = APIRouter()

class SlackMessage(BaseModel):
    """Model for a Slack message."""
    channel: str
    text: str
    blocks: Optional[List[Dict[str, Any]]] = None
    thread_ts: Optional[str] = None

class SlackResponse(BaseModel):
    """Model for a Slack response."""
    ok: bool
    ts: Optional[str] = None
    channel: Optional[str] = None
    message: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/messages", response_model=SlackResponse)
async def send_message(
    message: SlackMessage,
    slack_manager: SlackManager = Depends(get_slack_manager)
):
    """Send a message to Slack."""
    response = slack_manager.send_message(
        channel=message.channel,
        text=message.text,
        blocks=message.blocks,
        thread_ts=message.thread_ts
    )
    
    if not response or not response.get('ok'):
        error = response.get('error', 'Unknown error') if response else 'Failed to send message'
        raise HTTPException(status_code=500, detail=f"Error sending message: {error}")
    
    return response

@router.get("/channels")
async def list_channels(
    slack_manager: SlackManager = Depends(get_slack_manager)
):
    """List available Slack channels."""
    try:
        # Get the Slack client
        client = slack_manager.client
        
        # Get the list of channels
        response = client.conversations_list()
        
        if not response or not response.get('ok'):
            error = response.get('error', 'Unknown error') if response else 'Failed to list channels'
            raise HTTPException(status_code=500, detail=f"Error listing channels: {error}")
        
        # Extract channel information
        channels = []
        for channel in response.get('channels', []):
            channels.append({
                'id': channel.get('id'),
                'name': channel.get('name'),
                'is_private': channel.get('is_private', False),
                'is_archived': channel.get('is_archived', False),
                'num_members': channel.get('num_members', 0)
            })
        
        return {'channels': channels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing channels: {str(e)}")

@router.get("/users")
async def list_users(
    slack_manager: SlackManager = Depends(get_slack_manager)
):
    """List Slack users."""
    try:
        # Get the Slack client
        client = slack_manager.client
        
        # Get the list of users
        response = client.users_list()
        
        if not response or not response.get('ok'):
            error = response.get('error', 'Unknown error') if response else 'Failed to list users'
            raise HTTPException(status_code=500, detail=f"Error listing users: {error}")
        
        # Extract user information
        users = []
        for user in response.get('members', []):
            if not user.get('is_bot') and not user.get('deleted'):
                users.append({
                    'id': user.get('id'),
                    'name': user.get('name'),
                    'real_name': user.get('real_name'),
                    'display_name': user.get('profile', {}).get('display_name'),
                    'email': user.get('profile', {}).get('email'),
                    'image': user.get('profile', {}).get('image_72')
                })
        
        return {'users': users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing users: {str(e)}")

@router.get("/messages/{channel}")
async def get_messages(
    channel: str,
    limit: int = 100,
    slack_manager: SlackManager = Depends(get_slack_manager)
):
    """Get messages from a Slack channel."""
    try:
        # Get the Slack client
        client = slack_manager.client
        
        # Get the messages
        response = client.conversations_history(
            channel=channel,
            limit=limit
        )
        
        if not response or not response.get('ok'):
            error = response.get('error', 'Unknown error') if response else 'Failed to get messages'
            raise HTTPException(status_code=500, detail=f"Error getting messages: {error}")
        
        # Extract message information
        messages = response.get('messages', [])
        
        return {'messages': messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting messages: {str(e)}")

@router.post("/upload")
async def upload_file(
    channel: str,
    filename: str,
    content: str,
    title: Optional[str] = None,
    thread_ts: Optional[str] = None,
    slack_manager: SlackManager = Depends(get_slack_manager)
):
    """Upload a file to Slack."""
    try:
        # Get the Slack client
        client = slack_manager.client
        
        # Upload the file
        response = client.files_upload(
            channels=channel,
            content=content,
            filename=filename,
            title=title,
            thread_ts=thread_ts
        )
        
        if not response or not response.get('ok'):
            error = response.get('error', 'Unknown error') if response else 'Failed to upload file'
            raise HTTPException(status_code=500, detail=f"Error uploading file: {error}")
        
        return {'file': response.get('file')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")