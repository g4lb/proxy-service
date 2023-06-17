# Proxy Service

This repository contains a proxy service implemented in Python using FastAPI and Protocol Buffers (Proto3). The service acts as an intermediary between clients and a destination server, providing request validation, rule matching, forwarding capabilities, and internal statistics.

## Required Endpoints

### `/stream` - Proxy Endpoint

1. **Validate the Request's Signature and Strip the Header**

   The service validates the signature of incoming requests and removes the corresponding header. If the signature is invalid, the service should return the appropriate HTTP error code to indicate the issue.

2. **Match Request Body Against Configured Rules**

   The request body is compared against a list of rules specified in the configuration file. These rules define specific conditions that incoming requests must meet to be considered a match.

3. **Format and Forward Matched Requests to the Destination**

   If a request matches one of the configured rules, the service formats the request body into JSON. The resulting JSON should accurately represent the protobuf schema, preserving naming conventions and types.

4. **Forward Request Headers and Add `X-Grd-Reason` Header**

   The service forwards the request headers to the destination server. Additionally, it adds an additional `X-Grd-Reason` header based on the matching rule. The value of this header should be determined by the specific rule that triggered the match.

### `/stats` - Internal Stats Endpoint

This endpoint provides the following metrics per matched endpoint since the server start:

- Request Count
- Error Rate
- Incoming Bytes
- Outgoing Bytes
- Average Response Time

## Configuration

The proxy service relies on a configuration file to define the rules and settings. The configuration file should be provided in the appropriate format and contain the necessary information to validate requests, define rules, specify the destination server, and track internal statistics.

### How to Run

To run the proxy service, follow the steps below:

1. Clone the repository:

   ```bash
   git clone https://github.com/g4lb/proxy-service.git
   ```

2. Set the environment variable `POKEPROXY_CONFIG` to the path of your configuration file:

   ```bash
   export POKEPROXY_CONFIG=/path/to/config.json
   ```

   The proxy service will now be running on the specified port, ready to receive and process requests.

### Example Config File

An example configuration file (`config.json`) is provided below:

```json
{
	"rules": [
		{
			"url": "http://stream-service.com",
			"reason": "awesome pokemon",
			"match": [
				"hit_points == 20",
				"type_two != word",
				"special_defense > 10",
				"generation < 20"
			]
		}
	]
}
```

### Config Schema

The configuration file follows the following schema:

- `"rules"`: A list of rules that describe endpoints and routing match config.

Each rule is an object composed of:

- `"url"`: The downstream endpoint target.
- `"reason"`: A human-readable description of the reason this rule matched.
- `"match"`: An array of match rules.

Allowed operators for match rules: `==`, `!=`, `>`, `<`.
