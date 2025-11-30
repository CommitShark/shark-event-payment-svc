import asyncio
import json
from typing import Type, Callable, Dict, List, Any, cast
import logging

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer, ConsumerRecord  # type: ignore

from app.domain.events.base import DomainEvent
from app.domain.events.registry import EventRegistry
from app.domain.ports import IEventBus

logger = logging.getLogger(__name__)


class KafkaEventBus(IEventBus):

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = False,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.auto_offset_reset = auto_offset_reset
        self.enable_auto_commit = enable_auto_commit

        # Event handlers registry
        self._handlers: Dict[str, List[Callable[[DomainEvent[Any]], None]]] = {}

        # Kafka clients
        self._producer: AIOKafkaProducer | None = None
        self._consumer: AIOKafkaConsumer | None = None
        self._is_running = False

    async def connect(self):
        """Initialize Kafka producer and consumer"""
        try:
            # Create producer
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: v.encode("utf-8"),
                key_serializer=lambda v: v.encode("utf-8") if v else None,
            )
            await self._producer.start()

            # Create consumer
            self._consumer = AIOKafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset=self.auto_offset_reset,
                enable_auto_commit=self.enable_auto_commit,
                value_deserializer=lambda v: (
                    json.loads(v.decode("utf-8")) if v else None
                ),
                key_deserializer=lambda v: v.decode("utf-8") if v else None,
            )

            logger.info("Kafka event bus connected successfully")

        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    async def disconnect(self):
        """Stop Kafka consumer and producer cleanly"""
        self._is_running = False

        if hasattr(self, "_consume_task"):
            self._consume_task.cancel()
            try:
                await self._consume_task
            except asyncio.CancelledError:
                pass

        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped")

        logger.info("Kafka event bus disconnected")

    async def publish(self, event: DomainEvent):
        """Publish domain event to Kafka"""
        if not self._producer:
            raise RuntimeError("Event bus not connected")

        try:
            # Use event type as topic name
            topic = event.__class__._group

            # Use aggregate ID as key for partitioning (if exists)
            key = event.aggregate_id

            # Send message
            await self._producer.send_and_wait(
                topic=topic,
                value=event.to_json(),
                key=key,
            )

            logger.debug(f"Published event {event.__class__.__name__} to topic {topic}")

        except Exception as e:
            logger.error(f"Failed to publish event {event.__class__.__name__}: {e}")
            raise

    async def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable,
        type_as_topic=False,
    ):
        topic = (
            event_type._group
            if not type_as_topic
            else f"{event_type._group}.{event_type._event_name}"
        )

        if topic not in self._handlers:
            self._handlers[topic] = []

        self._handlers[topic].append(handler)

    async def start_consuming(self):
        """Start consuming events from subscribed topics"""
        if not self._consumer:
            raise RuntimeError("Event bus not connected")

        topics = list(self._handlers.keys())
        if not topics:
            logger.warning("No topics to subscribe to")
            return

        await self._consumer.start()

        self._consumer.subscribe(topics)
        self._is_running = True

        logger.info(f"Started consuming from topics: {topics}")

        async def consume_loop():
            """Background consumer loop"""
            if not self._consumer:
                raise RuntimeError("Event bus not connected")
            try:
                async for message in self._consumer:
                    if not self._is_running:
                        break
                    await self._handle_message(message)
            except asyncio.CancelledError:
                logger.info("Consumer task cancelled")
            except Exception as e:
                logger.error(f"Error in consumer loop: {e}", exc_info=True)
            finally:
                if self._consumer:
                    await self._consumer.stop()
                self._is_running = False
                logger.info("Consumer stopped")

        # Store the task so we can cancel it later during shutdown
        self._consume_task = asyncio.create_task(consume_loop())

    async def _handle_message(self, message: ConsumerRecord):
        """Handle incoming Kafka message"""
        try:
            topic = message.topic
            event_data = message.value

            logger.debug(f"Handler message Key: {message.key} Data: {event_data}")

            if topic not in self._handlers:
                logger.warning(f"No handlers for topic {topic}")
                return

            if not event_data:
                logger.warning(f"Event data is empty for topic {topic}")
                return

            event_data = cast(Dict, event_data)

            event_type = event_data.get("event_type")

            if not event_type:
                logger.warning(f"Event type is empty for event")
                return

            event_class = EventRegistry.get_event_class(event_type)

            logger.debug(f"Event class is: {event_class.__name__}")

            # Get event type from topic name
            event_payload = event_class.model_validate(event_data)

            # Call all handlers for this event type
            for handler in self._handlers[topic]:
                try:
                    # Pass the event data to the handler
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event_payload)
                    else:
                        handler(event_payload)

                    logger.debug(
                        f"Successfully handled event {event_payload.event_type}"
                    )

                    if self._consumer is None:
                        raise RuntimeError("Consumer not initialized")

                    await self._consumer.commit()
                    logger.debug(
                        f"Successfully processed and committed message from {message.topic}[{message.partition}] offset {message.offset}"
                    )

                except Exception as e:
                    logger.error(
                        f"Handler failed for event {event_payload.event_type}: {e}"
                    )
                    # Continue with other handlers even if one fails

        except Exception as e:
            logger.error(f"Failed to process message from topic {message.topic}: {e}")
