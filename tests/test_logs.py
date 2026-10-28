import json
import logging

from pic2cookie import logs
from pic2cookie.settings import LogSettings


def record(**extra) -> logging.LogRecord:
    rec = logging.LogRecord("pic2cookie.service", logging.INFO, "x.py", 1, "Generated %s", ("coaster",), None)
    rec.__dict__.update(extra)
    return rec


def test_json_lines_keep_the_context():
    line = json.loads(logs.JsonFormatter().format(record(design_id="abc", ms=12)))
    assert line["message"] == "Generated coaster"
    assert line["level"] == "info"
    assert line["design_id"] == "abc" and line["ms"] == 12


def test_text_appends_the_context():
    line = logs.TextFormatter().format(record(design_id="abc"))
    assert line.endswith("Generated coaster  design_id=abc")


def test_access_log_can_be_turned_off():
    try:
        logs.setup(LogSettings(access=False, format="json"))
        assert logging.getLogger("uvicorn.access").disabled
        assert isinstance(logging.getLogger().handlers[0].formatter, logs.JsonFormatter)
    finally:
        logs.setup(LogSettings())
