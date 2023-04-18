import json
import os
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from starlette.responses import JSONResponse

from utils import handle_config_schema, validate_pokemon_against_the_list_of_rules, verify_hmac
from stats import get_stats, update_metrics

app = FastAPI()

config_file = os.getenv('POKEPROXY_CONFIG')
if config_file is None:
    raise ValueError('POKEPROXY_CONFIG environment variable not set')

with open(config_file, 'r') as f:
    config = json.load(f)
    if not handle_config_schema(config):
        raise ValueError('POKEPROXY_CONFIG config schema is incorrect')


@app.middleware("http")
async def http_middleware(request, call_next):
    url = str(request.url)
    start = datetime.timestamp(datetime.now())
    request_body = await request.body()
    incoming_bytes_size = len(bytes(request_body))
    try:
        await verify_hmac(request, request_body)
        end = datetime.timestamp(datetime.now())
        update_metrics(url, end - start, False, incoming_bytes_size)
        response = await call_next(request)
        return response
    except HTTPException as e:
        end = datetime.timestamp(datetime.now())
        update_metrics(url, end - start, True, incoming_bytes_size)
        return JSONResponse(content={'error': e.detail}, status_code=e.status_code)
    except Exception as e:
        end = datetime.timestamp(datetime.now())
        update_metrics(url, end - start, True, incoming_bytes_size)
        return JSONResponse(content={'error': "Oops Something went wrong!"}, status_code=500)


@app.post("/stream")
async def stream(request: Request):
    try:
        request_body = await request.body()
        matched_pokemon = validate_pokemon_against_the_list_of_rules(request_body)
        if matched_pokemon is not None:
            headers = {"X-Grd-Reason": matched_pokemon['reason']}
            return JSONResponse(content=matched_pokemon['data'], headers=headers)
    except BaseException as exception:
        raise HTTPException(status_code=400, detail=exception)


@app.get("/stats")
def stats():
    stats_data = get_stats()
    # Calculate error rates and average response times
    for endpoint in stats_data:
        stats_data[endpoint]["error_rate"] = stats_data[endpoint]["error_count"] / stats_data[endpoint]["request_count"]
        stats_data[endpoint]["avg_response_time"] = round(stats_data[endpoint]["avg_response_time"], 2)

    return stats_data
