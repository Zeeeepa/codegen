"""
Webhook Integration System

This module provides webhook management capabilities for sending completion callbacks,
handling webhook deliveries with retry logic, and managing webhook configurations.
"""

import asyncio
import hmac
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from urllib.parse import urlparse

import aiohttp
from aiohttp import ClientTimeout, ClientError

from .schemas import WebhookConfig, TaskExecution, PipelineExecution, ExecutionStatus


logger = logging.getLogger(__name__)


@dataclass
class WebhookDelivery:
    """Record of a webhook delivery attempt."""
    id: str
    webhook_config: WebhookConfig
    payload: Dict[str, Any]
    status: str  # pending, success, failed, retrying
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    last_attempt_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    next_retry_at: Optional[datetime] = None


class WebhookDeliveryQueue:
    """Queue for managing webhook deliveries with retry logic."""
    
    def __init__(self, max_concurrent_deliveries: int = 10):
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.pending_queue: asyncio.Queue = asyncio.Queue()
        self.retry_queue: asyncio.Queue = asyncio.Queue()
        self.max_concurrent = max_concurrent_deliveries
        self.workers: List[asyncio.Task] = []
        self.retry_worker: Optional[asyncio.Task] = None
        self._shutdown = False
        
    async def start_workers(self):
        """Start background workers for processing deliveries."""
        # Start delivery workers
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._delivery_worker(f"worker-{i}"))
            self.workers.append(worker)
            
        # Start retry worker
        self.retry_worker = asyncio.create_task(self._retry_worker())
        
    async def stop_workers(self):
        """Stop all background workers."""
        self._shutdown = True
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
            
        if self.retry_worker:
            self.retry_worker.cancel()
            
        # Wait for workers to finish
        await asyncio.gather(*self.workers, self.retry_worker, return_exceptions=True)
        self.workers.clear()
        self.retry_worker = None
        
    async def enqueue_delivery(self, delivery: WebhookDelivery):
        """Add a webhook delivery to the queue."""
        self.deliveries[delivery.id] = delivery
        await self.pending_queue.put(delivery.id)
        
    async def _delivery_worker(self, worker_id: str):
        """Worker that processes webhook deliveries."""
        logger.info(f"Starting webhook delivery worker: {worker_id}")
        
        async with aiohttp.ClientSession() as session:
            while not self._shutdown:
                try:
                    # Wait for delivery with timeout
                    delivery_id = await asyncio.wait_for(
                        self.pending_queue.get(), timeout=1.0
                    )
                    
                    delivery = self.deliveries.get(delivery_id)
                    if not delivery:
                        continue
                        
                    await self._execute_delivery(session, delivery)
                    
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Delivery worker {worker_id} error: {e}")
                    
    async def _retry_worker(self):
        """Worker that handles delivery retries."""
        logger.info("Starting webhook retry worker")
        
        while not self._shutdown:
            try:
                current_time = datetime.now()
                
                # Check for deliveries that need retry
                for delivery in list(self.deliveries.values()):
                    if (
                        delivery.status == "retrying" and 
                        delivery.next_retry_at and
                        current_time >= delivery.next_retry_at and
                        delivery.attempts < delivery.max_attempts
                    ):
                        await self.pending_queue.put(delivery.id)
                        delivery.status = "pending"
                        delivery.next_retry_at = None
                        
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Retry worker error: {e}")
                
    async def _execute_delivery(self, session: aiohttp.ClientSession, delivery: WebhookDelivery):
        """Execute a single webhook delivery."""
        config = delivery.webhook_config
        delivery.attempts += 1
        delivery.last_attempt_at = datetime.now()
        
        try:
            # Prepare request
            headers = dict(config.headers) if config.headers else {}
            headers["Content-Type"] = "application/json"
            headers["User-Agent"] = "Codegen-Orchestration/1.0"
            
            # Add webhook signature if auth token is provided
            if config.auth_token:
                payload_str = json.dumps(delivery.payload, sort_keys=True)
                signature = hmac.new(
                    config.auth_token.encode(),
                    payload_str.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature-256"] = f"sha256={signature}"
                headers["X-Webhook-Timestamp"] = str(int(time.time()))
                
            timeout = ClientTimeout(total=config.timeout)
            
            logger.info(f"Delivering webhook to {config.url} (attempt {delivery.attempts})")
            
            async with session.request(
                method=config.method,
                url=config.url,
                json=delivery.payload,
                headers=headers,
                timeout=timeout
            ) as response:
                delivery.response_status = response.status
                delivery.response_body = await response.text()
                
                if 200 <= response.status < 300:
                    delivery.status = "success"
                    delivery.completed_at = datetime.now()
                    logger.info(f"Webhook delivered successfully to {config.url}")
                else:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"HTTP {response.status}: {delivery.response_body}"
                    )
                    
        except (ClientError, asyncio.TimeoutError) as e:
            delivery.error_message = str(e)
            
            if delivery.attempts < delivery.max_attempts:
                # Schedule retry
                delay = config.retry_delay * (2 ** (delivery.attempts - 1))  # Exponential backoff
                delivery.next_retry_at = datetime.now().replace(
                    microsecond=0
                ) + asyncio.get_event_loop().time() + delay
                delivery.status = "retrying"
                
                logger.warning(
                    f"Webhook delivery failed to {config.url} "
                    f"(attempt {delivery.attempts}/{delivery.max_attempts}). "
                    f"Retrying in {delay}s: {e}"
                )
            else:
                delivery.status = "failed"
                delivery.completed_at = datetime.now()
                logger.error(
                    f"Webhook delivery permanently failed to {config.url} "
                    f"after {delivery.attempts} attempts: {e}"
                )
                
        except Exception as e:
            delivery.error_message = str(e)
            delivery.status = "failed"
            delivery.completed_at = datetime.now()
            logger.error(f"Unexpected webhook delivery error to {config.url}: {e}")


class WebhookManager:
    """
    Manages webhook configurations and deliveries for pipeline execution events.
    """
    
    def __init__(self, max_concurrent_deliveries: int = 10):
        self.delivery_queue = WebhookDeliveryQueue(max_concurrent_deliveries)
        self.webhook_configs: Dict[str, List[WebhookConfig]] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        
    async def start(self):
        """Start the webhook manager."""
        await self.delivery_queue.start_workers()
        logger.info("Webhook manager started")
        
    async def stop(self):
        """Stop the webhook manager."""
        await self.delivery_queue.stop_workers()
        logger.info("Webhook manager stopped")
        
    def register_webhook_config(self, pipeline_id: str, config: WebhookConfig):
        """Register a webhook configuration for a pipeline."""
        if pipeline_id not in self.webhook_configs:
            self.webhook_configs[pipeline_id] = []
        self.webhook_configs[pipeline_id].append(config)
        
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler for webhook events."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    async def send_task_completion_webhook(self, task_execution: TaskExecution):
        """Send webhook for task completion."""
        pipeline_id = task_execution.pipeline_id
        webhooks = self.webhook_configs.get(pipeline_id, [])
        
        if not webhooks:
            return
            
        payload = {
            "event": "task_completed",
            "timestamp": datetime.now().isoformat(),
            "task": {
                "id": task_execution.id,
                "stage_id": task_execution.stage_id,
                "pipeline_id": task_execution.pipeline_id,
                "status": task_execution.status,
                "started_at": task_execution.started_at.isoformat() if task_execution.started_at else None,
                "completed_at": task_execution.completed_at.isoformat() if task_execution.completed_at else None,
                "duration_seconds": task_execution.duration_seconds,
                "result": task_execution.result,
                "error_message": task_execution.error_message,
                "agent_run_id": task_execution.agent_run_id,
                "agent_web_url": task_execution.agent_web_url
            }
        }
        
        await self._send_webhooks(webhooks, payload)
        
    async def send_pipeline_completion_webhook(self, pipeline_execution: PipelineExecution):
        """Send webhook for pipeline completion."""
        pipeline_id = pipeline_execution.pipeline_id
        webhooks = self.webhook_configs.get(pipeline_id, [])
        
        if not webhooks:
            return
            
        payload = {
            "event": "pipeline_completed",
            "timestamp": datetime.now().isoformat(),
            "pipeline": {
                "id": pipeline_execution.id,
                "pipeline_id": pipeline_execution.pipeline_id,
                "status": pipeline_execution.status,
                "started_at": pipeline_execution.started_at.isoformat() if pipeline_execution.started_at else None,
                "completed_at": pipeline_execution.completed_at.isoformat() if pipeline_execution.completed_at else None,
                "duration_seconds": pipeline_execution.duration_seconds,
                "total_stages": pipeline_execution.total_stages,
                "completed_stages": pipeline_execution.completed_stages,
                "failed_stages": pipeline_execution.failed_stages,
                "skipped_stages": pipeline_execution.skipped_stages,
                "triggered_by": pipeline_execution.triggered_by
            }
        }
        
        await self._send_webhooks(webhooks, payload)
        
    async def send_custom_webhook(
        self, 
        pipeline_id: str, 
        event_type: str, 
        data: Dict[str, Any]
    ):
        """Send a custom webhook event."""
        webhooks = self.webhook_configs.get(pipeline_id, [])
        
        if not webhooks:
            return
            
        payload = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        await self._send_webhooks(webhooks, payload)
        
    async def _send_webhooks(self, webhooks: List[WebhookConfig], payload: Dict[str, Any]):
        """Send payload to multiple webhook endpoints."""
        for webhook_config in webhooks:
            delivery = WebhookDelivery(
                id=str(uuid.uuid4()),
                webhook_config=webhook_config,
                payload=payload,
                status="pending",
                max_attempts=webhook_config.retry_attempts
            )
            
            await self.delivery_queue.enqueue_delivery(delivery)
            
        # Trigger event handlers
        event_type = payload.get("event", "unknown")
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(payload)
                else:
                    handler(payload)
            except Exception as e:
                logger.error(f"Event handler error for {event_type}: {e}")
                
    def get_delivery_status(self, pipeline_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get status of webhook deliveries."""
        deliveries = []
        
        for delivery in self.delivery_queue.deliveries.values():
            if pipeline_id and pipeline_id not in str(delivery.payload):
                continue
                
            deliveries.append({
                "id": delivery.id,
                "url": delivery.webhook_config.url,
                "status": delivery.status,
                "attempts": delivery.attempts,
                "max_attempts": delivery.max_attempts,
                "created_at": delivery.created_at.isoformat(),
                "last_attempt_at": delivery.last_attempt_at.isoformat() if delivery.last_attempt_at else None,
                "completed_at": delivery.completed_at.isoformat() if delivery.completed_at else None,
                "response_status": delivery.response_status,
                "error_message": delivery.error_message
            })
            
        return sorted(deliveries, key=lambda x: x["created_at"], reverse=True)
        
    async def verify_webhook_signature(
        self, 
        payload: bytes, 
        signature: str, 
        secret: str
    ) -> bool:
        """
        Verify webhook signature for incoming webhooks.
        
        Args:
            payload: Raw payload bytes
            signature: Signature from headers (format: "sha256=...")
            secret: Webhook secret
            
        Returns:
            True if signature is valid
        """
        try:
            if not signature.startswith("sha256="):
                return False
                
            expected_signature = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            provided_signature = signature[7:]  # Remove "sha256=" prefix
            
            return hmac.compare_digest(expected_signature, provided_signature)
            
        except Exception as e:
            logger.error(f"Webhook signature verification error: {e}")
            return False