async function postComment(form){
  const data = new FormData(form);
  await fetch(location.pathname, {method:'POST', body:data});
  location.reload();
}
async function deleteTicket(id){ if(!confirm('Delete ticket?')) return; await apiDelete(`/desk/ticket/${id}/delete`); }
