// Simple, safe templating: replaces {{var}} with values from vars (supports dot paths)
(function(){
  function getPath(obj, path) {
    try {
      return path.split('.').reduce((acc, key) => (acc && acc[key] != null ? acc[key] : undefined), obj);
    } catch (_) { return undefined; }
  }

  function renderTemplate(template, vars) {
    if (typeof template !== 'string') return '';
    return template.replace(/\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}/g, (m, key) => {
      const v = getPath(vars || {}, key);
      if (v == null) return '';
      return String(v);
    });
  }

  // Expose for browser and Node
  if (typeof window !== 'undefined') window.CGTemplate = { renderTemplate };
  module.exports = { renderTemplate };
})();

