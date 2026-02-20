// Simple AJAX helpers using jQuery and JSON conventions
(function(window, $){
  if (!$) return;

  function ensureSpinner(){
    if ($('#__global_ajax_spinner').length) return;
    const el = $('<div id="__global_ajax_spinner" style="position:fixed;z-index:99999;top:0;left:0;right:0;bottom:0;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,0.12)">')
      .append('<div style="background:#fff;padding:12px 16px;border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,0.12);font-weight:600">Loading...</div>');
    $('body').append(el);
  }

  function showLoading(){ ensureSpinner(); $('#__global_ajax_spinner').show(); }
  function hideLoading(){ $('#__global_ajax_spinner').hide(); }

  function apiAjax(opts){
    opts = opts || {};
    const dataObj = opts.data;
    // default JSON handling for non-multipart POSTs
    if (opts.type && opts.type.toUpperCase() !== 'GET' && !(opts.processData === false) && opts.contentType === undefined){
      opts.contentType = 'application/json';
      try { opts.data = JSON.stringify(dataObj); } catch(e) { /* leave as-is */ }
    }
    opts.dataType = opts.dataType || 'json';
    const userBefore = opts.beforeSend;
    const userComplete = opts.complete;
    opts.beforeSend = function(){ showLoading(); if (typeof userBefore === 'function') userBefore.apply(this, arguments); };
    opts.complete = function(){ hideLoading(); if (typeof userComplete === 'function') userComplete.apply(this, arguments); };
    return $.ajax(opts);
  }

  window.ajaxHelpers = {
    showLoading, hideLoading, apiAjax
  };
})(window, window.jQuery);
