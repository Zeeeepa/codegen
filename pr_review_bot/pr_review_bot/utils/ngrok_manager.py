"""
Ngrok manager for the PR Review Bot.
This module provides functionality for managing ngrok tunnels.
"""

import os
import logging
from typing import Optional
import pyngrok.conf
from pyngrok import ngrok, exception

logger = logging.getLogger(__name__)

class NgrokManager:
    """
    Manager for ngrok tunnels.
    
    This class provides functionality for starting and stopping ngrok tunnels.
    """
    
    def __init__(self, port: int, auth_token: Optional[str] = None):
        """
        Initialize the ngrok manager.
        
        Args:
            port: Port to expose
            auth_token: Ngrok auth token
        """
        self.port = port
        self.auth_token = auth_token
        self.tunnel = None
        
        # Set auth token if provided
        if self.auth_token:
            pyngrok.conf.get_default().auth_token = self.auth_token
    
    def start_tunnel(self) -> Optional[str]:
        """
        Start an ngrok tunnel.
        
        Returns:
            Public URL of the tunnel, or None if the tunnel could not be started
        """
        try:
            # Start the tunnel
            self.tunnel = ngrok.connect(self.port, "http")
            
            # Get the public URL
            public_url = self.tunnel.public_url
            
            logger.info(f"Ngrok tunnel established at {public_url}")
            return public_url
        except exception.PyngrokError as e:
            logger.error(f"Error starting ngrok tunnel: {e}")
            return None
    
    def stop_tunnel(self) -> None:
        """
        Stop the ngrok tunnel.
        """
        if self.tunnel:
            try:
                # Disconnect the tunnel
                ngrok.disconnect(self.tunnel.public_url)
                
                logger.info(f"Ngrok tunnel at {self.tunnel.public_url} stopped")
                self.tunnel = None
            except exception.PyngrokError as e:
                logger.error(f"Error stopping ngrok tunnel: {e}")
    
    def get_public_url(self) -> Optional[str]:
        """
        Get the public URL of the tunnel.
        
        Returns:
            Public URL of the tunnel, or None if the tunnel is not running
        """
        if self.tunnel:
            return self.tunnel.public_url
        return None
