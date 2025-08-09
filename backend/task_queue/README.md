# Redis Compatibility Layer for AgentFlow

This module provides a compatibility layer between different Redis clients and an in-memory fallback for when Redis is unavailable.

## Components

1. **UpstashAdapter**: Makes Upstash Redis API compatible with standard Redis
2. **InMemoryFallback**: Provides in-memory implementation of Redis operations
3. **EnhancedQueueManager**: Uses the appropriate client based on availability

## Usage

The system automatically selects the appropriate client:

1. First tries to use Upstash Redis with the compatibility adapter
2. Falls back to standard Redis if Upstash is unavailable
3. Uses in-memory fallback if both Redis clients are unavailable

## Testing

Run the test script to verify the Redis adapter:

```bash
./test_adapter.py
```

## Troubleshooting

If you encounter errors with Redis, check:

1. Redis connection settings in `.env`
2. Upstash Redis token and URL
3. Network connectivity to Redis server

## Implementation Details

- The UpstashAdapter translates between Upstash Redis API and standard Redis API
- The InMemoryFallback provides a complete in-memory implementation of Redis operations
- The EnhancedQueueManager handles client selection and fallback logic