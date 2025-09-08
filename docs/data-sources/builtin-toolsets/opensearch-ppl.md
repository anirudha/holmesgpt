# OpenSearch PPL

The OpenSearch PPL toolset allows HolmesGPT to execute [Piped Processing Language (PPL)](https://opensearch.org/docs/latest/ppl/index/) queries against an OpenSearch cluster.

## Configuration

```yaml-toolset-config
toolsets:
  opensearch/ppl:
    enabled: true
    config:
      opensearch_url: <your opensearch URL>
      index_pattern: <default index pattern>
      opensearch_auth_header: "ApiKey <...>" # Optional authorization header
```

## Capabilities

| Tool Name | Description |
|-----------|-------------|
| run_ppl_query | Execute a PPL query via the OpenSearch `_plugins/_ppl` endpoint |
