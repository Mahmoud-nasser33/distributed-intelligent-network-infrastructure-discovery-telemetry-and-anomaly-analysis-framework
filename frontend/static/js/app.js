var API = '/api';

function get(path, callback, errback) {
  fetch(API + path)
    .then(function(r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(callback)
    .catch(errback);
}

function post(path, data, callback, errback) {
  fetch(API + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
    .then(function(r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(callback)
    .catch(errback);
}

function $(id) { return document.getElementById(id); }

function badge(status) {
  return '<span class="badge badge-' + (status || 'unknown') + '">' + (status || 'unknown') + '</span>';
}

function time(s) {
  if (!s) return '—';
  return new Date(s).toLocaleString();
}

function safe(s) {
  if (!s) return '';
  var d = document.createElement('div');
  d.textContent = String(s);
  return d.innerHTML;
}

function loading(id, msg) {
  $(id).innerHTML = '<div class="loading"><div class="spinner"></div><p>' + (msg || 'Loading...') + '</p></div>';
}

function empty(id, msg) {
  $(id).innerHTML = '<div class="empty">' + msg + '</div>';
}

function error(id, msg) {
  $(id).innerHTML = '<div class="error"><p>' + safe(msg) + '</p></div>';
}
