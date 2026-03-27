def format_events(events):
    lines = []

    for e in events:
        data = e.get("data", {})
        etype = e.get("type")

        if etype == "process":
            lines.append(
                f"Process {data.get('process_name')} "
                f"(PID {data.get('pid')}) "
                f"Parent {data.get('parent_process')} "
                f"CPU {data.get('cpu_percent')}% "
                f"Memory {data.get('memory_mb')}MB "
                f"Reason {data.get('reason')}"
            )

        elif etype == "file":
            lines.append(
                f"File access: {data.get('file_path')} Action {data.get('action')}"
            )

        elif etype == "network":
            lines.append(
                f"Network: {data.get('process_name')} → {data.get('remote_ip')}:{data.get('remote_port')}"
            )

        elif etype == "auth":
            lines.append(
                f"Login: {data.get('username')} Status {data.get('status')} IP {data.get('source_ip')}"
            )

        else:
            lines.append(str(e))

    return "\n".join(lines)