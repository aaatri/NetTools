// PT-side runCode — evaluates a JS string and returns a {success, result, code} envelope.

function runCode(scriptText) {
  try {
    var wrapped = "(function(){" + scriptText + "})()";
    return { success: true, result: eval(wrapped), code: scriptText };
  } catch (error) {
    return {
      success: false,
      error: error.message || String(error),
      errorType: error.name || "Error",
      code: scriptText,
    };
  }
}
