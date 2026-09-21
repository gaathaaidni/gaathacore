async function adjustStock(id, form){
  const data = new FormData(form);
  await fetch(`/items/${id}/adjust`, {method:'POST', body:data});
  location.reload();
}
async function deleteItem(id){ if(!confirm('Delete item?')) return; await apiDelete(`/inventory/item/${id}/delete`); }
async function adjustStock(form){ const data = Object.fromEntries(new FormData(form)); const resp = await postJSON('/inventory/adjust-stock', data); console.log(resp);}