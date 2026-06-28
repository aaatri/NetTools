// User-callable functions exposed by the cisco-pt-mcp bridge.
// Each returns { success: bool, ... } and is invoked via $se('runCode', 'return <fn>(<args>);').

function fail(prefix, err) {
  var msg = (err && (err.message || String(err))) || "unknown error";
  return { success: false, error: prefix ? prefix + ": " + msg : msg };
}

addDevice = function (deviceName, deviceModel, x, y) {
  try {
    var deviceType = allDeviceTypes[deviceModel];

    if (deviceType === undefined) {
      return {
        success: false,
        error: `Unknown device model: ${deviceModel}`,
      };
    }

    var originalDeviceName = ipc
      .appWindow()
      .getActiveWorkspace()
      .getLogicalWorkspace()
      .addDevice(deviceType, deviceModel, x, y);

    if (!originalDeviceName) {
      return {
        success: false,
        error: `Failed to add device ${deviceName} (${deviceModel})`,
      };
    }

    var device = ipc.network().getDevice(originalDeviceName);
    device.setName(deviceName);

    // Always skip boot dialog — required for routers/switches too, not just PCs
    try { device.setPower(true); } catch (_) {}
    try { device.skipBoot(); } catch (_) {}

    return {
      success: true,
      message: `Device ${deviceName} added successfully`,
    };
  } catch (error) {
    return fail("Error adding device", error);
  }
};

addModule = function (deviceName, slot, model) {
  try {
    var device = ipc.network().getDevice(deviceName);

    if (!device) {
      return {
        success: false,
        error: `Device ${deviceName} not found`,
      };
    }

    var moduleType = allModuleTypes[model];

    if (moduleType === undefined) {
      return {
        success: false,
        error: `Unknown module model: ${model}`,
      };
    }

    var powerState = device.getPower();
    device.setPower(false);

    var result = device.addModule(slot, moduleType, model);

    if (powerState) {
      device.setPower(true);
      device.skipBoot();
    }

    if (result != true) {
      return {
        success: false,
        error: `Failed to add module ${model} to slot ${slot} on ${deviceName}`,
      };
    }

    return {
      success: true,
      message: `Module ${model} added to ${deviceName} slot ${slot}`,
    };
  } catch (error) {
    return fail("Error adding module", error);
  }
};

addLink = function (
  device1Name,
  device1Interface,
  device2Name,
  device2Interface,
  linkType
) {
  try {
    // Validate required params
    if (!device1Name || !device1Interface || !device2Name || !device2Interface) {
      return {
        success: false,
        error: "Missing required parameters: device1Name, device1Interface, device2Name, device2Interface are all required",
      };
    }

    if (!linkType) {
      return {
        success: false,
        error: "Missing required parameter: linkType (straight/cross/fiber/serial/auto)",
      };
    }

    var linkTypeValue = allLinkTypes[linkType];

    if (linkTypeValue === undefined) {
      return {
        success: false,
        error: "Unknown link type: " + linkType + ". Valid types: straight, cross, fiber, serial, auto, roll, console, wireless, coaxial, octal, cellular, usb, custom_io",
      };
    }

    var result = ipc
      .appWindow()
      .getActiveWorkspace()
      .getLogicalWorkspace()
      .createLink(
        device1Name,
        device1Interface,
        device2Name,
        device2Interface,
        linkTypeValue
      );

    if (result != true) {
      return {
        success: false,
        error: "Failed to create link between " + device1Name + ":" + device1Interface + " and " + device2Name + ":" + device2Interface,
      };
    }

    return {
      success: true,
      message: "Link created between " + device1Name + " and " + device2Name,
    };
  } catch (error) {
    return fail("Error creating link", error);
  }
};

configurePcIp = function (
  deviceName,
  dhcpEnabled,
  ipaddress,
  subnetMask,
  defaultGateway,
  dnsServer
) {
  try {
    var device = ipc.network().getDevice(deviceName);

    if (!device) {
      return {
        success: false,
        error: "Device " + deviceName + " not found",
      };
    }

    // Power on the device first
    try { device.setPower(true); } catch (_) {}

    // Find first available physical port (try common names first)
    var port = device.getPort("FastEthernet0");
    if (!port) port = device.getPort("Ethernet0");
    if (!port) port = device.getPort("GigabitEthernet0");

    // Fallback: enumerate all ports
    if (!port) {
      var portCount = device.getPortCount();
      for (var i = 0; i < portCount; i++) {
        port = device.getPortAt(i);
        if (port) break;
      }
    }

    if (!port) {
      return {
        success: false,
        error: "No network port found on " + deviceName,
      };
    }

    var portName = port.getName();

    if (dhcpEnabled !== undefined && dhcpEnabled !== null) {
      device.setDhcpFlag(dhcpEnabled);
    }
    if (ipaddress && subnetMask) {
      // Retry setIpSubnetMask if port is not yet functional
      for (var retry = 0; retry < 3; retry++) {
        try {
          port.setIpSubnetMask(ipaddress, subnetMask);
          break;
        } catch (e) {
          if (retry >= 2) throw e;
          // Wait briefly and retry (PT scripting is synchronous, so this is a simple loop)
        }
      }
    }
    if (defaultGateway) port.setDefaultGateway(defaultGateway);
    if (dnsServer) port.setDnsServerIp(dnsServer);

    return {
      success: true,
      message: "IP configuration applied to " + deviceName + " on " + portName,
      port: portName,
    };
  } catch (error) {
    return fail("Error configuring PC IP", error);
  }
};

configureIosDevice = function (deviceName, commands) {
  try {
    var device = ipc.network().getDevice(deviceName);
    if (!device) return { success: false, error: "Device " + deviceName + " not found" };

    // Power on and skip boot dialog
    try { device.setPower(true); } catch (_) {}
    try { device.skipBoot(); } catch (_) {}

    var commandsArray = commands.split("\n").filter(function(c) { return c.trim(); });
    var totalConfigCommands = 0;
    for (var ci = 0; ci < commandsArray.length; ci++) {
      var t = commandsArray[ci].trim();
      if (t !== "enable" && t !== "configure terminal" && t !== "end") totalConfigCommands++;
    }

    var executedCount = 0;
    var lastError = null;
    var cl = null;

    // === Method 1 (primary): device.getCommandLine().enterCommand(cmd) ===
    // This is the API used by packet-tracer-mcp project — proven to work on PT 9/8.2.1.
    try { cl = device.getCommandLine(); } catch (_) {}
    if (cl && typeof cl.enterCommand === 'function') {
      // Dismiss boot dialog with empty commands (packet-tracer-mcp pattern)
      try { cl.enterCommand(""); } catch (_) {}
      try { cl.enterCommand("no"); } catch (_) {}
      try { cl.enterCommand(""); } catch (_) {}

      // Enter enable mode and config terminal
      try { cl.enterCommand("enable"); } catch (_) {}
      try { cl.enterCommand("terminal length 0"); } catch (_) {}
      try { cl.enterCommand("configure terminal"); } catch (_) {}
      try { cl.enterCommand("no ip domain-lookup"); } catch (_) {}

      // Send each command individually (multi-line strings cause errors in PT's script engine)
      for (var c = 0; c < commandsArray.length; c++) {
        var command = commandsArray[c].trim();
        if (command === "enable" || command === "configure terminal") continue;
        if (command === "end") continue;
        if (command) {
          try {
            cl.enterCommand(command);
            executedCount++;
          } catch (e) {
            lastError = e;
          }
        }
      }

      try { cl.enterCommand("end"); } catch (_) {}
      try { cl.enterCommand("write memory"); } catch (_) {}
    }

    // === Method 2: device.enterCommand(cmd) without mode arg ===
    if (executedCount < totalConfigCommands) {
      try {
        device.enterCommand("enable");
        device.enterCommand("configure terminal");
      } catch (_) {}
      for (var c2 = 0; c2 < commandsArray.length; c2++) {
        var cmd2 = commandsArray[c2].trim();
        if (cmd2 === "enable" || cmd2 === "configure terminal" || cmd2 === "end") continue;
        if (!cmd2) continue;
        try {
          device.enterCommand(cmd2);
          executedCount++;
        } catch (e) {
          if (lastError === null) lastError = e;
        }
      }
      try { device.enterCommand("end"); } catch (_) {}
      try { device.enterCommand("write memory"); } catch (_) {}
    }

    // === Method 3: device.cli(multiLine) fallback ===
    if (executedCount < totalConfigCommands) {
      try {
        var body = commandsArray.filter(function(c) {
          var t = c.trim();
          return t !== "enable" && t !== "configure terminal" && t !== "end";
        }).join("\n");
        if (typeof device.cli === 'function') {
          device.cli("enable\nterminal length 0\nconfigure terminal\nno ip domain-lookup\n" + body + "\nend\nwrite memory");
          executedCount = totalConfigCommands;
        }
      } catch (e) {
        if (lastError === null) lastError = e;
      }
    }

    // === Method 4: device.applyConfig() fallback ===
    if (executedCount < totalConfigCommands) {
      try {
        var body = commandsArray.filter(function(c) {
          var t = c.trim();
          return t !== "enable" && t !== "configure terminal" && t !== "end";
        }).join("\n");
        if (typeof device.applyConfig === 'function') {
          device.applyConfig(body);
          executedCount = totalConfigCommands;
        }
      } catch (e) {
        if (lastError === null) lastError = e;
      }
    }

    // === Method 5: device.configure(cmd) per command ===
    if (executedCount < totalConfigCommands) {
      for (var c3 = 0; c3 < commandsArray.length; c3++) {
        var cmd3 = commandsArray[c3].trim();
        if (cmd3 === "enable" || cmd3 === "configure terminal" || cmd3 === "end") continue;
        if (!cmd3) continue;
        try {
          if (typeof device.configure === 'function') device.configure(cmd3);
          executedCount++;
        } catch (e) {
          if (lastError === null) lastError = e;
        }
      }
    }

    // === Method 6: device.executeCommand(cmd) per command ===
    if (executedCount < totalConfigCommands) {
      for (var c4 = 0; c4 < commandsArray.length; c4++) {
        var cmd4 = commandsArray[c4].trim();
        if (cmd4 === "enable" || cmd4 === "configure terminal" || cmd4 === "end") continue;
        if (!cmd4) continue;
        try {
          if (typeof device.executeCommand === 'function') device.executeCommand(cmd4);
          executedCount++;
        } catch (e) {
          if (lastError === null) lastError = e;
        }
      }
    }

    return {
      success: executedCount > 0,
      message: "Configuration applied to " + deviceName + " (" + executedCount + " of " + totalConfigCommands + " commands" + (lastError ? ", last error: " + (lastError.message || String(lastError)) : "") + ")",
      commandsExecuted: executedCount,
    };
  } catch (error) {
    return fail("Error configuring IOS device", error);
  }
};

getNetwork = function () {
  try {
    var deviceCount = ipc.network().getDeviceCount();
    var devices = [];
    var connections = [];
    var usedPortKeys = {};

    // 先构建设备列表
    for (var nd = 0; nd < deviceCount; nd++) {
      var dev = ipc.network().getDeviceAt(nd);
      var dn = dev.getName();
      var pc = dev.getPortCount();
      var interfaces = [];
      for (var pi = 0; pi < pc; pi++) {
        var pt = dev.getPortAt(pi);
        if (pt) interfaces.push({ name: pt.getName(), in_use: false });
      }
      devices.push({ name: dn, model: dev.getModel(), type: dev.getType(), interfaces: interfaces });
    }

    // 遍历每个设备的每个端口，通过 getLink() 检查是否有连接
    for (var nd = 0; nd < deviceCount; nd++) {
      var dev = ipc.network().getDeviceAt(nd);
      var dn = dev.getName();
      var pc = dev.getPortCount();
      for (var pi = 0; pi < pc; pi++) {
        var port = dev.getPortAt(pi);
        if (!port) continue;

        var link;
        try { link = port.getLink(); } catch (_) {}
        if (!link) continue;

        var p1, p2;
        try { p1 = link.getPort1(); p2 = link.getPort2(); } catch (_) {}
        if (!p1 || !p2) continue;

        var p1n = p1.getName();
        var p2n = p2.getName();

        // 判断哪个端口是"我们"（当前设备），哪个是"对方"
        var ourPort, theirPort, ourName, theirName;
        if (p1 === port) { ourPort = p1; ourName = p1n; theirPort = p2; theirName = p2n; }
        else if (p2 === port) { ourPort = p2; ourName = p2n; theirPort = p1; theirName = p1n; }
        else {
          // 引用相等失败，用端口名做一次判断
          if (p1n === port.getName()) { ourPort = p1; ourName = p1n; theirPort = p2; theirName = p2n; }
          else if (p2n === port.getName()) { ourPort = p2; ourName = p2n; theirPort = p1; theirName = p1n; }
          else continue;
        }

        // 跳过已处理的连接
        var pairKey = dn + ":" + ourName;
        if (usedPortKeys[pairKey]) continue;

        // 在 OTHER 设备中找到 theirPort 所属的设备
        var otherDevice = null;
        // 方法1：引用相等
        for (var nd2 = 0; nd2 < deviceCount; nd2++) {
          var dev2 = ipc.network().getDeviceAt(nd2);
          var dn2 = dev2.getName();
          if (dn2 === dn) continue;
          var pc2 = dev2.getPortCount();
          for (var pj = 0; pj < pc2; pj++) {
            if (dev2.getPortAt(pj) === theirPort) {
              otherDevice = dn2;
              break;
            }
          }
          if (otherDevice) break;
        }
        // 方法2：getPort(name) 引用相等
        if (!otherDevice) {
          for (var nd2 = 0; nd2 < deviceCount; nd2++) {
            var dev2 = ipc.network().getDeviceAt(nd2);
            var dn2 = dev2.getName();
            if (dn2 === dn) continue;
            try { if (dev2.getPort(theirName) === theirPort) { otherDevice = dn2; break; } } catch (_) {}
          }
        }
        // 方法3：名字匹配（fallback）
        if (!otherDevice) {
          for (var nd2 = 0; nd2 < deviceCount; nd2++) {
            var dev2 = ipc.network().getDeviceAt(nd2);
            var dn2 = dev2.getName();
            if (dn2 === dn) continue;
            try { if (dev2.getPort(theirName)) { otherDevice = dn2; break; } } catch (_) {}
          }
        }

        if (otherDevice) {
          usedPortKeys[dn + ":" + ourName] = true;
          usedPortKeys[otherDevice + ":" + theirName] = true;
          connections.push({
            from: dn, fromInterface: ourName,
            to: otherDevice, toInterface: theirName,
            type: link.getConnectionType()
          });
        }
      }
    }

    // 更新端口 in_use 状态
    for (var i = 0; i < devices.length; i++) {
      var d = devices[i];
      for (var j = 0; j < d.interfaces.length; j++) {
        d.interfaces[j].in_use = usedPortKeys[d.name + ":" + d.interfaces[j].name] === true;
      }
    }

    return {
      success: true,
      result: {
        deviceCount: devices.length,
        connectionCount: connections.length,
        devices: devices,
        connections: connections,
      },
    };
  } catch (error) {
    return fail("", error);
  }
};

getDeviceInfo = function (deviceName) {
  try {
    var net = getNetwork();
    if (!net || !net.success) {
      return net || { success: false, error: "getNetwork failed" };
    }
    var devices = net.result.devices;
    var connections = net.result.connections;
    for (var i = 0; i < devices.length; i++) {
      if (devices[i].name === deviceName) {
        var related = [];
        for (var j = 0; j < connections.length; j++) {
          var c = connections[j];
          if (c.from === deviceName || c.to === deviceName) related.push(c);
        }
        return {
          success: true,
          result: {
            device: devices[i],
            connections: related,
          },
        };
      }
    }
    return {
      success: false,
      error: `Device ${deviceName} not found`,
    };
  } catch (error) {
    return fail("Error getting device info", error);
  }
};

removeDevice = function (deviceNames) {
  try {
    var devicesToRemove = [];
    if (typeof deviceNames === "string") {
      devicesToRemove = [deviceNames];
    } else if (Array.isArray(deviceNames)) {
      devicesToRemove = deviceNames;
    } else {
      return {
        success: false,
        error:
          "Invalid input: provide a device name string or array of device names",
      };
    }

    var workspace = ipc.appWindow().getActiveWorkspace().getLogicalWorkspace();
    var results = [];
    var successCount = 0;
    var failCount = 0;

    for (var i = 0; i < devicesToRemove.length; i++) {
      var deviceName = devicesToRemove[i];
      var device = ipc.network().getDevice(deviceName);

      if (!device) {
        results.push({
          device: deviceName,
          success: false,
          error: "Device not found",
        });
        failCount++;
      } else {
        var result = workspace.removeDevice(deviceName);

        if (result === true) {
          results.push({
            device: deviceName,
            success: true,
            message: "Removed successfully",
          });
          successCount++;
        } else {
          results.push({
            device: deviceName,
            success: false,
            error: "Failed to remove",
          });
          failCount++;
        }
      }
    }

    return {
      success: failCount === 0,
      totalDevices: devicesToRemove.length,
      successCount: successCount,
      failCount: failCount,
      results: results,
    };
  } catch (error) {
    return fail("Error removing devices", error);
  }
};

setSimulationMode = function (toSimMode) {
  try {
    var sim = ipc.simulation();
    var current = sim.isSimulationMode();
    if (current === toSimMode) {
      return {
        success: true,
        message: "Already in " + (toSimMode ? "simulation" : "realtime") + " mode",
        mode: toSimMode ? "simulation" : "realtime",
      };
    }
    sim.setSimulationMode(toSimMode);
    return {
      success: true,
      message: "Switched to " + (toSimMode ? "simulation" : "realtime") + " mode",
      mode: toSimMode ? "simulation" : "realtime",
    };
  } catch (error) {
    return fail("Error setting simulation mode", error);
  }
};

getSimulationStatus = function () {
  try {
    var sim = ipc.simulation();
    var isSimMode = sim.isSimulationMode();
    var result = { mode: isSimMode ? "simulation" : "realtime" };
    if (isSimMode) {
      result.currentTime = sim.getCurrentSimTime();
      result.frameCount = sim.getFrameInstanceCount();
      result.currentFrameIndex = sim.getCurrentFrameInstanceIndex();
    }
    return { success: true, result: result };
  } catch (error) {
    return fail("Error getting simulation status", error);
  }
};

stepSimulation = function (direction, steps) {
  try {
    var sim = ipc.simulation();
    if (!sim.isSimulationMode()) {
      return {
        success: false,
        error: "Not in simulation mode. Call setSimulationMode(true) first.",
      };
    }
    if (direction === "reset") {
      sim.resetSimulation();
      return { success: true, message: "Simulation reset" };
    }
    var n = steps && steps >= 1 ? Math.min(steps, 100) : 1;
    for (var i = 0; i < n; i++) {
      if (direction === "forward") {
        sim.forward();
      } else if (direction === "backward") {
        sim.backward();
      } else {
        return { success: false, error: "Unknown direction: " + direction };
      }
    }
    return {
      success: true,
      message: direction + " " + n + " step(s)",
      currentTime: sim.getCurrentSimTime(),
      frameCount: sim.getFrameInstanceCount(),
    };
  } catch (error) {
    return fail("Error stepping simulation", error);
  }
};

var PDU_TRAFFIC_TYPES = {
  ICMP: 0,
  TCP: 1,
  UDP: 2,
  HTTP: 17,
  HTTPS: 18,
  DNS: 19,
};

sendPdu = function (sourceDevice, destinationDevice) {
  try {
    var sim = ipc.simulation();
    var modeEnabled = false;
    if (!sim.isSimulationMode()) {
      sim.setSimulationMode(true);
      modeEnabled = true;
    }
    if (!ipc.network().getDevice(sourceDevice)) {
      return { success: false, error: "Source device not found: " + sourceDevice };
    }
    if (!ipc.network().getDevice(destinationDevice)) {
      return { success: false, error: "Destination device not found: " + destinationDevice };
    }
    var errCode = ipc.appWindow().getUserCreatedPDU().addSimplePdu(sourceDevice, destinationDevice);
    // ADD_PDU_ERROR: 0 / falsy = success
    var errStr = String(errCode);
    if (errCode && errStr !== "0") {
      return { success: false, error: "PT rejected PDU (ADD_PDU_ERROR=" + errStr + ")" };
    }
    return {
      success: true,
      message: "ICMP PDU added from " + sourceDevice + " to " + destinationDevice,
      simulationModeEnabled: modeEnabled,
    };
  } catch (error) {
    return fail("Error sending PDU", error);
  }
};

renameDevice = function (deviceName, newName) {
  try {
    var device = ipc.network().getDevice(deviceName);
    if (!device) {
      return { success: false, error: "Device not found: " + deviceName };
    }
    device.setName(newName);
    return { success: true, message: "Renamed " + deviceName + " to " + newName };
  } catch (error) {
    return fail("Error renaming device", error);
  }
};

moveDevice = function (deviceName, x, y) {
  try {
    var device = ipc.network().getDevice(deviceName);
    if (!device) {
      return { success: false, error: "Device not found: " + deviceName };
    }
    device.moveToLocation(x, y);
    return {
      success: true,
      message: "Moved " + deviceName + " to (" + x + ", " + y + ")",
    };
  } catch (error) {
    return fail("Error moving device", error);
  }
};

// Maps both numeric and C++ enum-string forms of eTrafficType to readable names.
// PT's JS host may expose the enum as "0" or as "eTrafficType_Icmp" 鈥?handle both.
var TRAFFIC_TYPE_NAMES = {
  "0": "ICMP",  "eTrafficType_Icmp": "ICMP",
  "1": "TCP",   "eTrafficType_Tcp": "TCP",
  "2": "UDP",   "eTrafficType_Udp": "UDP",
  "3": "RIPv1", "eTrafficType_RipV1": "RIPv1",
  "4": "RIPv2", "eTrafficType_RipV2": "RIPv2",
  "5": "ARP",   "eTrafficType_Arp": "ARP",
  "6": "CDP",   "eTrafficType_Cdp": "CDP",
  "7": "DHCP",  "eTrafficType_Dhcp": "DHCP",
  "11": "STP",  "eTrafficType_Stp": "STP",
  "12": "OSPF", "eTrafficType_Ospf": "OSPF",
  "13": "DTP",  "eTrafficType_Dtp": "DTP",
  "17": "HTTP", "eTrafficType_Http": "HTTP",
  "18": "HTTPS","eTrafficType_Https": "HTTPS",
  "19": "DNS",  "eTrafficType_Dns": "DNS",
  "36": "BGP",  "eTrafficType_Bgp": "BGP",
  "1000": "Custom", "eTrafficType_Custom": "Custom",
};

getPduResults = function (types) {
  try {
    var sim = ipc.simulation();
    if (!sim.isSimulationMode()) {
      return { success: false, error: "Not in simulation mode. Call setSimulationMode(true) first." };
    }

    var typeFilter = null;
    if (Array.isArray(types) && types.length > 0) {
      typeFilter = {};
      for (var t = 0; t < types.length; t++) typeFilter[types[t].toUpperCase()] = true;
    }

    var total = sim.getFrameInstanceCount();
    var frames = [];
    for (var i = 0; i < total; i++) {
      var fi = sim.getFrameInstanceAt(i);
      if (!fi) continue;

      var rawType = String(fi.getUserTrafficType());
      var typeName = TRAFFIC_TYPE_NAMES[rawType] || rawType;

      if (typeFilter && !typeFilter[typeName.toUpperCase()]) continue;

      var status = "unknown";
      if (fi.isFrameAccepted())          status = "accepted";
      else if (fi.isFrameDropped())      status = "dropped";
      else if (fi.isFrameNotForwarded()) status = "not_forwarded";
      else if (fi.isFrameUnexpected())   status = "unexpected";
      else if (fi.isFrameCollidedOnLink() || fi.isFrameCollidedAtDevice()) status = "collision";
      else if (fi.isFrameBuffered())     status = "buffered";
      else if (fi.isFrameOnTransit())    status = "in_transit";
      else if (fi.isFrameSent())         status = "sent";

      frames.push({
        index: i,
        source: fi.getSourceString(),
        destination: fi.getDestinationString(),
        trafficType: typeName,
        status: status,
      });
    }
    return {
      success: true,
      result: { totalFrames: total, shown: frames.length, frames: frames },
    };
  } catch (error) {
    return fail("Error getting PDU results", error);
  }
};

getCommandLog = function (deviceName, limit) {
  try {
    var log = ipc.commandLog();
    var total = log.getEntryCount();
    var cap = limit && limit > 0 ? Math.min(limit, 500) : 50;
    var entries = [];

    for (var i = total - 1; i >= 0 && entries.length < cap; i--) {
      var entry = log.getEntryAt(i);
      if (!entry) continue;
      var dev = entry.getDeviceName();
      if (deviceName && dev !== deviceName) continue;
      entries.push({
        timestamp: entry.getTimeToString(),
        device: dev,
        prompt: entry.getPrompt(),
        command: entry.getCommand(),
        resolvedCommand: entry.getResolvedCommand(),
      });
    }

    return {
      success: true,
      result: { totalEntries: total, returned: entries.length, entries: entries },
    };
  } catch (error) {
    return fail("Error getting command log", error);
  }
};

setPower = function (deviceName, power) {
  try {
    var device = ipc.network().getDevice(deviceName);
    if (!device) {
      return { success: false, error: "Device not found: " + deviceName };
    }
    device.setPower(power);
    return {
      success: true,
      message: deviceName + " powered " + (power ? "on" : "off"),
    };
  } catch (error) {
    return fail("Error setting device power", error);
  }
};

getRunningConfig = function (deviceName) {
  try {
    var device = ipc.network().getDevice(deviceName);
    if (!device) return { success: false, error: "Device not found: " + deviceName };

    var cl = device.getCommandLine();
    if (!cl || typeof cl.enterCommand !== 'function') {
      return { success: false, error: "Device does not support CLI: " + deviceName };
    }

    // Disable paging and get running-config
    cl.enterCommand("terminal length 0");
    var before = cl.getOutput().length;
    cl.enterCommand("show running-config");
    var output = cl.getOutput().substring(before);

    return { success: true, result: output };
  } catch (error) {
    return fail("Error getting running config", error);
  }
};

removeLink = function (links) {
  try {
    var linksToRemove = [];

    if (typeof links === "object" && links !== null && !Array.isArray(links)) {
      linksToRemove = [links];
    } else if (Array.isArray(links)) {
      linksToRemove = links;
    } else {
      return {
        success: false,
        error:
          "Invalid input: provide link object {device, port} or array of link objects",
      };
    }

    var workspace = ipc.appWindow().getActiveWorkspace().getLogicalWorkspace();
    var results = [];
    var successCount = 0;
    var failCount = 0;

    for (var i = 0; i < linksToRemove.length; i++) {
      var link = linksToRemove[i];
      var deviceName = link.device || link.deviceName;
      var portName = link.port || link.portName;

      if (!deviceName || !portName) {
        results.push({
          device: deviceName,
          port: portName,
          success: false,
          error: "Missing device or port",
        });
        failCount++;
        continue;
      }

      var device = ipc.network().getDevice(deviceName);
      if (!device) {
        results.push({
          device: deviceName,
          port: portName,
          success: false,
          error: "Device not found",
        });
        failCount++;
        continue;
      }

      var result = workspace.deleteLink(deviceName, portName);

      if (result === true) {
        results.push({
          device: deviceName,
          port: portName,
          success: true,
          message: "Link removed successfully",
        });
        successCount++;
      } else {
        results.push({
          device: deviceName,
          port: portName,
          success: false,
          error: "Failed to remove link",
        });
        failCount++;
      }
    }

    return {
      success: failCount === 0,
      totalLinks: linksToRemove.length,
      successCount: successCount,
      failCount: failCount,
      results: results,
    };
  } catch (error) {
    return fail("Error removing links", error);
  }
};
