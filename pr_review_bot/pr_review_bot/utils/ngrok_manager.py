"""
Ngrok manager module for the PR Review Bot.
Provides functionality for creating and managing ngrok tunnels.
"""

import os
import logging
import time
import json
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class NgrokManager:
    """
    Manager for ngrok tunnels.
    
    Provides functionality for creating and managing ngrok tunnels
    for exposing local services to the internet.
    """
    
    def __init__(self, port: int, auth_token: Optional[str] = None, region: str = "us"):
        """
        Initialize the ngrok manager.
        
        Args:
            port: Port to expose
            auth_token: Ngrok auth token
            region: Ngrok region
        """
        self.port = port
        self.auth_token = auth_token
        self.region = region
        self.process = None
        self.tunnel_url = None
        
        # Check if pyngrok is installed
        try:
            from pyngrok import ngrok, conf
            self.ngrok = ngrok
            self.ngrok_conf = conf
            self.has_pyngrok = True
        except ImportError:
            logger.warning("pyngrok not installed, using subprocess instead")
            self.has_pyngrok = False
            import subprocess
            self.subprocess = subprocess
    
    def start_tunnel(self) -> Optional[str]:
        """
        Start an ngrok tunnel.
        
        Returns:
            Public URL of the tunnel
        """
        if self.has_pyngrok:
            return self._start_tunnel_pyngrok()
        else:
            return self._start_tunnel_subprocess()
    
    def _start_tunnel_pyngrok(self) -> Optional[str]:
        """
        Start an ngrok tunnel using pyngrok.
        
        Returns:
            Public URL of the tunnel
        """
        try:
            # Set auth token if provided
            if self.auth_token:
                self.ngrok_conf.get_default().auth_token = self.auth_token
            
            # Set region
            self.ngrok_conf.get_default().region = self.region
            
            # Start tunnel
            tunnel = self.ngrok.connect(self.port, "http")
            
            # Get public URL
            self.tunnel_url = tunnel.public_url
            
            logger.info(f"Started ngrok tunnel: {self.tunnel_url}")
            return self.tunnel_url
        except Exception as e:
            logger.error(f"Error starting ngrok tunnel: {e}")
            return None
    
    def _start_tunnel_subprocess(self) -> Optional[str]:
        """
        Start an ngrok tunnel using subprocess.
        
        Returns:
            Public URL of the tunnel
        """
        try:
            # Check if ngrok is installed
            try:
                self.subprocess.run(["ngrok", "--version"], check=True, capture_output=True)
            except (self.subprocess.CalledProcessError, FileNotFoundError):
                logger.error("ngrok not installed, please install it from https://ngrok.com/download")
                return None
            
            # Set auth token if provided
            if self.auth_token:
                try:
                    self.subprocess.run(["ngrok", "authtoken", self.auth_token], check=True, capture_output=True)
                except self.subprocess.CalledProcessError as e:
                    logger.error(f"Error setting ngrok auth token: {e}")
                    return None
            
            # Start ngrok
            cmd = ["ngrok", "http", str(self.port), "--region", self.region, "--log=stdout"]
            self.process = self.subprocess.Popen(
                cmd,
                stdout=self.subprocess.PIPE,
                stderr=self.subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for tunnel to start
            time.sleep(2)
            
            # Get public URL
            try:
                response = requests.get("http://localhost:4040/api/tunnels")
                tunnels = response.json()["tunnels"]
                
                if tunnels:
                    self.tunnel_url = tunnels[0]["public_url"]
                    logger.info(f"Started ngrok tunnel: {self.tunnel_url}")
                    return self.tunnel_url
                else:
                    logger.error("No ngrok tunnels found")
                    return None
            except Exception as e:
                logger.error(f"Error getting ngrok tunnel URL: {e}")
                return None
        except Exception as e:
            logger.error(f"Error starting ngrok tunnel: {e}")
            return None
    
    def stop_tunnel(self) -> None:
        """Stop the ngrok tunnel."""
        if self.has_pyngrok:
            self._stop_tunnel_pyngrok()
        else:
            self._stop_tunnel_subprocess()
    
    def _stop_tunnel_pyngrok(self) -> None:
        """Stop the ngrok tunnel using pyngrok."""
        try:
            if self.tunnel_url:
                # Extract the tunnel URL from the public URL
                tunnel_url = self.tunnel_url.replace("https://", "").replace("http://", "")
                
                # Disconnect the tunnel
                self.ngrok.disconnect(tunnel_url)
                
                logger.info(f"Stopped ngrok tunnel: {self.tunnel_url}")
                self.tunnel_url = None
        except Exception as e:
            logger.error(f"Error stopping ngrok tunnel: {e}")
    
    def _stop_tunnel_subprocess(self) -> None:
        """Stop the ngrok tunnel using subprocess."""
        try:
            if self.process:
                self.process.terminate()
                self.process.wait()
                
                logger.info(f"Stopped ngrok tunnel: {self.tunnel_url}")
                self.process = None
                self.tunnel_url = None
        except Exception as e:
            logger.error(f"Error stopping ngrok tunnel: {e}")
    
    def get_public_url(self) -> Optional[str]:
        """
        Get the public URL of the tunnel.
        
        Returns:
            Public URL of the tunnel
        """
        if self.tunnel_url:
            return self.tunnel_url
        
        # Try to get the URL from the ngrok API
        try:
            response = requests.get("http://localhost:4040/api/tunnels")
            tunnels = response.json()["tunnels"]
            
            if tunnels:
                self.tunnel_url = tunnels[0]["public_url"]
                return self.tunnel_url
            else:
                logger.warning("No ngrok tunnels found")
                return None
        except Exception as e:
            logger.warning(f"Error getting ngrok tunnel URL: {e}")
            return None
