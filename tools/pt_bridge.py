import asyncio
import json
import logging
import os
import threading
import uuid
from typing import Any

log = logging.getLogger(__name__)

BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 7531
TOOL_TIMEOUT = float(os.environ.get("PT_MCP_TOOL_TIMEOUT", "120"))

try:
    from aiohttp import web
except ImportError:
    web = None

# Force async driver registration for PyInstaller builds
try:
    import engineio.async_drivers.aiohttp  # noqa: F401
except ImportError:
    pass
try:
    import engineio.async_drivers._websocket_wsgi  # noqa: F401
except ImportError:
    pass


class PTBridge:
    def __init__(self):
        if web is None:
            raise RuntimeError("aiohttp not available")
        import socketio

        try:
            self._sio = socketio.AsyncServer(
                async_mode="aiohttp",
                cors_allowed_origins="*",
                async_handlers=True,
                logger=False,
                engineio_logger=False,
                transports=["websocket", "polling"],
            )
            self._app = web.Application()
            self._sio.attach(self._app)
            self._app.router.add_get("/health", self._health)
        except (ValueError, ImportError) as e:
            raise RuntimeError(
                f"Socket.IO aiohttp mode not available: {e}. "
                "Install dependencies: pip install aiohttp python-socketio"
            )
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._sid: str | None = None
        self._connected = asyncio.Event()
        self._pending: dict[str, asyncio.Future[dict]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._register_handlers()

    async def _health(self, request):
        return web.json_response({"status": "ok", "connected": self.is_connected})

    def _register_handlers(self):
        sio = self._sio

        @sio.event
        async def connect(sid: str, environ: dict, auth: Any = None):
            log.info("PT plugin connected sid=%s", sid)
            old_sid = self._sid
            self._sid = sid
            self._connected.set()
            if old_sid is not None and old_sid != sid:
                try:
                    await sio.disconnect(old_sid)
                except Exception:
                    pass

        @sio.event
        async def disconnect(sid: str):
            log.info("PT plugin disconnected sid=%s", sid)
            if self._sid == sid:
                self._sid = None
                self._connected.clear()
                for tcid, fut in list(self._pending.items()):
                    if not fut.done():
                        fut.set_exception(RuntimeError("PT plugin disconnected mid-call"))
                self._pending.clear()

        @sio.on("tool_result")
        async def on_tool_result(_sid: str, data: dict | None):
            if not isinstance(data, dict):
                return
            tcid = data.get("tool_call_id")
            if not isinstance(tcid, str) or not tcid:
                return
            fut = self._pending.pop(tcid, None)
            if fut is None or fut.done():
                return
            if "result" not in data:
                fut.set_exception(RuntimeError("tool_result missing 'result'"))
                return
            fut.set_result(data["result"])

    async def _start(self):
        self._loop = asyncio.get_running_loop()
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self.host, self.port, reuse_address=True)
        await self._site.start()
        log.info("PT bridge listening on %s:%d", self.host, self.port)

    def start_background(self, host=BRIDGE_HOST, port=BRIDGE_PORT):
        self.host = host
        self.port = port
        self._start_error = None
        self._started = threading.Event()

        def _run():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._start())
                self._started.set()
                loop.run_forever()
            except Exception as e:
                self._start_error = str(e)
                log.error("bridge start failed: %s", e)

        t = threading.Thread(target=_run, daemon=True, name="pt-bridge")
        t.start()
        # Give it a moment to fail fast (port conflict, etc.)
        self._started.wait(0.5)
        if self._start_error:
            raise RuntimeError(f"Bridge failed to start: {self._start_error}")
        return True

    async def _stop(self):
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(RuntimeError("bridge stopped"))
        self._pending.clear()
        self._sid = None
        self._connected.clear()
        if self._site:
            await self._site.stop()
            self._site = None
        if self._runner:
            await self._runner.cleanup()
            self._runner = None

    def stop(self):
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._stop(), self._loop)

    @property
    def is_connected(self):
        return self._sid is not None

    def wait_connected(self, timeout=30.0):
        if self.is_connected:
            return True
        if not self._loop or self._loop.is_closed():
            raise RuntimeError("bridge not started")
        fut = asyncio.run_coroutine_threadsafe(
            asyncio.wait_for(self._connected.wait(), timeout), self._loop
        )
        try:
            fut.result(timeout + 5)
            return True
        except asyncio.TimeoutError:
            raise RuntimeError(
                f"PT did not connect within {timeout}s. Load cisco-pt-mcp.pts in PT."
            )

    def call_tool(self, tool_name: str, tool_input: dict) -> dict:
        if not self._sid:
            raise RuntimeError("No PT plugin connected")
        if not self._loop or self._loop.is_closed():
            raise RuntimeError("bridge not started")

        tcid = uuid.uuid4().hex
        fut = asyncio.run_coroutine_threadsafe(
            self._do_call(tcid, tool_name, tool_input), self._loop
        )
        try:
            return fut.result(timeout=TOOL_TIMEOUT + 5)
        except asyncio.TimeoutError:
            raise RuntimeError(f"Tool '{tool_name}' timed out after {TOOL_TIMEOUT}s")

    async def _do_call(self, tcid, tool_name, tool_input):
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict] = loop.create_future()
        self._pending[tcid] = fut
        await self._sio.emit(
            "tool_call",
            {"tool_call_id": tcid, "tool_name": tool_name, "tool_input": tool_input},
            to=self._sid,
        )
        try:
            return await asyncio.wait_for(fut, timeout=TOOL_TIMEOUT)
        except asyncio.TimeoutError:
            self._pending.pop(tcid, None)
            raise


_bridge: PTBridge | None = None
_bridge_lock = threading.Lock()


def get_bridge():
    global _bridge
    if _bridge is None:
        with _bridge_lock:
            if _bridge is None:
                _bridge = PTBridge()
                _bridge.start_background()
    return _bridge


def wait_pt(timeout=30):
    try:
        bridge = get_bridge()
    except Exception as e:
        raise RuntimeError(f"Bridge failed to start: {e}")
    return bridge.wait_connected(timeout)


def _unwrap(resp):
    while isinstance(resp, dict):
        if resp.get("success") is False:
            raise RuntimeError(resp.get("error", "PT tool failed"))
        if "result" in resp:
            resp = resp["result"]
        else:
            break
    return resp


def call_pt(tool_name, **kwargs):
    return _unwrap(get_bridge().call_tool(tool_name, kwargs))


def is_pt_connected():
    return _bridge is not None and _bridge.is_connected


# Auto-start bridge on import so PT can connect immediately
try:
    get_bridge()
except Exception as e:
    log.warning("bridge auto-start deferred: %s", e)


def get_network():
    return call_pt("getNetwork")


def configure_ios(device_name, commands):
    return call_pt("configureIosDevice", deviceName=device_name, commands=commands)


def add_device(name, model, x, y):
    return call_pt("addDevice", deviceName=name, deviceModel=model, x=x, y=y)


def add_link(d1, i1, d2, i2, link_type="auto"):
    return call_pt("addLink", device1Name=d1, device1Interface=i1, device2Name=d2, device2Interface=i2, linkType=link_type)


def remove_device(names):
    if isinstance(names, str):
        names = [names]
    return call_pt("removeDevice", deviceNames=names)


def get_device_info(name):
    return call_pt("getDeviceInfo", deviceName=name)


def configure_pc_ip(name, dhcp=False, ip="", mask="", gateway="", dns=""):
    return call_pt("configurePcIp", deviceName=name, dhcpEnabled=dhcp, ipaddress=ip, subnetMask=mask, defaultGateway=gateway, dnsServer=dns)


def send_ios_commands(device_name, commands):
    if isinstance(commands, list):
        commands = "\n".join(commands)
    return call_pt("configureIosDevice", deviceName=device_name, commands=commands)


def add_module(name, slot, model):
    return call_pt("addModule", deviceName=name, slot=slot, model=model)


def set_power(name, on=True):
    return call_pt("setPower", deviceName=name, power=on)


def get_running_config(name):
    return call_pt("getRunningConfig", deviceName=name)


def rename_device(name, new_name):
    return call_pt("renameDevice", deviceName=name, newName=new_name)


def move_device(name, x, y):
    return call_pt("moveDevice", deviceName=name, x=x, y=y)


def check_bridge():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((BRIDGE_HOST, BRIDGE_PORT))
        s.close()
        return result == 0
    except Exception:
        return False


def get_status():
    return {
        "connected": is_pt_connected(),
        "alive": check_bridge(),
        "host": BRIDGE_HOST,
        "port": BRIDGE_PORT,
    }
