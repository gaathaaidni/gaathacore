async function apiDelete(url){
  const resp = await fetch(url, {method: 'POST'});
  if(resp.ok) window.location.reload();
  else alert('Delete failed');
}

async function postJSON(url, data){
  const resp = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data)});
  return resp.json();
}
