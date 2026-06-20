"""
monitoring/parsers.py

LogParser class — extracts the log-parsing logic from monitoring/views.py.
The view is now responsible only for caching and rendering;
all regex + data transformation lives here.

Usage:
    parser = LogParser(app_log_path, error_log_path)
    context = parser.parse()
    # context has: recent_events, recent_errors, event_counts,
    #              error_counts, total_events, total_errors,
    #              health_status, health_color
"""

import os
import re
from pathlib import Path


# [2026-06-19 11:15:36,249] INFO eduflow EVENT=ENROLLMENT user=hari course="Python Full Stack"
_LOG_PATTERN = re.compile(r"^\[(.*?)\]\s+(\w+)\s+(\w+)\s+(.*)$")

_TRACKED_EVENTS = frozenset({
    "ENROLLMENT",
    "QUIZ_ATTEMPT",
    "CERTIFICATE_ISSUED",
    "ANNOUNCEMENT_PUBLISHED",
    "DISCUSSION_REPLY",
    "LESSON_COMPLETED",
    "QUIZ_UNLOCKED",
})

_TRACKED_ERRORS = frozenset({
    "EMAIL_DELIVERY_FAILED",
    "CERTIFICATE_GENERATION_FAILED",
    "ANNOUNCEMENT_PUBLISH_FAILED",
    "DISCUSSION_REPLY_FAILED",
})


def _read_log_lines(filepath):
    """Return all lines from a log file, or [] if missing/unreadable."""
    if not Path(filepath).exists():
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            return fh.readlines()
    except OSError:
        return []


def get_mtime_safe(filepath):
    """Return the file's mtime, or 0 if the file does not exist."""
    try:
        return os.path.getmtime(filepath)
    except OSError:
        return 0


class LogParser:
    """
    Parses the EduFlow app.log and error.log files into structured data
    suitable for the monitoring dashboard context.
    """

    def __init__(self, app_log_path, error_log_path):
        self.app_log_path = app_log_path
        self.error_log_path = error_log_path

    def parse(self):
        """
        Parse both log files and return a context dict with:
          recent_events, recent_errors, event_counts, error_counts,
          total_events, total_errors, health_status, health_color
        """
        recent_events, event_counts = self._parse_app_log()
        recent_errors, error_counts = self._parse_error_log()
        total_events = sum(event_counts.values())
        total_errors = sum(error_counts.values())

        return {
            "recent_events": recent_events,
            "recent_errors": recent_errors,
            "event_counts": event_counts,
            "error_counts": error_counts,
            "total_events": total_events,
            "total_errors": total_errors,
            **self._health(total_errors),
        }

    # ── Internal parsers ──────────────────────────────────────────────────────

    def _parse_app_log(self):
        """Parse app.log — extract structured events and per-type counts."""
        events = []
        counts = {k: 0 for k in _TRACKED_EVENTS}

        for line in _read_log_lines(self.app_log_path):
            line = line.strip()
            if not line:
                continue
            m = _LOG_PATTERN.match(line)
            if not m:
                continue
            timestamp, level, _, message = m.groups()
            entry = self._parse_event_line(timestamp, level, message)
            if entry["event_type"] in counts:
                counts[entry["event_type"]] += 1
            events.append(entry)

        return list(reversed(events))[:50], counts

    def _parse_error_log(self):
        """Parse error.log — group multi-line entries with their tracebacks."""
        errors = []
        counts = {k: 0 for k in _TRACKED_ERRORS}
        current = None

        for line in _read_log_lines(self.error_log_path):
            m = _LOG_PATTERN.match(line.strip())
            if m:
                if current:
                    current["traceback_str"] = "".join(current.pop("_tb"))
                    errors.append(current)
                timestamp, level, _, message = m.groups()
                event_type, display_msg = self._extract_event(message)
                if event_type in counts:
                    counts[event_type] += 1
                current = {
                    "timestamp": timestamp,
                    "level": level,
                    "event_type": event_type,
                    "message": display_msg,
                    "_tb": [],
                }
            elif current:
                current["_tb"].append(line)

        if current:
            current["traceback_str"] = "".join(current.pop("_tb"))
            errors.append(current)

        return list(reversed(errors))[:50], counts

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_event(message):
        """Return (event_type, display_message) from a raw log message."""
        em = re.search(r"EVENT=(\w+)", message)
        event_type = em.group(1) if em else "UNKNOWN"
        display_msg = message.replace(f"EVENT={event_type}", "").strip() if em else message
        return event_type, display_msg

    @staticmethod
    def _parse_event_line(timestamp, level, message):
        """Return a structured event dict for a single app.log line."""
        if "EVENT=" in message:
            event_type, display_msg = LogParser._extract_event(message)
        else:
            event_type = "SYSTEM"
            display_msg = message
        return {
            "timestamp": timestamp,
            "level": level,
            "event_type": event_type,
            "message": display_msg,
        }

    @staticmethod
    def _health(total_errors):
        """Return health_status + health_color based on error count."""
        if total_errors == 0:
            return {"health_status": "Healthy", "health_color": "green"}
        if total_errors <= 5:
            return {"health_status": "Warning", "health_color": "amber"}
        return {"health_status": "Critical", "health_color": "red"}
