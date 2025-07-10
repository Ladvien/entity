var PluginVisualizer = (() => {
  var __create = Object.create;
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __getProtoOf = Object.getPrototypeOf;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __require = /* @__PURE__ */ ((x) => typeof require !== "undefined" ? require : typeof Proxy !== "undefined" ? new Proxy(x, {
    get: (a, b) => (typeof require !== "undefined" ? require : a)[b]
  }) : x)(function(x) {
    if (typeof require !== "undefined") return require.apply(this, arguments);
    throw Error('Dynamic require of "' + x + '" is not supported');
  });
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
    // If the importer is in node compatibility mode or this is not an ESM
    // file that has been converted to a CommonJS file using a Babel-
    // compatible transform (i.e. "__esModule" has not been set), then set
    // "default" to the CommonJS "module.exports" for node compatibility.
    isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
    mod
  ));
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // docs/src/components/PluginVisualizer.tsx
  var PluginVisualizer_exports = {};
  __export(PluginVisualizer_exports, {
    initVisualizer: () => initVisualizer
  });
  var import_react = __toESM(__require("react"));
  var import_client = __toESM(__require("react-dom/client"));
  var defaultPipeline = {
    SETUP: ["LoadConfig", "InitMemory"],
    DO: ["Reason", "Plan"],
    DELIVER: ["Respond"]
  };
  var PluginVisualizer = () => {
    const [pipeline, setPipeline] = (0, import_react.useState)(defaultPipeline);
    const [dragInfo, setDragInfo] = (0, import_react.useState)(null);
    const handleDragStart = (stage, index) => (e) => {
      setDragInfo({ stage, index });
      e.dataTransfer.effectAllowed = "move";
    };
    const handleDrop = (stage, index) => (e) => {
      e.preventDefault();
      if (!dragInfo) return;
      const plugin = pipeline[dragInfo.stage][dragInfo.index];
      const newPipeline = { ...pipeline };
      newPipeline[dragInfo.stage] = newPipeline[dragInfo.stage].filter((_, i) => i !== dragInfo.index);
      if (index === void 0) {
        newPipeline[stage].push(plugin);
      } else {
        newPipeline[stage].splice(index, 0, plugin);
      }
      setPipeline(newPipeline);
      setDragInfo(null);
    };
    const handleDragOver = (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
    };
    return /* @__PURE__ */ import_react.default.createElement("div", { className: "pipeline" }, Object.entries(pipeline).map(([stage, plugins]) => /* @__PURE__ */ import_react.default.createElement("div", { key: stage, className: "stage", onDragOver: handleDragOver, onDrop: handleDrop(stage) }, /* @__PURE__ */ import_react.default.createElement("h3", null, stage), plugins.map((plugin, index) => /* @__PURE__ */ import_react.default.createElement(
      "div",
      {
        key: `${stage}-${plugin}-${index}`,
        className: "plugin",
        draggable: true,
        onDragStart: handleDragStart(stage, index),
        onDrop: handleDrop(stage, index),
        onDragOver: handleDragOver
      },
      plugin
    )))));
  };
  function initVisualizer(elementId) {
    const container = document.getElementById(elementId);
    if (!container) return;
    const root = import_client.default.createRoot(container);
    root.render(/* @__PURE__ */ import_react.default.createElement(PluginVisualizer, null));
  }
  initVisualizer("plugin-visualizer");
  return __toCommonJS(PluginVisualizer_exports);
})();
