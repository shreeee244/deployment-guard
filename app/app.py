import os
import time
import random

from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

VERSION = os.getenv("APP_VERSION", "v1")
FAIL_RATE = float(os.getenv("FAIL_RATE", "0"))
EXTRA_LATENCY = float(os.getenv("EXTRA_LATENCY", "0"))

REQUESTS = Counter(
    "http_requests_total",
    "Total requests",
    ["path", "status"]
)

LATENCY = Histogram(
    "http_request_seconds",
    "Request latency",
    ["path"]
)


@app.before_request
def start_timer():
    request._start = time.time()


@app.after_request
def record_metrics(resp):
    if request.path != "/metrics":
        LATENCY.labels(request.path).observe(
            time.time() - request._start
        )

        REQUESTS.labels(
            request.path,
            resp.status_code
        ).inc()

    return resp


@app.route("/")
def index():
    time.sleep(EXTRA_LATENCY)

    if random.random() < FAIL_RATE:
        return jsonify(
            error="simulated failure",
            version=VERSION
        ), 500

    return jsonify(
        message="hello",
        version=VERSION
    )


@app.route("/health")
def health():
    return jsonify(
        status="ok",
        version=VERSION
    )


@app.route("/simulate-error")
def simulate_error():
    return jsonify(
        error="forced error",
        version=VERSION
    ), 500


@app.route("/simulate-slow")
def simulate_slow():
    time.sleep(2.5)

    return jsonify(
        message="slow response",
        version=VERSION
    )


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {
        "Content-Type": CONTENT_TYPE_LATEST
    }


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )